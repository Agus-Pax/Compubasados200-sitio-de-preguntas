from sqlalchemy import func
from sqlalchemy.exc import IntegrityError

from sitio_de_preguntas.extensions import db
from sitio_de_preguntas.models import Categoria
from sitio_de_preguntas.services.validaciones import (
    ValidacionError,
    validar_descripcion,
    validar_nombre,
    validate_id,
)

MAX_NOMBRE_CATEGORIA = 120
MAX_DESCRIPCION_CATEGORIA = 255

CATEGORIAS_INICIALES = (
    "Base de Datos",
    "Python",
    "Java",
    "General",
    "Flask",
    "HTML",
)


class NombreDeCategoriaYaEnUso(ValidacionError):
    pass


def crear_categoria(nombre: str, descripcion: str | None = None) -> Categoria:
    nombre = validar_nombre(nombre, MAX_NOMBRE_CATEGORIA)
    descripcion = validar_descripcion(descripcion, MAX_DESCRIPCION_CATEGORIA)

    # Atajo para dar un mensaje claro; la garantía real es el unique de la base.
    if Categoria.query.filter(
        func.lower(Categoria.nombre) == nombre.lower()
    ).first():
        raise NombreDeCategoriaYaEnUso(f"Ya existe la categoría {nombre!r}")

    try:
        categoria = Categoria(nombre=nombre, descripcion=descripcion)
        db.session.add(categoria)
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise NombreDeCategoriaYaEnUso(f"Ya existe la categoría {nombre!r}") from exc
    except Exception:
        db.session.rollback()
        raise
    return categoria


def cargar_categorias_iniciales() -> list[str]:
    """Crea las categorías iniciales que falten y devuelve las creadas."""
    creadas = []
    for nombre in CATEGORIAS_INICIALES:
        try:
            crear_categoria(nombre)
        except NombreDeCategoriaYaEnUso:
            continue
        creadas.append(nombre)
    return creadas


def listar_categorias():
    return Categoria.query.order_by(Categoria.nombre).all()


def obtener_categoria(cat_id: int) -> Categoria:
    validate_id(cat_id)
    return db.get_or_404(Categoria, cat_id)