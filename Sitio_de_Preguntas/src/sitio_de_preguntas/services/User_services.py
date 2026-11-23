from sqlalchemy.exc import IntegrityError

from sitio_de_preguntas.extensions import db
from sitio_de_preguntas.models import Autor, Pregunta, Respuesta, User, Voto

MAX_NOMBRE = 120
MAX_EMAIL = 255


class UsuarioInvalido(ValueError):
    pass


class EmailYaEnUso(ValueError):
    pass


class UsuarioConContenido(Exception):
    pass


# temporal: unificar con validate_id/IDInvalido del módulo compartido
def validate_id(id):
    if id is None:
        raise UsuarioInvalido("id vacío")
    if type(id) is not int:
        raise UsuarioInvalido(f"el id debe ser entero: {id!r}")
    if id < 1:
        raise UsuarioInvalido(f"el id debe ser positivo: {id!r}")


def _validar_email(email: str) -> None:
    local, sep, dominio = email.partition("@")
    if (
        not sep
        or not local
        or "@" in dominio
        or " " in email
        or "." not in dominio
        or dominio.startswith(".")
        or dominio.endswith(".")
    ):
        raise UsuarioInvalido("el email no tiene un formato válido")


def _validar_datos(name, email):
    if type(name) is not str or type(email) is not str:
        raise UsuarioInvalido("nombre y email deben ser texto")
    name = name.strip()
    email = email.strip().lower()
    if not name or not email:
        raise UsuarioInvalido("nombre y email no pueden estar vacíos")
    if len(name) > MAX_NOMBRE:
        raise UsuarioInvalido(f"el nombre supera {MAX_NOMBRE} caracteres")
    if len(email) > MAX_EMAIL:
        raise UsuarioInvalido(f"el email supera {MAX_EMAIL} caracteres")
    _validar_email(email)
    return name, email


def create_user(name: str, email: str) -> User:
    name, email = _validar_datos(name, email)
    try:
        user = User(name=name, email=email)
        db.session.add(user)
        db.session.flush()  # asigna user.id
        db.session.add(Autor(usuario_id=user.id))
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        if User.query.filter_by(email=email).first() is not None:
            raise EmailYaEnUso(f"El email {email} ya está en uso") from exc
        raise
    except Exception:
        db.session.rollback()
        raise
    return user


def modify_user(user_id: int, name: str, email: str) -> User:
    validate_id(user_id)
    name, email = _validar_datos(name, email)
    user = db.get_or_404(User, user_id)
    try:
        user.name = name
        user.email = email
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        otro = User.query.filter(User.email == email, User.id != user_id).first()
        if otro is not None:
            raise EmailYaEnUso(f"El email {email} ya está en uso") from exc
        raise
    except Exception:
        db.session.rollback()
        raise
    return user


def delete_user(user_id: int) -> None:
    validate_id(user_id)
    user = db.get_or_404(User, user_id)
    autor = Autor.query.filter_by(usuario_id=user.id).first()

    if autor is not None:
        tiene_contenido = (
            Pregunta.query.filter_by(autor_id=autor.id).first() is not None
            or Respuesta.query.filter_by(autor_id=autor.id).first() is not None
        )
        if tiene_contenido:
            raise UsuarioConContenido(
                f"El usuario {user_id} tiene preguntas o respuestas"
            )
    if Voto.query.filter_by(usuario_id=user.id).first() is not None:
        raise UsuarioConContenido(f"El usuario {user_id} tiene votos registrados")

    try:
        if autor is not None:
            db.session.delete(autor)
            db.session.flush()
        db.session.delete(user)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise