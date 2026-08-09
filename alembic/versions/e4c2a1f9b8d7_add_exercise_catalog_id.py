"""add exercise catalog id

Revision ID: e4c2a1f9b8d7
Revises: d8d7e6c5b4a3
Create Date: 2026-08-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e4c2a1f9b8d7"
down_revision: Union[str, Sequence[str], None] = "d8d7e6c5b4a3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("exercises", sa.Column("catalog_id", sa.String(), nullable=True))
    op.create_unique_constraint("uq_exercises_catalog_id", "exercises", ["catalog_id"])
    op.create_index("ix_exercises_catalog_id", "exercises", ["catalog_id"])


def downgrade() -> None:
    op.drop_index("ix_exercises_catalog_id", table_name="exercises")
    op.drop_constraint("uq_exercises_catalog_id", "exercises", type_="unique")
    op.drop_column("exercises", "catalog_id")