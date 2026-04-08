from uuid import uuid4

from sqlalchemy.orm import Session

from app.db.models.workout_session_muscle import WorkoutSessionMuscle
from app.db.models.workout_sessions import WorkoutSession


class WorkoutSessionRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def list_for_user(self, user_id):
        return self.session.query(WorkoutSession).filter(WorkoutSession.user_id == user_id).all()

    def create(self, split_id, user_id):
        workout_session = WorkoutSession(id=uuid4(), split_id=split_id, user_id=user_id)
        self.session.add(workout_session)
        self.session.flush()
        return workout_session

    def add_muscle(self, session_id, muscle_id, nr_of_exercises):
        self.session.add(
            WorkoutSessionMuscle(
                session_id=session_id,
                muscle_id=muscle_id,
                nr_of_exercises=nr_of_exercises,
            )
        )

    def commit(self):
        self.session.commit()

    def refresh(self, workout_session):
        self.session.refresh(workout_session)
