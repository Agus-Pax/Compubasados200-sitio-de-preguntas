from sitio_de_preguntas.extensions import db
from sitio_de_preguntas.models import Pregunta, Respuesta,TipoRespuesta
from sitio_de_preguntas.services.autor_services import get_autor
from sitio_de_preguntas.services.fabrica_respuestas import FabricaConcretaRespuestas
class ContenidoDeRespuestaInvalido(ValueError):
    pass

class IDInvalido(ValueError):
    pass

def crear_respuesta(pregunta_id, usuario_id, contenido) -> Respuesta:
    validate_id(pregunta_id)
    validate_id(usuario_id)
    validar_contenido(contenido)

    contenido=contenido.strip()
    pregunta = db.get_or_404(Pregunta, pregunta_id)
    autor = get_autor(usuario_id)
    fabrica = FabricaConcretaRespuestas()
    
    try:
        respuesta=fabrica.crear_respuesta(
        pregunta=pregunta, 
        autor=autor,
        contenido=contenido,
        tipo=TipoRespuesta.USUARIO)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return respuesta


def listar_respuestas(pregunta_id):
    validate_id(pregunta_id)
    return (
        Respuesta.query.filter_by(pregunta_id=pregunta_id)
        .order_by(Respuesta.votos.desc(), Respuesta.fecha_publicacion.asc())
        .all()
    )


def obtener_respuesta(id: int) -> Respuesta:
    validate_id(id)
    return db.get_or_404(Respuesta, id)

def validar_contenido(contenido):
    if contenido is None:
        raise ContenidoDeRespuestaInvalido("contenido vacio")
    if type(contenido) is not str:
        raise ContenidoDeRespuestaInvalido("no es un string")
    if len(contenido) > 25000:
        raise ContenidoDeRespuestaInvalido("sobre pasa el limite")
    c=contenido.strip()
    if not c:
        raise ContenidoDeRespuestaInvalido("espacio en blanco")
    return

def validate_id(id):
    if id is None:
        raise IDInvalido("id vacio")
    if type(id) is not int:
        raise IDInvalido("no es entero")
    if id < 1:
        raise IDInvalido("no existen ids negativos")
    return
