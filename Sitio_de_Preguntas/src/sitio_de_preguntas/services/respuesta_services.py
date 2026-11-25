from sqlalchemy import case

from sitio_de_preguntas.extensions import db
from sitio_de_preguntas.models import Pregunta, Respuesta, TipoRespuesta
from sitio_de_preguntas.services.autor_services import get_autor
from sitio_de_preguntas.services.fabrica_respuestas import FabricaConcretaRespuestas
from sitio_de_preguntas.services.pregunta_services import NoEsAutorDeLaPregunta
from sitio_de_preguntas.services.validaciones import validate_id


class ContenidoDeRespuestaInvalido(ValueError):
    pass


class RespuestaNoPertenecienteALaPregunta(ValueError):
    pass


def crear_respuesta(pregunta_id, usuario_id, contenido) -> Respuesta:
    validate_id(pregunta_id)
    validate_id(usuario_id)
    validar_contenido(contenido)

    contenido = contenido.strip()
    pregunta = db.get_or_404(Pregunta, pregunta_id)
    # Humanos y agentes IA pueden responder: get_autor devuelve cualquier Autor.
    autor = get_autor(usuario_id)
    fabrica = FabricaConcretaRespuestas()

    try:
        respuesta = fabrica.crear_respuesta(
            pregunta=pregunta,
            autor=autor,
            contenido=contenido,
            tipo=TipoRespuesta.USUARIO,
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return respuesta


def listar_respuestas(pregunta_id):
    validate_id(pregunta_id)
    consulta = Respuesta.query.filter_by(pregunta_id=pregunta_id)

    # La solución elegida por el autor va primero; el resto mantiene el orden
    # por votos y fecha. La aceptación no modifica ningún contador de votos.
    pregunta = db.session.get(Pregunta, pregunta_id)
    if pregunta is not None and pregunta.respuesta_aceptada_id is not None:
        consulta = consulta.order_by(
            case((Respuesta.id == pregunta.respuesta_aceptada_id, 0), else_=1)
        )

    return consulta.order_by(
        Respuesta.votos.desc(), Respuesta.fecha_publicacion.asc()
    ).all()


def obtener_respuesta(id: int) -> Respuesta:
    validate_id(id)
    return db.get_or_404(Respuesta, id)


def _verificar_autor(pregunta: Pregunta, autor_id) -> None:
    validate_id(autor_id)
    if pregunta.autor_id != autor_id:
        raise NoEsAutorDeLaPregunta(
            "Sólo el autor de la pregunta puede elegir la respuesta aceptada"
        )


def aceptar_respuesta(pregunta_id, respuesta_id, autor_id) -> Pregunta:
    """Marca una respuesta como solución; reemplaza la anterior si había una."""
    validate_id(pregunta_id)
    validate_id(respuesta_id)
    pregunta = db.get_or_404(Pregunta, pregunta_id)
    _verificar_autor(pregunta, autor_id)

    respuesta = db.get_or_404(Respuesta, respuesta_id)
    if respuesta.pregunta_id != pregunta.id:
        raise RespuestaNoPertenecienteALaPregunta(
            "La respuesta no pertenece a esta pregunta"
        )

    try:
        pregunta.respuesta_aceptada_id = respuesta.id
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return pregunta


def quitar_respuesta_aceptada(pregunta_id, autor_id) -> Pregunta:
    validate_id(pregunta_id)
    pregunta = db.get_or_404(Pregunta, pregunta_id)
    _verificar_autor(pregunta, autor_id)

    try:
        pregunta.respuesta_aceptada_id = None
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return pregunta


def validar_contenido(contenido):
    if contenido is None:
        raise ContenidoDeRespuestaInvalido("contenido vacio")
    if type(contenido) is not str:
        raise ContenidoDeRespuestaInvalido("no es un string")
    if len(contenido) > 25000:
        raise ContenidoDeRespuestaInvalido("sobre pasa el limite")
    c = contenido.strip()
    if not c:
        raise ContenidoDeRespuestaInvalido("espacio en blanco")
