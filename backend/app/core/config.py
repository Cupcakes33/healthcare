from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    CORS_ORIGINS: str = "http://localhost:3000"

    LLM_PROVIDER: str = "openai"
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"
    CHAT_MODEL: str = "gpt-4.1-nano"
    ANALYSIS_MODEL: str = "gpt-4.1"

    CHAT_MAX_TURNS: int = 8
    CHAT_SESSION_TTL_MINUTES: int = 30

    CHAT_RATE_LIMIT_PER_MINUTE: int = 5
    CHAT_RATE_LIMIT_PER_HOUR: int = 20
    CHAT_MAX_ACTIVE_SESSIONS: int = 100
    DAILY_LLM_CALL_LIMIT: int = 500
    CHAT_MESSAGE_MAX_LENGTH: int = 500

    LLM_MAX_RETRIES: int = 1
    LLM_MAX_TOKENS: int = 2048
    LLM_COMPLEMENT_CONFIDENCE_THRESHOLD: float = 0.75
    LLM_COMPLEMENT_MIN_RECOMMENDATIONS: int = 3
    MAX_RECOMMENDATIONS: int = 3

    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = ""

    model_config = {"env_file": ".env", "extra": "ignore"}

    @property
    def database_url_async(self) -> str:
        url = self.DATABASE_URL
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql+asyncpg://", 1)
        elif url.startswith("postgresql://"):
            url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
        return url

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
