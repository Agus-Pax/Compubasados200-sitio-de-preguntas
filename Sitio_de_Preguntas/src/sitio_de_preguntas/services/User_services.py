from sitio_de_preguntas.extensions import db
from sitio_de_preguntas.models import User

class EmailYaEnUso(Exception):
    pass

def create_user(name: str, email: str):
    if User.query.filter_by(email = email).first():
        raise EmailYaEnUso
    user = User(name, email)
    db.session.add(user)
    db.session.commit()
    return user

def delete_user(id: int):
    user = db.get_or_404(User, id)
    db.session.delete(user)
    db.session.commit()

def modify_user(id: int, name: str, email: str):
    if User.query.filter_by(email = email).first():
            raise EmailYaEnUso
    user = db.get_or_404(User, id)
    user.email = email
    user.name = name
    db.session.commit()
