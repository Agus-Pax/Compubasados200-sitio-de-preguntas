from sitio_de_preguntas.extensions import db
from sitio_de_preguntas.models import Pregunta, Respuesta
from sitio_de_preguntas.services.autor_services import obtener_o_crear_autor


class ContenidoDeRespuestaInvalido(ValueError):
    pass


def crear_respuesta(pregunta_id, usuario_id, contenido) -> Respuesta:
    contenido = (contenido or "").strip()
    if not contenido:
        raise ContenidoDeRespuestaInvalido("La respuesta no puede estar vacía")

    pregunta = db.get_or_404(Pregunta, int(pregunta_id))
    autor = obtener_o_crear_autor(usuario_id)
    return autor.crear_respuesta(pregunta=pregunta, contenido=contenido)


def listar_respuestas(pregunta_id):
    return (
        Respuesta.query.filter_by(pregunta_id=int(pregunta_id))
        .order_by(Respuesta.votos.desc(), Respuesta.fecha_publicacion.asc())
        .all()
    )


def obtener_respuesta(id: int) -> Respuesta:
    return db.get_or_404(Respuesta, id)
