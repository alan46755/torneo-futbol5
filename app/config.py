"""Configuración leída de variables de entorno (ver .env.example)."""
import os


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY", "cambiar-esta-clave-en-produccion")
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"

    DB_HOST = os.environ.get("DB_HOST", "127.0.0.1")
    DB_PORT = int(os.environ.get("DB_PORT", "3306"))
    DB_NAME = os.environ.get("DB_NAME", "torneo_futbol5")
    # Zona horaria de la sesión de MySQL: NOW() en los triggers usa la hora de Uruguay.
    DB_TIME_ZONE = os.environ.get("DB_TIME_ZONE", "-03:00")

    # Un usuario de base de datos por rol (permisos diferenciados en 02_seguridad.sql).
    DB_USUARIOS = {
        "auth": (os.environ.get("DB_AUTH_USER", "tf5_auth"),
                 os.environ.get("DB_AUTH_PASSWORD", "Auth.Tf5.2026")),
        "administrador": (os.environ.get("DB_ADMIN_USER", "tf5_admin"),
                          os.environ.get("DB_ADMIN_PASSWORD", "Admin.Tf5.2026")),
        "planillero": (os.environ.get("DB_PLANILLERO_USER", "tf5_planillero"),
                       os.environ.get("DB_PLANILLERO_PASSWORD", "Planillero.Tf5.2026")),
    }
