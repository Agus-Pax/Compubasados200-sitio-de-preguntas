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
    delete_user,
    establecer_password,
    modify_user,
    verificar_password,
)

web_bp = Blueprint("web", __name__)


def _usuario_actual() -> User | None:
    user_id = session.get("user_id")
    if user_id is None:
        return None
    return db.session.get(User, user_id)


def _perfil_o_redirect():
    """Devuelve (usuario, None) o (None, redirect) si no hay sesión válida."""
    usuario = _usuario_actual()
    if usuario is None:
        session.clear()
        return None, redirect(url_for("web.login"))
    return usuario, None


def _valores_perfil(usuario: User) -> dict:
    return {
        "nombre": usuario.name,
        "email": usuario.email,
        "password_actual": "",
        "password_nueva": "",
        "password_confirmacion": "",
        "password_eliminar": "",
        "confirmacion_eliminar": False,
    }


def _errores_perfil() -> dict:
    return {
        "nombre": None,
        "email": None,
        "password_actual": None,
        "password_nueva": None,
        "password_confirmacion": None,
        "password_eliminar": None,
        "confirmacion_eliminar": None,
        "general": None,
    }


def _render_perfil(usuario: User, valores=None, errores=None):
    return render_template(
        "auth/perfil.html",
        usuario=usuario,
        valores={**_valores_perfil(usuario), **(valores or {})},
        errores={**_errores_perfil(), **(errores or {})},
    )


def _mensaje(exc: Exception) -> str:
    """Convierte los mensajes de los servicios en texto listo para la UI."""
    texto = str(exc).strip()
    return texto[:1].upper() + texto[1:] + ("" if texto.endswith(".") else ".")


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
    usuario, respuesta = _perfil_o_redirect()
    if respuesta is not None:
        return respuesta
    return _render_perfil(usuario)


@web_bp.post("/perfil/nombre")
def modificar_nombre():
    usuario, respuesta = _perfil_o_redirect()
    if respuesta is not None:
        return respuesta

    nombre = request.form.get("nombre", "").strip()
    errores = _errores_perfil()

    if not nombre:
        errores["nombre"] = "Ingresá tu nombre."
    else:
        try:
            # El email no cambia: se reutiliza modify_user para no duplicar validaciones.
            modify_user(usuario.id, nombre, usuario.email)
        except UsuarioInvalido as exc:
            errores["nombre"] = _mensaje(exc)
        else:
            flash("Nombre actualizado correctamente.", "success")
            return redirect(url_for("web.perfil"))

    return _render_perfil(usuario, valores={"nombre": nombre}, errores=errores)


@web_bp.post("/perfil/email")
def modificar_email():
    usuario, respuesta = _perfil_o_redirect()
    if respuesta is not None:
        return respuesta

    email = request.form.get("email", "").strip()
    errores = _errores_perfil()

    if not email:
        errores["email"] = "Ingresá tu correo electrónico."
    else:
        try:
            modify_user(usuario.id, usuario.name, email)
        except EmailYaEnUso:
            errores["email"] = "Ese correo ya está registrado por otro usuario."
        except UsuarioInvalido as exc:
            errores["email"] = (
                "El correo electrónico no tiene un formato válido."
                if "formato" in str(exc)
                else _mensaje(exc)
            )
        else:
            flash("Correo electrónico actualizado correctamente.", "success")
            return redirect(url_for("web.perfil"))

    return _render_perfil(usuario, valores={"email": email}, errores=errores)


@web_bp.post("/perfil/contraseña")
def modificar_contraseña():
    usuario, respuesta = _perfil_o_redirect()
    if respuesta is not None:
        return respuesta

    password_actual = request.form.get("password_actual", "")
    password_nueva = request.form.get("password_nueva", "")
    confirmacion = request.form.get("password_confirmacion", "")
    errores = _errores_perfil()

    if not password_actual:
        errores["password_actual"] = "Ingresá tu contraseña actual."
    if not password_nueva:
        errores["password_nueva"] = "Ingresá la nueva contraseña."
    if not confirmacion:
        errores["password_confirmacion"] = "Confirmá la nueva contraseña."
    elif password_nueva and password_nueva != confirmacion:
        errores["password_confirmacion"] = "Las contraseñas nuevas no coinciden."

    if not any(errores.values()):
        if not verificar_password(usuario, password_actual):
            errores["password_actual"] = "La contraseña actual es incorrecta."
        else:
            try:
                # establecer_password aplica el mismo hash de siempre y resetea bloqueos.
                establecer_password(usuario, password_nueva)
            except UsuarioInvalido as exc:
                errores["password_nueva"] = _mensaje(exc)
            else:
                flash("Contraseña actualizada correctamente.", "success")
                return redirect(url_for("web.perfil"))

    # Por seguridad no se devuelven las contraseñas escritas al formulario.
    return _render_perfil(usuario, errores=errores)


@web_bp.get("/perfil/eliminar")
def confirmar_eliminacion():
    usuario, respuesta = _perfil_o_redirect()
    if respuesta is not None:
        return respuesta

    return render_template(
        "auth/confirmar_eliminacion.html",
        usuario=usuario,
        valores=_valores_perfil(usuario),
        errores=_errores_perfil(),
    )


@web_bp.post("/perfil/eliminar")
def eliminar_cuenta():
    usuario, respuesta = _perfil_o_redirect()
    if respuesta is not None:
        return respuesta

    password = request.form.get("password_eliminar", "")
    confirmado = bool(request.form.get("confirmacion_eliminar"))
    errores = _errores_perfil()

    if not confirmado:
        errores["confirmacion_eliminar"] = (
            "Marcá la casilla para confirmar que querés eliminar tu cuenta."
        )
    if not password:
        errores["password_eliminar"] = "Ingresá tu contraseña para continuar."

    if not any(errores.values()):
        if not verificar_password(usuario, password):
            errores["password_eliminar"] = "La contraseña es incorrecta."
        else:
            # delete_user respeta las cascadas definidas en los modelos.
            delete_user(usuario.id)
            session.clear()
            flash("Tu cuenta y sus datos fueron eliminados.", "success")
            return redirect(url_for("web.login"))

    return render_template(
        "auth/confirmar_eliminacion.html",
        usuario=usuario,
        valores={"confirmacion_eliminar": confirmado},
        errores=errores,
    )


@web_bp.post("/logout")
def logout():
    session.clear()
    flash("Cerraste sesión correctamente.", "info")
    return redirect(url_for("web.login"))
