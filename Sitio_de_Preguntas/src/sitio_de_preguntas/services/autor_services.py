from sitio_de_preguntas.extensions import db
from sitio_de_preguntas.models import User
from sitio_de_preguntas.services.validaciones import validate_id


class AutorNoEncontrado(ValueError):
    pass


def get_autor(user_id: int) -> User:
    """Devuelve el usuario como Autor (User ya hereda de Autor)."""
    validate_id(user_id)
    autor = db.session.get(User, user_id)
    if autor is None:
        raise AutorNoEncontrado(f"No existe un usuario con id {user_id}")
    return autor
