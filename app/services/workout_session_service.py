from fastapi import HTTPException

from app.schemas.workout_sessions import WorkoutSessionResponse
from app.repositories.muscle_repository import MuscleRepository
from app.repositories.workout_session_repository import WorkoutSessionRepository


class WorkoutSessionService:
    def __init__(
        self,
        session_repo: WorkoutSessionRepository,
        muscle_repo: MuscleRepository,
    ) -> None:
        self.session_repo = session_repo
        self.muscle_repo = muscle_repo

    async def get_workout_sessions(self) -> list[WorkoutSessionResponse]:
        sessions = self.session_repo.list_all()
        return [
            WorkoutSessionResponse(
                id=workout_session.id,
                date=workout_session.date,
                split_id=workout_session.split_id,
                muscles=[
                    {
                        "muscle_id": link.muscle_id,
                        "nr_of_exercises": link.nr_of_exercises,
                    }
                    for link in workout_session.muscles
                ],
            )
            for workout_session in sessions
        ]

    async def create_workout_session(self, data) -> WorkoutSessionResponse:
        workout_session = self.session_repo.create(data.split_id)

        for muscle_data in data.muscles:
            muscle_id = muscle_data["muscle_id"]
            nr_of_exercises = muscle_data["nr_of_exercises"]

            muscle = self.muscle_repo.get_by_id(muscle_id)
            if not muscle:
                raise HTTPException(status_code=400, detail=f"Muscle with ID {muscle_id} not found")

            self.session_repo.add_muscle(workout_session.id, muscle_id, nr_of_exercises)

        self.session_repo.commit()
        self.session_repo.refresh(workout_session)

        return WorkoutSessionResponse(
            id=workout_session.id,
            date=workout_session.date,
            split_id=workout_session.split_id,
            muscles=data.muscles,
        )
