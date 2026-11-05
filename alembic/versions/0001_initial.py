"""initial: vacancies + applications

Revision ID: 0001
Revises:
Create Date: 2026-11-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "vacancies",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("company", sa.String(length=255), nullable=False),
        sa.Column("url", sa.String(length=500), nullable=False, unique=True),
        sa.Column("salary_from", sa.Integer(), nullable=True),
        sa.Column("salary_to", sa.Integer(), nullable=True),
        sa.Column("remote", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column(
            "status",
            sa.String(length=20),
            nullable=False,
            server_default="new",
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_vacancies_title", "vacancies", ["title"])
    op.create_index("ix_vacancies_company", "vacancies", ["company"])
    op.create_index("ix_vacancies_status", "vacancies", ["status"])

    op.create_table(
        "applications",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "vacancy_id",
            sa.Integer(),
            sa.ForeignKey("vacancies.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("cover_letter", sa.Text(), nullable=False, server_default=""),
        sa.Column(
            "sent_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_applications_vacancy_id", "applications", ["vacancy_id"])


def downgrade() -> None:
    op.drop_index("ix_applications_vacancy_id", table_name="applications")
    op.drop_table("applications")
    op.drop_index("ix_vacancies_status", table_name="vacancies")
    op.drop_index("ix_vacancies_company", table_name="vacancies")
    op.drop_index("ix_vacancies_title", table_name="vacancies")
    op.drop_table("vacancies")
