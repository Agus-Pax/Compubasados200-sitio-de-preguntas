from flask import Blueprint, abort, jsonify, request, session

from sitio_de_preguntas.extensions import db
from sitio_de_preguntas.models import User
from sitio_de_preguntas.services.User_services import (
<<<<<<< HEAD
    CredencialesInvalidas,
    CuentaBloqueada,
    EmailYaEnUso,
    UsuarioInvalido,
    autenticar,
    create_user,
=======
    EmailYaEnUso,
    UsuarioInvalido,
    create_user,
    delete_user,
    establecer_password,
    modify_user,
    verificar_password,
>>>>>>> main
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
        usuario = create_user(
            datos.get("name", ""),
            datos.get("email", ""),
<<<<<<< HEAD
            datos.get("password"),  # opcional; PasswordInvalida es un UsuarioInvalido
=======
            datos.get("password", ""),
>>>>>>> main
        )
    except EmailYaEnUso:
        abort(400, description="El email ya está en uso")
    except (UsuarioInvalido, ValidacionError) as exc:
        abort(400, description=str(exc))
    return jsonify(id=usuario.id, name=usuario.name, email=usuario.email), 201

<<<<<<< HEAD

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
=======
@users_bp.delete("/usuarios/<int:id>")
def borrar_usuario(id: int):
    actual = db.get_or_404(User, id)
    datos = request.get_json(silent=True) or {}
    if not verificar_password(actual, datos.get("password")):
        abort(400, description="Contraseña incorrecta")
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

@users_bp.patch("/usuarios/<int:id>/contraseña")
def modificar_contraseña(id: int):
    datos = request.get_json(silent=True) or {}
    actual = db.get_or_404(User, id)

    password_old = datos.get("password_old","")
    password_new = datos.get("password_new","")

    if (not actual.check_password(password_old)):
        abort(400, description="Contraseña incorrecta")
    try:
        establecer_password(actual, password_new)
    except UsuarioInvalido:
        abort(400, description="Contraseña invalida")
    return jsonify(id=actual.id, name=actual.name, email=actual.email, password = password_new), 200
    
>>>>>>> main
