from datetime import timedelta

from flask import current_app

from sitio_de_preguntas.extensions import db
from sitio_de_preguntas.models import User
from sitio_de_preguntas.utils import utcnow_naive


class EmailYaEnUso(Exception):
    pass


class CredencialesInvalidas(Exception):
    def __init__(self, intentos_restantes: int | None = None):
        self.intentos_restantes = intentos_restantes
        super().__init__("Usuario o contraseña incorrectos")


class CuentaBloqueada(Exception):
    def __init__(self, hasta):
        self.hasta = hasta
        super().__init__("Cuenta bloqueada temporalmente")

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

def delete_user(id: int):
    user = db.get_or_404(User, id)
    db.session.delete(user)
    db.session.commit()

def modify_user(id: int, name: str, email: str):
    user = db.get_or_404(User, id)
    if user.email != email and User.query.filter_by(email = email).first():
        raise EmailYaEnUso
    user.email = email
    user.name = name
    db.session.commit()

    return user

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

