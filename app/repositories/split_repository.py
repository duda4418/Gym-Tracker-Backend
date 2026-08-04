from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db.models import Exercise, Muscle, SplitMuscle, WorkoutExercise, WorkoutSession
from app.db.models.splits import Split


class SplitRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_for_user(self, user_id):
        return self.session.query(Split).filter(Split.user_id == user_id).all()

    def get_for_user(self, split_id, user_id):
        return self.session.query(Split).filter(Split.id == split_id, Split.user_id == user_id).first()

    def get_today_exercise_counts_by_muscle(self, user_id):
        now_utc = datetime.now(timezone.utc)
        today_start = now_utc.replace(hour=0, minute=0, second=0, microsecond=0)

        rows = (
            self.session.query(Exercise.muscle_id, func.count(WorkoutExercise.id).label("count"))
            .join(WorkoutExercise, WorkoutExercise.exercise_id == Exercise.id)
            .join(WorkoutSession, WorkoutSession.id == WorkoutExercise.workout_session_id)
            .filter(WorkoutSession.user_id == user_id)
            .filter(WorkoutSession.started_at >= today_start)
            .group_by(Exercise.muscle_id)
            .all()
        )
        return {muscle_id: count for muscle_id, count in rows}

    def get_top_muscles_for_split(self, split_id, limit: int = 3):
        return (
            self.session.query(Muscle)
            .join(SplitMuscle, Muscle.id == SplitMuscle.muscle_id)
            .filter(SplitMuscle.split_id == split_id)
            .order_by(SplitMuscle.nr_of_exercises.desc())
            .limit(limit)
            .all()
        )

    def get_split_muscles_with_details(self, split_id):
        return (
            self.session.query(SplitMuscle, Muscle)
            .join(Muscle, SplitMuscle.muscle_id == Muscle.id)
            .filter(SplitMuscle.split_id == split_id)
            .all()
        )

    def create(self, user_id, name: str, pic: str | None):
        split = Split(id=uuid4(), user_id=user_id, name=name, pic=pic)
        self.session.add(split)
        self.session.flush()
        return split

    def add_split_muscle(self, split_id, muscle_id, nr_of_exercises: int):
        split_muscle = SplitMuscle(
            split_id=split_id,
            muscle_id=muscle_id,
            nr_of_exercises=nr_of_exercises,
        )
        self.session.add(split_muscle)

    def replace_split_muscles(self, split_id, muscles) -> None:
        self.session.query(SplitMuscle).filter(SplitMuscle.split_id == split_id).delete()
        for muscle in muscles:
            self.add_split_muscle(split_id, muscle.muscle_id, muscle.nr_of_exercises)

    def update(self, split, name: str, pic: str | None, muscles):
        split.name = name
        split.pic = pic
        self.replace_split_muscles(split.id, muscles)
        self.session.commit()
        self.session.refresh(split)
        return split

    def delete_split(self, split):
        self.session.query(SplitMuscle).filter(SplitMuscle.split_id == split.id).delete()
        self.session.delete(split)

    def commit(self):
        self.session.commit()
