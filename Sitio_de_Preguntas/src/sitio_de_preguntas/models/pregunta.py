from datetime import UTC, datetime

from sitio_de_preguntas.extensions import db

pregunta_etiquetas = db.Table(
    "pregunta_etiquetas",
    db.Column(
        "pregunta_id", db.Integer, db.ForeignKey("preguntas.id"), primary_key=True
    ),
    db.Column(
        "etiqueta_id", db.Integer, db.ForeignKey("etiquetas.id"), primary_key=True
    ),
)


class Pregunta(db.Model):
    __tablename__ = "preguntas"

    id = db.Column(db.Integer, primary_key=True)
    titulo = db.Column(db.String(200), nullable=False)
    contenido = db.Column(db.Text, nullable=False)
    fecha_publicacion = db.Column(
        db.DateTime, nullable=False, default=lambda: datetime.now(UTC)
    )
    autor_id = db.Column(
        db.Integer, db.ForeignKey("autores.id", ondelete="CASCADE"), nullable=False
    )
    categoria_id = db.Column(
        db.Integer, db.ForeignKey("categorias.id"), nullable=False
    )

    autor = db.relationship("Autor", back_populates="preguntas")
    categoria = db.relationship("Categoria")
    etiquetas = db.relationship("Etiqueta", secondary=pregunta_etiquetas)
    respuestas = db.relationship(
        "Respuesta", back_populates="pregunta", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Pregunta {self.titulo}>"
