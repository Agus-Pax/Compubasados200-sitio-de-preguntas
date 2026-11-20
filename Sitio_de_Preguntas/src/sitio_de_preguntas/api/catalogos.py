from flask import Blueprint, abort, jsonify, request

from sitio_de_preguntas.services.categoria_services import (
    NombreDeCategoriaYaEnUso,
    crear_categoria,
    listar_categorias,
)
from sitio_de_preguntas.services.etiqueta_services import (
    NombreDeEtiquetaYaEnUso,
    crear_etiqueta,
    listar_etiquetas,
)

catalogos_bp = Blueprint("api_catalogos", __name__, url_prefix="/api")


@catalogos_bp.errorhandler(400)
def _bad_request(error):
    return jsonify(error=error.description), 400


@catalogos_bp.get("/categorias")
def listar_categorias_api():
    categorias = listar_categorias()
    return jsonify(
        [{"id": c.id, "nombre": c.nombre, "descripcion": c.descripcion} for c in categorias]
    )


@catalogos_bp.post("/categorias")
def crear_categoria_api():
    datos = request.get_json(silent=True) or {}
    try:
        categoria = crear_categoria(
            datos.get("nombre", ""), datos.get("descripcion")
        )
    except (ValueError, NombreDeCategoriaYaEnUso) as exc:
        abort(400, description=str(exc))
    return jsonify(id=categoria.id, nombre=categoria.nombre), 201


@catalogos_bp.get("/etiquetas")
def listar_etiquetas_api():
    etiquetas = listar_etiquetas()
    return jsonify([{"id": e.id, "nombre": e.nombre} for e in etiquetas])


@catalogos_bp.post("/etiquetas")
def crear_etiqueta_api():
    datos = request.get_json(silent=True) or {}
    try:
        etiqueta = crear_etiqueta(datos.get("nombre", ""))
    except (ValueError, NombreDeEtiquetaYaEnUso) as exc:
        abort(400, description=str(exc))
    return jsonify(id=etiqueta.id, nombre=etiqueta.nombre), 201
