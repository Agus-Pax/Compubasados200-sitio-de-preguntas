from flask import Blueprint, jsonify, request, session

from sitio_de_preguntas.services.User_services import (
    CredencialesInvalidas,
    CuentaBloqueada,
    autenticar,
)

auth_bp = Blueprint("auth", __name__, url_prefix="/auth")


@auth_bp.post("/login")
def login():
    datos = request.get_json(silent=True) or {}
    try:
        user = autenticar(datos.get("email", ""), datos.get("password", ""))
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
    session["user_id"] = user.id
    return jsonify(message="Acceso correcto", user={"id": user.id, "name": user.name})


@auth_bp.post("/logout")
def logout():
    session.clear()
    return jsonify(message="Sesión cerrada")