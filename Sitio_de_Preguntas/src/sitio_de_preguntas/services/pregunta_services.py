from sitio_de_preguntas.extensions import db
from sitio_de_preguntas.models import Categoria, Etiqueta, Pregunta
from sitio_de_preguntas.services.autor_services import obtener_o_crear_autor
from sitio_de_preguntas.services.etiqueta_services import obtener_etiquetas


class DatosDePreguntaInvalidos(ValueError):
    pass


def _validar(titulo, contenido, categoria_id):
    titulo = (titulo or "").strip()
    contenido = (contenido or "").strip()
    if not titulo:
        raise DatosDePreguntaInvalidos("La pregunta debe tener un título")
    if not contenido:
        raise DatosDePreguntaInvalidos("La pregunta debe tener un contenido")

    if categoria_id is None or categoria_id == "":
        raise DatosDePreguntaInvalidos("La pregunta debe tener una categoría")
    if isinstance(categoria_id, (list, tuple, dict, set)):
        raise DatosDePreguntaInvalidos("La pregunta debe tener una sola categoría")
    try:
        categoria_id = int(categoria_id)
    except (TypeError, ValueError) as exc:
        raise DatosDePreguntaInvalidos("La categoría no es válida") from exc

    return titulo, contenido, categoria_id


def crear_pregunta(usuario_id, titulo, contenido, categoria_id, etiquetas_ids=None):
    titulo, contenido, categoria_id = _validar(titulo, contenido, categoria_id)

    categoria = db.session.get(Categoria, categoria_id)
    if categoria is None:
        raise DatosDePreguntaInvalidos("La categoría no existe")

    autor = obtener_o_crear_autor(usuario_id)
    pregunta = Pregunta(
        titulo=titulo,
        contenido=contenido,
        autor=autor,
        categoria=categoria,
        etiquetas=obtener_etiquetas(etiquetas_ids),
    )
    db.session.add(pregunta)
    db.session.commit()
    return pregunta


def modificar_pregunta(id, titulo, contenido, categoria_id, etiquetas_ids=None):
    pregunta = db.get_or_404(Pregunta, id)
    titulo, contenido, categoria_id = _validar(titulo, contenido, categoria_id)

    categoria = db.session.get(Categoria, categoria_id)
    if categoria is None:
        raise DatosDePreguntaInvalidos("La categoría no existe")

    pregunta.titulo = titulo
    pregunta.contenido = contenido
    pregunta.categoria = categoria
    # Si no se envían etiquetas se mantienen las actuales; una lista vacía
    # significa que se quieren quitar todas.
    if etiquetas_ids is not None:
        pregunta.etiquetas = obtener_etiquetas(etiquetas_ids)
    db.session.commit()
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
