"""Registra las estrategias IA en FabricaConcretaRespuestas segun la configuracion."""
from importlib import import_module

from flask import current_app

from sitio_de_preguntas.services.fabrica_respuestas import (
    FabricaConcretaRespuestas,
    StrategyUsuario,
    TipoDeRespuestaNoSoportado,
)

# tipo_rta -> (modulo, clase). Import perezoso: solo se carga el SDK del LLM elegido.
_ESTRATEGIAS_IA = {
    "CLAUDE": ("sitio_de_preguntas.services.ia.claude", "Claude"),
    "GEMINI": ("sitio_de_preguntas.services.ia.gemini", "Gemini"),
    "CHAT_GPT": ("sitio_de_preguntas.services.ia.chatgpt", "ChatGPT"),
}


def tipo_configurado() -> str:
    """Tipo de LLM elegido en LLM_PROVIDER (CLAUDE | GEMINI | CHAT_GPT)."""
    return current_app.config["LLM_PROVIDER"].upper()


def crear_estrategia_ia(tipo: str):
    try:
        modulo, clase = _ESTRATEGIAS_IA[tipo.upper()]
    except KeyError:
        raise TipoDeRespuestaNoSoportado(
            f"LLM '{tipo}' no soportado. Opciones: {', '.join(_ESTRATEGIAS_IA)}"
        ) from None
    return getattr(import_module(modulo), clase)()


def construir_fabrica(tipo: str | None = None) -> FabricaConcretaRespuestas:
    """Tu fabrica con USUARIO + el LLM elegido registrados como estrategias."""
    tipo = (tipo or tipo_configurado()).upper()
    return FabricaConcretaRespuestas(
        estrategias={"USUARIO": StrategyUsuario(), tipo: crear_estrategia_ia(tipo)}
    )