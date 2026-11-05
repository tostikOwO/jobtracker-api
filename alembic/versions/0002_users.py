"""users + vacancies.user_id

Revision ID: 0002
Revises: 0001
Create Date: 2026-11-05
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0002"
down_revision: str | None = "0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.func.now(),
        ),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # До появления пользователей вакансии никому не принадлежали: колонку
    # user_id нельзя сделать NOT NULL, пока такие строки есть. В dev-базе это
    # тестовые данные, поэтому чистим (applications уходят по ON DELETE CASCADE).
    op.execute("DELETE FROM vacancies")

    op.add_column("vacancies", sa.Column("user_id", sa.Integer(), nullable=False))
    op.create_foreign_key(
        "fk_vacancies_user_id",
        "vacancies",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.create_index("ix_vacancies_user_id", "vacancies", ["user_id"])

    # URL был уникален глобально; теперь — в рамках одного пользователя
    op.drop_constraint("vacancies_url_key", "vacancies", type_="unique")
    op.create_unique_constraint(
        "uq_vacancies_user_url", "vacancies", ["user_id", "url"]
    )


def downgrade() -> None:
    op.drop_constraint("uq_vacancies_user_url", "vacancies", type_="unique")
    op.create_unique_constraint("vacancies_url_key", "vacancies", ["url"])
    op.drop_index("ix_vacancies_user_id", table_name="vacancies")
    op.drop_constraint("fk_vacancies_user_id", "vacancies", type_="foreignkey")
    op.drop_column("vacancies", "user_id")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
