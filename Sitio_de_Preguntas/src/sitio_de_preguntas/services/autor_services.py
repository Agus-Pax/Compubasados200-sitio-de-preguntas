from sqlalchemy.exc import IntegrityError
from sitio_de_preguntas.extensions import db
from sitio_de_preguntas.models import Autor, User


class AutorNoEncontrado(ValueError):
    pass

def get_autor(user_id:int) -> Autor:
    __validate_id(user_id)
    auth = Autor.query.filter_by(usuario_id=user_id).first()
    if auth is not None:
        return auth
    else:
        raise AutorNoEncontrado

def __validate_id(user_id:int):
    if user_id is None:
        raise ValueError("valor vacio")
    if type(user_id) is not int:
        raise ValueError("valor no entero")
    if user_id < 0:
        raise ValueError("id negativo")
    return

