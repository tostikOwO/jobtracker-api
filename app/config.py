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

    # В проде секрет обязан приходить из окружения: дефолт только для тестов
    # и локального запуска.
    secret_key: str = "dev-only-secret-change-me-32-bytes-minimum"
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 15
    refresh_token_ttl_days: int = 7


@lru_cache
def get_settings() -> Settings:
    return Settings()
