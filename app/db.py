"""Подключение к БД и базовый класс моделей."""

from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from .config import get_settings

settings = get_settings()

# pool_pre_ping: соединение проверяется перед выдачей из пула — Postgres
# закрывает простаивающие соединения, без этого первый запрос после паузы падает.
engine = create_engine(
    settings.database_url,
    echo=settings.echo_sql,
    pool_pre_ping=True,
)

SessionLocal = sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


def get_db() -> Iterator[Session]:
    """Зависимость FastAPI: одна сессия на запрос, закрывается после ответа."""
    with SessionLocal() as session:
        yield session
