"""ABM de equipos y de sus planteles."""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from comun import mostrar_errores, torneo_seleccionado
from db import ErrorBD, consultar, ejecutar, transaccion
from seguridad import solo_admin
from validaciones import Validador

bp = Blueprint("equipos", __name__, url_prefix="/equipos")


def _equipo(id_equipo):
    return consultar("""
        SELECT e.*, f.nombre AS facultad, t.nombre AS torneo, t.estado AS estado_torneo,
               CONCAT(j.nombre, ' ', j.apellido) AS capitan
          FROM equipo e JOIN facultad f USING (id_facultad) JOIN torneo t USING (id_torneo)
          LEFT JOIN jugador j ON j.ci = e.ci_capitan
         WHERE e.id_equipo = %s""", (id_equipo,), uno=True) or abort(404)


@bp.route("/")
@solo_admin
def lista():
    t = torneo_seleccionado()
    filas = consultar("""
        SELECT e.id_equipo, e.nombre, f.nombre AS facultad, CONCAT(j.nombre, ' ', j.apellido) AS capitan,
               COUNT(ejt.ci_jugador) AS jugadores,
               SUM(jj.tipo IN ('docente', 'funcionario')) AS doc_func
          FROM equipo e JOIN facultad f USING (id_facultad)
          LEFT JOIN jugador j ON j.ci = e.ci_capitan
          LEFT JOIN equipo_jugador_torneo ejt ON ejt.id_equipo = e.id_equipo
          LEFT JOIN jugador jj ON jj.ci = ejt.ci_jugador
         WHERE e.id_torneo = %s
         GROUP BY e.id_equipo, e.nombre, f.nombre, j.nombre, j.apellido
         ORDER BY e.nombre""", (t["id_torneo"],)) if t else []
    return render_template("equipos/lista.html", filas=filas, torneo=t)


@bp.route("/nuevo", methods=["GET", "POST"])
@solo_admin
def nuevo():
    t = torneo_seleccionado() or abort(404)
    if request.method == "POST":
        v = Validador(request.form)
        nombre = v.texto("nombre", "El nombre", 2, 60)
        fac = v.entero("id_facultad", "La facultad", 1)
        if v.ok:
            try:
                nuevo_id = ejecutar("INSERT INTO equipo (nombre, id_torneo, id_facultad) VALUES (%s, %s, %s)",
                                    (nombre, t["id_torneo"], fac))
                flash("Equipo creado. Ahora cargue su plantel y asigne el capitán.", "ok")
                return redirect(url_for(".detalle", id_equipo=nuevo_id))
            except ErrorBD as e:
                v.error(str(e))
        mostrar_errores(v.errores)
    return render_template("equipos/form.html", e=request.form, torneo=t, nuevo=True,
                           facultades=consultar("SELECT * FROM facultad ORDER BY nombre"))


@bp.route("/<int:id_equipo>")
@solo_admin
def detalle(id_equipo):
    e = _equipo(id_equipo)
    plantel = consultar("""
        SELECT j.ci, j.nombre, j.apellido, j.tipo, ejt.numero_camiseta,
               (SELECT COUNT(*) FROM planilla_partido pp WHERE pp.ci_jugador = j.ci AND pp.id_equipo = ejt.id_equipo) AS partidos
          FROM equipo_jugador_torneo ejt JOIN jugador j ON j.ci = ejt.ci_jugador
         WHERE ejt.id_equipo = %s ORDER BY ejt.numero_camiseta""", (id_equipo,))
    # Candidatos: misma facultad y sin equipo en esta edición
    candidatos = consultar("""
        SELECT j.ci, j.nombre, j.apellido, j.tipo FROM jugador j
         WHERE j.id_facultad = %s
           AND NOT EXISTS (SELECT 1 FROM equipo_jugador_torneo x WHERE x.ci_jugador = j.ci AND x.id_torneo = %s)
         ORDER BY j.apellido, j.nombre""", (e["id_facultad"], e["id_torneo"]))
    return render_template("equipos/detalle.html", e=e, plantel=plantel, candidatos=candidatos)


@bp.route("/<int:id_equipo>/editar", methods=["GET", "POST"])
@solo_admin
def editar(id_equipo):
    e = _equipo(id_equipo)
    plantel = consultar("SELECT j.ci, j.nombre, j.apellido FROM equipo_jugador_torneo ejt "
                        "JOIN jugador j ON j.ci = ejt.ci_jugador WHERE ejt.id_equipo = %s "
                        "ORDER BY j.apellido", (id_equipo,))
    if request.method == "POST":
        v = Validador(request.form)
        nombre = v.texto("nombre", "El nombre", 2, 60)
        fac = v.entero("id_facultad", "La facultad", 1)
        cap = request.form.get("ci_capitan") or None
        if cap and cap not in [p["ci"] for p in plantel]:
            v.error("El capitán debe ser un jugador del plantel.")
        if v.ok:
            try:
                ejecutar("UPDATE equipo SET nombre=%s, id_facultad=%s, ci_capitan=%s WHERE id_equipo=%s",
                         (nombre, fac, cap, id_equipo))
                flash("Equipo actualizado.", "ok")
                return redirect(url_for(".detalle", id_equipo=id_equipo))
            except ErrorBD as ex:
                v.error(str(ex))
        mostrar_errores(v.errores)
        e = {**e, **request.form}
    return render_template("equipos/form.html", e=e, nuevo=False, plantel=plantel,
                           torneo={"nombre": e["torneo"]},
                           facultades=consultar("SELECT * FROM facultad ORDER BY nombre"))


@bp.route("/<int:id_equipo>/eliminar", methods=["POST"])
@solo_admin
def eliminar(id_equipo):
    try:
        with transaccion() as cur:
            # El capitán referencia al plantel: se libera antes de borrar en cascada.
            cur.execute("UPDATE equipo SET ci_capitan = NULL WHERE id_equipo = %s", (id_equipo,))
            cur.execute("DELETE FROM equipo WHERE id_equipo = %s", (id_equipo,))
        flash("Equipo eliminado.", "ok")
        return redirect(url_for(".lista"))
    except ErrorBD as e:
        flash(str(e), "error")
        return redirect(url_for(".detalle", id_equipo=id_equipo))


# ---- Plantel ------------------------------------------------------------------
@bp.route("/<int:id_equipo>/plantel", methods=["POST"])
@solo_admin
def agregar_jugador(id_equipo):
    e = _equipo(id_equipo)
    v = Validador(request.form)
    ci = v.ci("ci_jugador", "El jugador")
    camiseta = v.entero("numero_camiseta", "El número de camiseta", 1, 99)
    if v.ok:
        try:
            ejecutar("INSERT INTO equipo_jugador_torneo (id_equipo, ci_jugador, id_torneo, numero_camiseta) "
                     "VALUES (%s, %s, %s, %s)", (id_equipo, ci, e["id_torneo"], camiseta))
            flash("Jugador agregado al plantel.", "ok")
        except ErrorBD as ex:
            v.error(str(ex))
    mostrar_errores(v.errores)
    return redirect(url_for(".detalle", id_equipo=id_equipo))


@bp.route("/<int:id_equipo>/plantel/<ci>/camiseta", methods=["POST"])
@solo_admin
def cambiar_camiseta(id_equipo, ci):
    v = Validador(request.form)
    camiseta = v.entero("numero_camiseta", "El número de camiseta", 1, 99)
    if v.ok:
        try:
            ejecutar("UPDATE equipo_jugador_torneo SET numero_camiseta = %s WHERE id_equipo = %s AND ci_jugador = %s",
                     (camiseta, id_equipo, ci))
            flash("Número de camiseta actualizado.", "ok")
        except ErrorBD as ex:
            v.error(str(ex))
    mostrar_errores(v.errores)
    return redirect(url_for(".detalle", id_equipo=id_equipo))


@bp.route("/<int:id_equipo>/plantel/<ci>/quitar", methods=["POST"])
@solo_admin
def quitar_jugador(id_equipo, ci):
    try:
        ejecutar("DELETE FROM equipo_jugador_torneo WHERE id_equipo = %s AND ci_jugador = %s", (id_equipo, ci))
        flash("Jugador quitado del plantel.", "ok")
    except ErrorBD as e:
        flash(str(e), "error")
    return redirect(url_for(".detalle", id_equipo=id_equipo))


@bp.route("/<int:id_equipo>/capitan/<ci>", methods=["POST"])
@solo_admin
def asignar_capitan(id_equipo, ci):
    try:
        ejecutar("UPDATE equipo SET ci_capitan = %s WHERE id_equipo = %s", (ci, id_equipo))
        flash("Capitán asignado.", "ok")
    except ErrorBD as e:
        flash(str(e), "error")
    return redirect(url_for(".detalle", id_equipo=id_equipo))
