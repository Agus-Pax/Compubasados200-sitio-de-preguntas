#respuesta automática (LLM) a preguntas sin respuesta tras 1 semana.
import logging
from datetime import timedelta

from flask import current_app

from sitio_de_preguntas.extensions import db
from sitio_de_preguntas.models import Autor, Pregunta
from sitio_de_preguntas.services.ia.registro import construir_fabrica, tipo_configurado
from sitio_de_preguntas.utils import a_utc_naive, utcnow_naive

log = logging.getLogger(__name__)


def buscar_pendientes(ahora=None) -> list[Pregunta]:
    """Preguntas con >= N días de antigüedad y SIN ninguna respuesta (de nadie)."""
    ahora = ahora or utcnow_naive()
    limite = ahora - timedelta(days=current_app.config["AUTO_ANSWER_AFTER_DAYS"])
    return (
        Pregunta.query
        .filter(Pregunta.fecha_publicacion <= limite)
        .filter(~Pregunta.respuestas.any())
        .all()
    )


def obtener_autor_agente(tipo: str) -> Autor:
    """Autor-agente del LLM (proveedor = tipo en minúsculas). Se crea si no existe."""
    proveedor = tipo.lower()
    autor = Autor.query.filter_by(proveedor=proveedor).first()
    if autor is None:
        autor = Autor(proveedor=proveedor)
        db.session.add(autor)
        db.session.commit()
    return autor


def _paso_el_periodo(pregunta: Pregunta) -> bool:
    dias = current_app.config["AUTO_ANSWER_AFTER_DAYS"]
    antiguedad = utcnow_naive() - a_utc_naive(pregunta.fecha_publicacion)
    return antiguedad >= timedelta(days=dias)


def responder_pregunta(pregunta: Pregunta, tipo: str | None = None, fabrica=None):
    """Genera la respuesta automática si corresponde; devuelve Respuesta o None."""
    # Guardas de los criterios de validación.
    if pregunta.respuestas or not _paso_el_periodo(pregunta):
        return None

    tipo = (tipo or tipo_configurado()).upper()
    fabrica = fabrica or construir_fabrica(tipo)
    autor = obtener_autor_agente(tipo)
    # El contenido lo genera la estrategia IA, por eso se pasa vacío.
    return fabrica.crear_respuesta(
        pregunta=pregunta, autor=autor, contenido="", tipo=tipo
    )


def generar_respuestas_pendientes(tipo: str | None = None, fabrica=None) -> int:
    """Procesa todas las pendientes. Devuelve cuántas respuestas creó."""
    tipo = (tipo or tipo_configurado()).upper()
    fabrica = fabrica or construir_fabrica(tipo)
    creadas = 0
    for pregunta in buscar_pendientes():
        pregunta_id = pregunta.id
        try:
            if responder_pregunta(pregunta, tipo=tipo, fabrica=fabrica):
                creadas += 1
        except Exception:  # un fallo del LLM no frena al resto
            db.session.rollback()
            log.exception("Falló la respuesta automática de la pregunta %s", pregunta_id)
    return creadas