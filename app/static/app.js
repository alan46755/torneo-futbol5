// Validaciones del lado del cliente (primera capa; el backend y la base vuelven a validar).
(function () {
  "use strict";

  // Confirmación antes de acciones destructivas
  document.querySelectorAll("form[data-confirmar]").forEach(function (f) {
    f.addEventListener("submit", function (e) {
      if (!window.confirm(f.dataset.confirmar)) e.preventDefault();
    });
  });

  // Cédula uruguaya: dígito verificador
  function ciValida(valor) {
    var ci = (valor || "").replace(/[.\-\s]/g, "");
    if (!/^\d{7,8}$/.test(ci)) return false;
    ci = ci.padStart(8, "0");
    var pesos = "2987634", suma = 0;
    for (var i = 0; i < 7; i++) suma += parseInt(ci[i], 10) * parseInt(pesos[i], 10);
    return (10 - (suma % 10)) % 10 === parseInt(ci[7], 10);
  }
  document.querySelectorAll("input[data-ci]").forEach(function (inp) {
    inp.addEventListener("input", function () {
      inp.setCustomValidity(inp.value && !ciValida(inp.value) ? "Cédula inválida: revise el dígito verificador." : "");
    });
  });

  // Edad mínima
  document.querySelectorAll("input[data-edad-min]").forEach(function (inp) {
    inp.addEventListener("change", function () {
      var min = parseInt(inp.dataset.edadMin, 10), msg = "";
      if (inp.value) {
        var n = new Date(inp.value + "T00:00:00"), h = new Date();
        var edad = h.getFullYear() - n.getFullYear() - ((h.getMonth() < n.getMonth() || (h.getMonth() === n.getMonth() && h.getDate() < n.getDate())) ? 1 : 0);
        if (edad < min || edad > 100) msg = "El jugador debe tener entre " + min + " y 100 años.";
      }
      inp.setCustomValidity(msg);
    });
  });

  // Rango de fechas (inicio < fin)
  document.querySelectorAll("input[data-antes-de]").forEach(function (ini) {
    var fin = document.getElementById(ini.dataset.antesDe);
    function check() {
      fin.setCustomValidity(ini.value && fin.value && fin.value <= ini.value ? "La fecha de fin debe ser posterior a la de inicio." : "");
    }
    ini.addEventListener("change", check);
    fin.addEventListener("change", check);
  });

  // Partido: local distinto de visitante
  document.querySelectorAll("form[data-partido]").forEach(function (f) {
    var l = f.querySelector("#id_equipo_local"), v = f.querySelector("#id_equipo_visitante");
    function check() {
      v.setCustomValidity(l.value && l.value === v.value ? "Un equipo no puede enfrentarse a sí mismo." : "");
    }
    l.addEventListener("change", check);
    v.addEventListener("change", check);
  });
})();
