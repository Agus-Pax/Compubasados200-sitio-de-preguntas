from enum import Enum

from sitio_de_preguntas.extensions import db
from sitio_de_preguntas.models import Autor, Pregunta, Respuesta, Voto
from sitio_de_preguntas.services.validaciones import validate_id


class VotoInvalido(ValueError):
    pass


class PublicacionNoEncontrada(LookupError):
    pass


class PreguntaNoEncontrada(PublicacionNoEncontrada):
    pass


class RespuestaNoEncontrada(PublicacionNoEncontrada):
    pass


# Se mantienen por compatibilidad con los imports existentes.
class UsuarioNoEncontrado(LookupError):
    pass


class VotoPropioNoPermitido(Exception):
    pass


class TipoVoto(Enum):
    A_FAVOR = 1
    EN_CONTRA = -1


def _resolver(autor_id, *, pregunta_id=None, respuesta_id=None):
    """Valida y devuelve (publicación, nombre de la FK). No escribe nada."""
    validate_id(autor_id)
    if (pregunta_id is None) == (respuesta_id is None):
        raise VotoInvalido("Indicá exactamente una pregunta o una respuesta")

    # Autor incluye a humanos (User) y agentes IA: ambos pueden votar.
    if db.session.get(Autor, autor_id) is None:
        raise UsuarioNoEncontrado(f"No existe el autor con id {autor_id}")

    if pregunta_id is not None:
        validate_id(pregunta_id)
        publicacion = db.session.get(Pregunta, pregunta_id, with_for_update=True)
        if publicacion is None:
            raise PreguntaNoEncontrada(f"No existe la pregunta {pregunta_id}")
        return publicacion, "pregunta_id"

    validate_id(respuesta_id)
    publicacion = db.session.get(Respuesta, respuesta_id, with_for_update=True)
    if publicacion is None:
        raise RespuestaNoEncontrada(f"No existe la respuesta {respuesta_id}")
    return publicacion, "respuesta_id"


def _fijar(autor_id, tipo: TipoVoto, **publicacion_id) -> Pregunta | Respuesta:
    if not isinstance(tipo, TipoVoto):
        raise VotoInvalido("tipo de voto inválido")
    publicacion, clave = _resolver(autor_id, **publicacion_id)
    filtros = {"autor_id": autor_id, clave: publicacion.id}

    try:
        voto = Voto.query.filter_by(**filtros).first()
        if voto is None:
            db.session.add(Voto(valor=tipo.value, **filtros))
        else:
            # Un mismo autor tiene un solo voto: cambiar el valor lo reemplaza.
            voto.valor = tipo.value
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return publicacion


def _retirar(autor_id, **publicacion_id) -> Pregunta | Respuesta:
    publicacion, clave = _resolver(autor_id, **publicacion_id)
    try:
        Voto.query.filter_by(autor_id=autor_id, **{clave: publicacion.id}).delete()
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return publicacion


def _obtener(autor_id, **publicacion_id) -> Voto | None:
    validate_id(autor_id)
    if (publicacion_id.get("pregunta_id") is None) == (
        publicacion_id.get("respuesta_id") is None
    ):
        raise VotoInvalido("Indicá exactamente una pregunta o una respuesta")
    return Voto.query.filter_by(autor_id=autor_id, **publicacion_id).first()


# --- Respuestas (API existente) ---------------------------------------------

def fijar_voto(respuesta_id, usuario_id, tipo: TipoVoto) -> Respuesta:
    return _fijar(usuario_id, tipo, respuesta_id=respuesta_id)


def retirar_voto(respuesta_id, usuario_id) -> Respuesta:
    return _retirar(usuario_id, respuesta_id=respuesta_id)


def obtener_voto_usuario(respuesta_id, usuario_id) -> Voto | None:
    return _obtener(usuario_id, respuesta_id=respuesta_id)


# --- Preguntas ---------------------------------------------------------------

def fijar_voto_pregunta(pregunta_id, autor_id, tipo: TipoVoto) -> Pregunta:
    return _fijar(autor_id, tipo, pregunta_id=pregunta_id)


def retirar_voto_pregunta(pregunta_id, autor_id) -> Pregunta:
    return _retirar(autor_id, pregunta_id=pregunta_id)


def obtener_voto_pregunta(pregunta_id, autor_id) -> Voto | None:
    return _obtener(autor_id, pregunta_id=pregunta_id)


def listar_votos_usuario(autor_id) -> list[Voto]:
    validate_id(autor_id)
    return Voto.query.filter_by(autor_id=autor_id).all()
