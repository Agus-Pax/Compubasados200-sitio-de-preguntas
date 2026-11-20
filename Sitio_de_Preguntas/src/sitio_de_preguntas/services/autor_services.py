from sitio_de_preguntas.extensions import db
from sitio_de_preguntas.models import Autor, User


class UsuarioNoEncontrado(LookupError):
    pass


def obtener_o_crear_autor(usuario_id: int) -> Autor:
    """Devuelve el autor humano de un usuario, creándolo si todavía no existe.

    La función hace ``flush`` pero no hace ``commit``: quien la llama debe
    confirmar la transacción junto con la pregunta o respuesta creada.
    """
    usuario_id = int(usuario_id)
    autor = Autor.query.filter_by(usuario_id=usuario_id).first()
    if autor is not None:
        return autor

    if db.session.get(User, usuario_id) is None:
        raise UsuarioNoEncontrado(f"No existe el usuario con id {usuario_id}")

    autor = Autor(usuario_id=usuario_id)
    db.session.add(autor)
    db.session.flush()
    return autor
