"""Caja negra - 1. Iniciar sesión.

Clases de equivalencia (resumen):
  email             : texto y existe | no es texto | no existe
  contraseña        : texto y correcta | no es texto | incorrecta
  usuario           : existente | inexistente
  bloqueo           : sin bloqueo | vigente
  intentos_fallidos : < 3 | >= 3

Datos existentes (conftest): meli, charlie, luis -> <nombre>@universidad.edu,
contraseña <nombre>1234.
"""
from datetime import UTC, datetime, timedelta

import pytest

from sitio_de_preguntas.extensions import db
from sitio_de_preguntas.models import User
from sitio_de_preguntas.services.User_services import (
    CredencialesInvalidas,
    CuentaBloqueada,
    autenticar,
)


def _usuario(nombre):
    return User.query.filter_by(email=f"{nombre}@universidad.edu").first()


def _bloqueo_vigente():
    return datetime.now(UTC).replace(tzinfo=None) + timedelta(minutes=10)


def _estado():
    """Contadores y bloqueos de todos los usuarios (para comprobar que no cambian)."""
    return {u.email: (u.failed_attempts, u.locked_until) for u in User.query.all()}


# --- Casos de la tabla del PDF 

def test_caso1_credenciales_correctas_inicia_sesion(escenario):
    """<meli@universidad.edu, meli1234, meli, sin bloqueo, 2 intentos> -> VÁLIDO"""
    meli = _usuario("meli")
    meli.failed_attempts = 2
    db.session.commit()

    usuario = autenticar("meli@universidad.edu", "meli1234")

    assert usuario.name == "meli"
    assert usuario.failed_attempts == 0  # un login correcto reinicia el contador


# (email, contraseña, usuario, bloqueo, intentos_fallidos)
CASOS_INVALIDOS = [
    pytest.param(
        3.14, None, "lucas", True, 3,
        id="caso2-email-y-password-no-son-texto-usuario-inexistente",
    ),
    pytest.param(
        "charlie@gmail.com", 126783, "charlie", False, 1,
        id="caso3-email-inexistente-y-password-incorrecta",
    ),
]


@pytest.mark.parametrize(
    "email, password, usuario, bloqueo, intentos", CASOS_INVALIDOS
)
def test_casos_invalidos_no_inicia_sesion(
    escenario, email, password, usuario, bloqueo, intentos
):
    # "lucas" no existe: su bloqueo y sus intentos no se pueden preparar.
    existente = _usuario(usuario)
    if existente is not None:
        existente.failed_attempts = intentos
        if bloqueo:
            existente.locked_until = _bloqueo_vigente()
        db.session.commit()
    antes = _estado()

    with pytest.raises(CredencialesInvalidas):
        autenticar(email, password)

    # Un intento fallido contra un usuario que no se pudo identificar
    # no debe modificar a nadie.
    assert _estado() == antes


# --- Complementarios: una clase inválida por vez

def test_password_incorrecta_es_rechazada_y_cuenta_el_intento(escenario):
    with pytest.raises(CredencialesInvalidas) as exc:
        autenticar("meli@universidad.edu", "incorrecta1")

    assert exc.value.intentos_restantes == 2
    assert _usuario("meli").failed_attempts == 1


@pytest.mark.parametrize("password", [None, 126783, 3.14, ["meli1234"]])
def test_password_que_no_es_texto_es_rechazada(escenario, password):
    antes = _estado()
    with pytest.raises(CredencialesInvalidas):
        autenticar("meli@universidad.edu", password)
    assert _estado() == antes


@pytest.mark.parametrize("email", [None, 3.14, 42, ["meli@universidad.edu"]])
def test_email_que_no_es_texto_es_rechazado(escenario, email):
    antes = _estado()
    with pytest.raises(CredencialesInvalidas):
        autenticar(email, "meli1234")
    assert _estado() == antes


def test_email_inexistente_es_rechazado(escenario):
    with pytest.raises(CredencialesInvalidas) as exc:
        autenticar("nadie@universidad.edu", "meli1234")
    assert exc.value.intentos_restantes is None


def test_bloqueo_vigente_rechaza_incluso_la_password_correcta(escenario):
    meli = _usuario("meli")
    meli.locked_until = _bloqueo_vigente()
    db.session.commit()

    with pytest.raises(CuentaBloqueada) as exc:
        autenticar("meli@universidad.edu", "meli1234")

    assert exc.value.hasta is not None


def test_tres_intentos_fallidos_bloquean_la_cuenta(escenario):
    """intentos_fallidos >= 3 -> la cuenta queda bloqueada temporalmente."""
    for _ in range(2):
        with pytest.raises(CredencialesInvalidas):
            autenticar("meli@universidad.edu", "incorrecta1")

    with pytest.raises(CuentaBloqueada):
        autenticar("meli@universidad.edu", "incorrecta1")

    # Ya bloqueada: ni siquiera la contraseña correcta permite entrar.
    with pytest.raises(CuentaBloqueada):
        autenticar("meli@universidad.edu", "meli1234")