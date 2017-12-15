# par Guillaume DESFORGES

from flask import Flask, render_template, request
from datetime import datetime
import csv
import pandas as pd
import traceback


# ============= RECHOP

instance = "versaillesOpt"
df_fenetres = pd.read_csv("instances/"+instance+"_fenetres.csv", header=1, index_col=0, sep='\s*,\s*', engine='python')
df_gauches = pd.read_csv("instances/"+instance+"_voletsGauches.csv", header=1, index_col=0, sep='\s*,\s*', engine='python')
df_droites = pd.read_csv("instances/"+instance+"_voletsDroits.csv", header=1, index_col=0, sep='\s*,\s*', engine='python')

class Fenetre:
    def __init__(self, index, hauteur_totale, hauteur_gauche_intergonds, hauteur_gauche_gondsommet, hauteur_droite_intergonds, hauteur_droite_gondsommet, largeur):
        self.index = index
        self.hauteur_totale = hauteur_totale
        self.hauteur_gauche_intergonds = hauteur_gauche_intergonds
        self.hauteur_gauche_gondsommet = hauteur_gauche_gondsommet
        self.hauteur_droite_intergonds = hauteur_droite_intergonds
        self.hauteur_droite_gondsommet = hauteur_droite_gondsommet
        self.largeur = largeur

    def __str__(self):
        return str(self.index)

    def __format__(self):
        return str(self.index)


class Volet:
    def __init__(self, index, hauteur_totale, hauteur_intergonds, hauteur_gondsommet, largeur):
        self.index = index
        self.hauteur_totale = hauteur_totale
        self.hauteur_intergonds = hauteur_intergonds
        self.hauteur_gondsommet = hauteur_gondsommet
        self.largeur = largeur

    def __str__(self):
        return str(self.index)

    def __format__(self):
        return str(self.index)

fenetres = [Fenetre(fenetre_row.Index,
                    fenetre_row.hauteurTotale,
                    fenetre_row.hauteurInterGondsGauche,
                    fenetre_row.hauteurGondSommetGauche,
                    fenetre_row.hauteurInterGondsDroite,
                    fenetre_row.hauteurGondSommetDroite,
                    fenetre_row.largeurTotale
                   )
            for fenetre_row in df_fenetres.itertuples()]

gauches = [Volet(gauche_row.Index,
                    gauche_row.hauteurTotale,
                    gauche_row.hauteurInterGonds,
                    gauche_row.hauteurGondSommet,
                    gauche_row.largeur
                   )
            for gauche_row in df_gauches.itertuples()]

droites = [Volet(droite_row.Index,
                    droite_row.hauteurTotale,
                    droite_row.hauteurInterGonds,
                    droite_row.hauteurGondSommet,
                    droite_row.largeur
                   )
            for droite_row in df_droites.itertuples()]

assert(len(fenetres) > 0)
assert(len(gauches) > 0)
assert(len(droites) > 0)

def cost(fenetre, gauche, droite):
    c = 0
    if fenetre.largeur < gauche.largeur + droite.largeur:
        c += 1
    if gauche.hauteur_intergonds + gauche.hauteur_gondsommet > fenetre.hauteur_gauche_intergonds + fenetre.hauteur_gauche_gondsommet or gauche.hauteur_gondsommet > fenetre.hauteur_gauche_gondsommet:
        c += 1
    if gauche.hauteur_totale - (gauche.hauteur_intergonds + gauche.hauteur_gondsommet) > fenetre.hauteur_totale - (fenetre.hauteur_gauche_intergonds+fenetre.hauteur_gauche_gondsommet) and gauche.hauteur_totale - gauche.hauteur_gondsommet > fenetre.hauteur_totale - fenetre.hauteur_gauche_gondsommet:
        c += 1
    if droite.hauteur_intergonds + droite.hauteur_gondsommet > fenetre.hauteur_droite_intergonds + fenetre.hauteur_droite_gondsommet or droite.hauteur_gondsommet > fenetre.hauteur_droite_gondsommet:
        c += 1
    if droite.hauteur_totale - (droite.hauteur_intergonds + droite.hauteur_gondsommet) > fenetre.hauteur_totale - (fenetre.hauteur_droite_intergonds+fenetre.hauteur_droite_gondsommet) and droite.hauteur_totale - droite.hauteur_gondsommet > fenetre.hauteur_totale - fenetre.hauteur_droite_gondsommet:
        c += 1
    return c


# ============= WEB

# Init
app = Flask(__name__, static_url_path='/static')
ranking = []
with open('data/ranking.csv', 'r') as file:
    ranking_reader = csv.reader(file, delimiter=',')
    for row in ranking_reader:
        rank = int(row[0])
        name = row[1]
        score = int(row[2])
        date = row[3]
        ranking.append({
            'rank': rank,
            'name': name,
            'score': score,
            'date': date
        })

@app.route('/')
def index():
    return render_template('index.html', ranking=ranking)

def parse_solution(solution):
    solution_reader = csv.reader([line for line in solution.split('\n') if line != ""])
    solution_fenetres, solution_gauches, solution_droites = [], [], []
    for row in solution_reader:
        f, g, d = int(row[0]), int(row[1]), int(row[2])
        solution_fenetres.append(fenetres[f])
        solution_gauches.append(gauches[g])
        solution_droites.append(droites[d])
    return solution_fenetres, solution_gauches, solution_droites

def verify_solution(solution_fenetres, solution_gauches, solution_droites):
    N = len(fenetres)
    for i in range(N):
        if solution_fenetres.count(fenetres[i]) != 1:
            raise Exception("Invalid count fenetre {}".format(i))
        if solution_gauches.count(gauches[i]) != 1:
            raise Exception("Invalid count volet gauche {}".format(i))
        if solution_droites.count(droites[i]) != 1:
            raise Exception("Invalid count volet droit {}".format(i))
    return True

def solution_cost(solution_fenetres, solution_gauches, solution_droites):
    return sum([cost(fenetre, gauche, droite)
                    for fenetre, gauche, droite
                    in zip(solution_fenetres, solution_gauches, solution_droites)])


def add_submission(name, score):
    date = datetime.now().strftime('%d/%m/%Y')
    item = {
        'name': name,
        'score': score,
        'date': date
    }
    ranking.append(item)
    ranking.sort(key=lambda x: x['score'])
    for i, item in enumerate(ranking):
        item['rank'] = i+1

@app.route('/submit', methods=['POST'])
def new_submission():
    name = request.form['name']
    solution = request.form['solution']
    if name == '' or solution == '':
        return "Invalid inputs", 400
    try:
        solution_fenetres, solution_gauches, solution_droites = parse_solution(solution)
        verify_solution(solution_fenetres, solution_gauches, solution_droites)
        score = solution_cost(solution_fenetres, solution_gauches, solution_droites)
    except Exception as e:
        traceback.print_tb(e.__traceback__)
        return "Invalid solution given", 400
    add_submission(name, score)
    with open('data/ranking.csv', 'w') as file:
        ranking_writer = csv.writer(file)
        for item in ranking:
            ranking_writer.writerow([item['rank'], item['name'], item['score'], item['date']])
    return "Submission added", 200
