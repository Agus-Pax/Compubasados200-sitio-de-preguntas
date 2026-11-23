from sitio_de_preguntas.models import Autor
from sitio_de_preguntas.services.validaciones import validate_id


class AutorNoEncontrado(ValueError):
    pass

def get_autor(user_id:int) -> Autor:
    validate_id(user_id)
    auth = Autor.query.filter_by(usuario_id=user_id).first()
    if auth is not None:
        return auth
    else:
        raise AutorNoEncontrado(f"No existe un autor para el usuario {user_id}")


