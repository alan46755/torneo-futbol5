"""
Reportes para el área de deportes. Cada reporte es una consulta SQL
parametrizada por la edición del torneo (%(t)s). Las consultas se
muestran en pantalla para poder explicarlas en la defensa.
"""
from flask import Blueprint, render_template

from comun import torneo_seleccionado
from db import consultar
from seguridad import solo_admin

bp = Blueprint("reportes", __name__, url_prefix="/reportes")

REPORTES = [
    {
        "id": "posiciones",
        "titulo": "Tabla de posiciones",
        "descripcion": "3 puntos por victoria, 1 por empate. Desempate por diferencia de goles y luego goles a favor.",
        "columnas": [("pos", "#"), ("equipo", "Equipo"), ("facultad", "Facultad"), ("pj", "PJ"), ("pg", "PG"),
                     ("pe", "PE"), ("pp", "PP"), ("gf", "GF"), ("gc", "GC"), ("dg", "DG"), ("pts", "Pts")],
        "sql": """SELECT RANK() OVER (ORDER BY pts DESC, dg DESC, gf DESC) AS pos,
       equipo, facultad, pj, pg, pe, pp, gf, gc, dg, pts
  FROM v_tabla_posiciones
 WHERE id_torneo = %(t)s
 ORDER BY pos, equipo""",
    },
    {
        "id": "goleadores",
        "titulo": "Tabla de goleadores (top 10)",
        "descripcion": "No se cuentan los autogoles. A igual cantidad de goles se ordena por apellido.",
        "columnas": [("pos", "#"), ("jugador", "Jugador"), ("equipo", "Equipo"), ("goles", "Goles"),
                     ("partidos_con_gol", "Partidos con gol")],
        "sql": """SELECT RANK() OVER (ORDER BY goles DESC) AS pos,
       CONCAT(nombre, ' ', apellido) AS jugador, equipo, goles, partidos_con_gol
  FROM v_goleadores
 WHERE id_torneo = %(t)s
 ORDER BY goles DESC, apellido, nombre
 LIMIT 10""",
    },
    {
        "id": "fairplay",
        "titulo": "Fair play por equipo",
        "descripcion": "1 punto por amarilla y 3 por roja. El mejor equipo es el de menor puntaje.",
        "columnas": [("pos", "#"), ("equipo", "Equipo"), ("amarillas", "Amarillas"), ("rojas", "Rojas"),
                     ("puntaje", "Puntaje")],
        "sql": """SELECT RANK() OVER (ORDER BY puntaje) AS pos, equipo, amarillas, rojas, puntaje
  FROM v_fair_play
 WHERE id_torneo = %(t)s
 ORDER BY puntaje, equipo""",
    },
    {
        "id": "promedio",
        "titulo": "Promedio de goles por partido",
        "descripcion": "Por fecha y para toda la edición (fila de totales con WITH ROLLUP). Solo partidos jugados.",
        "columnas": [("fecha", "Fecha"), ("partidos", "Partidos"), ("goles", "Goles"), ("promedio", "Promedio")],
        "sql": """SELECT IF(GROUPING(numero_fecha), 'Toda la edición', CONCAT('Fecha ', numero_fecha)) AS fecha,
       COUNT(*) AS partidos,
       SUM(goles_local + goles_visitante) AS goles,
       ROUND(AVG(goles_local + goles_visitante), 2) AS promedio
  FROM v_resultado_partido
 WHERE id_torneo = %(t)s AND estado = 'jugado'
 GROUP BY numero_fecha WITH ROLLUP""",
    },
    {
        "id": "canchas",
        "titulo": "Canchas más utilizadas",
        "descripcion": "Partidos programados o jugados en cada cancha durante la edición.",
        "columnas": [("complejo", "Complejo"), ("cancha", "Cancha"), ("superficie", "Superficie"),
                     ("partidos", "Partidos"), ("jugados", "Jugados")],
        "sql": """SELECT c.nombre AS complejo, ca.nombre_cancha AS cancha, ca.superficie,
       COUNT(p.id_partido) AS partidos,
       COALESCE(SUM(p.estado = 'jugado'), 0) AS jugados
  FROM cancha ca
  JOIN complejo c ON c.id_complejo = ca.id_complejo
  LEFT JOIN partido p ON p.id_complejo = ca.id_complejo AND p.nombre_cancha = ca.nombre_cancha
                     AND p.id_torneo = %(t)s AND p.estado IN ('programado', 'jugado')
 GROUP BY c.nombre, ca.nombre_cancha, ca.superficie
 ORDER BY partidos DESC, complejo, cancha""",
    },
    {
        "id": "turnos",
        "titulo": "Turnos más utilizados",
        "descripcion": "Partidos programados o jugados en cada turno horario.",
        "columnas": [("turno", "Turno"), ("partidos", "Partidos"), ("porcentaje", "% del total")],
        "sql": """SELECT CONCAT(TIME_FORMAT(t.hora_inicio, '%%H:%%i'), ' a ', TIME_FORMAT(t.hora_fin, '%%H:%%i')) AS turno,
       COUNT(p.id_partido) AS partidos,
       ROUND(100 * COUNT(p.id_partido) / NULLIF(SUM(COUNT(p.id_partido)) OVER (), 0), 1) AS porcentaje
  FROM turno t
  LEFT JOIN partido p ON p.id_turno = t.id_turno AND p.id_torneo = %(t)s
                     AND p.estado IN ('programado', 'jugado')
 GROUP BY t.id_turno, t.hora_inicio, t.hora_fin
 ORDER BY partidos DESC, t.hora_inicio""",
    },
    {
        "id": "facultad_tipo",
        "titulo": "Jugadores por facultad y por tipo",
        "descripcion": "Jugadores registrados en el sistema; la última columna cuenta los inscriptos en planteles de esta edición.",
        "columnas": [("facultad", "Facultad"), ("grado", "Grado"), ("posgrado", "Posgrado"), ("docente", "Docente"),
                     ("funcionario", "Funcionario"), ("total", "Total"), ("en_edicion", "En planteles de la edición")],
        "sql": """SELECT COALESCE(f.nombre, 'TOTAL') AS facultad,
       COALESCE(SUM(j.tipo = 'grado'), 0)       AS grado,
       COALESCE(SUM(j.tipo = 'posgrado'), 0)    AS posgrado,
       COALESCE(SUM(j.tipo = 'docente'), 0)     AS docente,
       COALESCE(SUM(j.tipo = 'funcionario'), 0) AS funcionario,
       COUNT(j.ci)                               AS total,
       COUNT(ejt.ci_jugador)                     AS en_edicion
  FROM facultad f
  LEFT JOIN jugador j ON j.id_facultad = f.id_facultad
  LEFT JOIN equipo_jugador_torneo ejt ON ejt.ci_jugador = j.ci AND ejt.id_torneo = %(t)s
 GROUP BY f.nombre WITH ROLLUP""",
    },
    {
        "id": "sin_planilla",
        "titulo": "Inscriptos que nunca figuraron en una planilla",
        "descripcion": "Jugadores del plantel de algún equipo de la edición que todavía no jugaron ningún partido.",
        "columnas": [("ci", "CI"), ("jugador", "Jugador"), ("tipo", "Tipo"), ("equipo", "Equipo"),
                     ("numero_camiseta", "Camiseta")],
        "sql": """SELECT j.ci, CONCAT(j.nombre, ' ', j.apellido) AS jugador, j.tipo, e.nombre AS equipo,
       ejt.numero_camiseta
  FROM equipo_jugador_torneo ejt
  JOIN jugador j ON j.ci = ejt.ci_jugador
  JOIN equipo e ON e.id_equipo = ejt.id_equipo
 WHERE ejt.id_torneo = %(t)s
   AND NOT EXISTS (SELECT 1 FROM planilla_partido pp
                    WHERE pp.ci_jugador = ejt.ci_jugador AND pp.id_equipo = ejt.id_equipo)
 ORDER BY e.nombre, j.apellido""",
    },
    {
        "id": "sanciones",
        "titulo": "Sanciones por equipo y por motivo",
        "descripcion": "Cantidad de sanciones y total de fechas de suspensión acumuladas por cada equipo.",
        "columnas": [("equipo", "Equipo"), ("roja", "Roja"), ("amarillas", "Acum. amarillas"),
                     ("disciplinaria", "Disciplinaria"), ("total", "Total"), ("fechas", "Fechas de suspensión")],
        "sql": """SELECT e.nombre AS equipo,
       COALESCE(SUM(s.motivo = 'roja'), 0)                  AS roja,
       COALESCE(SUM(s.motivo = 'acumulacion_amarillas'), 0) AS amarillas,
       COALESCE(SUM(s.motivo = 'disciplinaria'), 0)         AS disciplinaria,
       COUNT(s.id_sancion)                                  AS total,
       COALESCE(SUM(s.cantidad_fechas), 0)                  AS fechas
  FROM equipo e
  LEFT JOIN v_sancion_detalle s ON s.id_equipo = e.id_equipo
 WHERE e.id_torneo = %(t)s
 GROUP BY e.id_equipo, e.nombre
 ORDER BY total DESC, equipo""",
    },
    {
        "id": "estados",
        "titulo": "Partidos jugados vs. postergados / cancelados",
        "descripcion": "Distribución de los partidos de la edición según su estado.",
        "columnas": [("estado", "Estado"), ("partidos", "Partidos"), ("porcentaje", "% del total")],
        "etiquetar": ["estado"],
        "sql": """SELECT estado, COUNT(*) AS partidos,
       ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS porcentaje
  FROM partido
 WHERE id_torneo = %(t)s
 GROUP BY estado
 ORDER BY partidos DESC""",
    },
    # ---- Consultas adicionales propuestas por el equipo ----------------------------
    {
        "id": "localia",
        "titulo": "(Adicional) Ventaja de jugar como local",
        "descripcion": "¿Influye ser el equipo local? Resultados y goles promedio según condición.",
        "columnas": [("partidos", "Partidos"), ("gana_local", "Gana local"), ("empates", "Empates"),
                     ("gana_visitante", "Gana visitante"), ("pct_local", "% local"),
                     ("goles_local", "Goles prom. local"), ("goles_visitante", "Goles prom. visitante")],
        "sql": """SELECT COUNT(*) AS partidos,
       SUM(goles_local > goles_visitante) AS gana_local,
       SUM(goles_local = goles_visitante) AS empates,
       SUM(goles_local < goles_visitante) AS gana_visitante,
       ROUND(100 * SUM(goles_local > goles_visitante) / COUNT(*), 1) AS pct_local,
       ROUND(AVG(goles_local), 2) AS goles_local,
       ROUND(AVG(goles_visitante), 2) AS goles_visitante
  FROM v_resultado_partido
 WHERE id_torneo = %(t)s AND estado = 'jugado'
HAVING COUNT(*) > 0""",
    },
    {
        "id": "valla",
        "titulo": "(Adicional) Valla menos vencida",
        "descripcion": "Goles recibidos por partido y cantidad de partidos sin recibir goles.",
        "columnas": [("equipo", "Equipo"), ("pj", "PJ"), ("gc", "Goles en contra"),
                     ("promedio_gc", "GC por partido"), ("vallas_invictas", "Partidos sin goles en contra")],
        "sql": """SELECT v.equipo, v.pj, v.gc, ROUND(v.gc / v.pj, 2) AS promedio_gc,
       (SELECT COUNT(*) FROM v_partido_equipo x
         WHERE x.id_equipo = v.id_equipo AND x.gc = 0) AS vallas_invictas
  FROM v_tabla_posiciones v
 WHERE v.id_torneo = %(t)s AND v.pj > 0
 ORDER BY promedio_gc, vallas_invictas DESC, v.equipo""",
    },
    {
        "id": "minutos",
        "titulo": "(Adicional) Goles por tramo del partido",
        "descripcion": "En qué momento del partido se convierten los goles (tramos de 10 minutos).",
        "columnas": [("tramo", "Minutos"), ("goles", "Goles"), ("porcentaje", "% de los goles")],
        "sql": """SELECT CONCAT(x.tramo * 10 + 1, ' a ', (x.tramo + 1) * 10) AS tramo,
       COUNT(*) AS goles,
       ROUND(100 * COUNT(*) / SUM(COUNT(*)) OVER (), 1) AS porcentaje
  FROM (SELECT (g.minuto - 1) DIV 10 AS tramo
          FROM gol g JOIN partido p ON p.id_partido = g.id_partido
         WHERE p.id_torneo = %(t)s AND p.estado = 'jugado') x
 GROUP BY x.tramo
 ORDER BY x.tramo""",
    },
]


@bp.route("/")
@solo_admin
def index():
    t = torneo_seleccionado()
    resultados = []
    for r in REPORTES:
        filas = consultar(r["sql"], {"t": t["id_torneo"]}) if t else []
        resultados.append({**r, "filas": filas, "sql_mostrar": r["sql"].replace("%%", "%")})
    return render_template("reportes.html", torneo=t, reportes=resultados)
