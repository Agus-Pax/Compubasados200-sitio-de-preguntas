from flask import Blueprint, abort, jsonify, request

from sitio_de_preguntas.models import User
from sitio_de_preguntas.services.User_services import EmailYaEnUso, create_user, delete_user

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
    return jsonify(id=usuario.id, name=usuario.name, email=usuario.email), 201

@users_bp.delete("/usuarios/<int:id>")
def borrar_usuario(id: int):
    delete_user(id)
    return jsonify(eliminado=True), 204
