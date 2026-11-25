"""respuesta aceptada

Agrega ``preguntas.respuesta_aceptada_id``: la solución elegida por el autor
de la pregunta. Es independiente de los votos y, al ser una única columna por
pregunta, no puede haber más de una respuesta aceptada a la vez.

La FK usa ``ON DELETE SET NULL`` para que borrar la respuesta no elimine la
pregunta. No se reescriben datos: las preguntas existentes quedan sin solución.

Revision ID: f7c92b6d4a13
Revises: e4b9d2f7a6c1
Create Date: 2026-11-25

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f7c92b6d4a13"
down_revision: str | Sequence[str] | None = "e4b9d2f7a6c1"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _meta(con_aceptada: bool) -> sa.MetaData:
    """Definición de ``preguntas`` para el modo batch de SQLite."""
    meta = sa.MetaData()
    columnas = [
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("titulo", sa.String(200), nullable=False),
        sa.Column("contenido", sa.Text(), nullable=False),
        sa.Column("fecha_publicacion", sa.DateTime(), nullable=False),
        sa.Column("autor_id", sa.Integer(), nullable=False),
        sa.Column("categoria_id", sa.Integer(), nullable=False),
    ]
    if con_aceptada:
        columnas.append(
            sa.Column("respuesta_aceptada_id", sa.Integer(), nullable=True)
        )
    restricciones = [
        sa.ForeignKeyConstraint(
            ["autor_id"], ["autores.id"], name="fk_preguntas_autores",
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["categoria_id"], ["categorias.id"], name="fk_preguntas_categorias"
        ),
    ]
    if con_aceptada:
        restricciones.append(
            sa.ForeignKeyConstraint(
                ["respuesta_aceptada_id"],
                ["respuestas.id"],
                name="fk_preguntas_respuesta_aceptada",
                ondelete="SET NULL",
            )
        )
    sa.Table("preguntas", meta, *columnas, *restricciones)
    return meta


def _fk_sqlite(activar: bool) -> None:
    if op.get_bind().dialect.name == "sqlite":
        op.execute("PRAGMA foreign_keys=ON" if activar else "PRAGMA foreign_keys=OFF")


def upgrade() -> None:
    # Al recrear la tabla con FOREIGN KEYs activas, SQLite borraría en cascada
    # las respuestas al soltar la vieja tabla 'preguntas'.
    _fk_sqlite(False)
    with op.batch_alter_table(
        "preguntas", copy_from=_meta(con_aceptada=False).tables["preguntas"]
    ) as batch_op:
        batch_op.add_column(
            sa.Column("respuesta_aceptada_id", sa.Integer(), nullable=True)
        )
        batch_op.create_foreign_key(
            "fk_preguntas_respuesta_aceptada",
            "respuestas",
            ["respuesta_aceptada_id"],
            ["id"],
            ondelete="SET NULL",
        )
    _fk_sqlite(True)


def downgrade() -> None:
    _fk_sqlite(False)
    with op.batch_alter_table(
        "preguntas", copy_from=_meta(con_aceptada=True).tables["preguntas"]
    ) as batch_op:
        batch_op.drop_constraint(
            "fk_preguntas_respuesta_aceptada", type_="foreignkey"
        )
        batch_op.drop_column("respuesta_aceptada_id")
    _fk_sqlite(True)
