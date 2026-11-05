"""ORM-модели: вакансия и отклик на неё."""

from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class VacancyStatus(StrEnum):
    NEW = "new"
    APPLIED = "applied"
    INTERVIEW = "interview"
    REJECTED = "rejected"


class Vacancy(Base):
    __tablename__ = "vacancies"

    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(255), index=True)
    company: Mapped[str] = mapped_column(String(255), index=True)
    # URL вакансии уникален: защита от повторного добавления того же поста
    url: Mapped[str] = mapped_column(String(500), unique=True)
    salary_from: Mapped[int | None] = mapped_column(default=None)
    salary_to: Mapped[int | None] = mapped_column(default=None)
    remote: Mapped[bool] = mapped_column(default=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default=VacancyStatus.NEW.value,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    applications: Mapped[list["Application"]] = relationship(
        back_populates="vacancy",
        cascade="all, delete-orphan",
        order_by="Application.id",
    )


class Application(Base):
    __tablename__ = "applications"

    id: Mapped[int] = mapped_column(primary_key=True)
    vacancy_id: Mapped[int] = mapped_column(
        ForeignKey("vacancies.id", ondelete="CASCADE"),
        index=True,
    )
    cover_letter: Mapped[str] = mapped_column(Text, default="")
    sent_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    vacancy: Mapped[Vacancy] = relationship(back_populates="applications")
