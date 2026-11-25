from flask import Blueprint, abort, jsonify, request, session

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
from sitio_de_preguntas.services.validaciones import ValidacionError

users_bp = Blueprint("api_users", __name__, url_prefix="/api")

@users_bp.errorhandler(400)
def _bad_request(error):
    return jsonify(error=error.description), 400

@users_bp.errorhandler(401)
def _unauthorized(error):
    return jsonify(error=error.description), 401


@users_bp.errorhandler(403)
def _forbidden(error):
    return jsonify(error=error.description), 403

@users_bp.errorhandler(404)
def _not_found(error):
    return jsonify(error="No encontrado"), 404


#---helpers---------
def _json_objeto() -> dict:
    """Devuelve el cuerpo JSON; si no es un objeto (o falta), responde 400."""
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        abort(400, description="El cuerpo debe ser un objeto JSON")
    return datos


def _exigir_propietario(id: int) -> None:
    """Solo el propio usuario (con sesión iniciada) puede modificarse o borrarse."""
    actual = session.get("user_id")
    if actual is None:
        abort(401, description="Hay que iniciar sesión")
    if actual != id:
        abort(403, description="No tenés permiso para operar sobre otro usuario")


@users_bp.get("/usuarios")
def listar_usuarios():
    usuarios = User.query.order_by(User.id).all()
    return jsonify(
        [{"id": u.id, "name": u.name, "email": u.email} for u in usuarios]
    )

#---rutas--------

@users_bp.post("/usuarios")
def crear_usuario():
    datos = _json_objeto()
    try:
        usuario = create_user(
            datos.get("name", ""),
            datos.get("email", ""),
            datos.get("password", ""),
        )
    except EmailYaEnUso:
        abort(400, description="El email ya está en uso")
    except (UsuarioInvalido, ValidacionError) as exc:
        abort(400, description=str(exc))
    return jsonify(id=usuario.id, name=usuario.name, email=usuario.email), 201


@users_bp.post("/usuarios/login")
def login():
    datos = _json_objeto()

    try:
        usuario = autenticar(datos.get("email"), datos.get("password"))
    except CuentaBloqueada as e:
        return jsonify(
            error="Cuenta bloqueada temporalmente por demasiados intentos fallidos.",
            bloqueada_hasta=e.hasta.isoformat() + "Z",
        ), 423
    except CredencialesInvalidas as e:
        cuerpo = {"error": "Usuario o contraseña incorrectos."}
        if e.intentos_restantes is not None:
            cuerpo["intentos_restantes"] = e.intentos_restantes
        return jsonify(cuerpo), 401

    session.clear()
    session["user_id"] = usuario.id
    return jsonify(
        message="Acceso correcto", user={"id": usuario.id, "name": usuario.name}
    )


@users_bp.post("/usuarios/logout")
def logout():
    session.clear()
    return jsonify(message="Sesión cerrada")


@users_bp.delete("/usuarios/<int:id>")
def borrar_usuario(id: int):
    _exigir_propietario(id)
    datos = _json_objeto()
    actual = db.get_or_404(User, id)
    if not verificar_password(actual, datos.get("password")):
        abort(400, description="Contraseña incorrecta")
    delete_user(id)
    session.clear()  # la cuenta ya no existe: se cierra la sesión
    return "", 204

@users_bp.patch("/usuarios/<int:id>")
def modificar_usuario(id: int):
    _exigir_propietario(id)
    datos = _json_objeto()
    actual = db.get_or_404(User, id)

    try:
        usuario = modify_user(
            id,
            datos.get("name", actual.name),
            datos.get("email", actual.email),
        )
    except EmailYaEnUso:
        abort(400, description="El email ya está en uso")
    except (UsuarioInvalido, ValidacionError) as exc:
        abort(400, description=str(exc))
    return jsonify(id=usuario.id, name=usuario.name, email=usuario.email), 200

@users_bp.patch("/usuarios/<int:id>/contraseña")
def modificar_contraseña(id: int):
    _exigir_propietario(id)
    datos = _json_objeto()
    actual = db.get_or_404(User, id)

    if not verificar_password(actual, datos.get("password_old")):
        abort(400, description="Contraseña incorrecta")
    try:
        establecer_password(actual, datos.get("password_new"))
    except UsuarioInvalido as exc:
        abort(400, description=str(exc))
    # No se devuelve la contraseña (antes se devolvía password_new en la respuesta).
    return jsonify(id=actual.id, name=actual.name, email=actual.email), 200