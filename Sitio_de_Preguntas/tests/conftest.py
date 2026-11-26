"""Fixtures compartidos por los tests de caja negra.

  CATEGORIA : 6
  AUTOR     : 0001 (agente IA) y 49845 (humano)
  ETIQUETA  : flask, html, java
  PREGUNTA  : 70, 60   (las escribe el humano 49845, en la categoría 6)
  USUARIOS  : meli, charlie, luis  (<nombre>@universidad.edu)
"""
from types import SimpleNamespace

import pytest
from flask import Flask

from sitio_de_preguntas.extensions import db
from sitio_de_preguntas.models import Autor, Categoria, Etiqueta, Pregunta, User

HUMANO_ID = 49845
CATEGORIA_ID = 6


class Escenario(SimpleNamespace):
    def autor(self, valor):
        """'ChatGPT' se traduce al id real del agente; cualquier otro valor
        (49845, 40000, None, "0000"...) se usa tal cual."""
        return self.chatgpt_id if valor == "ChatGPT" else valor

    def etiquetas_ids(self, nombres):
        """Ids de las etiquetas pedidas. Las que no existen (c++, github...)
        reciben un id que no está en la base."""
        return [self.etiquetas.get(n, 9000 + i) for i, n in enumerate(nombres)]


@pytest.fixture
def app_de_prueba():
    app = Flask(__name__)
    app.config.update(
        TESTING=True,
        SECRET_KEY="test",
        SQLALCHEMY_DATABASE_URI="sqlite:///:memory:",
        MAX_LOGIN_ATTEMPTS=3,
        LOCK_MINUTES=15,
        AUTO_ANSWER_AFTER_DAYS=7,
    )
    db.init_app(app)
    with app.app_context():
        db.create_all()
        yield app
        db.session.remove()
        db.drop_all()


@pytest.fixture
def escenario(app_de_prueba):
    categoria = Categoria(id=CATEGORIA_ID, nombre="Programación")
    etiquetas = [Etiqueta(nombre=n) for n in ("flask", "html", "java")]
    db.session.add(categoria)
    db.session.add_all(etiquetas)

    for nombre in ("meli", "charlie", "luis"):
        user = User(name=nombre, email=f"{nombre}@universidad.edu")
        user.set_password(f"{nombre}1234")
        db.session.add(user)

    humano = User(id=HUMANO_ID, name="Humano", email="humano@universidad.edu")
    humano.set_password("humano1234")
    chatgpt = Autor(proveedor="gpt")  # agente IA
    db.session.add_all([humano, chatgpt])
    db.session.commit()

    db.session.add_all(
        [
            Pregunta(
                id=pid,
                titulo=f"Pregunta {pid}",
                contenido=f"Contenido de la pregunta {pid}",
                autor_id=HUMANO_ID,
                categoria_id=CATEGORIA_ID,
            )
            for pid in (70, 60)
        ]
    )
    db.session.commit()

    return Escenario(
        chatgpt_id=chatgpt.id,
        etiquetas={e.nombre: e.id for e in etiquetas},
    )