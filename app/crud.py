"""Слой работы с БД: здесь живёт вся логика, роутеры только переводят в HTTP."""

from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from .models import Application, Vacancy, VacancyStatus
from .schemas import VacancyCreate, VacancyUpdate


class DuplicateUrl(Exception):
    """Такая вакансия уже добавлена (unique constraint на url)."""


class AlreadyApplied(Exception):
    """Отклик на эту вакансию уже отправлен."""


def create_vacancy(db: Session, data: VacancyCreate) -> Vacancy:
    payload = data.model_dump(exclude={"url"})
    payload["status"] = VacancyStatus(payload["status"]).value
    vacancy = Vacancy(**payload, url=str(data.url))
    db.add(vacancy)
    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateUrl(str(data.url)) from exc
    db.refresh(vacancy)
    return vacancy


def list_vacancies(
    db: Session,
    *,
    status: VacancyStatus | None = None,
    remote: bool | None = None,
    q: str | None = None,
    limit: int = 20,
    offset: int = 0,
) -> tuple[list[Vacancy], int]:
    stmt = select(Vacancy)
    if status is not None:
        stmt = stmt.where(Vacancy.status == status.value)
    if remote is not None:
        stmt = stmt.where(Vacancy.remote.is_(remote))
    if q:
        pattern = f"%{q.strip()}%"
        stmt = stmt.where(
            or_(Vacancy.title.ilike(pattern), Vacancy.company.ilike(pattern))
        )

    total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
    items = list(
        db.scalars(
            stmt.order_by(Vacancy.created_at.desc(), Vacancy.id.desc())
            .limit(limit)
            .offset(offset)
        )
    )
    return items, total


def get_vacancy(db: Session, vacancy_id: int) -> Vacancy | None:
    return db.get(Vacancy, vacancy_id)


def update_vacancy(db: Session, vacancy: Vacancy, data: VacancyUpdate) -> Vacancy:
    changes = data.model_dump(exclude_unset=True)
    if "url" in changes and changes["url"] is not None:
        changes["url"] = str(changes["url"])
    if "status" in changes and changes["status"] is not None:
        changes["status"] = VacancyStatus(changes["status"]).value

    # Частичное обновление: проверяем диапазон на итоговых значениях,
    # иначе PATCH только salary_from может дать from > to.
    salary_from = changes.get("salary_from", vacancy.salary_from)
    salary_to = changes.get("salary_to", vacancy.salary_to)
    if (
        salary_from is not None
        and salary_to is not None
        and salary_from > salary_to
    ):
        raise ValueError("salary_from не может быть больше salary_to")

    for field, value in changes.items():
        setattr(vacancy, field, value)

    try:
        db.commit()
    except IntegrityError as exc:
        db.rollback()
        raise DuplicateUrl(str(changes.get("url", vacancy.url))) from exc
    db.refresh(vacancy)
    return vacancy


def delete_vacancy(db: Session, vacancy: Vacancy) -> None:
    db.delete(vacancy)
    db.commit()


def apply_to_vacancy(db: Session, vacancy: Vacancy, letter: str) -> Application:
    if vacancy.applications:
        raise AlreadyApplied(str(vacancy.id))

    application = Application(vacancy_id=vacancy.id, cover_letter=letter)
    vacancy.status = VacancyStatus.APPLIED.value
    db.add(application)
    db.commit()
    db.refresh(application)
    return application


def list_applications(db: Session, vacancy_id: int) -> list[Application]:
    return list(
        db.scalars(
            select(Application)
            .where(Application.vacancy_id == vacancy_id)
            .order_by(Application.sent_at.desc(), Application.id.desc())
        )
    )


def get_stats(db: Session) -> dict:
    by_status = dict(
        db.execute(
            select(Vacancy.status, func.count()).group_by(Vacancy.status)
        ).all()
    )
    # Статусы, которых ещё нет в базе, отдаём нулями: фронту так проще.
    for status in VacancyStatus:
        by_status.setdefault(status.value, 0)

    return {
        "total": db.scalar(select(func.count()).select_from(Vacancy)) or 0,
        "by_status": by_status,
        "applications": db.scalar(select(func.count()).select_from(Application)) or 0,
    }
