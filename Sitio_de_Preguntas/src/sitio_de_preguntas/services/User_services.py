from datetime import UTC, datetime, timedelta

from flask import current_app
from sqlalchemy.exc import IntegrityError

from sitio_de_preguntas.extensions import db
from sitio_de_preguntas.models import User
from sitio_de_preguntas.utils import utcnow_naive
from sitio_de_preguntas.services.validaciones import validate_id

MAX_NOMBRE = 120
MAX_EMAIL = 255
MIN_PASSWORD = 8
MAX_PASSWORD = 128

class UsuarioInvalido(ValueError):
    pass


class PasswordInvalida(UsuarioInvalido):
    pass


class EmailYaEnUso(ValueError):
    pass


class CredencialesInvalidas(Exception):
    def __init__(self, intentos_restantes: int | None = None):
        self.intentos_restantes = intentos_restantes
        super().__init__("Usuario o contraseña incorrectos")


class CuentaBloqueada(Exception):
    def __init__(self, hasta):
        self.hasta = hasta
        super().__init__("Cuenta bloqueada temporalmente")


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

#confirmar si la contraseña cumple con las restrcciones
def _validar_password(password: str) -> str:
    """Confirma que la contraseña cumple las restricciones (no la hashea)."""
    if type(password) is not str:
        raise PasswordInvalida("la contraseña debe ser texto")
    if not password.strip():
        raise PasswordInvalida("la contraseña no puede estar vacía")
    if not MIN_PASSWORD <= len(password) <= MAX_PASSWORD:
        raise PasswordInvalida(
            f"la contraseña debe tener entre {MIN_PASSWORD} y {MAX_PASSWORD} caracteres"
        )
    return password


def _guardar() -> None:
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise


def create_user(name: str, email: str, password: str) -> User:
    name, email = _validar_datos(name, email)
    password = _validar_password(password)
    user = User(name=name, email=email)
    user.set_password(password)
    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        # Se consulta recién acá (y no antes de insertar) para no depender de
        # un chequeo previo que dos pedidos en paralelo podrían saltarse.
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

# borra el autor, el usuario, sus preguntas y respuestas en cascada

def delete_user(user_id: int) -> None:
    validate_id(user_id)
    user = db.get_or_404(User, user_id)
    try:
        db.session.delete(user)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise


# --- Historia 1: autenticación ---

def establecer_password(user: User, password: str) -> None:
    _validar_password(password)
    user.set_password(password)
    user.failed_attempts = 0
    user.locked_until = None
    _guardar()

#comprobar que la contraseña es la correcta para un usuario
def verificar_password(user: User, password: object) -> bool:
    if not isinstance(password, str):
        return False
    return user.check_password(password)


def autenticar(email: str, password: str) -> User:
    """Devuelve el User si las credenciales son correctas.

    - Usuario existente + contraseña correcta -> acceso normal.
    - Contraseña incorrecta -> CredencialesInvalidas (se notifica al usuario).
    - 3 fallos seguidos -> la cuenta se bloquea temporalmente (CuentaBloqueada).
    """
    if type(email) is not str or type(password) is not str:
        raise CredencialesInvalidas()
    email = email.strip().lower()  # create_user guarda los emails en minúsculas

    max_intentos = current_app.config["MAX_LOGIN_ATTEMPTS"]
    minutos = current_app.config["LOCK_MINUTES"]

    # with_for_update serializa los intentos sobre el mismo usuario: si no, dos
    # pedidos en paralelo podrían saltarse el límite de intentos.
    user = User.query.filter_by(email=email).with_for_update().first()
    if user is None:
        raise CredencialesInvalidas()

    if user.locked_until is not None:
        if user.is_locked():
            # Bloqueada: se rechaza incluso con la contraseña correcta.
            raise CuentaBloqueada(user.locked_until)
        user.locked_until = None  # el bloqueo ya venció
        user.failed_attempts = 0

    if user.check_password(password):
        user.failed_attempts = 0
        _guardar()
        return user

    user.failed_attempts += 1
    if user.failed_attempts >= max_intentos:
        hasta = utcnow_naive() + timedelta(minutes=minutos)
        user.locked_until = hasta
        user.failed_attempts = 0
        _guardar()
        raise CuentaBloqueada(hasta)

    restantes = max_intentos - user.failed_attempts
    _guardar()
    raise CredencialesInvalidas(restantes)