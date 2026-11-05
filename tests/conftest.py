"""Фикстуры: SQLite в памяти вместо Postgres + авторизованный клиент."""

from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, get_db
from app.main import app

TEST_USER = {"email": "test@example.com", "password": "secret-password"}
OTHER_USER = {"email": "other@example.com", "password": "another-password"}


@pytest.fixture
def client() -> Iterator[TestClient]:
    # StaticPool: все соединения видят одну и ту же in-memory БД,
    # иначе каждый коннект получает пустую базу.
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    TestingSession = sessionmaker(
        bind=engine,
        autoflush=False,
        expire_on_commit=False,
    )

    def override_get_db() -> Iterator[Session]:
        with TestingSession() as session:
            yield session

    app.dependency_overrides[get_db] = override_get_db
    try:
        with TestClient(app) as test_client:
            # По умолчанию клиент авторизован под первым пользователем:
            # так CRUD-тесты не дублируют заголовок в каждом запросе.
            test_client.post("/auth/register", json=TEST_USER)
            token = test_client.post("/auth/login", json=TEST_USER).json()[
                "access_token"
            ]
            test_client.headers.update({"Authorization": f"Bearer {token}"})
            yield test_client
    finally:
        app.dependency_overrides.clear()
        Base.metadata.drop_all(engine)
        engine.dispose()


@pytest.fixture
def auth_headers(client: TestClient) -> dict[str, str]:
    return {"Authorization": client.headers["Authorization"]}


@pytest.fixture
def other_headers(client: TestClient) -> dict[str, str]:
    """Второй пользователь — для проверки изоляции данных."""
    client.post("/auth/register", json=OTHER_USER)
    response = client.post("/auth/login", json=OTHER_USER)
    return {"Authorization": f"Bearer {response.json()['access_token']}"}


@pytest.fixture
def vacancy_payload() -> dict:
    return {
        "title": "Backend-разработчик (Python)",
        "company": "Ромашка",
        "url": "https://hh.ru/vacancy/1001",
        "salary_from": 60000,
        "salary_to": 90000,
        "remote": True,
    }
