
from sitio_de_preguntas.models import Pregunta, Respuesta, TipoRespuesta
from abc import ABC, abstractmethod

from sitio_de_preguntas.extensions import db

class TipoDeRespuestaNoSoportado(ValueError):
    pass


class FabricaAbsRespuestas(ABC):
    @abstractmethod
    def crear_respuesta(self, pregunta, autor, contenido, tipo: TipoRespuesta):
        """Crea y persiste una respuesta asociada a una pregunta."""


class StrategyRespuesta(ABC):
    @abstractmethod
    def crear_respuesta(self, pregunta, autor, contenido):
        """Construye la respuesta concreta según la estrategia."""


class StrategyUsuario(StrategyRespuesta):
    def crear_respuesta(self, pregunta, autor, contenido):
        return Respuesta(contenido=contenido, pregunta=pregunta, autor=autor)




class FabricaConcretaRespuestas(FabricaAbsRespuestas):
    """Elige la estrategia indicada por ``tipo`` (enum ``tipo_rta`` del diagrama).

    Por ahora sólo está registrada la estrategia de respuesta humana (USUARIO).
    Las estrategias de generación (LLM/agente) se registran aparte.
    """

    def __init__(self, estrategias=None):
        self._estrategias = (
            estrategias
            if estrategias is not None
            else {TipoRespuesta.USUARIO : StrategyUsuario()}
            #completar con soporte para llm
        )

    def crear_respuesta(self, pregunta:Pregunta, autor, contenido:str, tipo:TipoRespuesta):
        estrategia = self._estrategias.get(tipo)
        if estrategia is None:
            raise TipoDeRespuestaNoSoportado(
                f"Tipo de respuesta no soportado: {tipo}"
            )
        respuesta = estrategia.crear_respuesta(pregunta, autor, contenido)
        db.session.add(respuesta)
        db.session.flush()
        return respuesta
