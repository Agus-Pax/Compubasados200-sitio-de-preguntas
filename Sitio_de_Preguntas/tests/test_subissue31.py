"""Pruebas de la subissue #31: perfil y etiquetas en la UI."""

import pytest
from sqlalchemy import text

from sitio_de_preguntas import create_app
from sitio_de_preguntas.config import Config
from sitio_de_preguntas.extensions import db
from sitio_de_preguntas.models import (
    Categoria,
    Etiqueta,
    Pregunta,
    Respuesta,
    User,
    Voto,
)


class TestConfig(Config):
    TESTING = True
    SECRET_KEY = "clave-de-prueba"


@pytest.fixture
def app(tmp_path):
    class ConfigTemporal(TestConfig):
        SQLALCHEMY_DATABASE_URI = f"sqlite:///{tmp_path / 'subissue31.db'}"

    app = create_app(ConfigTemporal)
    with app.app_context():
        db.create_all()
        yield app


def crear_usuario(nombre, email, password="secreta123"):
    usuario = User(name=nombre, email=email)
    usuario.set_password(password)
    db.session.add(usuario)
    db.session.commit()
    return usuario


def iniciar_sesion(client, email="ana@ejemplo.com", password="secreta123"):
    return client.post(
        "/login", data={"email": email, "password": password}, follow_redirects=False
    )


def crear_datos(pregunta_id=None):
    categoria = Categoria(nombre="Categoría de prueba")
    etiqueta_python = Etiqueta(nombre="python")
    etiqueta_flask = Etiqueta(nombre="flask")
    db.session.add_all([categoria, etiqueta_python, etiqueta_flask])
    db.session.commit()
    return categoria, etiqueta_python, etiqueta_flask


def test_perfil_requiere_sesion(app):
    respuesta = app.test_client().get("/perfil")
    assert respuesta.status_code == 302
    assert "/login" in respuesta.headers["Location"]


def test_modificar_nombre_y_email(app):
    usuario = crear_usuario("Ana", "ana@ejemplo.com")
    client = app.test_client()
    assert iniciar_sesion(client).status_code == 302

    respuesta = client.post("/perfil/nombre", data={"nombre": "Ana María"})
    assert respuesta.status_code == 302
    assert db.session.get(User, usuario.id).name == "Ana María"

    respuesta = client.post("/perfil/email", data={"email": "ana@otro.com"})
    assert respuesta.status_code == 302
    assert db.session.get(User, usuario.id).email == "ana@otro.com"


def test_validaciones_de_nombre_y_email(app):
    crear_usuario("Ana", "ana@ejemplo.com")
    crear_usuario("Otro", "otro@ejemplo.com")
    client = app.test_client()
    iniciar_sesion(client)

    respuesta = client.post("/perfil/nombre", data={"nombre": "   "})
    assert respuesta.status_code == 200
    assert b"Ingres\xc3\xa1 tu nombre" in respuesta.data

    respuesta = client.post("/perfil/email", data={"email": "no-es-un-mail"})
    assert respuesta.status_code == 200
    assert b"formato" in respuesta.data

    respuesta = client.post("/perfil/email", data={"email": "otro@ejemplo.com"})
    assert respuesta.status_code == 200
    assert b"registrado por otro usuario" in respuesta.data
    assert db.session.get(User, 1).email == "ana@ejemplo.com"


def test_cambiar_contraseña_con_hash_y_validaciones(app):
    usuario = crear_usuario("Ana", "ana@ejemplo.com")
    hash_original = usuario.password_hash
    client = app.test_client()
    iniciar_sesion(client)

    respuesta = client.post(
        "/perfil/contraseña",
        data={
            "password_actual": "incorrecta",
            "password_nueva": "nuevaClave123",
            "password_confirmacion": "nuevaClave123",
        },
    )
    assert respuesta.status_code == 200
    assert b"contrase\xc3\xb1a actual es incorrecta" in respuesta.data
    assert db.session.get(User, usuario.id).password_hash == hash_original

    respuesta = client.post(
        "/perfil/contraseña",
        data={
            "password_actual": "secreta123",
            "password_nueva": "nuevaClave123",
            "password_confirmacion": "distinta123",
        },
    )
    assert respuesta.status_code == 200
    assert b"no coinciden" in respuesta.data

    respuesta = client.post(
        "/perfil/contraseña",
        data={
            "password_actual": "secreta123",
            "password_nueva": "nuevaClave123",
            "password_confirmacion": "nuevaClave123",
        },
    )
    assert respuesta.status_code == 302
    actualizado = db.session.get(User, usuario.id)
    assert actualizado.password_hash != hash_original
    assert actualizado.check_password("nuevaClave123")
    assert not actualizado.check_password("secreta123")


def test_eliminar_cuenta_requiere_confirmacion_y_cierra_sesion(app):
    usuario = crear_usuario("Ana", "ana@ejemplo.com")
    otro = crear_usuario("Otro", "otro@ejemplo.com")
    categoria, etiqueta, _ = crear_datos()
    pregunta = Pregunta(
        titulo="¿Cómo ordenar?",
        contenido="Detalle",
        autor=usuario,
        categoria=categoria,
        etiquetas=[etiqueta],
    )
    respuesta = Respuesta(contenido="Usá sorted()", autor=usuario, pregunta=pregunta)
    voto = Voto(pregunta=pregunta, autor=otro, valor=1)
    db.session.add_all([pregunta, respuesta, voto])
    db.session.commit()

    ids = {
        "usuario": usuario.id,
        "otro": otro.id,
        "pregunta": pregunta.id,
        "respuesta": respuesta.id,
    }
    client = app.test_client()
    iniciar_sesion(client)

    assert client.get("/perfil/eliminar").status_code == 200

    sin_confirmar = client.post(
        "/perfil/eliminar",
        data={"password_eliminar": "secreta123", "usuario_id": ids["otro"]},
    )
    assert sin_confirmar.status_code == 200
    assert b"Marc\xc3\xa1 la casilla" in sin_confirmar.data
    assert db.session.get(User, ids["usuario"]) is not None

    contrasena_mala = client.post(
        "/perfil/eliminar",
        data={"confirmacion_eliminar": "1", "password_eliminar": "mala"},
    )
    assert contrasena_mala.status_code == 200
    assert b"contrase\xc3\xb1a es incorrecta" in contrasena_mala.data

    eliminada = client.post(
        "/perfil/eliminar",
        data={
            "confirmacion_eliminar": "1",
            "password_eliminar": "secreta123",
            "usuario_id": ids["otro"],
        },
    )
    assert eliminada.status_code == 302
    assert "/login" in eliminada.headers["Location"]

    assert db.session.get(User, ids["usuario"]) is None
    assert db.session.get(User, ids["otro"]) is not None
    assert db.session.get(Pregunta, ids["pregunta"]) is None
    assert db.session.get(Respuesta, ids["respuesta"]) is None
    restantes = db.session.execute(
        text("SELECT count(*) FROM votos WHERE pregunta_id = :id"),
        {"id": ids["pregunta"]},
    ).scalar()
    assert restantes == 0
    asociaciones = db.session.execute(
        text("SELECT count(*) FROM pregunta_etiquetas WHERE pregunta_id = :id"),
        {"id": ids["pregunta"]},
    ).scalar()
    assert asociaciones == 0

    # La sesión quedó cerrada: no se puede volver al perfil.
    perfil = client.get("/perfil")
    assert perfil.status_code == 302 and "/login" in perfil.headers["Location"]


def test_etiquetas_al_crear_y_editar_pregunta(app):
    crear_usuario("Ana", "ana@ejemplo.com")
    crear_usuario("Otro", "otro@ejemplo.com")
    categoria, python, flask = crear_datos()

    client = app.test_client()
    iniciar_sesion(client)

    formulario = client.get("/preguntas/nueva")
    assert formulario.status_code == 200
    assert b'name="etiquetas_ids"' in formulario.data

    creada = client.post(
        "/preguntas/nueva",
        data={
            "titulo": "¿Cómo ordenar?",
            "contenido": "Detalle de la duda",
            "categoria_id": str(categoria.id),
            "etiquetas_ids": [str(python.id), str(flask.id)],
        },
    )
    assert creada.status_code == 302
    pregunta_id = int(creada.headers["Location"].rsplit("/", 1)[-1])

    home = client.get("/home")
    detalle = client.get(f"/preguntas/{pregunta_id}")
    assert b"python" in home.data and b"flask" in home.data
    assert b"python" in detalle.data and b"flask" in detalle.data

    edicion = client.get(f"/preguntas/{pregunta_id}/editar")
    assert edicion.status_code == 200
    assert b"Guardar cambios" in edicion.data
    assert edicion.data.count(b"checked") >= 2

    guardada = client.post(
        f"/preguntas/{pregunta_id}/editar",
        data={
            "titulo": "Título actualizado",
            "contenido": "Contenido actualizado",
            "categoria_id": str(categoria.id),
            "etiquetas_ids": [str(flask.id)],
        },
    )
    assert guardada.status_code == 302
    actualizada = db.session.get(Pregunta, pregunta_id)
    assert [etiqueta.nombre for etiqueta in actualizada.etiquetas] == ["flask"]

    # Otro usuario no puede abrir el formulario de edición.
    otro_client = app.test_client()
    iniciar_sesion(otro_client, email="otro@ejemplo.com")
    assert otro_client.get(f"/preguntas/{pregunta_id}/editar").status_code == 302
