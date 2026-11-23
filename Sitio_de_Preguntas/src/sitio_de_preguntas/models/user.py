from sitio_de_preguntas.extensions import db


class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(255), nullable=False, unique=True)

     # autenticación (la lógica está en services/User_services.py) ---
    password_hash = db.Column(db.String(255), nullable=True)
    failed_attempts = db.Column(
        db.Integer, nullable=False, default=0, server_default="0"
    )
    locked_until = db.Column(db.DateTime, nullable=True)

    def __repr__(self) -> str:
        return f"<User {self.email}>"
