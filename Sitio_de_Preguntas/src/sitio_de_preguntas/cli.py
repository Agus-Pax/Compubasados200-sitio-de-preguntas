import click
from flask.cli import with_appcontext

from sitio_de_preguntas.services.categoria_services import (
    CATEGORIAS_INICIALES,
    cargar_categorias_iniciales,
)
from sitio_de_preguntas.services.fabrica_respuestas import TipoDeRespuestaNoSoportado
from sitio_de_preguntas.services.respuestas_automaticas import (
    generar_respuestas_pendientes,
)


@click.command("respuestas-automaticas")
@click.option("--llm", default=None, help="CLAUDE | GEMINI | GPT (por defecto LLM_PROVIDER)")
@with_appcontext
def respuestas_automaticas_command(llm):
    """Responde con un LLM las preguntas sin respuesta tras 1 semana."""
    try:
        n = generar_respuestas_pendientes(tipo=llm)
    except TipoDeRespuestaNoSoportado as exc:
        raise click.UsageError(str(exc)) from exc
    click.echo(f"Respuestas automáticas generadas: {n}")


@click.command("init-categorias")
@with_appcontext
def init_categorias_command():
    """Carga las categorías iniciales sin duplicar las que ya existen."""
    creadas = cargar_categorias_iniciales()
    for nombre in CATEGORIAS_INICIALES:
        estado = "Creada" if nombre in creadas else "Ya existía"
        click.echo(f"{estado}: {nombre}")
