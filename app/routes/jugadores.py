"""ABM de jugadores."""
from datetime import date

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from comun import TIPOS_JUGADOR, mostrar_errores
from db import ErrorBD, consultar, ejecutar
from seguridad import solo_admin
from validaciones import Validador, edad

bp = Blueprint("jugadores", __name__, url_prefix="/jugadores")


def _facultades():
    return consultar("SELECT id_facultad, nombre FROM facultad ORDER BY nombre")


def _validar(form, con_ci=True):
    v = Validador(form)
    if con_ci:
        v.ci("ci")
    v.nombre_propio("nombre", "El nombre")
    v.nombre_propio("apellido", "El apellido")
    v.email("email")
    fnac = v.fecha("fecha_nacimiento", "La fecha de nacimiento", maximo=date.today())
    if fnac and not 16 <= edad(fnac) <= 100:
        v.error("El jugador debe tener entre 16 y 100 años.")
    v.entero("id_facultad", "La facultad", 1)
    v.opcion("tipo", "El tipo de jugador", TIPOS_JUGADOR)
    return v


@bp.route("/")
@solo_admin
def lista():
    q = (request.args.get("q") or "").strip()
    fac = request.args.get("facultad", type=int)
    tipo = request.args.get("tipo") if request.args.get("tipo") in TIPOS_JUGADOR else None
    sql = """SELECT j.*, f.nombre AS facultad,
                    (SELECT COUNT(*) FROM equipo_jugador_torneo e WHERE e.ci_jugador = j.ci) AS planteles
               FROM jugador j JOIN facultad f USING (id_facultad) WHERE 1 = 1"""
    params = []
    if q:
        sql += " AND (j.ci LIKE %s OR j.nombre LIKE %s OR j.apellido LIKE %s OR j.email LIKE %s)"
        params += [f"%{q}%"] * 4
    if fac:
        sql += " AND j.id_facultad = %s"
        params.append(fac)
    if tipo:
        sql += " AND j.tipo = %s"
        params.append(tipo)
    sql += " ORDER BY j.apellido, j.nombre"
    return render_template("jugadores/lista.html", filas=consultar(sql, params), facultades=_facultades(),
                           tipos=TIPOS_JUGADOR, filtro={"q": q, "facultad": fac, "tipo": tipo})


@bp.route("/nuevo", methods=["GET", "POST"])
@solo_admin
def nuevo():
    if request.method == "POST":
        v = _validar(request.form)
        if v.ok:
            d = v.datos
            try:
                ejecutar("""INSERT INTO jugador (ci, nombre, apellido, email, fecha_nacimiento, id_facultad, tipo)
                            VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                         (d["ci"], d["nombre"], d["apellido"], d["email"], d["fecha_nacimiento"],
                          d["id_facultad"], d["tipo"]))
                flash("Jugador registrado.", "ok")
                return redirect(url_for(".lista"))
            except ErrorBD as e:
                v.error(str(e))
        mostrar_errores(v.errores)
    return render_template("jugadores/form.html", j=request.form, nuevo=True,
                           facultades=_facultades(), tipos=TIPOS_JUGADOR)


@bp.route("/<ci>/editar", methods=["GET", "POST"])
@solo_admin
def editar(ci):
    j = consultar("SELECT * FROM jugador WHERE ci = %s", (ci,), uno=True) or abort(404)
    if request.method == "POST":
        v = _validar(request.form, con_ci=False)
        if v.ok:
            d = v.datos
            try:
                ejecutar("""UPDATE jugador SET nombre=%s, apellido=%s, email=%s, fecha_nacimiento=%s,
                                   id_facultad=%s, tipo=%s WHERE ci=%s""",
                         (d["nombre"], d["apellido"], d["email"], d["fecha_nacimiento"],
                          d["id_facultad"], d["tipo"], ci))
                flash("Jugador actualizado.", "ok")
                return redirect(url_for(".lista"))
            except ErrorBD as e:
                v.error(str(e))
        mostrar_errores(v.errores)
        j = {**j, **request.form, "ci": ci}
    return render_template("jugadores/form.html", j=j, nuevo=False,
                           facultades=_facultades(), tipos=TIPOS_JUGADOR)


@bp.route("/<ci>/eliminar", methods=["POST"])
@solo_admin
def eliminar(ci):
    try:
        ejecutar("DELETE FROM jugador WHERE ci = %s", (ci,))
        flash("Jugador eliminado.", "ok")
    except ErrorBD as e:
        flash(str(e) + " (integra o integró algún plantel)", "error")
    return redirect(url_for(".lista"))
