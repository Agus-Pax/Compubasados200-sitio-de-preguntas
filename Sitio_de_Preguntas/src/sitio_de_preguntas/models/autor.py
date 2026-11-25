from typing import ClassVar

from ..extensions import db


# Los usuarios son autores (User hereda de Autor con tablas separadas).
# Los agentes de IA también son autores, pero no tienen fila en users:
# se distinguen por el discriminador `tipo_autor` y por tener `proveedor`.
class Autor(db.Model):
    __tablename__ = "autores"

    id = db.Column(db.Integer, primary_key=True)
    proveedor = db.Column(db.String(20), unique=True, nullable=True)  # gemini / claude / agente...
    tipo_autor = db.Column(db.String(20), nullable=False)

    __table_args__ = (
        db.CheckConstraint(
            "(tipo_autor = 'usuario' AND proveedor IS NULL) OR "
            "(tipo_autor = 'agente' AND proveedor IS NOT NULL)",
            name="ck_autor_tipo",
        ),
    )

    __mapper_args__: ClassVar[dict] = {
        "polymorphic_on": "tipo_autor",
        "polymorphic_identity": "agente",
    }

    # Si se borra el autor se borra todo su contenido. Las respuestas de esas
    # preguntas y sus votos se borran en cascada desde Pregunta/Respuesta.
    preguntas = db.relationship(
        "Pregunta", back_populates="autor", cascade="all, delete-orphan"
    )
    respuestas = db.relationship(
        "Respuesta", back_populates="autor", cascade="all, delete-orphan"
    )

    @property
    def es_agente(self) -> bool:
        return self.proveedor is not None

    def can_ask(self) -> bool:
        return not self.es_agente

    def __repr__(self) -> str:
        return f"<Autor {self.tipo_autor} {self.id}>"
