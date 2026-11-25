from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from sitio_de_preguntas.extensions import db
from sitio_de_preguntas.models import User
from sitio_de_preguntas.services.categoria_services import listar_categorias
from sitio_de_preguntas.services.etiqueta_services import (
    EtiquetaNoEncontrada,
    EtiquetasInvalidas,
    listar_etiquetas,
)
from sitio_de_preguntas.services.pregunta_services import (
    AutorNoPuedePreguntar,
    NoEsAutorDeLaPregunta,
    crear_pregunta,
    listar_preguntas,
    modificar_pregunta,
    obtener_pregunta,
)
from sitio_de_preguntas.services.respuesta_services import (
    ContenidoDeRespuestaInvalido,
    aceptar_respuesta,
    crear_respuesta,
    listar_respuestas,
    obtener_respuesta,
    quitar_respuesta_aceptada,
)
from sitio_de_preguntas.services.voto_services import (
    TipoVoto,
    fijar_voto,
    fijar_voto_pregunta,
    listar_votos_usuario,
    retirar_voto,
    retirar_voto_pregunta,
)

home_bp = Blueprint("home", __name__)


def _usuario_actual() -> User | None:
    user_id = session.get("user_id")
    if user_id is None:
        return None
    return db.session.get(User, user_id)


def _usuario_o_redirect():
    """Devuelve (usuario, None) o (None, redirect) si no hay sesión válida."""
    usuario = _usuario_actual()
    if usuario is None:
        session.clear()
        return None, redirect(url_for("web.login"))
    return usuario, None


def _nombre_autor(autor) -> str:
    if autor is None:
        return "Autor no disponible"
    nombre = getattr(autor, "name", None)
    if nombre:
        return nombre
    proveedor = getattr(autor, "proveedor", None)
    if proveedor:
        return f"Agente {proveedor}"
    autor_id = getattr(autor, "id", None)
    return f"Autor #{autor_id}" if autor_id else "Autor no disponible"


def _fecha(fecha) -> str:
    return fecha.strftime("%d/%m/%Y") if fecha else "Fecha no disponible"


def _id_formulario(valor) -> int | None:
    """Los ids llegan como texto desde el formulario; el servicio exige int."""
    try:
        return int(valor)
    except (TypeError, ValueError):
        return None


def _ids_etiquetas_formulario() -> list[int]:
    ids = (
        _id_formulario(valor)
        for valor in request.form.getlist("etiquetas_ids")
    )
    return [id_ for id_ in ids if id_ is not None]


def _valores_pregunta(pregunta=None) -> dict:
    """Valores iniciales del formulario, ya sea para crear o para editar."""
    if pregunta is None:
        return {
            "titulo": "",
            "contenido": "",
            "categoria_id": "",
            "etiquetas_ids": [],
        }
    return {
        "titulo": pregunta.titulo,
        "contenido": pregunta.contenido,
        "categoria_id": str(pregunta.categoria_id),
        "etiquetas_ids": [str(etiqueta.id) for etiqueta in pregunta.etiquetas],
    }


def _errores_pregunta() -> dict:
    return {"titulo": None, "contenido": None, "categoria": None, "general": None}


def _render_formulario_pregunta(usuario, valores, errores, pregunta=None):
    return render_template(
        "home/nueva.html",
        usuario=usuario,
        categorias=listar_categorias(),
        etiquetas=listar_etiquetas(),
        valores=valores,
        errores=errores,
        pregunta=pregunta,
        es_edicion=pregunta is not None,
    )


def _votos_usuario(usuario):
    """Devuelve (votos a preguntas, votos a respuestas) indexados por id."""
    votos = listar_votos_usuario(usuario.id)
    return (
        {v.pregunta_id: v.valor for v in votos if v.pregunta_id is not None},
        {v.respuesta_id: v.valor for v in votos if v.respuesta_id is not None},
    )


def _valor_voto():
    """1, -1 para fijar; 0 para quitar; None si el formulario vino mal."""
    try:
        valor = int(request.form.get("valor", ""))
    except (TypeError, ValueError):
        return None
    return valor if valor in (-1, 0, 1) else None


def _destino_voto(pregunta_id):
    if request.form.get("origen") == "home":
        return redirect(url_for("home.inicio"))
    return redirect(url_for("home.detalle", pregunta_id=pregunta_id))


def _render_detalle(usuario, pregunta, valores=None, errores=None):
    votos_preguntas, votos_respuestas = _votos_usuario(usuario)
    return render_template(
        "home/detalle.html",
        usuario=usuario,
        pregunta=pregunta,
        respuestas=listar_respuestas(pregunta.id),
        autor=_nombre_autor(pregunta.autor),
        es_autor=usuario.id == pregunta.autor_id,
        fecha_pregunta=_fecha(pregunta.fecha_publicacion),
        nombre_autor=_nombre_autor,
        fecha=_fecha,
        votos_preguntas=votos_preguntas,
        votos_respuestas=votos_respuestas,
        valores=valores or {"contenido": ""},
        errores=errores or {"contenido": None, "general": None},
    )


@home_bp.get("/home")
def inicio():
    usuario, respuesta = _usuario_o_redirect()
    if respuesta is not None:
        return respuesta

    preguntas = listar_preguntas()
    votos_preguntas, _ = _votos_usuario(usuario)
    return render_template(
        "home/index.html",
        usuario=usuario,
        preguntas=preguntas,
        nombre_autor=_nombre_autor,
        fecha=_fecha,
        votos_preguntas=votos_preguntas,
    )


@home_bp.get("/preguntas/<int:pregunta_id>")
def detalle(pregunta_id: int):
    usuario, respuesta = _usuario_o_redirect()
    if respuesta is not None:
        return respuesta

    return _render_detalle(usuario, obtener_pregunta(pregunta_id))


@home_bp.post("/preguntas/<int:pregunta_id>/voto")
def votar_pregunta(pregunta_id: int):
    usuario, respuesta = _usuario_o_redirect()
    if respuesta is not None:
        return respuesta

    obtener_pregunta(pregunta_id)  # 404 si no existe
    anterior = _votos_usuario(usuario)[0].get(pregunta_id)
    valor = _valor_voto()
    if valor is None:
        flash("Voto inválido.", "info")
    else:
        try:
            if valor == 0:
                retirar_voto_pregunta(pregunta_id, usuario.id)
                mensaje = "Voto quitado."
            else:
                fijar_voto_pregunta(pregunta_id, usuario.id, TipoVoto(valor))
                mensaje = "Voto actualizado." if anterior is not None else "Voto registrado."
        except (ValueError, LookupError) as exc:
            flash(f"No pudimos guardar el voto: {exc}", "info")
        else:
            flash(mensaje, "success")
    return _destino_voto(pregunta_id)


@home_bp.post("/respuestas/<int:respuesta_id>/voto")
def votar_respuesta(respuesta_id: int):
    usuario, respuesta = _usuario_o_redirect()
    if respuesta is not None:
        return respuesta

    pregunta_id = obtener_respuesta(respuesta_id).pregunta_id
    anterior = _votos_usuario(usuario)[1].get(respuesta_id)
    valor = _valor_voto()
    if valor is None:
        flash("Voto inválido.", "info")
    else:
        try:
            if valor == 0:
                retirar_voto(respuesta_id, usuario.id)
                mensaje = "Voto quitado."
            else:
                fijar_voto(respuesta_id, usuario.id, TipoVoto(valor))
                mensaje = "Voto actualizado." if anterior is not None else "Voto registrado."
        except (ValueError, LookupError) as exc:
            flash(f"No pudimos guardar el voto: {exc}", "info")
        else:
            flash(mensaje, "success")
    return redirect(url_for("home.detalle", pregunta_id=pregunta_id))


@home_bp.post("/preguntas/<int:pregunta_id>/respuesta-aceptada")
def seleccionar_respuesta_aceptada(pregunta_id: int):
    usuario, respuesta = _usuario_o_redirect()
    if respuesta is not None:
        return respuesta

    obtener_pregunta(pregunta_id)  # 404 si no existe
    respuesta_id = _id_formulario(request.form.get("respuesta_id"))
    if respuesta_id is None:
        flash("Selección de respuesta inválida.", "info")
    else:
        try:
            if respuesta_id == 0:
                quitar_respuesta_aceptada(pregunta_id, usuario.id)
                mensaje = "Se quitó la respuesta aceptada."
            else:
                aceptar_respuesta(pregunta_id, respuesta_id, usuario.id)
                mensaje = "Respuesta marcada como aceptada."
        except NoEsAutorDeLaPregunta:
            flash("Sólo el autor de la pregunta puede elegir la solución.", "info")
        except (ValueError, LookupError) as exc:
            flash(f"No pudimos guardar la selección: {exc}", "info")
        else:
            flash(mensaje, "success")
    return redirect(url_for("home.detalle", pregunta_id=pregunta_id))


@home_bp.post("/preguntas/<int:pregunta_id>/respuestas")
def responder(pregunta_id: int):
    usuario, respuesta = _usuario_o_redirect()
    if respuesta is not None:
        return respuesta

    pregunta = obtener_pregunta(pregunta_id)
    contenido = request.form.get("contenido", "").strip()
    errores = {"contenido": None, "general": None}

    if not contenido:
        errores["contenido"] = "Escribí una respuesta antes de publicarla."

    if not any(errores.values()):
        try:
            crear_respuesta(
                pregunta_id=pregunta_id,
                usuario_id=usuario.id,
                contenido=contenido,
            )
        except ContenidoDeRespuestaInvalido as exc:
            errores["general"] = str(exc)
        except ValueError as exc:
            errores["general"] = f"No pudimos publicar la respuesta: {exc}"
        else:
            flash("Respuesta publicada correctamente.", "success")
            return redirect(url_for("home.detalle", pregunta_id=pregunta_id))

    return _render_detalle(
        usuario,
        pregunta,
        valores={"contenido": contenido},
        errores=errores,
    )


@home_bp.route("/preguntas/nueva", methods=["GET", "POST"])
def crear():
    usuario, respuesta = _usuario_o_redirect()
    if respuesta is not None:
        return respuesta

    valores = _valores_pregunta()
    errores = _errores_pregunta()

    if request.method == "POST":
        valores["titulo"] = request.form.get("titulo", "").strip()
        valores["contenido"] = request.form.get("contenido", "").strip()
        valores["categoria_id"] = request.form.get("categoria_id", "")
        etiquetas_ids = _ids_etiquetas_formulario()
        valores["etiquetas_ids"] = [str(id_) for id_ in etiquetas_ids]

        categoria_id = _id_formulario(valores["categoria_id"])

        if not valores["titulo"]:
            errores["titulo"] = "Ingresá un título para la pregunta."
        if not valores["contenido"]:
            errores["contenido"] = "Contá cuál es tu duda."
        if categoria_id is None:
            errores["categoria"] = "Elegí una categoría."

        if not any(errores.values()):
            try:
                pregunta = crear_pregunta(
                    usuario_id=usuario.id,
                    titulo=valores["titulo"],
                    contenido=valores["contenido"],
                    categoria_id=categoria_id,
                    etiquetas_ids=etiquetas_ids,
                )
            except AutorNoPuedePreguntar:
                errores["general"] = "Tu cuenta no puede crear preguntas."
            except EtiquetasInvalidas as exc:
                errores["general"] = f"Etiquetas inválidas: {exc}"
            except EtiquetaNoEncontrada as exc:
                errores["general"] = f"No pudimos guardar las etiquetas: {exc}"
            except ValueError as exc:
                errores["general"] = f"No pudimos crear la pregunta: {exc}"
            else:
                flash("Pregunta publicada correctamente.", "success")
                return redirect(url_for("home.detalle", pregunta_id=pregunta.id))

    return _render_formulario_pregunta(usuario, valores, errores)


@home_bp.route("/preguntas/<int:pregunta_id>/editar", methods=["GET", "POST"])
def editar(pregunta_id: int):
    usuario, respuesta = _usuario_o_redirect()
    if respuesta is not None:
        return respuesta

    pregunta = obtener_pregunta(pregunta_id)
    if pregunta.autor_id != usuario.id:
        flash("Sólo el autor de la pregunta puede editarla.", "info")
        return redirect(url_for("home.detalle", pregunta_id=pregunta_id))

    valores = _valores_pregunta(pregunta)
    errores = _errores_pregunta()

    if request.method == "POST":
        valores["titulo"] = request.form.get("titulo", "").strip()
        valores["contenido"] = request.form.get("contenido", "").strip()
        valores["categoria_id"] = request.form.get("categoria_id", "")
        etiquetas_ids = _ids_etiquetas_formulario()
        valores["etiquetas_ids"] = [str(id_) for id_ in etiquetas_ids]

        categoria_id = _id_formulario(valores["categoria_id"])

        if not valores["titulo"]:
            errores["titulo"] = "Ingresá un título para la pregunta."
        if not valores["contenido"]:
            errores["contenido"] = "Contá cuál es tu duda."
        if categoria_id is None:
            errores["categoria"] = "Elegí una categoría."

        if not any(errores.values()):
            try:
                modificar_pregunta(
                    pregunta_id=pregunta_id,
                    usuario_id=usuario.id,
                    titulo=valores["titulo"],
                    contenido=valores["contenido"],
                    categoria_id=categoria_id,
                    etiquetas_ids=etiquetas_ids,
                )
            except (AutorNoPuedePreguntar, NoEsAutorDeLaPregunta):
                errores["general"] = "No tenés permiso para editar esta pregunta."
            except EtiquetasInvalidas as exc:
                errores["general"] = f"Etiquetas inválidas: {exc}"
            except EtiquetaNoEncontrada as exc:
                errores["general"] = f"No pudimos guardar las etiquetas: {exc}"
            except ValueError as exc:
                errores["general"] = f"No pudimos guardar la pregunta: {exc}"
            else:
                flash("Pregunta actualizada correctamente.", "success")
                return redirect(url_for("home.detalle", pregunta_id=pregunta_id))

    return _render_formulario_pregunta(usuario, valores, errores, pregunta=pregunta)
