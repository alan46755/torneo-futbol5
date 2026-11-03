"""ABM de partidos (fixture) y generación automática del fixture."""
from datetime import date, timedelta

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from comun import mostrar_errores, torneo_seleccionado
from db import ErrorBD, consultar, ejecutar, transaccion
from seguridad import solo_admin
from validaciones import Validador

bp = Blueprint("partidos", __name__, url_prefix="/partidos")

SQL_PARTIDOS = """
    SELECT p.id_partido, p.id_torneo, p.numero_fecha, p.dia, p.id_turno, p.id_complejo, p.nombre_cancha,
           p.estado, p.id_equipo_local, p.id_equipo_visitante,
           t.hora_inicio, t.hora_fin, el.nombre AS local, ev.nombre AS visitante, c.nombre AS complejo,
           r.goles_local, r.goles_visitante,
           (SELECT COUNT(*) FROM planilla_partido pp WHERE pp.id_partido = p.id_partido) AS en_planilla,
           TIMESTAMP(p.dia, t.hora_inicio) <= NOW() AS comenzo,
           TIMESTAMP(p.dia, t.hora_fin) <= NOW() AS termino,
           NOW() <= TIMESTAMP(p.dia, t.hora_fin) + INTERVAL 48 HOUR AS en_ventana
      FROM partido p
      JOIN turno t USING (id_turno)
      JOIN equipo el ON el.id_equipo = p.id_equipo_local
      JOIN equipo ev ON ev.id_equipo = p.id_equipo_visitante
      JOIN complejo c ON c.id_complejo = p.id_complejo
      JOIN v_resultado_partido r ON r.id_partido = p.id_partido
"""


def _opciones(id_torneo):
    return dict(
        equipos=consultar("SELECT e.id_equipo, e.nombre, COUNT(x.ci_jugador) AS jugadores FROM equipo e "
                          "LEFT JOIN equipo_jugador_torneo x USING (id_equipo) WHERE e.id_torneo = %s "
                          "GROUP BY e.id_equipo ORDER BY e.nombre", (id_torneo,)),
        turnos=consultar("SELECT * FROM turno ORDER BY hora_inicio"),
        canchas=consultar("SELECT ca.id_complejo, ca.nombre_cancha, c.nombre AS complejo, ca.superficie, ca.techada "
                          "FROM cancha ca JOIN complejo c USING (id_complejo) ORDER BY c.nombre, ca.nombre_cancha"),
    )


def _validar(form, torneo, opciones, exigir_futuro=True):
    v = Validador(form)
    v.entero("numero_fecha", "El número de fecha", 1, 50)
    ids_eq = [e["id_equipo"] for e in opciones["equipos"]]
    loc = v.opcion("id_equipo_local", "El equipo local", ids_eq)
    vis = v.opcion("id_equipo_visitante", "El equipo visitante", ids_eq)
    if loc and loc == vis:
        v.error("Un equipo no puede enfrentarse a sí mismo.")
    minimo = max(torneo["fecha_inicio"], date.today()) if exigir_futuro else torneo["fecha_inicio"]
    v.fecha("dia", "El día", minimo=minimo, maximo=torneo["fecha_fin"])
    v.opcion("id_turno", "El turno", [t["id_turno"] for t in opciones["turnos"]])
    cancha = v.opcion("cancha", "La cancha", [f'{c["id_complejo"]}|{c["nombre_cancha"]}' for c in opciones["canchas"]])
    if cancha:
        comp, nombre = cancha.split("|", 1)
        v.datos["id_complejo"], v.datos["nombre_cancha"] = int(comp), nombre
    return v


@bp.route("/")
@solo_admin
def lista():
    t = torneo_seleccionado()
    if not t:
        return render_template("partidos/lista.html", torneo=None, filas=[], fechas=[])
    fecha = request.args.get("fecha", type=int)
    estado = request.args.get("estado")
    sql = SQL_PARTIDOS + " WHERE p.id_torneo = %s"
    params = [t["id_torneo"]]
    if fecha:
        sql += " AND p.numero_fecha = %s"
        params.append(fecha)
    if estado in ("programado", "jugado", "postergado", "cancelado"):
        sql += " AND p.estado = %s"
        params.append(estado)
    sql += " ORDER BY p.numero_fecha, p.dia, t.hora_inicio"
    fechas = [r["numero_fecha"] for r in consultar(
        "SELECT DISTINCT numero_fecha FROM partido WHERE id_torneo = %s ORDER BY 1", (t["id_torneo"],))]
    return render_template("partidos/lista.html", torneo=t, filas=consultar(sql, params), fechas=fechas,
                           filtro={"fecha": fecha, "estado": estado})


@bp.route("/nuevo", methods=["GET", "POST"])
@solo_admin
def nuevo():
    t = torneo_seleccionado() or abort(404)
    op = _opciones(t["id_torneo"])
    if request.method == "POST":
        v = _validar(request.form, t, op)
        if v.ok:
            d = v.datos
            try:
                ejecutar("""INSERT INTO partido (id_torneo, numero_fecha, id_equipo_local, id_equipo_visitante,
                                                 dia, id_turno, id_complejo, nombre_cancha)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                         (t["id_torneo"], d["numero_fecha"], d["id_equipo_local"], d["id_equipo_visitante"],
                          d["dia"], d["id_turno"], d["id_complejo"], d["nombre_cancha"]))
                flash("Partido programado.", "ok")
                return redirect(url_for(".lista", fecha=d["numero_fecha"]))
            except ErrorBD as e:
                v.error(str(e))
        mostrar_errores(v.errores)
    return render_template("partidos/form.html", p=request.form, torneo=t, nuevo=True, **op)


@bp.route("/<int:id_partido>/editar", methods=["GET", "POST"])
@solo_admin
def editar(id_partido):
    p = consultar(SQL_PARTIDOS + " WHERE p.id_partido = %s", (id_partido,), uno=True) or abort(404)
    t = consultar("SELECT * FROM torneo WHERE id_torneo = %s", (p["id_torneo"],), uno=True)
    op = _opciones(p["id_torneo"])
    if p["estado"] in ("jugado", "cancelado"):
        flash(f"Un partido {p['estado']} no puede modificarse.", "error")
        return redirect(url_for(".lista"))
    if request.method == "POST":
        cambia_dia = request.form.get("dia") != p["dia"].isoformat()
        v = _validar(request.form, t, op, exigir_futuro=cambia_dia)
        v.opcion("estado", "El estado", ["programado", "postergado", "cancelado"])
        if v.ok:
            d = v.datos
            try:
                ejecutar("""UPDATE partido SET numero_fecha=%s, id_equipo_local=%s, id_equipo_visitante=%s, dia=%s,
                                   id_turno=%s, id_complejo=%s, nombre_cancha=%s, estado=%s WHERE id_partido=%s""",
                         (d["numero_fecha"], d["id_equipo_local"], d["id_equipo_visitante"], d["dia"],
                          d["id_turno"], d["id_complejo"], d["nombre_cancha"], d["estado"], id_partido))
                flash("Partido actualizado.", "ok")
                return redirect(url_for(".lista", fecha=d["numero_fecha"]))
            except ErrorBD as e:
                v.error(str(e))
        mostrar_errores(v.errores)
        p = {**p, **request.form}
    else:
        p = {**p, "cancha": f'{p["id_complejo"]}|{p["nombre_cancha"]}'}
    return render_template("partidos/form.html", p=p, torneo=t, nuevo=False, **op)


@bp.route("/<int:id_partido>/estado", methods=["POST"])
@solo_admin
def cambiar_estado(id_partido):
    estado = request.form.get("estado")
    if estado not in ("postergado", "cancelado"):
        abort(400)
    try:
        ejecutar("UPDATE partido SET estado = %s WHERE id_partido = %s", (estado, id_partido))
        flash(f"Partido {estado}.", "ok")
    except ErrorBD as e:
        flash(str(e), "error")
    return redirect(request.referrer or url_for(".lista"))


@bp.route("/<int:id_partido>/eliminar", methods=["POST"])
@solo_admin
def eliminar(id_partido):
    try:
        ejecutar("DELETE FROM partido WHERE id_partido = %s", (id_partido,))
        flash("Partido eliminado.", "ok")
    except ErrorBD as e:
        flash(str(e), "error")
    return redirect(request.referrer or url_for(".lista"))


# ---- Generación automática del fixture -------------------------------------------
def todos_contra_todos(ids):
    """Método del círculo: devuelve una lista de fechas, cada una con sus cruces (local, visitante)."""
    ids = list(ids)
    if len(ids) % 2:
        ids.append(None)                     # equipo libre
    n = len(ids)
    fechas = []
    for f in range(n - 1):
        cruces = []
        for i in range(n // 2):
            a, b = ids[i], ids[n - 1 - i]
            if a is not None and b is not None:
                cruces.append((a, b) if (f + i) % 2 == 0 else (b, a))
        fechas.append(cruces)
        ids = [ids[0], ids[-1]] + ids[1:-1]
    return fechas


@bp.route("/generar", methods=["POST"])
@solo_admin
def generar():
    t = torneo_seleccionado() or abort(404)
    v = Validador(request.form)
    desde = v.fecha("desde", "La fecha de la primera fecha", minimo=max(t["fecha_inicio"], date.today()),
                    maximo=t["fecha_fin"])
    cada = v.entero("dias_entre_fechas", "Los días entre fechas", 1, 30)
    equipos = [e["id_equipo"] for e in consultar("SELECT id_equipo FROM equipo WHERE id_torneo = %s ORDER BY id_equipo",
                                                 (t["id_torneo"],))]
    if len(equipos) < 2:
        v.error("Se necesitan al menos 2 equipos para generar el fixture.")
    if consultar("SELECT 1 FROM partido WHERE id_torneo = %s LIMIT 1", (t["id_torneo"],)):
        v.error("El fixture automático solo se genera cuando la edición aún no tiene partidos.")
    canchas = consultar("SELECT id_complejo, nombre_cancha FROM cancha ORDER BY id_complejo, nombre_cancha")
    turnos = [r["id_turno"] for r in consultar("SELECT id_turno FROM turno ORDER BY hora_inicio")]
    if not canchas or not turnos:
        v.error("Debe haber canchas y turnos cargados.")
    if not v.ok:
        mostrar_errores(v.errores)
        return redirect(url_for(".lista"))

    franjas = [(c["id_complejo"], c["nombre_cancha"], tu) for tu in turnos for c in canchas]
    total = 0
    try:
        with transaccion() as cur:
            for nro, cruces in enumerate(todos_contra_todos(equipos), start=1):
                base = desde + timedelta(days=(nro - 1) * cada)
                for k, (loc, vis) in enumerate(cruces):
                    comp, cancha, turno = franjas[k % len(franjas)]
                    dia = base + timedelta(days=k // len(franjas))
                    cur.execute("""INSERT INTO partido (id_torneo, numero_fecha, id_equipo_local, id_equipo_visitante,
                                                        dia, id_turno, id_complejo, nombre_cancha)
                                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s)""",
                                (t["id_torneo"], nro, loc, vis, dia, turno, comp, cancha))
                    total += 1
        flash(f"Fixture generado: {total} partidos en {len(equipos) - 1 + len(equipos) % 2} fechas.", "ok")
    except ErrorBD as e:
        flash(f"No se pudo generar el fixture: {e}", "error")
    return redirect(url_for(".lista"))
