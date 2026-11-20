from sitio_de_preguntas.extensions import db
from sitio_de_preguntas.models import Etiqueta


class NombreDeEtiquetaYaEnUso(Exception):
    pass


class EtiquetaNoEncontrada(LookupError):
    pass


def crear_etiqueta(nombre: str) -> Etiqueta:
    nombre = (nombre or "").strip()
    if not nombre:
        raise ValueError("La etiqueta debe tener un nombre")
    if Etiqueta.query.filter_by(nombre=nombre).first():
        raise NombreDeEtiquetaYaEnUso(f"Ya existe la etiqueta {nombre}")

    etiqueta = Etiqueta(nombre=nombre)
    db.session.add(etiqueta)
    db.session.commit()
    return etiqueta


def listar_etiquetas():
    return Etiqueta.query.order_by(Etiqueta.nombre).all()


def obtener_etiquetas(ids) -> list:
    """Devuelve las etiquetas con esos ids, sin repetidos, o falla si falta una."""
    if ids is None:
        ids = []
    if not isinstance(ids, (list, tuple, set)):
        raise TypeError("Las etiquetas deben enviarse como una lista de ids")
    ids = list(dict.fromkeys(int(id) for id in ids))
    if not ids:
        return []

    etiquetas = Etiqueta.query.filter(Etiqueta.id.in_(ids)).all()
    if len(etiquetas) != len(ids):
        raise EtiquetaNoEncontrada("Una de las etiquetas no existe")
    return etiquetas
