"""Caja negra - 2. Crear pregunta.

Clases de equivalencia (resumen):
  título       : 0 < t < 200 | t > 200 | vacío | no es texto
  contenido    : 0 < c < 25.000 | c > 25.000 | vacío | no es texto
  ID_categoría : entero positivo existente | entero positivo inexistente | inválido
  ID_autor     : IA | humano existente | humano inexistente | inválido
  etiqueta     : existe | no existe

Los 4 casos de la tabla son INVÁLIDOS. Los valores numéricos de título y
contenido de la tabla (70, 100, 205, 25.001) son longitudes en caracteres.
"""
import pytest

from sitio_de_preguntas.models import Pregunta
from sitio_de_preguntas.services.autor_services import AutorNoEncontrado
from sitio_de_preguntas.services.etiqueta_services import EtiquetaNoEncontrada
from sitio_de_preguntas.services.pregunta_services import (
    AutorNoPuedePreguntar,
    DatosDePreguntaInvalidos,
    crear_pregunta,
)
from sitio_de_preguntas.services.validaciones import IDInvalido

HUMANO = 49845
CATEGORIA = 6
ETIQUETAS_VALIDAS = ["flask", "html", "java"]

# Cualquiera de estas excepciones significa "entrada inválida". Un TypeError,
# AttributeError, etc. NO está acá a propósito: sería un bug, no una validación.
INVALIDO = (ValueError, LookupError, AutorNoPuedePreguntar)


def _crear(escenario, *, titulo="a" * 70, contenido="b" * 100,
           categoria_id=CATEGORIA, autor=HUMANO, etiquetas=ETIQUETAS_VALIDAS):
    """Llama a crear_pregunta con datos válidos, salvo lo que se indique."""
    return crear_pregunta(
        usuario_id=escenario.autor(autor),
        titulo=titulo,
        contenido=contenido,
        categoria_id=categoria_id,
        etiquetas_ids=escenario.etiquetas_ids(etiquetas),
    )


# --- Caso válido (referencia)

def test_todos_los_datos_validos_crea_la_pregunta(escenario):
    antes = Pregunta.query.count()

    pregunta = _crear(escenario)

    assert Pregunta.query.count() == antes + 1
    assert pregunta.autor_id == HUMANO
    assert pregunta.categoria_id == CATEGORIA
    assert {e.nombre for e in pregunta.etiquetas} == set(ETIQUETAS_VALIDAS)


# --- Casos de la tabla del PDF (todos INVÁLIDOS) 
# (título, contenido, ID_categoría, ID_autor, etiquetas, excepción esperada)

CASOS_PDF = [
    # 1: todo válido salvo que el autor es una IA, y una IA no puede preguntar.
    pytest.param(
        "a" * 70, "b" * 100, 6, "ChatGPT", ["flask", "html", "java"],
        AutorNoPuedePreguntar,
        id="caso1-autor-IA",
    ),
    # 2: título > 200, contenido > 25.000, categoría 2 inexistente,
    #    autor "0000" inválido, etiqueta c++ inexistente.
    pytest.param(
        "a" * 205, "b" * 25_001, 2, "0000", ["flask", "html", "c++"],
        INVALIDO,
        id="caso2-titulo-contenido-largos-categoria-y-etiqueta-inexistentes",
    ),
    # 3: título y contenido vacíos, categoría 0 inválida.
    pytest.param(
        "", "", 0, HUMANO, ["flask", "html", "java"],
        INVALIDO,
        id="caso3-vacios-categoria-invalida",
    ),
    # 4: título y contenido no son texto, autor None, etiqueta inexistente.
    pytest.param(
        3.14, None, 6, None, ["github"],
        INVALIDO,
        id="caso4-no-texto-autor-invalido-etiqueta-inexistente",
    ),
]


@pytest.mark.parametrize(
    "titulo, contenido, categoria_id, autor, etiquetas, excepcion", CASOS_PDF
)
def test_casos_del_pdf_son_invalidos(
    escenario, titulo, contenido, categoria_id, autor, etiquetas, excepcion
):
    antes = Pregunta.query.count()

    with pytest.raises(excepcion):
        _crear(
            escenario, titulo=titulo, contenido=contenido,
            categoria_id=categoria_id, autor=autor, etiquetas=etiquetas,
        )

    # Una pregunta inválida no debe dejar nada guardado.
    assert Pregunta.query.count() == antes


# --- Complementarios: una sola clase inválida por vez 

UNA_FALLA = [
    # título
    pytest.param({"titulo": "a" * 201}, DatosDePreguntaInvalidos, id="titulo-mas-de-200"),
    pytest.param({"titulo": ""}, DatosDePreguntaInvalidos, id="titulo-vacio"),
    pytest.param({"titulo": 3.14}, DatosDePreguntaInvalidos, id="titulo-no-es-texto"),
    # contenido
    pytest.param({"contenido": "b" * 25_001}, DatosDePreguntaInvalidos, id="contenido-mas-de-25000"),
    pytest.param({"contenido": ""}, DatosDePreguntaInvalidos, id="contenido-vacio"),
    pytest.param({"contenido": None}, DatosDePreguntaInvalidos, id="contenido-no-es-texto"),
    # ID_categoría
    pytest.param({"categoria_id": 2}, DatosDePreguntaInvalidos, id="categoria-inexistente"),
    pytest.param({"categoria_id": 0}, IDInvalido, id="categoria-cero"),
    pytest.param({"categoria_id": None}, IDInvalido, id="categoria-none"),
    pytest.param({"categoria_id": "6"}, IDInvalido, id="categoria-texto"),
    # ID_autor
    pytest.param({"autor": "ChatGPT"}, AutorNoPuedePreguntar, id="autor-IA"),
    pytest.param({"autor": 40000}, AutorNoEncontrado, id="autor-inexistente"),
    pytest.param({"autor": None}, IDInvalido, id="autor-none"),
    pytest.param({"autor": "0000"}, IDInvalido, id="autor-texto"),
    # etiqueta
    pytest.param({"etiquetas": ["flask", "html", "c++"]}, EtiquetaNoEncontrada, id="etiqueta-inexistente"),
]


@pytest.mark.parametrize("cambio, excepcion", UNA_FALLA)
def test_una_sola_clase_invalida_es_detectada(escenario, cambio, excepcion):
    antes = Pregunta.query.count()

    with pytest.raises(excepcion):
        _crear(escenario, **cambio)

    assert Pregunta.query.count() == antes