"""ABM de facultades (dato maestro)."""
from flask import Blueprint, flash, redirect, render_template, request, url_for

from comun import mostrar_errores
from db import ErrorBD, consultar, ejecutar
from seguridad import solo_admin
from validaciones import Validador

bp = Blueprint("facultades", __name__, url_prefix="/facultades")


@bp.route("/", methods=["GET", "POST"])
@solo_admin
def lista():
    if request.method == "POST":           # alta
        v = Validador(request.form)
        nombre = v.texto("nombre", "El nombre", 3, 100)
        if v.ok:
            try:
                ejecutar("INSERT INTO facultad (nombre) VALUES (%s)", (nombre,))
                flash("Facultad creada.", "ok")
                return redirect(url_for(".lista"))
            except ErrorBD as e:
                v.error(str(e))
        mostrar_errores(v.errores)
    filas = consultar("""
        SELECT f.id_facultad, f.nombre,
               (SELECT COUNT(*) FROM jugador j WHERE j.id_facultad = f.id_facultad) AS jugadores,
               (SELECT COUNT(*) FROM equipo e WHERE e.id_facultad = f.id_facultad) AS equipos
          FROM facultad f ORDER BY f.nombre""")
    return render_template("facultades.html", filas=filas)


@bp.route("/<int:id_facultad>/editar", methods=["POST"])
@solo_admin
def editar(id_facultad):
    v = Validador(request.form)
    nombre = v.texto("nombre", "El nombre", 3, 100)
    if v.ok:
        try:
            ejecutar("UPDATE facultad SET nombre = %s WHERE id_facultad = %s", (nombre, id_facultad))
            flash("Facultad actualizada.", "ok")
        except ErrorBD as e:
            v.error(str(e))
    mostrar_errores(v.errores)
    return redirect(url_for(".lista"))


@bp.route("/<int:id_facultad>/eliminar", methods=["POST"])
@solo_admin
def eliminar(id_facultad):
    try:
        ejecutar("DELETE FROM facultad WHERE id_facultad = %s", (id_facultad,))
        flash("Facultad eliminada.", "ok")
    except ErrorBD as e:
        flash(str(e), "error")
    return redirect(url_for(".lista"))
