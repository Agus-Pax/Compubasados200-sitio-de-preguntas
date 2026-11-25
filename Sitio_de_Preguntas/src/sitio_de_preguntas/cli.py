import click
from flask.cli import with_appcontext

from sitio_de_preguntas.services.categoria_services import (
    NombreDeCategoriaYaEnUso,
    crear_categoria,
)
from sitio_de_preguntas.services.fabrica_respuestas import TipoDeRespuestaNoSoportado
from sitio_de_preguntas.services.respuestas_automaticas import (
    generar_respuestas_pendientes,
)

CATEGORIAS_INICIALES = (
    "Base de Datos",
    "Python",
    "Java",
    "General",
    "Flask",
    "HTML",
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
    for nombre in CATEGORIAS_INICIALES:
        try:
            crear_categoria(nombre)
        except NombreDeCategoriaYaEnUso:
            click.echo(f"Ya existía: {nombre}")
        else:
            click.echo(f"Creada: {nombre}")
