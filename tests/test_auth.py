"""Аутентификация и авторизация: токены, 401/403, изоляция данных."""

from fastapi.testclient import TestClient

from app.main import app
from tests.conftest import OTHER_USER, TEST_USER


def test_register_and_duplicate(client: TestClient) -> None:
    payload = {"email": "new@example.com", "password": "strong-password"}
    created = client.post("/auth/register", json=payload)
    assert created.status_code == 201, created.text
    assert created.json()["email"] == "new@example.com"
    # пароль никогда не возвращается
    assert "password" not in created.json()

    duplicate = client.post("/auth/register", json=payload)
    assert duplicate.status_code == 409


def test_register_rejects_short_password(client: TestClient) -> None:
    response = client.post(
        "/auth/register",
        json={"email": "weak@example.com", "password": "short"},
    )
    assert response.status_code == 422


def test_login_success_and_failure(client: TestClient) -> None:
    ok = client.post("/auth/login", json=TEST_USER)
    assert ok.status_code == 200
    body = ok.json()
    assert body["token_type"] == "bearer"
    assert body["access_token"] and body["refresh_token"]
    assert body["expires_in"] > 0

    wrong = client.post(
        "/auth/login",
        json={"email": TEST_USER["email"], "password": "wrong-password"},
    )
    assert wrong.status_code == 401

    missing = client.post(
        "/auth/login",
        json={"email": "nobody@example.com", "password": "whatever123"},
    )
    assert missing.status_code == 401


def test_protected_endpoint_requires_token(client: TestClient) -> None:
    # Новый клиент без заголовка авторизации
    anon = TestClient(app)
    assert anon.get("/vacancies").status_code == 401
    assert anon.get("/stats").status_code == 401
    assert anon.get("/auth/me").status_code == 401


def test_invalid_token_rejected(client: TestClient) -> None:
    response = client.get(
        "/auth/me",
        headers={"Authorization": "Bearer not-a-real-token"},
    )
    assert response.status_code == 401


def test_me_returns_current_user(client: TestClient) -> None:
    me = client.get("/auth/me")
    assert me.status_code == 200
    assert me.json()["email"] == TEST_USER["email"]


def test_refresh_issues_new_pair(client: TestClient) -> None:
    pair = client.post("/auth/login", json=TEST_USER).json()
    refreshed = client.post(
        "/auth/refresh",
        json={"refresh_token": pair["refresh_token"]},
    )
    assert refreshed.status_code == 200
    new_access = refreshed.json()["access_token"]

    me = client.get("/auth/me", headers={"Authorization": f"Bearer {new_access}"})
    assert me.status_code == 200


def test_access_token_cannot_be_used_as_refresh(client: TestClient) -> None:
    pair = client.post("/auth/login", json=TEST_USER).json()
    response = client.post(
        "/auth/refresh",
        json={"refresh_token": pair["access_token"]},
    )
    assert response.status_code == 401


def test_user_cannot_see_another_users_vacancy(
    client: TestClient,
    other_headers: dict[str, str],
    vacancy_payload: dict,
) -> None:
    created = client.post("/vacancies", json=vacancy_payload)
    vacancy_id = created.json()["id"]

    # Второй пользователь не видит и не может изменить чужую вакансию
    assert client.get(f"/vacancies/{vacancy_id}", headers=other_headers).status_code == 404
    assert (
        client.patch(
            f"/vacancies/{vacancy_id}",
            json={"status": "rejected"},
            headers=other_headers,
        ).status_code
        == 404
    )
    assert client.get("/vacancies", headers=other_headers).json()["total"] == 0


def test_same_url_allowed_for_different_users(
    client: TestClient,
    other_headers: dict[str, str],
    vacancy_payload: dict,
) -> None:
    assert client.post("/vacancies", json=vacancy_payload).status_code == 201
    # Тот же URL у другого пользователя — не конфликт
    assert (
        client.post("/vacancies", json=vacancy_payload, headers=other_headers).status_code
        == 201
    )


def test_stats_are_per_user(
    client: TestClient,
    other_headers: dict[str, str],
    vacancy_payload: dict,
) -> None:
    client.post("/vacancies", json=vacancy_payload)
    mine = client.get("/stats").json()
    theirs = client.get("/stats", headers=other_headers).json()

    assert mine["total"] == 1
    assert theirs["total"] == 0
    assert OTHER_USER["email"]  # второй пользователь действительно существует
