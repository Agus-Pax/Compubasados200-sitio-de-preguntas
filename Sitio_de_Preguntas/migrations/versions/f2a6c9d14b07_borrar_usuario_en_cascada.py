"""borrar usuario en cascada

Ahora se puede borrar un usuario aunque tenga preguntas, respuestas o votos:

* Las foreign keys hacia ``autores``/``users`` (y las que encadenan preguntas,
  respuestas y votos) pasan a tener ``ON DELETE CASCADE``.
* Las relaciones ORM complementan esto con ``delete-orphan`` para que
  SQLAlchemy borre los hijos cargados en la sesión antes que al padre.
* ``respuestas.votos`` pasa a ser nullable: el modelo ya no la escribe (es un
  ``column_property`` calculado) y si no, falla cualquier INSERT en una BD
  migrada.

En SQLite hay que recrear las tablas para cambiar una FK; por eso se usa el
modo batch con ``copy_from`` (para no perder índices ni constraints).

Revision ID: f2a6c9d14b07
Revises: c3f9a1d72b4e
Create Date: 2026-11-23

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "f2a6c9d14b07"
down_revision: str | Sequence[str] | None = "c3f9a1d72b4e"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def _meta() -> sa.MetaData:
    """Definición actual de las tablas, necesaria para `copy_from`."""
    meta = sa.MetaData()

    sa.Table(
        "preguntas",
        meta,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("titulo", sa.String(200), nullable=False),
        sa.Column("contenido", sa.Text, nullable=False),
        sa.Column("fecha_publicacion", sa.DateTime, nullable=False),
        sa.Column("autor_id", sa.Integer, nullable=False),
        sa.Column("categoria_id", sa.Integer, nullable=False),
        sa.ForeignKeyConstraint(
            ["autor_id"], ["autores.id"], name="fk_preguntas_autores"
        ),
        sa.ForeignKeyConstraint(
            ["categoria_id"], ["categorias.id"], name="fk_preguntas_categorias"
        ),
    )

    sa.Table(
        "respuestas",
        meta,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("contenido", sa.Text, nullable=False),
        sa.Column("fecha_publicacion", sa.DateTime, nullable=False),
        sa.Column("pregunta_id", sa.Integer, nullable=False),
        sa.Column("autor_id", sa.Integer, nullable=False),
        sa.Column("votos", sa.Integer, nullable=False),
        sa.Index("ix_respuestas_pregunta_id", "pregunta_id"),
        sa.ForeignKeyConstraint(
            ["autor_id"], ["autores.id"], name="fk_respuestas_autores"
        ),
        sa.ForeignKeyConstraint(
            ["pregunta_id"], ["preguntas.id"], name="fk_respuestas_preguntas"
        ),
    )

    sa.Table(
        "votos",
        meta,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("usuario_id", sa.Integer, nullable=False),
        sa.Column("respuesta_id", sa.Integer, nullable=False),
        sa.Column("valor", sa.Integer, nullable=False),
        sa.Index("ix_votos_respuesta_id", "respuesta_id"),
        sa.CheckConstraint("valor IN (-1, 1)", name="ck_voto_valor"),
        sa.ForeignKeyConstraint(
            ["respuesta_id"], ["respuestas.id"], name="fk_votos_respuestas"
        ),
        sa.ForeignKeyConstraint(["usuario_id"], ["users.id"], name="fk_votos_usuarios"),
        sa.UniqueConstraint(
            "usuario_id", "respuesta_id", name="uq_voto_usuario_respuesta"
        ),
    )

    sa.Table(
        "users",
        meta,
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column("name", sa.String(120), nullable=False),
        sa.Column("email", sa.String(255), nullable=False),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column(
            "failed_attempts", sa.Integer, nullable=False, server_default="0"
        ),
        sa.Column("locked_until", sa.DateTime, nullable=True),
        sa.UniqueConstraint("email"),
        sa.ForeignKeyConstraint(["id"], ["autores.id"], name="fk_users_autor"),
    )

    return meta


# (tabla, nombre de la FK, columna local, tabla referida, columna referida)
_FKS = (
    ("preguntas", "fk_preguntas_autores", "autor_id", "autores", "id"),
    ("respuestas", "fk_respuestas_autores", "autor_id", "autores", "id"),
    ("respuestas", "fk_respuestas_preguntas", "pregunta_id", "preguntas", "id"),
    ("votos", "fk_votos_respuestas", "respuesta_id", "respuestas", "id"),
    ("votos", "fk_votos_usuarios", "usuario_id", "users", "id"),
    ("users", "fk_users_autor", "id", "autores", "id"),
)


def _recambiar_fks(ondelete: str | None, *, votos_respuesta_nullable: bool) -> None:
    meta = _meta()
    # Agrupamos por tabla para recrearla una sola vez.
    por_tabla: dict[str, list[tuple[str, str, str, str]]] = {}
    for tabla, nombre, columna, referida, referida_col in _FKS:
        por_tabla.setdefault(tabla, []).append(
            (nombre, columna, referida, referida_col)
        )

    for tabla, fks in por_tabla.items():
        with op.batch_alter_table(tabla, copy_from=meta.tables[tabla]) as batch_op:
            for nombre, _columna, _referida, _referida_col in fks:
                batch_op.drop_constraint(nombre, type_="foreignkey")
            for nombre, columna, referida, referida_col in fks:
                batch_op.create_foreign_key(
                    nombre,
                    referida,
                    [columna],
                    [referida_col],
                    ondelete=ondelete,
                )
            if tabla == "respuestas":
                # El modelo ya no escribe esta columna (ahora es un
                # column_property calculado), así que debe poder quedar vacía.
                batch_op.alter_column(
                    "votos",
                    existing_type=sa.Integer,
                    nullable=votos_respuesta_nullable,
                    server_default="0" if votos_respuesta_nullable else None,
                )


def _fk_sqlite(activar: bool) -> None:
    if op.get_bind().dialect.name == "sqlite":
        op.execute("PRAGMA foreign_keys=ON" if activar else "PRAGMA foreign_keys=OFF")


def upgrade() -> None:
    _fk_sqlite(False)
    _recambiar_fks(ondelete="CASCADE", votos_respuesta_nullable=True)
    _fk_sqlite(True)


def downgrade() -> None:
    _fk_sqlite(False)
    _recambiar_fks(ondelete=None, votos_respuesta_nullable=False)
    _fk_sqlite(True)
