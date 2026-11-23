from enum import Enum,auto

#temporalmente...
class TipoRespuesta(Enum):
    USUARIO=auto()
    CLAUDE=auto()
    GPT=auto()
    GEMINI=auto()
    GENERADA=auto()

#extender si es necesario