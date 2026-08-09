"""reseed authoritative exercise catalog

Revision ID: a7d3e5f9b2c6
Revises: f6a9d2c4e7b1
Create Date: 2026-08-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "a7d3e5f9b2c6"
down_revision: Union[str, Sequence[str], None] = "f6a9d2c4e7b1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DELETE FROM user_favorite_exercises")
    op.execute("DELETE FROM workout_exercises")
    op.execute("DELETE FROM exercise_secondary_muscles")
    op.execute("DELETE FROM split_muscle")
    op.execute("DELETE FROM exercises")
    op.execute("DELETE FROM muscles")


def downgrade() -> None:
    pass