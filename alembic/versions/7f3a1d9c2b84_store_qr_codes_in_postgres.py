"""store qr codes in postgres

Revision ID: 7f3a1d9c2b84
Revises: c3e8f8d142a1
Create Date: 2026-08-05 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "7f3a1d9c2b84"
down_revision: Union[str, Sequence[str], None] = "c3e8f8d142a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("qr_code_data", sa.LargeBinary(), nullable=True))
    op.add_column("users", sa.Column("qr_code_content_type", sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "qr_code_content_type")
    op.drop_column("users", "qr_code_data")