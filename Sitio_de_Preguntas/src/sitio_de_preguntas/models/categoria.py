from sitio_de_preguntas.extensions import db


class Categoria(db.Model):
    __tablename__ = "categorias"

    id = db.Column(db.Integer, primary_key=True)
    nombre = db.Column(db.String(120), nullable=False, unique=True)
    descripcion = db.Column(db.String(255), nullable=True)

    def __repr__(self) -> str:
        return f"<Categoria {self.nombre}>"
