from flask import current_app

from sitio_de_preguntas.models import TipoRespuesta
from sitio_de_preguntas.services.ia.strategy_ia import StrategyIA


class ChatGPT(StrategyIA):
    tipo = TipoRespuesta.GPT

    def generar_texto(self, prompt: str) -> str:
        from openai import OpenAI  # pip install openai

        client = OpenAI(api_key=current_app.config["OPENAI_API_KEY"])
        resp = client.chat.completions.create(
            model=current_app.config["OPENAI_MODEL"],
            messages=[{"role": "user", "content": prompt}],
        )
        return resp.choices[0].message.content