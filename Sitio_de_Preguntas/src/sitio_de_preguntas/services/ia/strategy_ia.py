"""StrategyIA del diagrama: estrategia de tu fabrica que genera el texto con un LLM."""
from abc import abstractmethod

from sitio_de_preguntas.models import Respuesta
from sitio_de_preguntas.services.fabrica_respuestas import StrategyRespuesta

PROMPT = (
    "Sos un asistente de un sitio de preguntas y respuestas. "
    "Responde en espaniol, de forma clara, correcta y concisa.\n\n"
    "Categoria: {categoria}\n"
    "Etiquetas: {etiquetas}\n"
    "Titulo de la pregunta: {titulo}\n"
    "Detalle: {contenido}"
)


class RespuestaIAVacia(Exception):
    pass


class StrategyIA(StrategyRespuesta):
    #: clave del enum tipo_rta (CLAUDE, GEMINI, CHAT_GPT). El Autor-agente usa tipo.lower().
    tipo: str

    @abstractmethod
    def generar_texto(self, prompt: str) -> str:
        """Llama al LLM concreto y devuelve el texto."""

    @staticmethod
    def construir_prompt(pregunta) -> str:
        return PROMPT.format(
            categoria=pregunta.categoria.nombre if pregunta.categoria else "-",
            etiquetas=", ".join(e.nombre for e in pregunta.etiquetas) or "-",
            titulo=pregunta.titulo,
            contenido=pregunta.contenido,
        )

    def crear_respuesta(self, pregunta, autor, contenido=None):
        # `contenido` se ignora: lo genera el LLM a partir de la pregunta.
        texto = (self.generar_texto(self.construir_prompt(pregunta)) or "").strip()
        if not texto:
            raise RespuestaIAVacia(f"{self.tipo} devolvio una respuesta vacia")
        return Respuesta(contenido=texto, pregunta=pregunta, autor=autor)