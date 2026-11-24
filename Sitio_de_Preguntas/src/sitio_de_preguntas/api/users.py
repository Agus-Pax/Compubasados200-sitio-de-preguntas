from flask import Blueprint, abort, jsonify, request, session

from sitio_de_preguntas.models import User
from sitio_de_preguntas.services.User_services import (
    CredencialesInvalidas,
    CuentaBloqueada,
    EmailYaEnUso,
    UsuarioInvalido,
    autenticar,
    create_user,
)
from sitio_de_preguntas.services.validaciones import ValidacionError

users_bp = Blueprint("api_users", __name__, url_prefix="/api")


@users_bp.errorhandler(400)
def _bad_request(error):
    return jsonify(error=error.description), 400


@users_bp.get("/usuarios")
def listar_usuarios():
    usuarios = User.query.order_by(User.id).all()
    return jsonify(
        [{"id": u.id, "name": u.name, "email": u.email} for u in usuarios]
    )


@users_bp.post("/usuarios")
def crear_usuario():
    datos = request.get_json(silent=True) or {}
    try:
        usuario = create_user(
            datos.get("name", ""),
            datos.get("email", ""),
            datos.get("password"),  # opcional; PasswordInvalida es un UsuarioInvalido
        )
    except EmailYaEnUso:
        abort(400, description="El email ya está en uso")
    except (UsuarioInvalido, ValidacionError) as exc:
        abort(400, description=str(exc))
    return jsonify(id=usuario.id, name=usuario.name, email=usuario.email), 201


@users_bp.post("/usuarios/login")
def login():
    datos = request.get_json(silent=True)
    if not isinstance(datos, dict):
        abort(400, description="El cuerpo debe ser un objeto JSON")

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