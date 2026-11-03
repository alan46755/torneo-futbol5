"""ABM de sanciones. Las automáticas (roja / amarillas) las crea la base;
desde aquí se gestionan las disciplinarias."""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from comun import mostrar_errores, torneo_seleccionado
from db import ErrorBD, consultar, ejecutar
from seguridad import solo_admin
from validaciones import Validador

bp = Blueprint("sanciones", __name__, url_prefix="/sanciones")


def _jugadores_torneo(id_torneo):
    return consultar("""SELECT j.ci, j.nombre, j.apellido, e.nombre AS equipo
                          FROM equipo_jugador_torneo ejt JOIN jugador j ON j.ci = ejt.ci_jugador
                          JOIN equipo e ON e.id_equipo = ejt.id_equipo
                         WHERE ejt.id_torneo = %s ORDER BY e.nombre, j.apellido""", (id_torneo,))


def _validar(form, jugadores, con_jugador=True):
    v = Validador(form)
    if con_jugador:
        v.opcion("ci_jugador", "El jugador", [j["ci"] for j in jugadores])
    v.entero("numero_fecha_inicio", "La fecha de inicio", 1, 51)
    v.entero("cantidad_fechas", "La cantidad de fechas", 1, 20)
    v.texto("observaciones", "El detalle", 5, 255)
    return v


@bp.route("/")
@solo_admin
def lista():
    t = torneo_seleccionado()
    motivo = request.args.get("motivo")
    sql = "SELECT * FROM v_sancion_detalle WHERE id_torneo = %s"
    params = [t["id_torneo"]] if t else [0]
    if motivo in ("roja", "acumulacion_amarillas", "disciplinaria"):
        sql += " AND motivo = %s"
        params.append(motivo)
    sql += " ORDER BY numero_fecha_inicio DESC, equipo, apellido"
    return render_template("sanciones/lista.html", filas=consultar(sql, params), torneo=t, motivo=motivo)


@bp.route("/nueva", methods=["GET", "POST"])
@solo_admin
def nueva():
    t = torneo_seleccionado() or abort(404)
    jugadores = _jugadores_torneo(t["id_torneo"])
    if request.method == "POST":
        v = _validar(request.form, jugadores)
        if v.ok:
            d = v.datos
            try:
                ejecutar("""INSERT INTO sancion_jugador (ci_jugador, id_torneo, motivo, numero_fecha_inicio,
                                                         cantidad_fechas, observaciones)
                            VALUES (%s, %s, 'disciplinaria', %s, %s, %s)""",
                         (d["ci_jugador"], t["id_torneo"], d["numero_fecha_inicio"], d["cantidad_fechas"],
                          d["observaciones"]))
                flash("Sanción disciplinaria registrada.", "ok")
                return redirect(url_for(".lista"))
            except ErrorBD as e:
                v.error(str(e))
        mostrar_errores(v.errores)
    return render_template("sanciones/form.html", s=request.form, jugadores=jugadores, torneo=t, nuevo=True)


@bp.route("/<int:id_sancion>/editar", methods=["GET", "POST"])
@solo_admin
def editar(id_sancion):
    s = consultar("SELECT * FROM v_sancion_detalle WHERE id_sancion = %s", (id_sancion,), uno=True) or abort(404)
    if s["motivo"] != "disciplinaria":
        flash("Las sanciones automáticas se corrigen eliminando la tarjeta desde la planilla del partido.", "error")
        return redirect(url_for(".lista"))
    if request.method == "POST":
        v = _validar(request.form, [], con_jugador=False)
        if v.ok:
            d = v.datos
            try:
                ejecutar("UPDATE sancion_jugador SET numero_fecha_inicio=%s, cantidad_fechas=%s, observaciones=%s "
                         "WHERE id_sancion=%s",
                         (d["numero_fecha_inicio"], d["cantidad_fechas"], d["observaciones"], id_sancion))
                flash("Sanción actualizada.", "ok")
                return redirect(url_for(".lista"))
            except ErrorBD as e:
                v.error(str(e))
        mostrar_errores(v.errores)
        s = {**s, **request.form}
    return render_template("sanciones/form.html", s=s, jugadores=[], torneo=None, nuevo=False)


@bp.route("/<int:id_sancion>/eliminar", methods=["POST"])
@solo_admin
def eliminar(id_sancion):
    try:
        n = ejecutar("DELETE FROM sancion_jugador WHERE id_sancion = %s AND motivo = 'disciplinaria'", (id_sancion,))
        flash("Sanción eliminada." if n else "Solo pueden eliminarse sanciones disciplinarias.", "ok" if n else "error")
    except ErrorBD as e:
        flash(str(e), "error")
    return redirect(url_for(".lista"))
