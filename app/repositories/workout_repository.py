from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import String, cast, desc
from sqlalchemy.orm import Session

from app.db.models.workouts import Workout


class WorkoutRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_for_user(self, user_id) -> list[Workout]:
        return self.session.query(Workout).filter(Workout.user_id == user_id).all()

    def list_today(self, user_id) -> list[Workout]:
        now_utc = datetime.now(timezone.utc)
        today_start = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)
        all_workouts = self.session.query(Workout).filter(Workout.user_id == user_id).all()
        return [
            workout
            for workout in all_workouts
            if workout.date.replace(tzinfo=timezone.utc) >= today_start
        ]

    def list_for_exercise(self, user_id, exercise_id: str) -> list[Workout]:
        return (
            self.session.query(Workout)
            .filter(Workout.user_id == user_id)
            .filter(cast(Workout.exercise_id, String) == exercise_id)
            .order_by(desc(Workout.date))
            .all()
        )

    def get_for_user(self, workout_id: str, user_id):
        return self.session.query(Workout).filter_by(id=workout_id, user_id=user_id).first()

    def create(self, user_id, exercise_id, reps, weights):
        workout = Workout(
            id=uuid4(),
            user_id=user_id,
            exercise_id=exercise_id,
            reps=reps,
            weights=weights,
        )
        self.session.add(workout)
        self.session.commit()
        self.session.refresh(workout)
        return workout

    def delete(self, workout):
        self.session.delete(workout)
        self.session.commit()
