"""ABM de ediciones del torneo y cambio de etapa."""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from comun import mostrar_errores
from db import ErrorBD, consultar, ejecutar
from seguridad import solo_admin
from validaciones import Validador

bp = Blueprint("torneos", __name__, url_prefix="/torneos")

SIGUIENTE_ESTADO = {"inscripcion": "en_curso", "en_curso": "finalizado"}


def _validar(form):
    v = Validador(form)
    v.texto("nombre", "El nombre", 3, 100)
    v.entero("anio", "El año", 2000, 2100)
    v.opcion("semestre", "El semestre", [1, 2])
    ini = v.fecha("fecha_inicio", "La fecha de inicio")
    fin = v.fecha("fecha_fin", "La fecha de fin")
    if ini and fin and fin <= ini:
        v.error("La fecha de fin debe ser posterior a la de inicio.")
    return v


@bp.route("/")
@solo_admin
def lista():
    filas = consultar("""
        SELECT t.*, (SELECT COUNT(*) FROM equipo e WHERE e.id_torneo = t.id_torneo) AS equipos,
               (SELECT COUNT(*) FROM partido p WHERE p.id_torneo = t.id_torneo) AS partidos
          FROM torneo t ORDER BY anio DESC, semestre DESC""")
    return render_template("torneos/lista.html", filas=filas, siguiente=SIGUIENTE_ESTADO)


@bp.route("/nuevo", methods=["GET", "POST"])
@solo_admin
def nuevo():
    if request.method == "POST":
        v = _validar(request.form)
        if v.ok:
            d = v.datos
            try:
                ejecutar("INSERT INTO torneo (nombre, anio, semestre, fecha_inicio, fecha_fin) "
                         "VALUES (%s, %s, %s, %s, %s)",
                         (d["nombre"], d["anio"], d["semestre"], d["fecha_inicio"], d["fecha_fin"]))
                flash("Torneo creado en etapa de inscripción.", "ok")
                return redirect(url_for(".lista"))
            except ErrorBD as e:
                v.error(str(e))
        mostrar_errores(v.errores)
    return render_template("torneos/form.html", t=request.form, nuevo=True)


@bp.route("/<int:id_torneo>/editar", methods=["GET", "POST"])
@solo_admin
def editar(id_torneo):
    t = consultar("SELECT * FROM torneo WHERE id_torneo = %s", (id_torneo,), uno=True) or abort(404)
    if request.method == "POST":
        v = _validar(request.form)
        if v.ok:
            d = v.datos
            try:
                ejecutar("UPDATE torneo SET nombre=%s, anio=%s, semestre=%s, fecha_inicio=%s, fecha_fin=%s "
                         "WHERE id_torneo=%s",
                         (d["nombre"], d["anio"], d["semestre"], d["fecha_inicio"], d["fecha_fin"], id_torneo))
                flash("Torneo actualizado.", "ok")
                return redirect(url_for(".lista"))
            except ErrorBD as e:
                v.error(str(e))
        mostrar_errores(v.errores)
        t = {**t, **request.form}
    return render_template("torneos/form.html", t=t, nuevo=False)


@bp.route("/<int:id_torneo>/avanzar", methods=["POST"])
@solo_admin
def avanzar(id_torneo):
    t = consultar("SELECT estado FROM torneo WHERE id_torneo = %s", (id_torneo,), uno=True) or abort(404)
    nuevo_estado = SIGUIENTE_ESTADO.get(t["estado"])
    if not nuevo_estado:
        flash("El torneo ya está finalizado.", "error")
    else:
        try:
            ejecutar("UPDATE torneo SET estado = %s WHERE id_torneo = %s", (nuevo_estado, id_torneo))
            flash("Etapa del torneo actualizada.", "ok")
        except ErrorBD as e:
            flash(str(e), "error")
    return redirect(url_for(".lista"))


@bp.route("/<int:id_torneo>/eliminar", methods=["POST"])
@solo_admin
def eliminar(id_torneo):
    try:
        ejecutar("DELETE FROM torneo WHERE id_torneo = %s", (id_torneo,))
        flash("Torneo eliminado.", "ok")
    except ErrorBD as e:
        flash(str(e), "error")
    return redirect(url_for(".lista"))
