from enum import Enum

from sqlalchemy import func

from sitio_de_preguntas.extensions import db
from sitio_de_preguntas.models import Respuesta, User, Voto
from sitio_de_preguntas.services.validaciones import validate_id


class VotoInvalido(ValueError):
    pass

class RespuestaNoEncontrada(LookupError):
    pass

class VotoPropioNoPermitido(Exception):
    pass

class UsuarioNoEncontrado(LookupError):
    pass

class TipoVoto(Enum):
    A_FAVOR = 1
    EN_CONTRA = -1


def _resolver(respuesta_id, usuario_id):
    """Valida y devuelve la respuesta ya bloqueada. No escribe nada."""
    validate_id(respuesta_id)
    validate_id(usuario_id)
    if db.session.get(User, usuario_id) is None:
        raise UsuarioNoEncontrado(f"No existe el usuario {usuario_id}")
    # with_for_update serializa los votos sobre la misma respuesta
    respuesta = db.session.get(Respuesta, respuesta_id, with_for_update=True)
    if respuesta is None:
        raise RespuestaNoEncontrada(f"No existe la respuesta {respuesta_id}")
    # User hereda de Autor: autor_id coincide con el id del usuario.
    if respuesta.autor_id == usuario_id:
        raise VotoPropioNoPermitido("No podés votar tu propia respuesta")
    return respuesta


def _recalcular(respuesta):
    respuesta.votos = (
        db.session.query(func.coalesce(func.sum(Voto.valor), 0))
        .filter(Voto.respuesta_id == respuesta.id)
        .scalar()
    )


def fijar_voto(respuesta_id, usuario_id, tipo: TipoVoto) -> Respuesta:
    if not isinstance(tipo, TipoVoto):
        raise VotoInvalido("tipo de voto inválido")
    try:
        respuesta = _resolver(respuesta_id, usuario_id)
        voto = Voto.query.filter_by(
            respuesta_id=respuesta.id, usuario_id=usuario_id
        ).first()
        if voto is None:
            db.session.add(
                Voto(respuesta_id=respuesta.id, usuario_id=usuario_id, valor=tipo.value)
            )
        else:
            voto.valor = tipo.value #repetirlo no cambia nada
        db.session.flush()
        _recalcular(respuesta)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return respuesta


def retirar_voto(respuesta_id, usuario_id) -> Respuesta:
    try:
        respuesta = _resolver(respuesta_id, usuario_id)
        Voto.query.filter_by(
            respuesta_id=respuesta.id, usuario_id=usuario_id
        ).delete()  # si no existe, no hace nada
        db.session.flush()
        _recalcular(respuesta)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return respuesta

def obtener_voto_usuario(respuesta_id, usuario_id):
    validate_id(respuesta_id)
    validate_id(usuario_id)
    return Voto.query.filter_by(
        respuesta_id=int(respuesta_id), usuario_id=int(usuario_id)
    ).first()
