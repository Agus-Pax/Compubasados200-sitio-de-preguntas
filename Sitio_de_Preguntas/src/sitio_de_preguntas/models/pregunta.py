from datetime import UTC, datetime

from sqlalchemy import func, select
from sqlalchemy.orm import column_property

from sitio_de_preguntas.extensions import db
from sitio_de_preguntas.models.voto import Voto

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
    # Solución elegida por el autor. Independiente de los votos.
    respuesta_aceptada_id = db.Column(
        db.Integer,
        db.ForeignKey(
            "respuestas.id",
            ondelete="SET NULL",
            use_alter=True,
            name="fk_preguntas_respuesta_aceptada",
        ),
        nullable=True,
    )

    # Atributos calculados: la tabla de votos es la única fuente de verdad.
    votos = column_property(
        select(func.coalesce(func.sum(Voto.valor), 0))
        .where(Voto.pregunta_id == id)
        .correlate_except(Voto)
        .scalar_subquery()
    )
    votos_positivos = column_property(
        select(func.count(Voto.id))
        .where(Voto.pregunta_id == id, Voto.valor == 1)
        .correlate_except(Voto)
        .scalar_subquery()
    )
    votos_negativos = column_property(
        select(func.count(Voto.id))
        .where(Voto.pregunta_id == id, Voto.valor == -1)
        .correlate_except(Voto)
        .scalar_subquery()
    )

    autor = db.relationship("Autor", back_populates="preguntas")
    categoria = db.relationship("Categoria")
    etiquetas = db.relationship("Etiqueta", secondary=pregunta_etiquetas)
    respuestas = db.relationship(
        "Respuesta",
        back_populates="pregunta",
        foreign_keys="Respuesta.pregunta_id",
        cascade="all, delete-orphan",
    )
    respuesta_aceptada = db.relationship(
        "Respuesta", foreign_keys=[respuesta_aceptada_id]
    )
    votos_usuarios = db.relationship(
        "Voto", back_populates="pregunta", cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Pregunta {self.titulo}>"
