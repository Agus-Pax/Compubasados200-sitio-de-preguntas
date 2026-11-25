from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from sitio_de_preguntas.extensions import db
from sitio_de_preguntas.models import User
from sitio_de_preguntas.services.User_services import (
    CredencialesInvalidas,
    CuentaBloqueada,
    EmailYaEnUso,
    UsuarioInvalido,
    autenticar,
    create_user,
)

web_bp = Blueprint("web", __name__)


def _usuario_actual() -> User | None:
    user_id = session.get("user_id")
    if user_id is None:
        return None
    return db.session.get(User, user_id)


@web_bp.get("/")
def inicio():
    if _usuario_actual() is None:
        return redirect(url_for("web.login"))
    return redirect(url_for("home.inicio"))


@web_bp.route("/login", methods=["GET", "POST"])
def login():
    if _usuario_actual() is not None:
        return redirect(url_for("home.inicio"))

    errores = {"email": None, "password": None, "general": None}
    email = ""

    if request.method == "POST":
        email = request.form.get("email", "").strip()
        password = request.form.get("password", "")

        if not email:
            errores["email"] = "Ingresá tu correo electrónico."
        if not password:
            errores["password"] = "Ingresá tu contraseña."

        if not any(errores.values()):
            try:
                usuario = autenticar(email.lower(), password)
            except CredencialesInvalidas as exc:
                mensaje = "Correo electrónico o contraseña incorrectos."
                if exc.intentos_restantes is not None:
                    mensaje += f" Te quedan {exc.intentos_restantes} intentos."
                errores["general"] = mensaje
            except CuentaBloqueada:
                errores["general"] = (
                    "Cuenta bloqueada temporalmente por demasiados intentos "
                    "fallidos. Probá nuevamente más tarde."
                )
            else:
                session.clear()
                session["user_id"] = usuario.id
                return redirect(url_for("home.inicio"))

    return render_template("auth/login.html", email=email, errores=errores)


@web_bp.route("/registro", methods=["GET", "POST"])
def registro():
    if _usuario_actual() is not None:
        return redirect(url_for("home.inicio"))

    errores = {
        "nombre": None,
        "email": None,
        "password": None,
        "confirmacion": None,
        "general": None,
    }
    valores = {"nombre": "", "email": ""}

    if request.method == "POST":
        valores["nombre"] = request.form.get("nombre", "").strip()
        valores["email"] = request.form.get("email", "").strip()
        password = request.form.get("password", "")
        confirmacion = request.form.get("confirmacion", "")

        if not valores["nombre"]:
            errores["nombre"] = "Ingresá tu nombre."
        if not valores["email"]:
            errores["email"] = "Ingresá tu correo electrónico."
        if not password:
            errores["password"] = "Ingresá tu contraseña."
        if not confirmacion:
            errores["confirmacion"] = "Confirmá tu contraseña."
        elif password and password != confirmacion:
            errores["confirmacion"] = "Las contraseñas no coinciden."

        if not any(errores.values()):
            try:
                create_user(valores["nombre"], valores["email"], password)
            except EmailYaEnUso:
                errores["email"] = "Ese correo ya está registrado. Iniciá sesión o usá otro."
            except UsuarioInvalido as exc:
                errores["general"] = f"No pudimos crear la cuenta: {exc}"
            else:
                flash("Cuenta creada correctamente. Ya podés iniciar sesión.", "success")
                return redirect(url_for("web.login"))

    return render_template("auth/registro.html", valores=valores, errores=errores)


@web_bp.get("/perfil")
def perfil():
    usuario = _usuario_actual()
    if usuario is None:
        session.clear()
        return redirect(url_for("web.login"))
    return render_template("auth/perfil.html", usuario=usuario)


@web_bp.post("/logout")
def logout():
    session.clear()
    flash("Cerraste sesión correctamente.", "info")
    return redirect(url_for("web.login"))
