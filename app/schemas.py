"""Схемы запросов и ответов (Pydantic v2)."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, HttpUrl, model_validator

from .models import VacancyStatus


class VacancyBase(BaseModel):
    title: str = Field(min_length=1, max_length=255)
    company: str = Field(min_length=1, max_length=255)
    url: HttpUrl
    salary_from: int | None = Field(default=None, ge=0)
    salary_to: int | None = Field(default=None, ge=0)
    remote: bool = False

    @model_validator(mode="after")
    def check_salary_range(self) -> "VacancyBase":
        if (
            self.salary_from is not None
            and self.salary_to is not None
            and self.salary_from > self.salary_to
        ):
            raise ValueError("salary_from не может быть больше salary_to")
        return self


class VacancyCreate(VacancyBase):
    status: VacancyStatus = VacancyStatus.NEW


class VacancyUpdate(BaseModel):
    """PATCH: меняем только переданные поля."""

    title: str | None = Field(default=None, min_length=1, max_length=255)
    company: str | None = Field(default=None, min_length=1, max_length=255)
    url: HttpUrl | None = None
    salary_from: int | None = Field(default=None, ge=0)
    salary_to: int | None = Field(default=None, ge=0)
    remote: bool | None = None
    status: VacancyStatus | None = None


class VacancyRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    title: str
    company: str
    url: str
    salary_from: int | None
    salary_to: int | None
    remote: bool
    status: VacancyStatus
    created_at: datetime


class VacancyList(BaseModel):
    items: list[VacancyRead]
    total: int
    limit: int
    offset: int


class ApplicationCreate(BaseModel):
    cover_letter: str = Field(default="", max_length=4000)


class ApplicationRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    vacancy_id: int
    cover_letter: str
    sent_at: datetime


class Stats(BaseModel):
    total: int
    by_status: dict[str, int]
    applications: int
