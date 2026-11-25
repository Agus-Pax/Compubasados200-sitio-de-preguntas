from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import column_property

from sitio_de_preguntas.extensions import db
from sitio_de_preguntas.models.voto import Voto


class Respuesta(db.Model):
    __tablename__ = "respuestas"

    id = db.Column(db.Integer, primary_key=True)
    contenido = db.Column(db.Text, nullable=False)
    fecha_publicacion = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(UTC)
    )
    pregunta_id = db.Column(
        db.Integer,
        db.ForeignKey("preguntas.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    autor_id = db.Column(
        db.Integer, db.ForeignKey("autores.id", ondelete="CASCADE"), nullable=False
    )
    # Atributo calculado para garantizar consistencia (neto = favor - contra).
    votos = column_property(
        select(func.coalesce(func.sum(Voto.valor), 0))
        .where(Voto.respuesta_id == id)
        .correlate_except(Voto)
        .scalar_subquery()
    )
    votos_positivos = column_property(
        select(func.count(Voto.id))
        .where(Voto.respuesta_id == id, Voto.valor == 1)
        .correlate_except(Voto)
        .scalar_subquery()
    )
    votos_negativos = column_property(
        select(func.count(Voto.id))
        .where(Voto.respuesta_id == id, Voto.valor == -1)
        .correlate_except(Voto)
        .scalar_subquery()
    )

    pregunta = db.relationship(
        "Pregunta", back_populates="respuestas", foreign_keys=[pregunta_id]
    )
    autor = db.relationship("Autor", back_populates="respuestas")
    votos_usuarios = db.relationship(
        "Voto", back_populates="respuesta", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Respuesta {self.id}>"
