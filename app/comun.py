"""Utilidades compartidas por las vistas: torneo seleccionado, etiquetas, etc."""
from flask import flash, request, session

from db import consultar

ETIQUETAS = {
    "inscripcion": "Inscripción", "en_curso": "En curso", "finalizado": "Finalizado",
    "programado": "Programado", "jugado": "Jugado", "postergado": "Postergado", "cancelado": "Cancelado",
    "grado": "Grado", "posgrado": "Posgrado", "docente": "Docente", "funcionario": "Funcionario",
    "sintetico": "Sintético", "parquet": "Parquet",
    "roja": "Tarjeta roja", "acumulacion_amarillas": "Acumulación de amarillas", "disciplinaria": "Disciplinaria",
    "amarilla": "Amarilla", "administrador": "Administrador", "planillero": "Planillero",
}

DEPARTAMENTOS = ["Artigas", "Canelones", "Cerro Largo", "Colonia", "Durazno", "Flores", "Florida",
                 "Lavalleja", "Maldonado", "Montevideo", "Paysandú", "Río Negro", "Rivera", "Rocha",
                 "Salto", "San José", "Soriano", "Tacuarembó", "Treinta y Tres"]
TIPOS_JUGADOR = ["grado", "posgrado", "docente", "funcionario"]


def etiqueta(valor):
    return ETIQUETAS.get(str(valor), str(valor).replace("_", " ").capitalize() if valor is not None else "")


def torneos():
    return consultar("SELECT id_torneo, nombre, anio, semestre, estado, fecha_inicio, fecha_fin "
                     "FROM torneo ORDER BY anio DESC, semestre DESC")


def torneo_seleccionado():
    """Torneo elegido en el selector (?torneo=) o, por defecto, la edición más reciente."""
    lista = torneos()
    if not lista:
        return None
    pedido = request.args.get("torneo", type=int) or session.get("torneo")
    elegido = next((t for t in lista if t["id_torneo"] == pedido), None)
    if elegido is None:
        elegido = next((t for t in lista if t["estado"] != "finalizado"), lista[0])
    session["torneo"] = elegido["id_torneo"]
    return elegido


def mostrar_errores(errores):
    for e in errores:
        flash(e, "error")
