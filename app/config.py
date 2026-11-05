"""Настройки приложения: читаются из окружения или .env с префиксом JT_."""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_prefix="JT_",
        extra="ignore",
    )

    app_name: str = "jobtracker-api"
    database_url: str = (
        "postgresql+psycopg://jobtracker:jobtracker@localhost:5432/jobtracker"
    )
    echo_sql: bool = False


@lru_cache
def get_settings() -> Settings:
    return Settings()
