from ..extensions import db


#cada usuario se relaciona con al menos un autor, la creacion
#de usuarios y autores va ligada, cada alta de un usuario implica el alta de un autor
#un agente tambien es autor, por tanto no se liga a un usuario, id nulleable.
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
