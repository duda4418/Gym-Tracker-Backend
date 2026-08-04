"""normalize workout sessions

Revision ID: c3e8f8d142a1
Revises: 9d7b7b0c4c24
Create Date: 2026-08-04 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision: str = "c3e8f8d142a1"
down_revision: Union[str, Sequence[str], None] = "9d7b7b0c4c24"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


set_type = postgresql.ENUM(
    "standard",
    "warmup",
    "drop",
    "failure",
    name="workout_set_type",
    create_type=False,
)


def upgrade() -> None:
    op.add_column(
        "splits",
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    op.drop_table("workout_session_muscle")
    op.add_column("workout_sessions", sa.Column("started_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("workout_sessions", sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True))
    op.add_column("workout_sessions", sa.Column("notes", sa.String(), nullable=True))
    op.execute("UPDATE workout_sessions SET started_at = COALESCE(date, NOW())")
    op.alter_column("workout_sessions", "started_at", nullable=False)
    op.alter_column("workout_sessions", "split_id", existing_type=sa.UUID(), nullable=True)
    op.drop_constraint("workout_sessions_split_id_fkey", "workout_sessions", type_="foreignkey")
    op.create_foreign_key(
        "workout_sessions_split_id_fkey",
        "workout_sessions",
        "splits",
        ["split_id"],
        ["id"],
        ondelete="SET NULL",
    )

    op.create_table(
        "workout_exercises",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("workout_session_id", sa.UUID(), nullable=False),
        sa.Column("exercise_id", sa.UUID(), nullable=False),
        sa.Column("order_index", sa.Integer(), nullable=False),
        sa.Column("superset_group_id", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["exercise_id"], ["exercises.id"], ondelete="RESTRICT"),
        sa.ForeignKeyConstraint(["workout_session_id"], ["workout_sessions.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workout_session_id", "order_index", name="uq_workout_exercise_order"),
    )
    op.create_index("ix_workout_exercises_id", "workout_exercises", ["id"])
    op.create_index("ix_workout_exercises_exercise_id", "workout_exercises", ["exercise_id"])
    op.create_index("ix_workout_exercises_workout_session_id", "workout_exercises", ["workout_session_id"])

    set_type.create(op.get_bind(), checkfirst=True)
    op.create_table(
        "workout_sets",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("workout_exercise_id", sa.UUID(), nullable=False),
        sa.Column("set_number", sa.Integer(), nullable=False),
        sa.Column("set_type", set_type, nullable=False),
        sa.Column("target_weight", sa.Float(), nullable=True),
        sa.Column("target_reps", sa.Integer(), nullable=True),
        sa.Column("target_rir", sa.Integer(), nullable=True),
        sa.Column("actual_weight", sa.Float(), nullable=True),
        sa.Column("actual_reps", sa.Integer(), nullable=True),
        sa.Column("actual_rir", sa.Integer(), nullable=True),
        sa.Column("completed", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(["workout_exercise_id"], ["workout_exercises.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("workout_exercise_id", "set_number", name="uq_workout_set_number"),
    )
    op.create_index("ix_workout_sets_id", "workout_sets", ["id"])
    op.create_index("ix_workout_sets_workout_exercise_id", "workout_sets", ["workout_exercise_id"])

    op.execute(
        """
        DO $$
        DECLARE
            workout_row RECORD;
            session_uuid UUID;
            exercise_uuid UUID;
            set_row RECORD;
            next_order INTEGER;
        BEGIN
            FOR workout_row IN SELECT * FROM workouts ORDER BY date, id LOOP
                session_uuid := workout_row.session_id;
                IF session_uuid IS NULL THEN
                    session_uuid := gen_random_uuid();
                    INSERT INTO workout_sessions (id, user_id, split_id, started_at, completed_at, notes)
                    VALUES (session_uuid, workout_row.user_id, NULL, workout_row.date, workout_row.date, NULL);
                END IF;

                SELECT COALESCE(MAX(order_index), -1) + 1 INTO next_order
                FROM workout_exercises
                WHERE workout_session_id = session_uuid;

                exercise_uuid := gen_random_uuid();
                INSERT INTO workout_exercises (
                    id, workout_session_id, exercise_id, order_index, superset_group_id
                ) VALUES (
                    exercise_uuid, session_uuid, workout_row.exercise_id, next_order, NULL
                );

                FOR set_row IN
                    SELECT value, ordinality
                    FROM json_array_elements(workout_row.reps) WITH ORDINALITY
                LOOP
                    INSERT INTO workout_sets (
                        id, workout_exercise_id, set_number, set_type,
                        actual_weight, actual_reps, completed, completed_at
                    ) VALUES (
                        gen_random_uuid(), exercise_uuid, set_row.ordinality, 'standard',
                        (workout_row.weights ->> (set_row.ordinality - 1)::INTEGER)::DOUBLE PRECISION,
                        (set_row.value #>> '{}')::INTEGER, TRUE, workout_row.date
                    );
                END LOOP;
            END LOOP;
        END $$;
        """
    )

    op.drop_index("ix_workouts_id", table_name="workouts")
    op.drop_table("workouts")
    op.drop_column("workout_sessions", "date")


def downgrade() -> None:
    op.add_column("workout_sessions", sa.Column("date", sa.DateTime(), nullable=True))
    op.execute("UPDATE workout_sessions SET date = started_at")

    op.create_table(
        "workouts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("exercise_id", sa.UUID(), nullable=False),
        sa.Column("session_id", sa.UUID(), nullable=True),
        sa.Column("reps", sa.JSON(), nullable=False),
        sa.Column("weights", sa.JSON(), nullable=False),
        sa.Column("date", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["exercise_id"], ["exercises.id"]),
        sa.ForeignKeyConstraint(["session_id"], ["workout_sessions.id"]),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_workouts_id", "workouts", ["id"])
    op.execute(
        """
        INSERT INTO workouts (id, user_id, exercise_id, session_id, reps, weights, date)
        SELECT
            gen_random_uuid(),
            workout_sessions.user_id,
            workout_exercises.exercise_id,
            workout_sessions.id,
            COALESCE(json_agg(workout_sets.actual_reps ORDER BY workout_sets.set_number), '[]'::json),
            COALESCE(json_agg(workout_sets.actual_weight ORDER BY workout_sets.set_number), '[]'::json),
            workout_sessions.started_at
        FROM workout_exercises
        JOIN workout_sessions ON workout_sessions.id = workout_exercises.workout_session_id
        LEFT JOIN workout_sets ON workout_sets.workout_exercise_id = workout_exercises.id
        GROUP BY workout_exercises.id, workout_sessions.id
        """
    )

    op.drop_index("ix_workout_sets_workout_exercise_id", table_name="workout_sets")
    op.drop_index("ix_workout_sets_id", table_name="workout_sets")
    op.drop_table("workout_sets")
    op.drop_index("ix_workout_exercises_workout_session_id", table_name="workout_exercises")
    op.drop_index("ix_workout_exercises_exercise_id", table_name="workout_exercises")
    op.drop_index("ix_workout_exercises_id", table_name="workout_exercises")
    op.drop_table("workout_exercises")
    set_type.drop(op.get_bind(), checkfirst=True)

    op.execute("UPDATE workouts SET session_id = NULL WHERE session_id IN (SELECT id FROM workout_sessions WHERE split_id IS NULL)")
    op.execute("DELETE FROM workout_sessions WHERE split_id IS NULL")
    op.drop_constraint("workout_sessions_split_id_fkey", "workout_sessions", type_="foreignkey")
    op.create_foreign_key(
        "workout_sessions_split_id_fkey",
        "workout_sessions",
        "splits",
        ["split_id"],
        ["id"],
    )
    op.alter_column("workout_sessions", "split_id", existing_type=sa.UUID(), nullable=False)
    op.create_table(
        "workout_session_muscle",
        sa.Column("session_id", sa.UUID(), nullable=False),
        sa.Column("muscle_id", sa.UUID(), nullable=False),
        sa.Column("nr_of_exercises", sa.Integer(), nullable=True),
        sa.ForeignKeyConstraint(["muscle_id"], ["muscles.id"]),
        sa.ForeignKeyConstraint(["session_id"], ["workout_sessions.id"]),
        sa.PrimaryKeyConstraint("session_id", "muscle_id"),
    )
    op.drop_column("workout_sessions", "notes")
    op.drop_column("workout_sessions", "completed_at")
    op.drop_column("workout_sessions", "started_at")
    op.drop_column("splits", "created_at")