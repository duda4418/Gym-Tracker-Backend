from datetime import datetime
from uuid import uuid4

from sqlalchemy import desc, func
from sqlalchemy.orm import Session
from sqlalchemy.orm import selectinload

from app.db.models.workout_exercises import WorkoutExercise
from app.db.models.workout_sessions import WorkoutSession
from app.db.models.workout_sets import WorkoutSet


class WorkoutRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_sessions(self, user_id, limit: int, before: datetime | None) -> list[WorkoutSession]:
        query = self.session.query(WorkoutSession).filter(WorkoutSession.user_id == user_id)
        if before is not None:
            query = query.filter(WorkoutSession.started_at < before)
        return query.order_by(desc(WorkoutSession.started_at)).limit(limit).all()

    def get_session_for_user(self, session_id, user_id) -> WorkoutSession | None:
        return (
            self.session.query(WorkoutSession)
            .options(selectinload(WorkoutSession.exercises).selectinload(WorkoutExercise.sets))
            .filter(WorkoutSession.id == session_id, WorkoutSession.user_id == user_id)
            .first()
        )

    def create_session(self, user_id, split_id) -> WorkoutSession:
        workout_session = WorkoutSession(id=uuid4(), user_id=user_id, split_id=split_id)
        self.session.add(workout_session)
        self._commit_and_refresh(workout_session)
        return workout_session

    def update_session(self, workout_session: WorkoutSession, changes: dict) -> WorkoutSession:
        for field, value in changes.items():
            setattr(workout_session, field, value)
        self._commit_and_refresh(workout_session)
        return workout_session

    def delete_session(self, workout_session: WorkoutSession) -> None:
        self.session.delete(workout_session)
        self.session.commit()

    def get_workout_exercise_for_user(self, workout_exercise_id, user_id) -> WorkoutExercise | None:
        return (
            self.session.query(WorkoutExercise)
            .join(WorkoutSession)
            .options(selectinload(WorkoutExercise.sets))
            .filter(WorkoutExercise.id == workout_exercise_id, WorkoutSession.user_id == user_id)
            .first()
        )

    def get_workout_exercise_in_session(self, workout_exercise_id, session_id, user_id) -> WorkoutExercise | None:
        return (
            self.session.query(WorkoutExercise)
            .join(WorkoutSession)
            .options(selectinload(WorkoutExercise.sets))
            .filter(
                WorkoutExercise.id == workout_exercise_id,
                WorkoutExercise.workout_session_id == session_id,
                WorkoutSession.user_id == user_id,
            )
            .first()
        )

    def order_index_exists(self, session_id, order_index: int) -> bool:
        return (
            self.session.query(WorkoutExercise.id)
            .filter(
                WorkoutExercise.workout_session_id == session_id,
                WorkoutExercise.order_index == order_index,
            )
            .first()
            is not None
        )

    def add_exercise(self, session_id, exercise_id, order_index: int) -> WorkoutExercise:
        workout_exercise = WorkoutExercise(
            id=uuid4(),
            workout_session_id=session_id,
            exercise_id=exercise_id,
            order_index=order_index,
        )
        self.session.add(workout_exercise)
        self._commit_and_refresh(workout_exercise)
        return workout_exercise

    def delete_exercise(self, workout_exercise: WorkoutExercise) -> None:
        self.session.delete(workout_exercise)
        self.session.commit()

    def next_superset_group_id(self, session_id) -> int:
        current_max = (
            self.session.query(func.max(WorkoutExercise.superset_group_id))
            .filter(WorkoutExercise.workout_session_id == session_id)
            .scalar()
        )
        return (current_max or 0) + 1

    def set_superset_group(self, workout_exercises: list[WorkoutExercise], group_id: int | None) -> None:
        for workout_exercise in workout_exercises:
            workout_exercise.superset_group_id = group_id
        self.session.commit()

    def get_superset_exercises(self, session_id, user_id, group_id: int) -> list[WorkoutExercise]:
        return (
            self.session.query(WorkoutExercise)
            .join(WorkoutSession)
            .filter(
                WorkoutExercise.workout_session_id == session_id,
                WorkoutExercise.superset_group_id == group_id,
                WorkoutSession.user_id == user_id,
            )
            .all()
        )

    def set_number_exists(self, workout_exercise_id, set_number: int, exclude_set_id=None) -> bool:
        query = self.session.query(WorkoutSet.id).filter(
            WorkoutSet.workout_exercise_id == workout_exercise_id,
            WorkoutSet.set_number == set_number,
        )
        if exclude_set_id is not None:
            query = query.filter(WorkoutSet.id != exclude_set_id)
        return query.first() is not None

    def create_set(self, workout_exercise_id, values: dict) -> WorkoutSet:
        workout_set = WorkoutSet(id=uuid4(), workout_exercise_id=workout_exercise_id, **values)
        self.session.add(workout_set)
        self._commit_and_refresh(workout_set)
        return workout_set

    def get_set_for_user(self, set_id, user_id) -> WorkoutSet | None:
        return (
            self.session.query(WorkoutSet)
            .join(WorkoutExercise)
            .join(WorkoutSession)
            .filter(WorkoutSet.id == set_id, WorkoutSession.user_id == user_id)
            .first()
        )

    def update_set(self, workout_set: WorkoutSet, changes: dict) -> WorkoutSet:
        for field, value in changes.items():
            setattr(workout_set, field, value)
        self._commit_and_refresh(workout_set)
        return workout_set

    def delete_set(self, workout_set: WorkoutSet) -> None:
        self.session.delete(workout_set)
        self.session.commit()

    def list_exercise_history(self, user_id, exercise_id, limit: int, before: datetime | None):
        query = (
            self.session.query(WorkoutExercise)
            .join(WorkoutSession)
            .options(selectinload(WorkoutExercise.sets))
            .filter(
                WorkoutSession.user_id == user_id,
                WorkoutExercise.exercise_id == exercise_id,
                WorkoutExercise.sets.any(WorkoutSet.completed.is_(True)),
            )
        )
        if before is not None:
            query = query.filter(WorkoutSession.started_at < before)
        return query.order_by(desc(WorkoutSession.started_at)).limit(limit).all()

    def get_last_completed_set(self, user_id, exercise_id) -> WorkoutSet | None:
        return (
            self.session.query(WorkoutSet)
            .join(WorkoutExercise)
            .join(WorkoutSession)
            .filter(
                WorkoutSession.user_id == user_id,
                WorkoutExercise.exercise_id == exercise_id,
                WorkoutSet.completed.is_(True),
                WorkoutSet.completed_at.is_not(None),
            )
            .order_by(desc(WorkoutSet.completed_at))
            .first()
        )

    def _commit_and_refresh(self, instance) -> None:
        self.session.commit()
        self.session.refresh(instance)
