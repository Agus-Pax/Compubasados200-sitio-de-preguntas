from flask import Blueprint, abort, jsonify, request
from werkzeug.exceptions import NotFound

from sitio_de_preguntas.services.autor_services import UsuarioNoEncontrado
from sitio_de_preguntas.services.etiqueta_services import EtiquetaNoEncontrada
from sitio_de_preguntas.services.pregunta_services import (
    DatosDePreguntaInvalidos,
    crear_pregunta,
    listar_preguntas,
    modificar_pregunta,
    obtener_pregunta,
)
from sitio_de_preguntas.services.respuesta_services import (
    ContenidoDeRespuestaInvalido,
    crear_respuesta,
    listar_respuestas,
)
from sitio_de_preguntas.services.voto_services import VotoInvalido, votar_respuesta

api_questions_bp = Blueprint("api_questions", __name__, url_prefix="/api")


@api_questions_bp.errorhandler(400)
def _bad_request(error):
    return jsonify(error=error.description), 400


@api_questions_bp.errorhandler(404)
def _not_found(error):
    return jsonify(error="No encontrado"), 404


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


@api_questions_bp.get("/preguntas")
def listar_preguntas_api():
    preguntas = listar_preguntas(
        request.args.get("categoria_id"), request.args.get("etiqueta_id")
    )
    return jsonify([_pregunta_json(p) for p in preguntas])


@api_questions_bp.post("/preguntas")
def crear_pregunta_api():
    datos = request.get_json(silent=True) or {}
    try:
        pregunta = crear_pregunta(
            usuario_id=datos.get("usuario_id"),
            titulo=datos.get("titulo", ""),
            contenido=datos.get("contenido", ""),
            categoria_id=datos.get("categoria_id"),
            etiquetas_ids=datos.get("etiquetas_ids"),
        )
    except (
        DatosDePreguntaInvalidos,
        EtiquetaNoEncontrada,
        UsuarioNoEncontrado,
        ValueError,
        TypeError,
    ) as exc:
        abort(400, description=str(exc))
    return jsonify(_pregunta_json(pregunta)), 201


@api_questions_bp.get("/preguntas/<int:id>")
def detalle_pregunta_api(id):
    return jsonify(_pregunta_json(obtener_pregunta(id), incluir_respuestas=True))


@api_questions_bp.route("/preguntas/<int:id>", methods=["PATCH", "PUT"])
def modificar_pregunta_api(id):
    datos = request.get_json(silent=True) or {}
    pregunta = obtener_pregunta(id)
    try:
        pregunta = modificar_pregunta(
            id=id,
            titulo=datos.get("titulo", pregunta.titulo),
            contenido=datos.get("contenido", pregunta.contenido),
            categoria_id=datos.get("categoria_id", pregunta.categoria_id),
            etiquetas_ids=datos.get("etiquetas_ids"),
        )
    except (DatosDePreguntaInvalidos, EtiquetaNoEncontrada, ValueError, TypeError) as exc:
        abort(400, description=str(exc))
    return jsonify(_pregunta_json(pregunta))


@api_questions_bp.post("/preguntas/<int:id>/respuestas")
def crear_respuesta_api(id):
    datos = request.get_json(silent=True) or {}
    try:
        respuesta = crear_respuesta(
            pregunta_id=id,
            usuario_id=datos.get("usuario_id"),
            contenido=datos.get("contenido", ""),
        )
    except (ContenidoDeRespuestaInvalido, UsuarioNoEncontrado, ValueError) as exc:
        abort(400, description=str(exc))
    return jsonify(_respuesta_json(respuesta)), 201


@api_questions_bp.post("/respuestas/<int:id>/votos")
def votar_respuesta_api(id):
    datos = request.get_json(silent=True) or {}
    try:
        respuesta = votar_respuesta(
            respuesta_id=id,
            usuario_id=datos.get("usuario_id"),
            valor=datos.get("valor"),
        )
    except (VotoInvalido, UsuarioNoEncontrado, ValueError, TypeError) as exc:
        abort(400, description=str(exc))
    except NotFound:
        abort(404, description="La respuesta no existe")
    return jsonify(id=respuesta.id, votos=respuesta.votos)
