from sitio_de_preguntas.extensions import db
from sitio_de_preguntas.models import Categoria


class NombreDeCategoriaYaEnUso(Exception):
    pass


def crear_categoria(nombre: str, descripcion: str | None = None) -> Categoria:
    nombre = (nombre or "").strip()
    if not nombre:
        raise ValueError("La categoría debe tener un nombre")
    if Categoria.query.filter_by(nombre=nombre).first():
        raise NombreDeCategoriaYaEnUso(f"Ya existe la categoría {nombre}")

    categoria = Categoria(nombre=nombre, descripcion=descripcion)
    db.session.add(categoria)
    db.session.commit()
    return categoria


def listar_categorias():
    return Categoria.query.order_by(Categoria.nombre).all()


def obtener_categoria(id: int) -> Categoria:
    return db.get_or_404(Categoria, id)
