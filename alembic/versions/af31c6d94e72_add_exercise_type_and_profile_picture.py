"""add exercise type and profile picture

Revision ID: af31c6d94e72
Revises: 7f3a1d9c2b84
Create Date: 2026-08-06 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "af31c6d94e72"
down_revision: Union[str, Sequence[str], None] = "7f3a1d9c2b84"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "exercises",
        sa.Column("exercise_type", sa.String(), server_default="weighted", nullable=False),
    )
    op.create_check_constraint(
        "ck_exercises_exercise_type",
        "exercises",
        "exercise_type IN ('body weight', 'weighted', 'negative')",
    )
    op.add_column("users", sa.Column("profile_pic_data", sa.LargeBinary(), nullable=True))
    op.add_column("users", sa.Column("profile_pic_content_type", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "profile_pic_content_type")
    op.drop_column("users", "profile_pic_data")
    op.drop_constraint("ck_exercises_exercise_type", "exercises", type_="check")
    op.drop_column("exercises", "exercise_type")