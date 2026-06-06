"""initial schema

Revision ID: 0001_initial_schema
Revises:
Create Date: 2026-06-07 00:00:00.000000
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "group",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
    )
    op.create_index(op.f("ix_group_name"), "group", ["name"], unique=False)

    op.create_table(
        "user",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.UniqueConstraint("email"),
    )
    op.create_index(op.f("ix_user_email"), "user", ["email"], unique=False)
    op.create_index(op.f("ix_user_name"), "user", ["name"], unique=False)

    op.create_table(
        "groupmember",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("group.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
    )

    op.create_table(
        "expenses",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("group.id", ondelete="CASCADE"), nullable=False),
        sa.Column("paid_by_user_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("total_amount", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_index(op.f("ix_expenses_title"), "expenses", ["title"], unique=False)

    op.create_table(
        "expensesplits",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("expense_id", sa.Integer(), sa.ForeignKey("expenses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="CASCADE"), nullable=False),
        sa.Column("amount_owed", sa.Float(), nullable=False),
        sa.Column("amount_paid", sa.Float(), nullable=False),
    )

    op.create_table(
        "settlement",
        sa.Column("id", sa.Integer(), primary_key=True, nullable=False),
        sa.Column("group_id", sa.Integer(), sa.ForeignKey("group.id", ondelete="CASCADE"), nullable=False),
        sa.Column("from_user_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("to_user_id", sa.Integer(), sa.ForeignKey("user.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("amount", sa.Float(), nullable=False),
        sa.Column("settled_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("settlement")
    op.drop_table("expensesplits")
    op.drop_index(op.f("ix_expenses_title"), table_name="expenses")
    op.drop_table("expenses")
    op.drop_table("groupmember")
    op.drop_index(op.f("ix_user_name"), table_name="user")
    op.drop_index(op.f("ix_user_email"), table_name="user")
    op.drop_table("user")
    op.drop_index(op.f("ix_group_name"), table_name="group")
    op.drop_table("group")