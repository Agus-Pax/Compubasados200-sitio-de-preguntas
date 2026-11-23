"""contraseña obligatoria

``users.password_hash`` pasa a ser NOT NULL, como ya lo exige el modelo.

Las filas que no tenían hash (o lo tenían vacío) reciben uno aleatorio
inutilizable: esos usuarios ya no podían iniciar sesión de todos modos, y así
no se crea una contraseña conocida por defecto.

Revision ID: a7c4e9f2b8d1
Revises: f2a6c9d14b07
Create Date: 2026-11-23

"""

import secrets
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from werkzeug.security import generate_password_hash

revision: str = "a7c4e9f2b8d1"
down_revision: str | Sequence[str] | None = "f2a6c9d14b07"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    conn = op.get_bind()
    sin_hash = conn.execute(
        sa.text("SELECT id FROM users WHERE password_hash IS NULL OR password_hash = ''")
    ).scalars().all()
    for user_id in sin_hash:
        conn.execute(
            sa.text("UPDATE users SET password_hash = :hash WHERE id = :id"),
            {"hash": generate_password_hash(secrets.token_urlsafe(32)), "id": user_id},
        )

    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column("password_hash", existing_type=sa.String(255), nullable=False)


def downgrade() -> None:
    with op.batch_alter_table("users") as batch_op:
        batch_op.alter_column("password_hash", existing_type=sa.String(255), nullable=True)
