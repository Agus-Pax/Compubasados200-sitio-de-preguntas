from abc import ABC, abstractmethod

from sitio_de_preguntas.extensions import db
from sitio_de_preguntas.models import Autor, Pregunta, Respuesta, TipoRespuesta


class TipoDeRespuestaNoSoportado(ValueError):
    pass


class FabricaAbsRespuestas(ABC):
    @abstractmethod
    def crear_respuesta(self, pregunta: Pregunta, autor: Autor, contenido: str, tipo: TipoRespuesta
    ) -> Respuesta:
        """Crea y persiste una respuesta asociada a una pregunta."""


class StrategyRespuesta(ABC):
    @abstractmethod
    def crear_respuesta(self, pregunta: Pregunta, autor: Autor, contenido: str
    ) -> Respuesta:
        """Construye la respuesta concreta según la estrategia."""


class StrategyUsuario(StrategyRespuesta):
    def crear_respuesta(self, pregunta: Pregunta, autor: Autor, contenido: str
    ) -> Respuesta:
        return Respuesta(contenido=contenido, pregunta=pregunta, autor=autor)




class FabricaConcretaRespuestas(FabricaAbsRespuestas):
    """Elige la estrategia indicada por ``tipo`` (enum ``TipoRespuesta``).

    Por defecto registra USUARIO y todos los LLM soportados (CLAUDE, GEMINI,
    GPT). Qué LLM se usa lo decide quien llama mediante ``tipo`` (sale de la
    configuración LLM_PROVIDER): cambiar de LLM no requiere tocar código.
    """

    def __init__(self, estrategias: dict | None = None):
        self._estrategias = (
            estrategias
            if estrategias is not None
            else self._estrategias_por_defecto()
        )

    @staticmethod
    def _estrategias_por_defecto() -> dict:
        # Import acá (y no arriba) para evitar un import circular: las
        # estrategias IA heredan de StrategyRespuesta, definida en este módulo.
        from sitio_de_preguntas.services.ia.registro import estrategias_ia

        return {TipoRespuesta.USUARIO: StrategyUsuario(), **estrategias_ia()}

    def crear_respuesta(self, pregunta: Pregunta, autor: Autor, contenido: str, tipo: TipoRespuesta
    ) -> Respuesta:
        """Crea la respuesta y la deja en la sesión (flush). El commit lo hace
        quien llama."""
        estrategia = self._estrategias.get(tipo)
        if estrategia is None:
            raise TipoDeRespuestaNoSoportado(f"Tipo de respuesta no soportado: {tipo}")
        respuesta = estrategia.crear_respuesta(pregunta, autor, contenido)
        db.session.add(respuesta)
        db.session.flush()
        return respuesta
