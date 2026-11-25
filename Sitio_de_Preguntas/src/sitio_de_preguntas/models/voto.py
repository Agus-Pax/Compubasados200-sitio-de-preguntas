from sitio_de_preguntas.extensions import db


class Voto(db.Model):
    """Un voto por autor y publicación (una pregunta o una respuesta)."""

    __tablename__ = "votos"

    id = db.Column(db.Integer, primary_key=True)
    pregunta_id = db.Column(
        db.Integer,
        db.ForeignKey("preguntas.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    respuesta_id = db.Column(
        db.Integer,
        db.ForeignKey("respuestas.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    # Los agentes IA son Autores, pero no tienen fila en users.
    autor_id = db.Column(
        db.Integer,
        db.ForeignKey("autores.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    valor = db.Column(db.Integer, nullable=False)

    __table_args__ = (
        db.UniqueConstraint("autor_id", "pregunta_id", name="uq_voto_autor_pregunta"),
        db.UniqueConstraint("autor_id", "respuesta_id", name="uq_voto_autor_respuesta"),
        db.CheckConstraint("valor IN (-1, 1)", name="ck_voto_valor"),
        db.CheckConstraint(
            "(pregunta_id IS NOT NULL AND respuesta_id IS NULL) OR "
            "(pregunta_id IS NULL AND respuesta_id IS NOT NULL)",
            name="ck_voto_objetivo",
        ),
    )

    autor = db.relationship("Autor", back_populates="votos")
    pregunta = db.relationship("Pregunta", back_populates="votos_usuarios")
    respuesta = db.relationship("Respuesta", back_populates="votos_usuarios")

    def __repr__(self) -> str:
        return f"<Voto {self.valor:+d}>"
