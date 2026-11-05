"""Отклики: статус меняется, повторный отклик запрещён, статистика считается."""

from fastapi.testclient import TestClient


def test_apply_sets_status_and_conflicts(
    client: TestClient, vacancy_payload: dict
) -> None:
    vacancy_id = client.post("/vacancies", json=vacancy_payload).json()["id"]

    applied = client.post(
        f"/vacancies/{vacancy_id}/applications",
        json={"cover_letter": "Здравствуйте! Готов работать по ГПХ."},
    )
    assert applied.status_code == 201, applied.text
    assert applied.json()["vacancy_id"] == vacancy_id

    vacancy = client.get(f"/vacancies/{vacancy_id}").json()
    assert vacancy["status"] == "applied"

    again = client.post(
        f"/vacancies/{vacancy_id}/applications",
        json={"cover_letter": "ещё раз"},
    )
    assert again.status_code == 409

    listed = client.get(f"/vacancies/{vacancy_id}/applications")
    assert listed.status_code == 200
    assert len(listed.json()) == 1


def test_apply_to_missing_vacancy_returns_404(client: TestClient) -> None:
    response = client.post("/vacancies/424242/applications", json={})
    assert response.status_code == 404


def test_stats_counts_by_status(
    client: TestClient, vacancy_payload: dict
) -> None:
    first = client.post("/vacancies", json=vacancy_payload).json()["id"]
    client.post(
        "/vacancies",
        json=vacancy_payload | {"url": "https://hh.ru/vacancy/2002"},
    )
    client.post(f"/vacancies/{first}/applications", json={"cover_letter": ""})

    response = client.get("/stats")
    assert response.status_code == 200
    stats = response.json()
    assert stats["total"] == 2
    assert stats["applications"] == 1
    assert stats["by_status"]["applied"] == 1
    assert stats["by_status"]["new"] == 1
    # Статусы без записей отдаются нулями, а не отсутствуют
    assert stats["by_status"]["rejected"] == 0
