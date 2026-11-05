"""CRUD вакансий: создание, чтение, фильтры, обновление, удаление."""

from fastapi.testclient import TestClient


def test_health(client: TestClient) -> None:
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_create_and_get(client: TestClient, vacancy_payload: dict) -> None:
    created = client.post("/vacancies", json=vacancy_payload)
    assert created.status_code == 201, created.text
    body = created.json()
    assert body["id"] > 0
    assert body["status"] == "new"
    assert body["title"] == vacancy_payload["title"]

    fetched = client.get(f"/vacancies/{body['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["url"] == vacancy_payload["url"]


def test_get_missing_returns_404(client: TestClient) -> None:
    response = client.get("/vacancies/999999")
    assert response.status_code == 404


def test_duplicate_url_returns_409(
    client: TestClient, vacancy_payload: dict
) -> None:
    assert client.post("/vacancies", json=vacancy_payload).status_code == 201
    duplicate = client.post("/vacancies", json=vacancy_payload)
    assert duplicate.status_code == 409


def test_salary_range_validated(client: TestClient, vacancy_payload: dict) -> None:
    payload = vacancy_payload | {"salary_from": 100000, "salary_to": 50000}
    response = client.post("/vacancies", json=payload)
    assert response.status_code == 422


def test_list_filters(client: TestClient, vacancy_payload: dict) -> None:
    other = vacancy_payload | {
        "title": "QA-инженер",
        "company": "Лютик",
        "url": "https://hh.ru/vacancy/1002",
        "remote": False,
    }
    client.post("/vacancies", json=vacancy_payload)
    client.post("/vacancies", json=other)

    everything = client.get("/vacancies")
    assert everything.status_code == 200
    assert everything.json()["total"] == 2

    remote_only = client.get("/vacancies", params={"remote": "true"})
    assert remote_only.json()["total"] == 1

    by_text = client.get("/vacancies", params={"q": "qa"})
    assert by_text.json()["total"] == 1
    assert by_text.json()["items"][0]["company"] == "Лютик"

    page = client.get("/vacancies", params={"limit": 1, "offset": 1})
    assert page.json()["total"] == 2
    assert len(page.json()["items"]) == 1


def test_patch(client: TestClient, vacancy_payload: dict) -> None:
    vacancy_id = client.post("/vacancies", json=vacancy_payload).json()["id"]

    updated = client.patch(
        f"/vacancies/{vacancy_id}",
        json={"status": "interview", "salary_to": 120000},
    )
    assert updated.status_code == 200
    assert updated.json()["status"] == "interview"
    assert updated.json()["salary_to"] == 120000
    assert updated.json()["title"] == vacancy_payload["title"]


def test_patch_partial_salary_validated(
    client: TestClient, vacancy_payload: dict
) -> None:
    vacancy_id = client.post("/vacancies", json=vacancy_payload).json()["id"]
    response = client.patch(f"/vacancies/{vacancy_id}", json={"salary_from": 200000})
    assert response.status_code == 422


def test_delete(client: TestClient, vacancy_payload: dict) -> None:
    vacancy_id = client.post("/vacancies", json=vacancy_payload).json()["id"]
    assert client.delete(f"/vacancies/{vacancy_id}").status_code == 204
    assert client.get(f"/vacancies/{vacancy_id}").status_code == 404
