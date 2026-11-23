from flask import Blueprint, abort, jsonify, request

from sitio_de_preguntas.services.autor_services import AutorNoEncontrado
from sitio_de_preguntas.services.etiqueta_services import EtiquetaNoEncontrada
from sitio_de_preguntas.services.pregunta_services import (
    AutorNoPuedePreguntar,
    NoEsAutorDeLaPregunta,
    crear_pregunta,
    listar_preguntas,
    modificar_pregunta,
    obtener_pregunta,
)
from sitio_de_preguntas.services.respuesta_services import (
    crear_respuesta,
    listar_respuestas,
)
from sitio_de_preguntas.services.voto_services import (
    RespuestaNoEncontrada,
    TipoVoto,
    UsuarioNoEncontrado,
    VotoPropioNoPermitido,
    fijar_voto,
    retirar_voto,
)

api_questions_bp = Blueprint("api_questions", __name__, url_prefix="/api")


# --- Manejo de errores centralizado -----------------------------------------
# Una excepción nueva que no esté acá termina en 500 a propósito: así los bugs
# de programación (TypeError, AttributeError, etc.) no se disfrazan de 400.

@api_questions_bp.errorhandler(400)
def _bad_request(error):
    return jsonify(error=error.description), 400


@api_questions_bp.errorhandler(404)
def _not_found(error):
    return jsonify(error="No encontrado"), 404


def _registrar(status, *excepciones):
    for exc in excepciones:
        api_questions_bp.register_error_handler(
            exc, lambda e, s=status: (jsonify(error=str(e)), s)
        )


# ValueError cubre todas las excepciones de validación (IDInvalido,
# DatosDePreguntaInvalidos, ContenidoDeRespuestaInvalido, VotoInvalido...).
# Mientras pregunta_services siga lanzando ValueError plano para ids, hace falta.
_registrar(400, ValueError, EtiquetaNoEncontrada)
_registrar(403, AutorNoPuedePreguntar, NoEsAutorDeLaPregunta, VotoPropioNoPermitido)
_registrar(404, AutorNoEncontrado, UsuarioNoEncontrado, RespuestaNoEncontrada)


# --- Helpers ----------------------------------------------------------------

def _datos():
    """Devuelve el cuerpo JSON como dict, o 400 si no es un objeto."""
    datos = request.get_json(silent=True)
    if datos is None:
        return {}
    if not isinstance(datos, dict):
        abort(400, description="El cuerpo debe ser un objeto JSON")
    return datos


def _respuesta_json(respuesta):
    return {
        "id": respuesta.id,
        "contenido": respuesta.contenido,
        "autor_id": respuesta.autor_id,
        "votos": respuesta.votos,
        "fecha_publicacion": respuesta.fecha_publicacion.isoformat(),
    }


def _pregunta_json(pregunta, incluir_respuestas=False):
    datos = {
        "id": pregunta.id,
        "titulo": pregunta.titulo,
        "contenido": pregunta.contenido,
        "autor_id": pregunta.autor_id,
        "fecha_publicacion": pregunta.fecha_publicacion.isoformat(),
        "categoria": {"id": pregunta.categoria.id, "nombre": pregunta.categoria.nombre},
        "etiquetas": [{"id": e.id, "nombre": e.nombre} for e in pregunta.etiquetas],
    }
    if incluir_respuestas:
        datos["respuestas"] = [
            _respuesta_json(r) for r in listar_respuestas(pregunta.id)
        ]
    return datos


# --- Preguntas --------------------------------------------------------------

@api_questions_bp.get("/preguntas")
def listar_preguntas_api():
    preguntas = listar_preguntas(
        request.args.get("categoria_id"), request.args.get("etiqueta_id")
    )
    return jsonify([_pregunta_json(p) for p in preguntas])


@api_questions_bp.post("/preguntas")
def crear_pregunta_api():
    datos = _datos()
    pregunta = crear_pregunta(
        usuario_id=datos.get("usuario_id"),
        titulo=datos.get("titulo", ""),
        contenido=datos.get("contenido", ""),
        categoria_id=datos.get("categoria_id"),
        etiquetas_ids=datos.get("etiquetas_ids"),
    )
    return jsonify(_pregunta_json(pregunta)), 201


@api_questions_bp.get("/preguntas/<int:id>")
def detalle_pregunta_api(id):
    return jsonify(_pregunta_json(obtener_pregunta(id), incluir_respuestas=True))


@api_questions_bp.route("/preguntas/<int:id>", methods=["PATCH", "PUT"])
def modificar_pregunta_api(id):
    datos = _datos()
    actual = obtener_pregunta(id)  # solo para tomar valores por defecto
    pregunta = modificar_pregunta(
        pregunta_id=id,
        usuario_id=datos.get("usuario_id"),
        titulo=datos.get("titulo", actual.titulo),
        contenido=datos.get("contenido", actual.contenido),
        categoria_id=datos.get("categoria_id", actual.categoria_id),
        etiquetas_ids=datos.get("etiquetas_ids"),
    )
    return jsonify(_pregunta_json(pregunta))


# --- Respuestas -------------------------------------------------------------

@api_questions_bp.post("/preguntas/<int:id>/respuestas")
def crear_respuesta_api(id):
    datos = _datos()
    respuesta = crear_respuesta(
        pregunta_id=id,
        usuario_id=datos.get("usuario_id"),
        contenido=datos.get("contenido", ""),
    )
    return jsonify(_respuesta_json(respuesta)), 201


# --- Votos ------------------------------------------------------------------
# usuario_id viaja en el body mientras no haya autenticación (provisorio).
# Cuando exista el token, debe salir de ahí y nunca del cliente.

@api_questions_bp.put("/respuestas/<int:id>/voto")
def fijar_voto_api(id):
    datos = _datos()
    try:
        tipo = TipoVoto[str(datos.get("tipo", "")).upper()]
    except KeyError:
        abort(400, description="tipo debe ser A_FAVOR o EN_CONTRA")
    respuesta = fijar_voto(id, datos.get("usuario_id"), tipo)
    return jsonify(id=respuesta.id, votos=respuesta.votos)


@api_questions_bp.delete("/respuestas/<int:id>/voto")
def retirar_voto_api(id):
    datos = _datos()
    respuesta = retirar_voto(id, datos.get("usuario_id"))
    return jsonify(id=respuesta.id, votos=respuesta.votos)