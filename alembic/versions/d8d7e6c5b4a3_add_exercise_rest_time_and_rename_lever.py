"""add exercise rest time and rename lever exercises

Revision ID: d8d7e6c5b4a3
Revises: af31c6d94e72
Create Date: 2026-08-07 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "d8d7e6c5b4a3"
down_revision: Union[str, Sequence[str], None] = "af31c6d94e72"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "exercises",
        sa.Column("rest_time", sa.Integer(), server_default="90", nullable=False),
    )
    op.execute(
        """
        UPDATE exercises AS exercise
        SET name = replace(exercise.name, 'Lever', 'Machine')
        WHERE exercise.name LIKE '%Lever%'
          AND NOT EXISTS (
              SELECT 1
              FROM exercises AS existing
              WHERE existing.name = replace(exercise.name, 'Lever', 'Machine')
          )
        """
    )


def downgrade() -> None:
    op.execute(
        """
        UPDATE exercises AS exercise
        SET name = replace(exercise.name, 'Machine', 'Lever')
        WHERE exercise.name LIKE '%Machine%'
          AND NOT EXISTS (
              SELECT 1
              FROM exercises AS existing
              WHERE existing.name = replace(exercise.name, 'Machine', 'Lever')
          )
        """
    )
    op.drop_column("exercises", "rest_time")