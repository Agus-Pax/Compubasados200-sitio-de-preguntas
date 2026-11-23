"""usuario hereda de autor

User pasa a ser una subclase de Autor (herencia joined-table). Por eso:

* ``autores.usuario_id`` desaparece: el mismo ``autores.id`` identifica al
  usuario, y ``users.id`` es una FK a esaPK.
* Se agrega el discriminador ``autores.tipo_autor`` ('usuario' / 'agente').
* Se agregan a ``users`` las columnas de autenticación que ya tenía el modelo.

La migración reescribe los ids de los autores-usuario para que coincidan con
``users.id``, ajusta las referencias en preguntas y respuestas y corre los ids
de los agentes (+1000000) para evitar colisiones. Esos ids de agentes no se
restauran en ``downgrade``. Probar siempre primero sobre una copia de la base.

Revision ID: c3f9a1d72b4e
Revises: 45d586dad807
Create Date: 2026-11-23

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

# revision identifiers, used by Alembic.
revision: str = "c3f9a1d72b4e"
down_revision: str | Sequence[str] | None = "45d586dad807"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

_AUTORES = "autores"
_USUARIOS = "users"


def _desactivar_fk_sqlite() -> None:
    if op.get_bind().dialect.name == "sqlite":
        # PRAGMA foreign_keys no se puede cambiar dentro de una transacción.
        op.execute("PRAGMA foreign_keys=OFF")


def _activar_fk_sqlite() -> None:
    if op.get_bind().dialect.name == "sqlite":
        op.execute("PRAGMA foreign_keys=ON")


def upgrade() -> None:
    _desactivar_fk_sqlite()

    # 1) Los agentes pueden tener el mismo id que un usuario. Los corremos
    #    primero para liberar los valores que van a tomar los usuarios.
    op.execute(
        """
        UPDATE preguntas SET autor_id = autor_id + 1000000
         WHERE autor_id IN (SELECT id FROM autores WHERE usuario_id IS NULL)
        """
    )
    op.execute(
        """
        UPDATE respuestas SET autor_id = autor_id + 1000000
         WHERE autor_id IN (SELECT id FROM autores WHERE usuario_id IS NULL)
        """
    )
    op.execute("UPDATE autores SET id = id + 1000000 WHERE usuario_id IS NULL")

    # 2) Las referencias de los autores-usuario pasan a usar users.id.
    for tabla in ("preguntas", "respuestas"):
        op.execute(
            f"""
            UPDATE {tabla}
               SET autor_id = (
                    SELECT a.usuario_id FROM autores AS a
                     WHERE a.id = {tabla}.autor_id
               )
             WHERE autor_id IN (SELECT id FROM autores WHERE usuario_id IS NOT NULL)
            """
        )
    op.execute("UPDATE autores SET id = usuario_id WHERE usuario_id IS NOT NULL")

    # 3) Discriminador: los que tienen proveedor son agentes, el resto usuarios.
    with op.batch_alter_table(_AUTORES) as batch_op:
        batch_op.add_column(sa.Column("tipo_autor", sa.String(20), nullable=True))

    op.execute(
        """
        UPDATE autores
           SET tipo_autor = CASE WHEN proveedor IS NULL THEN 'usuario' ELSE 'agente' END
        """
    )

    with op.batch_alter_table(_AUTORES) as batch_op:
        batch_op.alter_column("tipo_autor", nullable=False)
        batch_op.drop_constraint("ck_autor_usuario_o_agente", type_="check")
        batch_op.drop_column("usuario_id")
        batch_op.create_check_constraint(
            "ck_autor_tipo",
            "(tipo_autor = 'usuario' AND proveedor IS NULL) OR "
            "(tipo_autor = 'agente' AND proveedor IS NOT NULL)",
        )

    # 4) users.id pasa a ser la FK hacia autores.id. También se agregan las
    #    columnas de login que el esquema inicial no tenía.
    with op.batch_alter_table(_USUARIOS) as batch_op:
        batch_op.add_column(sa.Column("password_hash", sa.String(255), nullable=True))
        batch_op.add_column(
            sa.Column(
                "failed_attempts",
                sa.Integer(),
                nullable=False,
                server_default="0",
            )
        )
        batch_op.add_column(sa.Column("locked_until", sa.DateTime(), nullable=True))
        batch_op.create_foreign_key(
            "fk_users_autor", _AUTORES, ["id"], ["id"]
        )

    _activar_fk_sqlite()


def downgrade() -> None:
    _desactivar_fk_sqlite()

    with op.batch_alter_table(_USUARIOS) as batch_op:
        batch_op.drop_constraint("fk_users_autor", type_="foreignkey")
        batch_op.drop_column("locked_until")
        batch_op.drop_column("failed_attempts")
        batch_op.drop_column("password_hash")

    with op.batch_alter_table(_AUTORES) as batch_op:
        batch_op.add_column(sa.Column("usuario_id", sa.Integer(), nullable=True))

    op.execute("UPDATE autores SET usuario_id = id WHERE tipo_autor = 'usuario'")

    with op.batch_alter_table(_AUTORES) as batch_op:
        batch_op.drop_constraint("ck_autor_tipo", type_="check")
        batch_op.drop_column("tipo_autor")
        batch_op.create_check_constraint(
            "ck_autor_usuario_o_agente",
            "(usuario_id IS NULL) != (proveedor IS NULL)",
        )
        batch_op.create_unique_constraint("uq_autores_usuario_id", ["usuario_id"])
        batch_op.create_foreign_key(
            "fk_autores_usuario", _USUARIOS, ["usuario_id"], ["id"]
        )

    _activar_fk_sqlite()
