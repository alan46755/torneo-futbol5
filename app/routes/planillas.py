"""Registro de planillas de juego, goles y tarjetas (administradores y planilleros)."""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from comun import mostrar_errores, torneo_seleccionado
from db import ErrorBD, consultar, ejecutar, transaccion
from routes.partidos import SQL_PARTIDOS
from seguridad import rol_requerido
from validaciones import Validador

bp = Blueprint("planillas", __name__, url_prefix="/planillas")
acceso = rol_requerido("administrador", "planillero")


def _partido(id_partido):
    p = consultar(SQL_PARTIDOS + " WHERE p.id_partido = %s", (id_partido,), uno=True) or abort(404)
    p["editable"] = bool((p["estado"] == "programado" and p["comenzo"])
                         or (p["estado"] == "jugado" and p["en_ventana"]))
    return p


def _volver(id_partido):
    return redirect(url_for(".detalle", id_partido=id_partido))


@bp.route("/")
@acceso
def lista():
    t = torneo_seleccionado()
    filas = consultar(SQL_PARTIDOS + """ WHERE p.id_torneo = %s AND p.estado IN ('programado', 'jugado')
                                         ORDER BY (p.estado = 'programado' AND TIMESTAMP(p.dia, t.hora_inicio) <= NOW()) DESC,
                                                  p.dia DESC, t.hora_inicio""", (t["id_torneo"],)) if t else []
    return render_template("planillas/lista.html", filas=filas, torneo=t)


@bp.route("/<int:id_partido>")
@acceso
def detalle(id_partido):
    p = _partido(id_partido)
    equipos = []
    for id_eq, nombre in ((p["id_equipo_local"], p["local"]), (p["id_equipo_visitante"], p["visitante"])):
        plantel = consultar("""
            SELECT j.ci, j.nombre, j.apellido, ejt.numero_camiseta,
                   (pp.ci_jugador IS NOT NULL) AS en_planilla,
                   fn_jugador_suspendido(j.ci, %s, %s) AS suspendido,
                   (e.ci_capitan = j.ci) AS capitan
              FROM equipo_jugador_torneo ejt
              JOIN jugador j ON j.ci = ejt.ci_jugador
              JOIN equipo e ON e.id_equipo = ejt.id_equipo
              LEFT JOIN planilla_partido pp ON pp.id_partido = %s AND pp.ci_jugador = j.ci
             WHERE ejt.id_equipo = %s ORDER BY ejt.numero_camiseta""",
                            (p["id_torneo"], p["numero_fecha"], id_partido, id_eq))
        equipos.append({"id": id_eq, "nombre": nombre, "plantel": plantel})
    goles = consultar("""
        SELECT g.*, j.nombre, j.apellido, e.nombre AS equipo
          FROM gol g JOIN jugador j ON j.ci = g.ci_jugador
          JOIN planilla_partido pp ON pp.id_partido = g.id_partido AND pp.ci_jugador = g.ci_jugador
          JOIN equipo e ON e.id_equipo = pp.id_equipo
         WHERE g.id_partido = %s ORDER BY g.minuto""", (id_partido,))
    tarjetas = consultar("""
        SELECT t.*, j.nombre, j.apellido, e.nombre AS equipo
          FROM tarjeta t JOIN jugador j ON j.ci = t.ci_jugador
          JOIN planilla_partido pp ON pp.id_partido = t.id_partido AND pp.ci_jugador = t.ci_jugador
          JOIN equipo e ON e.id_equipo = pp.id_equipo
         WHERE t.id_partido = %s ORDER BY t.minuto""", (id_partido,))
    en_planilla = [dict(j, equipo=eq["nombre"]) for eq in equipos for j in eq["plantel"] if j["en_planilla"]]
    return render_template("planillas/detalle.html", p=p, equipos=equipos, goles=goles,
                           tarjetas=tarjetas, en_planilla=en_planilla)


@bp.route("/<int:id_partido>/jugadores", methods=["POST"])
@acceso
def guardar_jugadores(id_partido):
    p = _partido(id_partido)
    validos = {}
    for id_eq in (p["id_equipo_local"], p["id_equipo_visitante"]):
        for r in consultar("SELECT ci_jugador FROM equipo_jugador_torneo WHERE id_equipo = %s", (id_eq,)):
            validos[r["ci_jugador"]] = id_eq
    elegidos = set(request.form.getlist("jugadores"))
    if not elegidos <= set(validos):
        abort(400, "Jugadores inválidos para este partido.")
    actuales = {r["ci_jugador"] for r in consultar(
        "SELECT ci_jugador FROM planilla_partido WHERE id_partido = %s", (id_partido,))}
    try:
        with transaccion() as cur:
            for ci in actuales - elegidos:
                cur.execute("DELETE FROM planilla_partido WHERE id_partido = %s AND ci_jugador = %s",
                            (id_partido, ci))
            for ci in elegidos - actuales:
                cur.execute("INSERT INTO planilla_partido (id_partido, ci_jugador, id_equipo) VALUES (%s, %s, %s)",
                            (id_partido, ci, validos[ci]))
        flash("Planilla guardada.", "ok")
    except ErrorBD as e:
        flash(f"No se guardaron los cambios: {e}", "error")
    return _volver(id_partido)


@bp.route("/<int:id_partido>/goles", methods=["POST"])
@acceso
def agregar_gol(id_partido):
    v = Validador(request.form)
    ci = v.ci("ci_jugador", "El jugador")
    minuto = v.entero("minuto", "El minuto", 1, 60)
    autogol = v.booleano("autogol")
    if v.ok:
        try:
            ejecutar("INSERT INTO gol (id_partido, ci_jugador, minuto, autogol) VALUES (%s, %s, %s, %s)",
                     (id_partido, ci, minuto, autogol))
            flash("Gol registrado.", "ok")
        except ErrorBD as e:
            v.error(str(e))
    mostrar_errores(v.errores)
    return _volver(id_partido)


@bp.route("/<int:id_partido>/goles/<int:id_gol>/eliminar", methods=["POST"])
@acceso
def eliminar_gol(id_partido, id_gol):
    try:
        ejecutar("DELETE FROM gol WHERE id_gol = %s AND id_partido = %s", (id_gol, id_partido))
        flash("Gol eliminado.", "ok")
    except ErrorBD as e:
        flash(str(e), "error")
    return _volver(id_partido)


@bp.route("/<int:id_partido>/tarjetas", methods=["POST"])
@acceso
def agregar_tarjeta(id_partido):
    v = Validador(request.form)
    ci = v.ci("ci_jugador", "El jugador")
    minuto = v.entero("minuto", "El minuto", 1, 60)
    color = v.opcion("color", "El color", ["amarilla", "roja"])
    if v.ok:
        try:
            ejecutar("INSERT INTO tarjeta (id_partido, ci_jugador, minuto, color) VALUES (%s, %s, %s, %s)",
                     (id_partido, ci, minuto, color))
            msg = "Tarjeta registrada."
            if color == "roja":
                msg += " Se generó automáticamente la suspensión para la fecha siguiente."
            flash(msg, "ok")
        except ErrorBD as e:
            v.error(str(e))
    mostrar_errores(v.errores)
    return _volver(id_partido)


@bp.route("/<int:id_partido>/tarjetas/<int:id_tarjeta>/eliminar", methods=["POST"])
@acceso
def eliminar_tarjeta(id_partido, id_tarjeta):
    try:
        ejecutar("DELETE FROM tarjeta WHERE id_tarjeta = %s AND id_partido = %s", (id_tarjeta, id_partido))
        flash("Tarjeta eliminada (las sanciones automáticas se recalcularon).", "ok")
    except ErrorBD as e:
        flash(str(e), "error")
    return _volver(id_partido)


@bp.route("/<int:id_partido>/cerrar", methods=["POST"])
@acceso
def cerrar(id_partido):
    try:
        ejecutar("UPDATE partido SET estado = 'jugado' WHERE id_partido = %s", (id_partido,))
        flash("Partido marcado como jugado. El resultado puede corregirse durante 48 horas.", "ok")
    except ErrorBD as e:
        flash(str(e), "error")
    return _volver(id_partido)
