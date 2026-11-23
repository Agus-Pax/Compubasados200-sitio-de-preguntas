from sitio_de_preguntas.extensions import db
from sitio_de_preguntas.models import Categoria, Etiqueta, Pregunta
from sitio_de_preguntas.services.autor_services import get_autor
from sitio_de_preguntas.services.etiqueta_services import obtener_etiquetas


class DatosDePreguntaInvalidos(ValueError):
    pass
class AutorNoPuedePreguntar(Exception):
    pass
class NoEsAutorDeLaPregunta(Exception):
    pass

def _validar(titulo, contenido, categoria_id):
    if type(titulo) is not str or type(contenido) is not str:
        raise DatosDePreguntaInvalidos("debe ser un string")
    titulo = (titulo or "").strip()
    contenido = (contenido or "").strip()
    if not titulo or not contenido:
        raise DatosDePreguntaInvalidos("titulo o contenido invalido")
    if len(titulo) > 200:
        raise DatosDePreguntaInvalidos("El titulo debe tener menos de 200 caracteres")
    if len(contenido) > 25000:
        raise DatosDePreguntaInvalidos("El contenido debe tener menos 25000 caracteres")
    validate_id(categoria_id)
    return titulo, contenido, categoria_id


def crear_pregunta(usuario_id, titulo, contenido, categoria_id, etiquetas_ids=None):
    titulo, contenido, categoria_id = _validar(titulo, contenido, categoria_id)
    validate_id(usuario_id)
    auth = get_autor(usuario_id)
    if not auth.can_ask():
        raise AutorNoPuedePreguntar("pregunta de agente")
    
    categoria = db.session.get(Categoria, categoria_id)
    if categoria is None:
        raise DatosDePreguntaInvalidos("La categoría no existe")
    et = obtener_etiquetas(etiquetas_ids)
    try:
        pregunta = Pregunta(
            titulo=titulo,
            contenido=contenido,
            autor=auth,
            categoria=categoria,
            etiquetas=et,
            )
        db.session.add(pregunta)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return pregunta


def modificar_pregunta(pregunta_id,usuario_id, titulo, contenido, categoria_id, etiquetas_ids=None):
    validate_id(usuario_id)
    validate_id(pregunta_id)
    pregunta = db.get_or_404(Pregunta, pregunta_id)
    
    auth=get_autor(usuario_id)
    if auth.id != pregunta.autor_id:
        raise NoEsAutorDeLaPregunta("Id registrado en pregunta no equivale al del usuario")

    titulo, contenido, categoria_id = _validar(titulo, contenido, categoria_id)

    categoria = db.session.get(Categoria, categoria_id)

    if categoria is None:
        raise DatosDePreguntaInvalidos("La categoría no existe")

    et = obtener_etiquetas(etiquetas_ids)
    try:
        pregunta.titulo = titulo
        pregunta.contenido = contenido
        pregunta.categoria = categoria
        # Si no se envían etiquetas se mantienen las actuales; una lista vacía
        # significa que se quieren quitar todas.
        if etiquetas_ids is not None:
            pregunta.etiquetas = et
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return pregunta


def listar_preguntas(categoria_id=None, etiqueta_id=None):
    consulta = Pregunta.query
    if categoria_id:
        consulta = consulta.filter(Pregunta.categoria_id == int(categoria_id))
    if etiqueta_id:
        consulta = consulta.join(Pregunta.etiquetas).filter(
            Etiqueta.id == int(etiqueta_id)
        )
    return consulta.order_by(Pregunta.fecha_publicacion.desc()).all()


def obtener_pregunta(id: int) -> Pregunta:
    return db.get_or_404(Pregunta, id)

#value error es temporal
def validate_id(id):
    if id is None:
        raise ValueError("id vacio")
    if type(id) is not int:
        raise ValueError("no es entero")
    if id < 1:
        raise ValueError("no existen ids negativos")
    return