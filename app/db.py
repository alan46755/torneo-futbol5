"""
Acceso a datos sin ORM: SQL escrito a mano con consultas parametrizadas
(mysql-connector-python). Cada request usa la conexión del usuario de base
de datos que corresponde al rol del usuario logueado.
"""
import re
from contextlib import contextmanager

import mysql.connector
from flask import current_app, g, session


class ErrorBD(Exception):
    """Error de base de datos ya traducido a un mensaje para el usuario."""


# Mensajes para las restricciones con nombre definidas en 01_esquema.sql
MENSAJES = {
    "chk_login_correo": "El correo no tiene un formato válido.",
    "chk_facultad_nombre": "El nombre de la facultad debe tener al menos 3 caracteres.",
    "uq_facultad_nombre": "Ya existe una facultad con ese nombre.",
    "chk_jugador_ci": "La cédula debe tener 7 u 8 dígitos (sin puntos ni guion).",
    "chk_jugador_nombre": "El nombre debe tener al menos 2 caracteres.",
    "chk_jugador_apellido": "El apellido debe tener al menos 2 caracteres.",
    "chk_jugador_email": "El email no tiene un formato válido.",
    "chk_jugador_fnac": "La fecha de nacimiento no es válida.",
    "uq_jugador_email": "Ya existe un jugador con ese email.",
    "jugador.PRIMARY": "Ya existe un jugador con esa cédula.",
    "uq_torneo_edicion": "Ya existe una edición del torneo para ese año y semestre.",
    "chk_torneo_semestre": "El semestre debe ser 1 o 2.",
    "chk_torneo_anio": "El año no es válido.",
    "chk_torneo_fechas": "La fecha de fin debe ser posterior a la de inicio.",
    "chk_torneo_nombre": "El nombre del torneo debe tener al menos 3 caracteres.",
    "uq_equipo_nombre": "Ya existe un equipo con ese nombre en esta edición.",
    "chk_equipo_nombre": "El nombre del equipo debe tener al menos 2 caracteres.",
    "fk_equipo_capitan": "El capitán debe ser un jugador del plantel del equipo.",
    "equipo_jugador_torneo.PRIMARY": "El jugador ya integra este plantel.",
    "uq_plantel_jugador_torneo": "El jugador ya integra otro equipo en esta edición del torneo.",
    "uq_plantel_camiseta": "Ese número de camiseta ya está usado en el equipo.",
    "chk_plantel_camiseta": "El número de camiseta debe estar entre 1 y 99.",
    "uq_complejo_nombre": "Ya existe un complejo con ese nombre.",
    "chk_complejo_nombre": "El nombre del complejo debe tener al menos 3 caracteres.",
    "chk_complejo_direccion": "La dirección debe tener al menos 5 caracteres.",
    "cancha.PRIMARY": "Ya existe una cancha con ese nombre en el complejo.",
    "chk_partido_rivales": "Un equipo no puede enfrentarse a sí mismo.",
    "chk_partido_fecha": "El número de fecha no es válido.",
    "uq_partido_cruce": "Estos equipos ya tienen un partido (no cancelado) en esta edición.",
    "uq_partido_cancha": "La cancha ya tiene un partido asignado en ese día y turno.",
    "planilla_partido.PRIMARY": "El jugador ya figura en la planilla.",
    "fk_planilla_plantel": "El jugador no pertenece al plantel del equipo indicado.",
    "fk_gol_planilla": "Solo pueden convertir goles los jugadores que figuran en la planilla.",
    "fk_tarjeta_planilla": "Solo pueden recibir tarjetas los jugadores que figuran en la planilla.",
    "chk_gol_minuto": "El minuto debe estar entre 1 y 60.",
    "chk_tarjeta_minuto": "El minuto debe estar entre 1 y 60.",
    "chk_sancion_cantidad": "La cantidad de fechas debe estar entre 1 y 20.",
    "chk_sancion_fecha": "La fecha de inicio de la sanción no es válida.",
    "chk_sancion_origen": "Las sanciones manuales deben ser de tipo disciplinaria.",
    "fk_sancion_plantel": "El jugador no integra ningún plantel en esa edición del torneo.",
}


def traducir_error(err: mysql.connector.Error) -> str:
    errno = getattr(err, "errno", None)
    msg = getattr(err, "msg", str(err))
    if errno == 1644:                       # SIGNAL desde trigger/procedimiento
        return msg
    if errno == 1062:                       # clave duplicada
        m = re.search(r"for key '([^']+)'", msg)
        clave = m.group(1) if m else ""
        return MENSAJES.get(clave) or MENSAJES.get(clave.split(".")[-1]) or "Ya existe un registro con esos datos."
    if errno == 3819:                       # CHECK violado
        m = re.search(r"Check constraint '([^']+)'", msg)
        return MENSAJES.get(m.group(1) if m else "", "Algún dato no cumple las restricciones de la base.")
    if errno in (1451, 3008):               # fila padre referenciada
        return "No se puede eliminar o modificar: el registro tiene información asociada."
    if errno == 1452:                       # FK hija inválida
        m = re.search(r"CONSTRAINT `([^`]+)`", msg)
        return MENSAJES.get(m.group(1) if m else "", "Algún dato hace referencia a un registro que no existe.")
    if errno in (1142, 1143, 1370):
        return "Su usuario no tiene permisos para realizar esta operación."
    if errno == 1406:
        return "Algún valor excede el largo permitido."
    if errno in (1265, 1292, 1366):
        return "Algún valor ingresado no tiene el formato correcto."
    if errno in (2003, 2005, 2013, 1045):
        return "No se pudo conectar con la base de datos."
    return f"Error de base de datos ({errno}): {msg}"


def _conectar(rol: str):
    cfg = current_app.config
    usuario, clave = cfg["DB_USUARIOS"][rol]
    return mysql.connector.connect(
        host=cfg["DB_HOST"], port=cfg["DB_PORT"], database=cfg["DB_NAME"],
        user=usuario, password=clave, autocommit=False,
        charset="utf8mb4", collation="utf8mb4_0900_ai_ci", time_zone=cfg["DB_TIME_ZONE"],
    )


def conexion(rol: str | None = None):
    """Conexión del request actual, con el usuario de BD del rol logueado."""
    rol = rol or session.get("rol")
    if rol not in ("auth", "administrador", "planillero"):
        raise ErrorBD("Sesión no válida.")
    clave = f"db_{rol}"
    if clave not in g:
        try:
            setattr(g, clave, _conectar(rol))
        except mysql.connector.Error as e:
            raise ErrorBD(traducir_error(e)) from e
    return getattr(g, clave)


def cerrar_conexiones(_exc=None):
    for rol in ("auth", "administrador", "planillero"):
        cn = g.pop(f"db_{rol}", None)
        if cn is not None:
            try:
                cn.close()
            except mysql.connector.Error:
                pass


def consultar(sql: str, params=None, uno: bool = False, rol: str | None = None):
    cn = conexion(rol)
    try:
        cur = cn.cursor(dictionary=True)
        cur.execute(sql, params or ())
        filas = cur.fetchall()
        cur.close()
        cn.commit()          # cierra la transacción de lectura (ve datos frescos)
    except mysql.connector.Error as e:
        cn.rollback()
        raise ErrorBD(traducir_error(e)) from e
    return (filas[0] if filas else None) if uno else filas


def ejecutar(sql: str, params=None) -> int:
    """Ejecuta una sentencia de escritura y confirma. Devuelve lastrowid o rowcount."""
    with transaccion() as cur:
        cur.execute(sql, params or ())
        return cur.lastrowid or cur.rowcount


@contextmanager
def transaccion():
    """Varias sentencias en una única transacción: todo o nada."""
    cn = conexion()
    cur = cn.cursor(dictionary=True)
    try:
        yield cur
        cn.commit()
    except mysql.connector.Error as e:
        cn.rollback()
        raise ErrorBD(traducir_error(e)) from e
    except Exception:
        cn.rollback()
        raise
    finally:
        cur.close()
