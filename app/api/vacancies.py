"""HTTP-слой: только разбор запроса и перевод доменных ошибок в коды ответа."""

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from .. import crud
from ..db import get_db
from ..deps import get_current_user
from ..models import User, Vacancy, VacancyStatus
from ..schemas import (
    ApplicationCreate,
    ApplicationRead,
    VacancyCreate,
    VacancyList,
    VacancyRead,
    VacancyUpdate,
)

# Весь роутер требует авторизации: вакансии принадлежат пользователю
router = APIRouter(prefix="/vacancies", tags=["vacancies"])


def _get_or_404(db: Session, vacancy_id: int, user_id: int) -> Vacancy:
    vacancy = crud.get_vacancy(db, vacancy_id, user_id)
    if vacancy is None:
        # Чужая вакансия неотличима от несуществующей — не подтверждаем,
        # что такой id вообще есть
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Вакансия {vacancy_id} не найдена",
        )
    return vacancy


@router.post("", response_model=VacancyRead, status_code=status.HTTP_201_CREATED)
def create_vacancy(
    payload: VacancyCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Vacancy:
    try:
        return crud.create_vacancy(db, payload, current_user.id)
    except crud.DuplicateUrl as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Вакансия с таким URL уже добавлена",
        ) from exc


@router.get("", response_model=VacancyList)
def list_vacancies(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
    vacancy_status: VacancyStatus | None = Query(default=None, alias="status"),
    remote: bool | None = Query(default=None),
    q: str | None = Query(default=None, description="Поиск по названию и компании"),
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
) -> VacancyList:
    items, total = crud.list_vacancies(
        db,
        current_user.id,
        status=vacancy_status,
        remote=remote,
        q=q,
        limit=limit,
        offset=offset,
    )
    return VacancyList(items=items, total=total, limit=limit, offset=offset)


@router.get("/{vacancy_id}", response_model=VacancyRead)
def get_vacancy(
    vacancy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Vacancy:
    return _get_or_404(db, vacancy_id, current_user.id)


@router.patch("/{vacancy_id}", response_model=VacancyRead)
def update_vacancy(
    vacancy_id: int,
    payload: VacancyUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Vacancy:
    vacancy = _get_or_404(db, vacancy_id, current_user.id)
    try:
        return crud.update_vacancy(db, vacancy, payload)
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=str(exc),
        ) from exc
    except crud.DuplicateUrl as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Вакансия с таким URL уже добавлена",
        ) from exc


@router.delete("/{vacancy_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_vacancy(
    vacancy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> None:
    vacancy = _get_or_404(db, vacancy_id, current_user.id)
    crud.delete_vacancy(db, vacancy)


@router.post(
    "/{vacancy_id}/applications",
    response_model=ApplicationRead,
    status_code=status.HTTP_201_CREATED,
)
def apply_to_vacancy(
    vacancy_id: int,
    payload: ApplicationCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    vacancy = _get_or_404(db, vacancy_id, current_user.id)
    try:
        return crud.apply_to_vacancy(db, vacancy, payload.cover_letter)
    except crud.AlreadyApplied as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="На эту вакансию уже есть отклик",
        ) from exc


@router.get("/{vacancy_id}/applications", response_model=list[ApplicationRead])
def list_applications(
    vacancy_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _get_or_404(db, vacancy_id, current_user.id)
    return crud.list_applications(db, vacancy_id)
