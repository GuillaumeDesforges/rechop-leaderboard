$("#submit").click(function(event) {
    event.preventDefault();
    var name = $("#name").val();
    var solution = $("#solution").val();
    $.post("./submit", { name: name, solution: solution }, function (data) {
        alert("Solution bien reçue !")
        location.reload();
    }).fail(function() {
        alert("Impossible de poster cette solution !");
    });
});
