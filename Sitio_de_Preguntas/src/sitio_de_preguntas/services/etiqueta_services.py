from sqlalchemy.exc import IntegrityError

from sitio_de_preguntas.extensions import db
from sitio_de_preguntas.models import Etiqueta
from sitio_de_preguntas.services.validaciones import (
    ValidacionError, validar_nombre, validate_id,
)

MAX_NOMBRE_ETIQUETA = 120
MAX_ETIQUETAS = 10


class NombreDeEtiquetaYaEnUso(ValidacionError):
    pass


class EtiquetasInvalidas(ValidacionError):
    pass


class EtiquetaNoEncontrada(LookupError):
    pass


def crear_etiqueta(nombre: str) -> Etiqueta:
    # Se guarda en minúsculas: así el unique de la base cubre "Python" vs "python"
    nombre = validar_nombre(nombre, MAX_NOMBRE_ETIQUETA, minusculas=True)

    if Etiqueta.query.filter_by(nombre=nombre).first():
        raise NombreDeEtiquetaYaEnUso(f"Ya existe la etiqueta {nombre!r}")

    try:
        etiqueta = Etiqueta(nombre=nombre)
        db.session.add(etiqueta)
        db.session.commit()
    except IntegrityError as exc:
        db.session.rollback()
        raise NombreDeEtiquetaYaEnUso(f"Ya existe la etiqueta {nombre!r}") from exc
    except Exception:
        db.session.rollback()
        raise
    return etiqueta


def listar_etiquetas():
    return Etiqueta.query.order_by(Etiqueta.nombre).all()


def obtener_etiquetas(ids) -> list[Etiqueta]:
    """Devuelve las etiquetas pedidas (sin repetidos, en el orden recibido)
    o falla indicando cuáles no existen."""
    if ids is None:
        return []
    if not isinstance(ids, (list, tuple, set)):
        raise EtiquetasInvalidas("Las etiquetas deben enviarse como una lista de ids")

    for etiqueta_id in ids:
        validate_id(etiqueta_id)
    ids = list(dict.fromkeys(ids))  # deduplica conservando el orden

    if not ids:
        return []
    if len(ids) > MAX_ETIQUETAS:
        raise EtiquetasInvalidas(f"Máximo {MAX_ETIQUETAS} etiquetas por pregunta")

    encontradas = {
        e.id: e for e in Etiqueta.query.filter(Etiqueta.id.in_(ids)).all()
    }
    faltantes = [i for i in ids if i not in encontradas]
    if faltantes:
        raise EtiquetaNoEncontrada(f"No existen las etiquetas: {faltantes}")
    return [encontradas[i] for i in ids]