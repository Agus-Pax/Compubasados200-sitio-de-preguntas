from sitio_de_preguntas.extensions import db
from sitio_de_preguntas.models import Autor
from sitio_de_preguntas.services.validaciones import validate_id


class AutorNoEncontrado(ValueError):
    pass


def get_autor(autor_id: int) -> Autor:
    """Devuelve el autor por id, sea humano (User) o agente IA."""
    validate_id(autor_id)
    autor = db.session.get(Autor, autor_id)
    if autor is None:
        raise AutorNoEncontrado(f"No existe un autor con id {autor_id}")
    return autor
