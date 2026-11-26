"""Caja negra - 3. Crear respuesta.

Clases de equivalencia (resumen):
  ID_pregunta : entero positivo existente | entero positivo inexistente | inválido
  ID_autor    : IA existente | humano existente | autor inexistente | inválido
  contenido   : 1 a 25.000 caracteres | más de 25.000 | vacío | no es texto

Datos existentes (conftest): preguntas 70 y 60, autores ChatGPT (IA) y 49845 (humano).
Los números de contenido de la tabla (3000, 25034, 0, 14844) son longitudes.
"""
import pytest
from werkzeug.exceptions import NotFound

from sitio_de_preguntas.models import Respuesta
from sitio_de_preguntas.services.autor_services import AutorNoEncontrado
from sitio_de_preguntas.services.respuesta_services import (
    ContenidoDeRespuestaInvalido,
    crear_respuesta,
)
from sitio_de_preguntas.services.validaciones import IDInvalido

HUMANO = 49845

# Entrada inválida: ValueError (validaciones), LookupError, o NotFound (404) cuando
# la pregunta no existe (db.get_or_404). Un TypeError, AttributeError, etc. NO está
# acá a propósito: sería un bug, no una validación.
INVALIDO = (ValueError, LookupError, NotFound)


def _crear(escenario, *, pregunta_id=70, autor=HUMANO, contenido="c" * 100):
    """Llama a crear_respuesta con datos válidos, salvo lo que se indique."""
    return crear_respuesta(pregunta_id, escenario.autor(autor), contenido)


# --- Caso válido (referencia) 

def test_todos_los_datos_validos_crea_la_respuesta(escenario):
    antes = Respuesta.query.count()

    respuesta = _crear(escenario, contenido="c" * 3000)

    assert Respuesta.query.count() == antes + 1
    assert respuesta.pregunta_id == 70
    assert respuesta.autor_id == HUMANO
    assert respuesta.contenido == "c" * 3000


# --- Casos de la tabla del PDF (todos INVÁLIDOS) 
# (ID_pregunta, ID_autor, contenido)

CASOS_PDF = [
    pytest.param(
        70, "ChatGPT", "c" * 3000,
        id="caso1-autor-IA",
        marks=pytest.mark.xfail(
            strict=True,
            reason="El PDF pide rechazar autores IA, pero crear_respuesta los acepta. "
                   "Si el PDF manda: agregar el rechazo al service y sacar este xfail. "
                   "Si el código manda: corregir el PDF y esperar una respuesta válida.",
        ),
    ),
    # 2: la pregunta 1 no existe y el contenido supera los 25.000 caracteres.
    pytest.param(1, HUMANO, "c" * 25_034, id="caso2-pregunta-inexistente-contenido-largo"),

    # 3: ID_pregunta None (inválido) y contenido vacío (autor 40000 inexistente).
    pytest.param(None, 40000, "", id="caso3-pregunta-invalida-contenido-vacio"),

    # 4: ID_autor None (inválido).
    pytest.param(60, None, "c" * 14_844, id="caso4-autor-invalido"),
]


@pytest.mark.parametrize("pregunta_id, autor, contenido", CASOS_PDF)
def test_casos_del_pdf_son_invalidos(escenario, pregunta_id, autor, contenido):
    antes = Respuesta.query.count()

    with pytest.raises(INVALIDO):
        _crear(escenario, pregunta_id=pregunta_id, autor=autor, contenido=contenido)

    # Una respuesta inválida no debe dejar nada guardado.
    assert Respuesta.query.count() == antes


# --- Complementarios: una sola clase inválida por vez 

UNA_FALLA = [
    # ID_pregunta
    pytest.param({"pregunta_id": 1}, NotFound, id="pregunta-inexistente"),
    pytest.param({"pregunta_id": None}, IDInvalido, id="pregunta-none"),
    pytest.param({"pregunta_id": 0}, IDInvalido, id="pregunta-cero"),
    pytest.param({"pregunta_id": -1}, IDInvalido, id="pregunta-negativa"),
    pytest.param({"pregunta_id": "70"}, IDInvalido, id="pregunta-texto"),
    pytest.param({"pregunta_id": True}, IDInvalido, id="pregunta-booleano"),

    # ID_autor
    pytest.param({"autor": 40000}, AutorNoEncontrado, id="autor-inexistente"),
    pytest.param({"autor": None}, IDInvalido, id="autor-none"),
    pytest.param({"autor": "0000"}, IDInvalido, id="autor-texto"),
    pytest.param({"autor": 0}, IDInvalido, id="autor-cero"),

    # contenido
    pytest.param({"contenido": ""}, ContenidoDeRespuestaInvalido, id="contenido-vacio"),
    pytest.param({"contenido": "   "}, ContenidoDeRespuestaInvalido, id="contenido-solo-espacios"),
    pytest.param({"contenido": "c" * 25_001}, ContenidoDeRespuestaInvalido, id="contenido-mas-de-25000"),
    pytest.param({"contenido": None}, ContenidoDeRespuestaInvalido, id="contenido-none"),
    pytest.param({"contenido": 3.14}, ContenidoDeRespuestaInvalido, id="contenido-no-es-texto"),
]


@pytest.mark.parametrize("cambio, excepcion", UNA_FALLA)
def test_una_sola_clase_invalida_es_detectada(escenario, cambio, excepcion):
    antes = Respuesta.query.count()

    with pytest.raises(excepcion):
        _crear(escenario, **cambio)

    assert Respuesta.query.count() == antes