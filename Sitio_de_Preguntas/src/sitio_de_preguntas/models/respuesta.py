from datetime import UTC, datetime

from sitio_de_preguntas.extensions import db


class Respuesta(db.Model):
    __tablename__ = "respuestas"

    id = db.Column(db.Integer, primary_key=True)
    contenido = db.Column(db.Text, nullable=False)
    fecha_publicacion = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(UTC)
    )
    pregunta_id = db.Column(
        db.Integer, db.ForeignKey("preguntas.id"), nullable=False, index=True
    )
    autor_id = db.Column(db.Integer, db.ForeignKey("autores.id"), nullable=False)
    votos = db.Column(db.Integer, nullable=False, default=0)

    pregunta = db.relationship("Pregunta", back_populates="respuestas")
    autor = db.relationship("Autor")
    votos_usuarios = db.relationship(
        "Voto", back_populates="respuesta", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Respuesta {self.id}>"
