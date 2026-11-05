"""ORM-модели: вакансия и отклик на неё."""

from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from .db import Base


class VacancyStatus(StrEnum):
    NEW = "new"
    APPLIED = "applied"
    INTERVIEW = "interview"
    REJECTED = "rejected"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )

    vacancies: Mapped[list["Vacancy"]] = relationship(
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Vacancy(Base):
    __tablename__ = "vacancies"
    # Один и тот же URL может быть у разных пользователей, но не дважды у одного
    __table_args__ = (
        UniqueConstraint("user_id", "url", name="uq_vacancies_user_url"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    # Владелец вакансии: без него запись не видна никому
    user_id: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), index=True)
    company: Mapped[str] = mapped_column(String(255), index=True)
    # URL вакансии уникален: защита от повторного добавления того же поста
    url: Mapped[str] = mapped_column(String(500))
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

    user: Mapped["User"] = relationship(back_populates="vacancies")


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
