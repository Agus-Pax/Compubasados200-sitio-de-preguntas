from sitio_de_preguntas.extensions import db


class Voto(db.Model):
    __tablename__ = "votos"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    respuesta_id = db.Column(
        db.Integer, db.ForeignKey("respuestas.id"), nullable=False, index=True
    )
    valor = db.Column(db.Integer, nullable=False)

    __table_args__ = (
        db.UniqueConstraint(
            "usuario_id", "respuesta_id", name="uq_voto_usuario_respuesta"
        ),
        db.CheckConstraint("valor IN (-1, 1)", name="ck_voto_valor"),
    )

    usuario = db.relationship("User")
    respuesta = db.relationship("Respuesta", back_populates="votos_usuarios")

    def __repr__(self) -> str:
        return f"<Voto {self.valor:+d}>"
