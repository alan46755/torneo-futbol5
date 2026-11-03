"""Login, control de acceso por rol y protección CSRF."""
import secrets
from functools import wraps

from flask import (Blueprint, abort, flash, redirect, render_template, request, session, url_for)
from werkzeug.security import check_password_hash

from db import ErrorBD, consultar
from validaciones import Validador

bp = Blueprint("auth", __name__)


def login_requerido(vista):
    @wraps(vista)
    def envoltura(*args, **kwargs):
        if "usuario" not in session:
            return redirect(url_for("auth.login", siguiente=request.path))
        return vista(*args, **kwargs)
    return envoltura


def rol_requerido(*roles):
    def decorador(vista):
        @wraps(vista)
        @login_requerido
        def envoltura(*args, **kwargs):
            if session.get("rol") not in roles:
                abort(403)
            return vista(*args, **kwargs)
        return envoltura
    return decorador


solo_admin = rol_requerido("administrador")


# ---- CSRF -----------------------------------------------------------------
def csrf_token():
    if "_csrf" not in session:
        session["_csrf"] = secrets.token_hex(16)
    return session["_csrf"]


def verificar_csrf():
    if request.method == "POST":
        token = request.form.get("_csrf")
        if not token or token != session.get("_csrf"):
            abort(400, "Token CSRF inválido. Recargue la página e intente de nuevo.")


# ---- Rutas ------------------------------------------------------------------
@bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        v = Validador(request.form)
        correo = v.email("correo", "El correo")
        clave = v.texto("contrasena", "La contraseña", 1, 100)
        if v.ok:
            try:
                u = consultar("SELECT correo, contrasena, rol, activo FROM login WHERE correo = %s",
                              (correo,), uno=True, rol="auth")
            except ErrorBD as e:
                flash(str(e), "error")
                return render_template("login.html", correo=correo)
            if u and u["activo"] and check_password_hash(u["contrasena"], clave):
                session.clear()
                session["usuario"] = u["correo"]
                session["rol"] = u["rol"]
                destino = request.args.get("siguiente") or ""
                if not destino.startswith("/") or destino.startswith("//"):
                    destino = url_for("inicio")
                return redirect(destino)
            v.error("Correo o contraseña incorrectos.")
        for e in v.errores:
            flash(e, "error")
        return render_template("login.html", correo=request.form.get("correo", ""))
    return render_template("login.html")


@bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    flash("Sesión cerrada.", "ok")
    return redirect(url_for("auth.login"))
