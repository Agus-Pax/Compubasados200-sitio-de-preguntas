from typing import ClassVar

from werkzeug.security import check_password_hash, generate_password_hash

from sitio_de_preguntas.extensions import db
from sitio_de_preguntas.models.autor import Autor
from sitio_de_preguntas.utils import a_utc_naive, utcnow_naive


class User(Autor):
    __tablename__ = "users"

    id = db.Column(
        db.Integer, db.ForeignKey("autores.id", ondelete="CASCADE"), primary_key=True
    )
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)

    password_hash = db.Column(db.String(255), nullable=True)
    failed_attempts = db.Column(
        db.Integer, nullable=False, default=0, server_default="0"
    )
    locked_until = db.Column(db.DateTime, nullable=True)

    __mapper_args__: ClassVar[dict] = {"polymorphic_identity": "usuario"}

    votos = db.relationship(
        "Voto", back_populates="usuario", cascade="all, delete-orphan"
    )

    # --- autenticación -----------------------------------------------------
    # La lógica de login está en services/User_services.py; acá solo está lo
    # que necesita el objeto User (hash y estado de bloqueo).

    def set_password(self, password: str) -> None:
        self.password_hash = generate_password_hash(password)

    def check_password(self, password: str) -> bool:
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)

    def is_locked(self) -> bool:
        if self.locked_until is None:
            return False
        return a_utc_naive(self.locked_until) > utcnow_naive()

    def __repr__(self) -> str:
        return f"<User {self.email}>"
