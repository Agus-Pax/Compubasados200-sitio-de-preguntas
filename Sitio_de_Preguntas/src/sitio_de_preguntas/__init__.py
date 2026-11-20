from flask import Flask

from sitio_de_preguntas.config import Config
from sitio_de_preguntas.extensions import db


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    db.init_app(app)

    from sitio_de_preguntas.api.catalogos import catalogos_bp
    from sitio_de_preguntas.api.health import health_bp
    from sitio_de_preguntas.api.questions import api_questions_bp
    from sitio_de_preguntas.api.users import users_bp

    app.register_blueprint(health_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(catalogos_bp)
    app.register_blueprint(api_questions_bp)

    return app


def main():
    create_app().run()
