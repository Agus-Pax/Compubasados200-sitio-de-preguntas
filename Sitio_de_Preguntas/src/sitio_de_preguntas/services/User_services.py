from datetime import UTC, datetime, timedelta

from flask import current_app
from sqlalchemy.exc import IntegrityError
from werkzeug.security import check_password_hash, generate_password_hash

from sitio_de_preguntas.extensions import db
from sitio_de_preguntas.models import Autor, Pregunta, Respuesta, User, Voto
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


class UsuarioConContenido(Exception):
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


def _hashear_password(password) -> str:
    if type(password) is not str:
        raise PasswordInvalida("la contraseña debe ser texto")
    if not MIN_PASSWORD <= len(password) <= MAX_PASSWORD:
        raise PasswordInvalida(
            f"la contraseña debe tener entre {MIN_PASSWORD} y {MAX_PASSWORD} caracteres"
        )
    return generate_password_hash(password)


def create_user(name: str, email: str, password: str | None = None) -> User:
    """``password`` es opcional para no romper los llamados existentes, pero
    un usuario sin contraseña no puede iniciar sesión."""
    name, email = _validar_datos(name, email)
    password_hash = _hashear_password(password) if password is not None else None
    try:
        user = User(name=name, email=email, password_hash=password_hash)
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


# --- Historia 1: autenticación ---

def _guardar() -> None:
    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise


def establecer_password(user_id: int, password: str) -> None:
    """Para darle contraseña a un usuario existente o cambiársela."""
    validate_id(user_id)
    password_hash = _hashear_password(password)
    user = db.get_or_404(User, user_id)
    user.password_hash = password_hash
    user.failed_attempts = 0
    user.locked_until = None
    _guardar()


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
        # Mismo error que una contraseña mala: no revela qué emails existen.
        raise CredencialesInvalidas()

    ahora = datetime.now(UTC).replace(tzinfo=None)
    if user.locked_until is not None:
        if user.locked_until > ahora:
            # Bloqueada: se rechaza incluso con la contraseña correcta.
            raise CuentaBloqueada(user.locked_until)
        user.locked_until = None  # el bloqueo ya venció
        user.failed_attempts = 0

    if user.password_hash and check_password_hash(user.password_hash, password):
        user.failed_attempts = 0
        _guardar()
        return user

    user.failed_attempts += 1
    if user.failed_attempts >= max_intentos:
        hasta = ahora + timedelta(minutes=minutos)
        user.locked_until = hasta
        user.failed_attempts = 0
        _guardar()
        raise CuentaBloqueada(hasta)

    restantes = max_intentos - user.failed_attempts
    _guardar()
    raise CredencialesInvalidas(restantes)