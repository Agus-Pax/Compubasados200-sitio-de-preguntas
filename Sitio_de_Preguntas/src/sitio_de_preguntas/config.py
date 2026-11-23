import os


class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "development-only-key")
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "sqlite:///app.db",
    )

    # login
    MAX_LOGIN_ATTEMPTS = int(os.getenv("MAX_LOGIN_ATTEMPTS", "3"))
    LOCK_MINUTES = int(os.getenv("LOCK_MINUTES", "15"))

    # respuestas automáticas 
    AUTO_ANSWER_AFTER_DAYS = int(os.getenv("AUTO_ANSWER_AFTER_DAYS", "7"))

    # LLM a usar: CLAUDE | GEMINI | CHAT_GPT 
    # Se cambia SOLO con la variable de entorno
    LLM_PROVIDER = os.getenv("LLM_PROVIDER", "CLAUDE")
    ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
    CLAUDE_MODEL = os.getenv("CLAUDE_MODEL", "claude-sonnet-5-5")
    GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
    OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
    OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")