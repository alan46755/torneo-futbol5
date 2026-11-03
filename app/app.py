"""
Sistema de gestión del Torneo Interfacultades de Fútbol 5 - UCU
Punto de entrada de la aplicación Flask.
"""
from datetime import date

from flask import Flask, redirect, render_template, session, url_for

from comun import etiqueta, torneo_seleccionado, torneos
from config import Config
from db import ErrorBD, cerrar_conexiones, consultar
from seguridad import bp as auth_bp, csrf_token, login_requerido, verificar_csrf


def crear_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    from routes.complejos import bp as complejos_bp
    from routes.equipos import bp as equipos_bp
    from routes.facultades import bp as facultades_bp
    from routes.jugadores import bp as jugadores_bp
    from routes.partidos import bp as partidos_bp
    from routes.planillas import bp as planillas_bp
    from routes.reportes import bp as reportes_bp
    from routes.sanciones import bp as sanciones_bp
    from routes.torneos import bp as torneos_bp
    for bp in (auth_bp, torneos_bp, facultades_bp, jugadores_bp, equipos_bp, complejos_bp,
               partidos_bp, planillas_bp, sanciones_bp, reportes_bp):
        app.register_blueprint(bp)

    app.before_request(verificar_csrf)
    app.teardown_appcontext(cerrar_conexiones)
    app.jinja_env.globals.update(csrf_token=csrf_token, hoy=date.today)
    app.jinja_env.filters["etiqueta"] = etiqueta
    app.jinja_env.filters["fecha"] = lambda d: d.strftime("%d/%m/%Y") if d else ""
    app.jinja_env.filters["hora"] = lambda t: (str(t)[:-3] if t is not None else "")

    @app.context_processor
    def contexto():
        if "usuario" not in session:
            return {}
        try:
            return {"lista_torneos": torneos()}
        except ErrorBD:
            return {"lista_torneos": []}

    @app.errorhandler(ErrorBD)
    def error_bd(e):
        return render_template("error.html", codigo=500, mensaje=str(e)), 500

    @app.errorhandler(400)
    @app.errorhandler(403)
    @app.errorhandler(404)
    def error_http(e):
        mensajes = {403: "No tiene permisos para acceder a esta sección.",
                    404: "La página o el registro solicitado no existe."}
        return render_template("error.html", codigo=e.code,
                               mensaje=mensajes.get(e.code, e.description)), e.code

    @app.route("/")
    @login_requerido
    def inicio():
        if session.get("rol") == "planillero":
            return redirect(url_for("planillas.lista"))
        t = torneo_seleccionado()
        if not t:
            return render_template("inicio.html", torneo=None)
        p = (t["id_torneo"],)
        resumen = consultar("""
            SELECT (SELECT COUNT(*) FROM equipo WHERE id_torneo = %s) AS equipos,
                   (SELECT COUNT(*) FROM equipo_jugador_torneo WHERE id_torneo = %s) AS jugadores,
                   (SELECT COUNT(*) FROM partido WHERE id_torneo = %s AND estado = 'jugado') AS jugados,
                   (SELECT COUNT(*) FROM partido WHERE id_torneo = %s AND estado = 'programado') AS programados,
                   (SELECT COUNT(*) FROM sancion_jugador WHERE id_torneo = %s) AS sanciones
        """, p * 5, uno=True)
        tabla = consultar("SELECT * FROM v_tabla_posiciones WHERE id_torneo = %s "
                          "ORDER BY pts DESC, dg DESC, gf DESC, equipo LIMIT 5", p)
        proximos = consultar("""
            SELECT p.id_partido, p.numero_fecha, p.dia, t.hora_inicio, el.nombre AS local,
                   ev.nombre AS visitante, c.nombre AS complejo, p.nombre_cancha
              FROM partido p JOIN turno t USING (id_turno)
              JOIN equipo el ON el.id_equipo = p.id_equipo_local
              JOIN equipo ev ON ev.id_equipo = p.id_equipo_visitante
              JOIN complejo c ON c.id_complejo = p.id_complejo
             WHERE p.id_torneo = %s AND p.estado = 'programado'
               AND TIMESTAMP(p.dia, t.hora_inicio) >= NOW()
             ORDER BY p.dia, t.hora_inicio LIMIT 6""", p)
        return render_template("inicio.html", torneo=t, resumen=resumen, tabla=tabla, proximos=proximos)

    return app


app = crear_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False)
