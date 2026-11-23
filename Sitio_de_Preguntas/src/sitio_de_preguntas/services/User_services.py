from datetime import timedelta

from flask import current_app
from sqlalchemy.exc import IntegrityError

from sitio_de_preguntas.utils import utcnow_naive
from sitio_de_preguntas.extensions import db
from sitio_de_preguntas.models import Autor, Pregunta, Respuesta, User, Voto
from sitio_de_preguntas.services.validaciones import validate_id

MAX_NOMBRE = 120
MAX_EMAIL = 255

class UsuarioInvalido(ValueError):
    pass


class CredencialesInvalidas(Exception):
    def __init__(self, intentos_restantes: int | None = None):
        self.intentos_restantes = intentos_restantes
        super().__init__("Usuario o contraseña incorrectos")


class CuentaBloqueada(Exception):
    def __init__(self, hasta):
        self.hasta = hasta
        super().__init__("Cuenta bloqueada temporalmente")


class EmailYaEnUso(ValueError):
    pass


class UsuarioConContenido(Exception):
    pass


def create_user(name: str, email: str, password: str | None = None):
    """``password`` es opcional para no romper los llamados existentes,
    pero un usuario sin contraseña no puede iniciar sesión."""
    if User.query.filter_by(email = email).first():
        raise EmailYaEnUso
    user = User(name=name, email=email)
    if password:
        user.set_password(password)
    db.session.add(user)
    db.session.commit()
    return user


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
# --- autenticación ---

def establecer_password(user: User, password: str) -> None:
    """Úsala cuando un usuario cambie su contraseña (o para dársela por primera vez)."""
    user.set_password(password)
    user.failed_attempts = 0
    user.locked_until = None
    db.session.commit()


def autenticar(email: str, password: str) -> User:
    """Devuelve el User si las credenciales son correctas.

    - Usuario existente + contraseña correcta -> acceso normal.
    - Contraseña incorrecta -> CredencialesInvalidas (se notifica al usuario).
    - 3 fallos seguidos -> la cuenta se bloquea temporalmente (CuentaBloqueada).
    """
    max_intentos = current_app.config["MAX_LOGIN_ATTEMPTS"]
    minutos = current_app.config["LOCK_MINUTES"]

    user = User.query.filter_by(email=email).first()
    if user is None:
        # Mismo error que una contraseña mala: no revela qué emails existen.
        raise CredencialesInvalidas()

    # Bloqueo vencido -> se limpia.
    if user.locked_until is not None and not user.is_locked():
        user.locked_until = None
        user.failed_attempts = 0
        db.session.commit()

    # Bloqueada: se rechaza incluso con la contraseña correcta.
    if user.is_locked():
        raise CuentaBloqueada(user.locked_until)

    if user.check_password(password):
        user.failed_attempts = 0
        db.session.commit()
        return user

    user.failed_attempts += 1
    if user.failed_attempts >= max_intentos:
        user.locked_until = utcnow_naive() + timedelta(minutes=minutos)
        user.failed_attempts = 0
        db.session.commit()
        raise CuentaBloqueada(user.locked_until)

    db.session.commit()
    raise CredencialesInvalidas(max_intentos - user.failed_attempts)