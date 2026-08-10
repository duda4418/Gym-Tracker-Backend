"""set catalog exercise rest times

Revision ID: c8e4a6d1f3b7
Revises: a7d3e5f9b2c6
Create Date: 2026-08-10 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "c8e4a6d1f3b7"
down_revision: Union[str, Sequence[str], None] = "a7d3e5f9b2c6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        r"""
        UPDATE exercises AS exercise
        SET rest_time = CASE
            WHEN muscle.name = 'abdominals' THEN 60
            WHEN exercise.name ~* '(upright row|straight arm pulldown|glute ham raise|nordic hamstrings|back extension|reverse hyperextension)' THEN 90
            WHEN exercise.name ~* '(squat|lunge|deadlift|hip thrust|leg press|step up|good morning|rack pull|box jump|frog jump|burpee|kettlebell swing|sled push|wall ball|clean|snatch|thruster|split jerk|overhead squat)' THEN 180
            WHEN exercise.name ~* '(bench press|chest press|floor press|hex press|squeeze press|push up|pushup|dip|pull up|pullup|chin up|chinup| row|row \(|pulldown|shoulder press|overhead press|military press|push press|handstand push|pike push|muscle up)' THEN 120
            ELSE 90
        END
        FROM muscles AS muscle
        WHERE exercise.muscle_id = muscle.id
        """
    )


def downgrade() -> None:
    op.execute("UPDATE exercises SET rest_time = 90")