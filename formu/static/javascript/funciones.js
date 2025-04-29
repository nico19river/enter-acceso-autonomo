function actualizarModelos() {
    var marcaSelect = document.getElementById("marca");
    var modeloSelect = document.getElementById("modelo");
    var marca = marcaSelect.value;

    modeloSelect.innerHTML = "";

    var modelosPorMarca = {
        "Toyota": ["Corolla", "Hilux", "Etios"],
        "Ford": ["Focus", "Ranger", "Ka"],
        "Chevrolet": ["Cruze", "Tracker", "Onix"]
    };

    if (modelosPorMarca[marca]) {
        modelosPorMarca[marca].forEach(function(modelo) {
            var opcion = document.createElement("option");
            opcion.value = modelo;
            opcion.textContent = modelo;
            modeloSelect.appendChild(opcion);
        });
    }
}
