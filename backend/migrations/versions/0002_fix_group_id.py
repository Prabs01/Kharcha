"""fix group id autoincrement

Revision ID: 0002_fix_group_id
Revises: 0001_initial_schema
Create Date: 2026-06-07 00:00:00.000000
"""

from typing import Sequence, Union
from alembic import op

revision: str = "0002_fix_group_id"
down_revision: Union[str, Sequence[str], None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE SEQUENCE IF NOT EXISTS group_id_seq")
    op.execute("SELECT setval('group_id_seq', COALESCE((SELECT MAX(id) FROM \"group\"), 1))")
    op.execute("ALTER TABLE \"group\" ALTER COLUMN id SET DEFAULT nextval('group_id_seq')")
    op.execute("ALTER SEQUENCE group_id_seq OWNED BY \"group\".id")


def downgrade() -> None:
    op.execute("ALTER TABLE \"group\" ALTER COLUMN id DROP DEFAULT")
    op.execute("DROP SEQUENCE IF EXISTS group_id_seq")