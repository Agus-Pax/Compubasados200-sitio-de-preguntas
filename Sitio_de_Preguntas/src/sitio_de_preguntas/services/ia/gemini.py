from flask import current_app

from sitio_de_preguntas.services.ia.strategy_ia import StrategyIA


class Gemini(StrategyIA):
    tipo = "GEMINI"

    def generar_texto(self, prompt: str) -> str:
        from google import genai  # pip install google-genai

        client = genai.Client(api_key=current_app.config["GEMINI_API_KEY"])
        resp = client.models.generate_content(
            model=current_app.config["GEMINI_MODEL"], contents=prompt
        )
        return resp.text