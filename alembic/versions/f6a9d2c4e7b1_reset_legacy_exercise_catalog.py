"""reset legacy exercise catalog

Revision ID: f6a9d2c4e7b1
Revises: e4c2a1f9b8d7
Create Date: 2026-08-09 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f6a9d2c4e7b1"
down_revision: Union[str, Sequence[str], None] = "e4c2a1f9b8d7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DELETE FROM user_favorite_exercises")
    op.execute("DELETE FROM workout_exercises")
    op.execute("DELETE FROM exercise_secondary_muscles")
    op.execute("DELETE FROM split_muscle")
    op.execute("DELETE FROM exercises")
    op.execute("DELETE FROM muscles")
    op.add_column("exercises", sa.Column("type", sa.String(), nullable=True))
    op.add_column("exercises", sa.Column("thumbnail_url", sa.String(), nullable=True))
    op.add_column("exercises", sa.Column("video_url", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("exercises", "video_url")
    op.drop_column("exercises", "thumbnail_url")
    op.drop_column("exercises", "type")