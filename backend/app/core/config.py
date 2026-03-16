from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:password@localhost:5432/healthcare"

    model_config = {"env_file": ".env", "extra": "ignore"}


settings = Settings()
