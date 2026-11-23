from flask import Blueprint, abort, jsonify, request

from sitio_de_preguntas.extensions import db
from sitio_de_preguntas.models import User
from sitio_de_preguntas.services.User_services import (
    EmailYaEnUso,
    UsuarioInvalido,
    create_user,
    delete_user,
    modify_user,
)
from sitio_de_preguntas.services.validaciones import ValidacionError

users_bp = Blueprint("api_users", __name__, url_prefix="/api")


@users_bp.errorhandler(400)
def _bad_request(error):
    return jsonify(error=error.description), 400

@users_bp.errorhandler(404)
def _not_found(error):
    return jsonify(error="No encontrado"), 404


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
        usuario = create_user(datos.get("name", ""), datos.get("email", ""))
    except EmailYaEnUso:
        abort(400, description="El email ya está en uso")
    except (UsuarioInvalido, ValidacionError) as exc:
        abort(400, description=str(exc))
    return jsonify(id=usuario.id, name=usuario.name, email=usuario.email), 201

@users_bp.delete("/usuarios/<int:id>")
def borrar_usuario(id: int):
    delete_user(id)
    return "", 204

@users_bp.patch("/usuarios/<int:id>")
def modificar_usuario(id: int):
    datos = request.get_json(silent=True) or {}
    actual = db.get_or_404(User, id)
    
    nombre = datos.get("name", actual.name)
    email = datos.get("email", actual.email)

    if not isinstance(nombre, str) or not isinstance(email, str):
        abort(400, description="nombre e email deben ser strings")

    try:
        usuario = modify_user(id, nombre, email)
    except EmailYaEnUso:
        abort(400, description="El email ya está en uso")
    return jsonify(id=usuario.id, name=usuario.name, email=usuario.email), 200
    
