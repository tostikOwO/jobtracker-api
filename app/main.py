"""Точка входа: сборка приложения из роутеров."""

from fastapi import FastAPI

from .api import stats, vacancies
from .config import get_settings

settings = get_settings()


def create_app() -> FastAPI:
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        summary="Учёт вакансий и откликов: REST API на FastAPI + SQLAlchemy 2.0",
    )
    app.include_router(vacancies.router)
    app.include_router(stats.router)

    @app.get("/health", tags=["service"])
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
