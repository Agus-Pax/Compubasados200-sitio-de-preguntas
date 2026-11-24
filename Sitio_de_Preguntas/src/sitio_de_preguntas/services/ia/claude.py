from flask import current_app

from sitio_de_preguntas.models import TipoRespuesta
from sitio_de_preguntas.services.ia.strategy_ia import StrategyIA


class Claude(StrategyIA):
    tipo = TipoRespuesta.CLAUDE

    def generar_texto(self, prompt: str) -> str:
        import anthropic  # pip install anthropic

        client = anthropic.Anthropic(api_key=current_app.config["ANTHROPIC_API_KEY"])
        msg = client.messages.create(
            model=current_app.config["CLAUDE_MODEL"],
            max_tokens=1000,
            messages=[{"role": "user", "content": prompt}],
        )
        return "".join(b.text for b in msg.content if b.type == "text")