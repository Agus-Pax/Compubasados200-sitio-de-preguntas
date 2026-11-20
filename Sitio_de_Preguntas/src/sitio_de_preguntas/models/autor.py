from ..extensions import db


class Autor(db.Model):
    __tablename__ = "autores"

    id = db.Column(db.Integer, primary_key=True)
    usuario_id = db.Column(db.Integer, db.ForeignKey("users.id"), unique=True, nullable=True)
    proveedor = db.Column(db.String(20), unique=True, nullable=True)  # gemini / claude / agente...

    __table_args__ = (
        db.CheckConstraint("(usuario_id IS NULL) != (proveedor IS NULL)",
                           name="ck_autor_usuario_o_agente"),
    )

    @property
    def es_agente(self) -> bool:
        return self.proveedor is not None

    def can_ask(self) -> bool:
        return not self.es_agente

    def crear_respuesta(self, pregunta, contenido, tipo="USUARIO"):
        """El autor es quien usa la fábrica para crear sus respuestas."""
        from sitio_de_preguntas.services.fabrica_respuestas import (
            FabricaConcretaRespuestas,
        )

        return FabricaConcretaRespuestas().crear_respuesta(
            pregunta=pregunta, autor=self, contenido=contenido, tipo=tipo
        )