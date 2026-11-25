"""Qué LLM hay disponibles y cuál está elegido en la configuración."""
from flask import current_app

from sitio_de_preguntas.models import TipoRespuesta
from sitio_de_preguntas.services.fabrica_respuestas import TipoDeRespuestaNoSoportado
from sitio_de_preguntas.services.ia.chatgpt import ChatGPT
from sitio_de_preguntas.services.ia.claude import Claude
from sitio_de_preguntas.services.ia.gemini import Gemini

# Para sumar un LLM nuevo: crear su clase (hereda de StrategyIA) y agregarla acá.
# Los SDK se importan recién al generar texto, así que no hace falta tenerlos todos.
_CLASES_IA = (Claude, Gemini, ChatGPT)


def estrategias_ia() -> dict:
    """{TipoRespuesta: StrategyIA} con todos los LLM soportados."""
    return {clase.tipo: clase() for clase in _CLASES_IA}


def tipo_ia(valor) -> TipoRespuesta:
    """Convierte a TipoRespuesta (acepta texto) y valida que sea un LLM."""
    if isinstance(valor, TipoRespuesta):
        tipo = valor
    else:
        try:
            tipo = TipoRespuesta[str(valor).strip().upper()]
        except KeyError:
            tipo = None
    if tipo not in {clase.tipo for clase in _CLASES_IA}:
        opciones = ", ".join(clase.tipo.name for clase in _CLASES_IA)
        raise TipoDeRespuestaNoSoportado(
            f"'{valor}' no es un LLM soportado. Opciones: {opciones}"
        )
    return tipo


def tipo_configurado() -> TipoRespuesta:
    """LLM elegido en LLM_PROVIDER (CLAUDE | GEMINI | GPT)."""
    return tipo_ia(current_app.config["LLM_PROVIDER"])