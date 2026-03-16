from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    CORS_ORIGINS: str = "http://localhost:3000"

    LLM_PROVIDER: str = "openai"
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    OPENAI_MODEL: str = "gpt-4o-mini"
    ANTHROPIC_MODEL: str = "claude-sonnet-4-20250514"
    LLM_MAX_RETRIES: int = 1
    LLM_COMPLEMENT_CONFIDENCE_THRESHOLD: float = 0.75
    LLM_COMPLEMENT_MIN_RECOMMENDATIONS: int = 3
    MAX_RECOMMENDATIONS: int = 3

    ADMIN_USERNAME: str = "admin"
    ADMIN_PASSWORD: str = "1111"

    model_config = {"env_file": ".env", "extra": "ignore"}

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


settings = Settings()
