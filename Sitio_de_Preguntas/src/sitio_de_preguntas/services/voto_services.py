from sqlalchemy import func

from sitio_de_preguntas.extensions import db
from sitio_de_preguntas.models import Respuesta, User, Voto
from sitio_de_preguntas.services.autor_services import UsuarioNoEncontrado


class VotoInvalido(ValueError):
    pass


def votar_respuesta(respuesta_id, usuario_id, valor) -> Respuesta:
    try:
        valor = int(valor)
    except (TypeError, ValueError) as exc:
        raise VotoInvalido("El voto debe ser 1 o -1") from exc
    if valor not in (1, -1):
        raise VotoInvalido("El voto debe ser 1 o -1")

    respuesta = db.get_or_404(Respuesta, int(respuesta_id))
    usuario_id = int(usuario_id)
    if db.session.get(User, usuario_id) is None:
        raise UsuarioNoEncontrado(f"No existe el usuario con id {usuario_id}")

    voto = Voto.query.filter_by(
        respuesta_id=respuesta.id, usuario_id=usuario_id
    ).first()
    if voto is None:
        db.session.add(Voto(respuesta=respuesta, usuario_id=usuario_id, valor=valor))
    elif voto.valor == valor:
        db.session.delete(voto)  # volver a votar lo mismo quita el voto
    else:
        voto.valor = valor

    db.session.flush()
    respuesta.votos = (
        db.session.query(func.coalesce(func.sum(Voto.valor), 0))
        .filter(Voto.respuesta_id == respuesta.id)
        .scalar()
    )
    db.session.commit()
    return respuesta


def obtener_voto_usuario(respuesta_id, usuario_id):
    return Voto.query.filter_by(
        respuesta_id=int(respuesta_id), usuario_id=int(usuario_id)
    ).first()
