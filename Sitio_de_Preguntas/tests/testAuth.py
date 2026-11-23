from sitio_de_preguntas.extensions import db
from sitio_de_preguntas.models.user import User
from sitio_de_preguntas.services.User_services import establecer_password


def crear_ana():
    u = User(name="Ana", email="a@a.com")
    db.session.add(u)
    db.session.commit()
    establecer_password(u, "secreta")
    return u


def login(client, pw):
    return client.post("/auth/login", json={"email": "a@a.com", "password": pw})


def test_login_correcto(app):
    crear_ana()
    assert login(app.test_client(), "secreta").status_code == 200


def test_password_incorrecta_notifica_error(app):
    crear_ana()
    r = login(app.test_client(), "mala")
    assert r.status_code == 401 and r.json["intentos_restantes"] == 2


def test_usuario_inexistente(app):
    assert login(app.test_client(), "x").status_code == 401


def test_bloqueo_tras_3_intentos(app):
    crear_ana()
    c = app.test_client()
    assert [login(c, "mala").status_code for _ in range(3)] == [401, 401, 423]
    assert login(c, "secreta").status_code == 423