"""Historia 2: respuesta automática (LLM) a preguntas sin respuesta tras 1 semana."""
import logging
from datetime import UTC, datetime, timedelta

from flask import current_app

from sitio_de_preguntas.extensions import db
from sitio_de_preguntas.models import Autor, Pregunta
from sitio_de_preguntas.services.fabrica_respuestas import FabricaConcretaRespuestas
from sitio_de_preguntas.services.ia.registro import tipo_configurado, tipo_ia

log = logging.getLogger(__name__)


def _ahora() -> datetime:
    # La BD devuelve fechas sin tzinfo (todas en UTC), así que se compara en naive.
    return datetime.now(UTC).replace(tzinfo=None)


def buscar_pendientes(ahora=None) -> list[Pregunta]:
    """Preguntas con >= N días de antigüedad y SIN ninguna respuesta (de nadie)."""
    ahora = ahora or _ahora()
    limite = ahora - timedelta(days=current_app.config["AUTO_ANSWER_AFTER_DAYS"])
    return (
        Pregunta.query
        .filter(Pregunta.fecha_publicacion <= limite)
        .filter(~Pregunta.respuestas.any())
        .all()
    )


def obtener_autor_agente(tipo) -> Autor:
    """Autor-agente del LLM (proveedor = nombre del tipo en minúsculas:
    claude / gemini / gpt). Se crea si no existe.

    Igual que en los demás services, hace ``flush`` pero no ``commit``.
    """
    proveedor = tipo.name.lower()
    autor = Autor.query.filter_by(proveedor=proveedor).first()
    if autor is None:
        autor = Autor(proveedor=proveedor)
        db.session.add(autor)
        db.session.flush()
    return autor


def _paso_el_periodo(pregunta: Pregunta) -> bool:
    dias = current_app.config["AUTO_ANSWER_AFTER_DAYS"]
    antiguedad = _ahora() - pregunta.fecha_publicacion.replace(tzinfo=None)
    return antiguedad >= timedelta(days=dias)


def responder_pregunta(pregunta: Pregunta, tipo=None, fabrica=None):
    """Genera la respuesta automática si corresponde; devuelve Respuesta o None."""
    # Guardas de los criterios de validación.
    if pregunta.respuestas or not _paso_el_periodo(pregunta):
        return None

    tipo = tipo_ia(tipo) if tipo else tipo_configurado()
    fabrica = fabrica or FabricaConcretaRespuestas()
    try:
        autor = obtener_autor_agente(tipo)
        # El contenido lo genera la estrategia IA, por eso se pasa vacío.
        respuesta = fabrica.crear_respuesta(
            pregunta=pregunta, autor=autor, contenido="", tipo=tipo
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return respuesta


def generar_respuestas_pendientes(tipo=None, fabrica=None) -> int:
    """Procesa todas las pendientes. Devuelve cuántas respuestas creó."""
    tipo = tipo_ia(tipo) if tipo else tipo_configurado()
    fabrica = fabrica or FabricaConcretaRespuestas()
    creadas = 0
    for pregunta in buscar_pendientes():
        pregunta_id = pregunta.id
        try:
            if responder_pregunta(pregunta, tipo=tipo, fabrica=fabrica):
                creadas += 1
        except Exception:  # un fallo del LLM no frena al resto
            log.exception("Falló la respuesta automática de la pregunta %s", pregunta_id)
    return creadas