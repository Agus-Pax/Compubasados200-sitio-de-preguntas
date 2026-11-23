import click
from flask.cli import with_appcontext

from sitio_de_preguntas.services.respuestas_automaticas import (
    generar_respuestas_pendientes,
)


@click.command("respuestas-automaticas")
@click.option("--llm", default=None, help="CLAUDE | GEMINI | CHAT_GPT (por defecto LLM_PROVIDER)")
@with_appcontext
def respuestas_automaticas_command(llm):
    """Responde con un LLM las preguntas sin respuesta tras 1 semana."""
    n = generar_respuestas_pendientes(tipo=llm)
    click.echo(f"Respuestas automáticas generadas: {n}")