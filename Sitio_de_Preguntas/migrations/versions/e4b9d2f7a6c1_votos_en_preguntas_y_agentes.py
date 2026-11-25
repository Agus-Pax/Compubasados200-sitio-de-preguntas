"""votos en preguntas y agentes

``votos`` pasa a representar un voto por autor sobre una pregunta O una
respuesta. Antes sólo podía votar un ``User`` (FK a ``users``) y sólo una
respuesta; los agentes IA son ``Autor`` pero no tienen fila en ``users``.

La tabla se recrea copiando las filas existentes (hoy no hay ninguna), sin
tocar preguntas, respuestas ni usuarios. Los votos de agentes no se pueden
representar en el esquema viejo, por eso se descartan en ``downgrade``.

Revision ID: e4b9d2f7a6c1
Revises: a7c4e9f2b8d1
Create Date: 2026-11-25

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "e4b9d2f7a6c1"
down_revision: str | Sequence[str] | None = "a7c4e9f2b8d1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _crear_tabla_nueva() -> None:
    op.create_table(
        "votos_nuevos",
        sa.Column("id", sa.Integer(), primary_key=True, autoincrement=True),
        sa.Column("pregunta_id", sa.Integer(), nullable=True),
        sa.Column("respuesta_id", sa.Integer(), nullable=True),
        sa.Column("autor_id", sa.Integer(), nullable=False),
        sa.Column("valor", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["pregunta_id"], ["preguntas.id"], name="fk_votos_preguntas",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["respuesta_id"], ["respuestas.id"], name="fk_votos_respuestas",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["autor_id"], ["autores.id"], name="fk_votos_autores",
            ondelete="CASCADE",
        ),
        sa.UniqueConstraint(
            "autor_id", "pregunta_id", name="uq_voto_autor_pregunta"
        ),
        sa.UniqueConstraint(
            "autor_id", "respuesta_id", name="uq_voto_autor_respuesta"
        ),
        sa.CheckConstraint("valor IN (-1, 1)", name="ck_voto_valor"),
        sa.CheckConstraint(
            "(pregunta_id IS NOT NULL AND respuesta_id IS NULL) OR "
            "(pregunta_id IS NULL AND respuesta_id IS NOT NULL)",
            name="ck_voto_objetivo",
        ),
    )


def _fk_sqlite(activar: bool) -> None:
    if op.get_bind().dialect.name == "sqlite":
        op.execute("PRAGMA foreign_keys=ON" if activar else "PRAGMA foreign_keys=OFF")


def upgrade() -> None:
    _fk_sqlite(False)
    _crear_tabla_nueva()
    op.execute(
        "INSERT INTO votos_nuevos (respuesta_id, autor_id, valor) "
        "SELECT respuesta_id, usuario_id, valor FROM votos"
    )
    op.drop_table("votos")
    op.rename_table("votos_nuevos", "votos")
    op.create_index("ix_votos_pregunta_id", "votos", ["pregunta_id"])
    op.create_index("ix_votos_respuesta_id", "votos", ["respuesta_id"])
    op.create_index("ix_votos_autor_id", "votos", ["autor_id"])
    _fk_sqlite(True)


def downgrade() -> None:
    _fk_sqlite(False)
    op.create_table(
        "votos_viejos",
        sa.Column("respuesta_id", sa.Integer(), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("valor", sa.Integer(), nullable=False),
        sa.PrimaryKeyConstraint("respuesta_id", "usuario_id"),
        sa.CheckConstraint("valor IN (-1, 1)", name="ck_voto_valor"),
        sa.UniqueConstraint(
            "usuario_id", "respuesta_id", name="uq_voto_usuario_respuesta"
        ),
        sa.ForeignKeyConstraint(
            ["respuesta_id"], ["respuestas.id"], name="fk_votos_respuestas",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["usuario_id"], ["users.id"], name="fk_votos_usuarios",
            ondelete="CASCADE",
        ),
    )
    op.execute(
        "INSERT INTO votos_viejos (respuesta_id, usuario_id, valor) "
        "SELECT respuesta_id, autor_id, valor FROM votos "
        "WHERE pregunta_id IS NULL AND autor_id IN (SELECT id FROM users)"
    )
    op.drop_table("votos")
    op.rename_table("votos_viejos", "votos")
    op.create_index("ix_votos_respuesta_id", "votos", ["respuesta_id"])
    _fk_sqlite(True)
