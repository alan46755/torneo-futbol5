"""ABM de complejos deportivos y sus canchas."""
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from comun import DEPARTAMENTOS, mostrar_errores
from db import ErrorBD, consultar, ejecutar
from seguridad import solo_admin
from validaciones import Validador

bp = Blueprint("complejos", __name__, url_prefix="/complejos")


def _validar_complejo(form):
    v = Validador(form)
    v.texto("nombre", "El nombre", 3, 80)
    v.texto("direccion", "La dirección", 5, 150)
    v.opcion("departamento", "El departamento", DEPARTAMENTOS)
    return v


def _validar_cancha(form):
    v = Validador(form)
    v.texto("nombre_cancha", "El nombre de la cancha", 1, 40)
    v.opcion("superficie", "La superficie", ["sintetico", "parquet"])
    v.booleano("techada")
    return v


@bp.route("/")
@solo_admin
def lista():
    filas = consultar("""
        SELECT c.*, COUNT(ca.nombre_cancha) AS canchas
          FROM complejo c LEFT JOIN cancha ca USING (id_complejo)
         GROUP BY c.id_complejo ORDER BY c.nombre""")
    return render_template("complejos/lista.html", filas=filas)


@bp.route("/nuevo", methods=["GET", "POST"])
@solo_admin
def nuevo():
    if request.method == "POST":
        v = _validar_complejo(request.form)
        if v.ok:
            d = v.datos
            try:
                nid = ejecutar("INSERT INTO complejo (nombre, direccion, departamento) VALUES (%s, %s, %s)",
                               (d["nombre"], d["direccion"], d["departamento"]))
                flash("Complejo creado. Agregue sus canchas.", "ok")
                return redirect(url_for(".detalle", id_complejo=nid))
            except ErrorBD as e:
                v.error(str(e))
        mostrar_errores(v.errores)
    return render_template("complejos/form.html", c=request.form, nuevo=True, departamentos=DEPARTAMENTOS)


@bp.route("/<int:id_complejo>")
@solo_admin
def detalle(id_complejo):
    c = consultar("SELECT * FROM complejo WHERE id_complejo = %s", (id_complejo,), uno=True) or abort(404)
    canchas = consultar("""
        SELECT ca.*, (SELECT COUNT(*) FROM partido p WHERE p.id_complejo = ca.id_complejo
                         AND p.nombre_cancha = ca.nombre_cancha) AS partidos
          FROM cancha ca WHERE ca.id_complejo = %s ORDER BY ca.nombre_cancha""", (id_complejo,))
    return render_template("complejos/detalle.html", c=c, canchas=canchas)


@bp.route("/<int:id_complejo>/editar", methods=["GET", "POST"])
@solo_admin
def editar(id_complejo):
    c = consultar("SELECT * FROM complejo WHERE id_complejo = %s", (id_complejo,), uno=True) or abort(404)
    if request.method == "POST":
        v = _validar_complejo(request.form)
        if v.ok:
            d = v.datos
            try:
                ejecutar("UPDATE complejo SET nombre=%s, direccion=%s, departamento=%s WHERE id_complejo=%s",
                         (d["nombre"], d["direccion"], d["departamento"], id_complejo))
                flash("Complejo actualizado.", "ok")
                return redirect(url_for(".detalle", id_complejo=id_complejo))
            except ErrorBD as e:
                v.error(str(e))
        mostrar_errores(v.errores)
        c = {**c, **request.form}
    return render_template("complejos/form.html", c=c, nuevo=False, departamentos=DEPARTAMENTOS)


@bp.route("/<int:id_complejo>/eliminar", methods=["POST"])
@solo_admin
def eliminar(id_complejo):
    try:
        ejecutar("DELETE FROM complejo WHERE id_complejo = %s", (id_complejo,))
        flash("Complejo eliminado (junto con sus canchas).", "ok")
        return redirect(url_for(".lista"))
    except ErrorBD as e:
        flash(str(e) + " Sus canchas tienen partidos asignados.", "error")
        return redirect(url_for(".detalle", id_complejo=id_complejo))


# ---- Canchas ------------------------------------------------------------------
@bp.route("/<int:id_complejo>/canchas", methods=["POST"])
@solo_admin
def agregar_cancha(id_complejo):
    v = _validar_cancha(request.form)
    if v.ok:
        d = v.datos
        try:
            ejecutar("INSERT INTO cancha (id_complejo, nombre_cancha, superficie, techada) VALUES (%s, %s, %s, %s)",
                     (id_complejo, d["nombre_cancha"], d["superficie"], d["techada"]))
            flash("Cancha agregada.", "ok")
        except ErrorBD as e:
            v.error(str(e))
    mostrar_errores(v.errores)
    return redirect(url_for(".detalle", id_complejo=id_complejo))


@bp.route("/<int:id_complejo>/canchas/<path:nombre>/editar", methods=["POST"])
@solo_admin
def editar_cancha(id_complejo, nombre):
    v = _validar_cancha(request.form)
    if v.ok:
        d = v.datos
        try:
            # Renombrar la cancha actualiza en cascada los partidos (ON UPDATE CASCADE).
            ejecutar("UPDATE cancha SET nombre_cancha=%s, superficie=%s, techada=%s "
                     "WHERE id_complejo=%s AND nombre_cancha=%s",
                     (d["nombre_cancha"], d["superficie"], d["techada"], id_complejo, nombre))
            flash("Cancha actualizada.", "ok")
        except ErrorBD as e:
            v.error(str(e))
    mostrar_errores(v.errores)
    return redirect(url_for(".detalle", id_complejo=id_complejo))


@bp.route("/<int:id_complejo>/canchas/<path:nombre>/eliminar", methods=["POST"])
@solo_admin
def eliminar_cancha(id_complejo, nombre):
    try:
        ejecutar("DELETE FROM cancha WHERE id_complejo = %s AND nombre_cancha = %s", (id_complejo, nombre))
        flash("Cancha eliminada.", "ok")
    except ErrorBD as e:
        flash(str(e) + " La cancha tiene partidos asignados.", "error")
    return redirect(url_for(".detalle", id_complejo=id_complejo))
