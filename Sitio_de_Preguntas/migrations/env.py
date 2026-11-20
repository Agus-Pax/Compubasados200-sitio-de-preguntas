from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from sitio_de_preguntas import create_app, models  # noqa: F401
from sitio_de_preguntas.extensions import db

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config


def _configurar_url() -> None:
    """Usar la URL de la app para apuntar siempre a la misma base de datos."""
    app = create_app()
    with app.app_context():
        url = str(db.engine.url)
    # ConfigParser interpreta '%' como interpolación.
    config.set_main_option("sqlalchemy.url", url.replace("%", "%%"))


_configurar_url()

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Los modelos se importan arriba para que db.metadata los tenga registrados.
target_metadata = db.metadata

# other values from the config, defined by the needs of env.py,
# can be acquired:
# my_important_option = config.get_main_option("my_important_option")
# ... etc.


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
