from fastapi import HTTPException
from sqlalchemy import UUID

from app.schemas.workouts import WorkoutResponse
from app.repositories.exercise_repository import ExerciseRepository
from app.repositories.user_repository import UserRepository
from app.repositories.workout_repository import WorkoutRepository


class WorkoutService:
    def __init__(
        self,
        workout_repo: WorkoutRepository,
        user_repo: UserRepository,
        exercise_repo: ExerciseRepository,
    ) -> None:
        self.workout_repo = workout_repo
        self.user_repo = user_repo
        self.exercise_repo = exercise_repo

    @staticmethod
    def _to_response(workout) -> WorkoutResponse:
        return WorkoutResponse(
            id=workout.id,
            exercise_id=workout.exercise_id,
            reps=workout.reps,
            weights=workout.weights,
            date=workout.date,
        )

    async def get_todays_workouts(self, auth_id: str) -> list[WorkoutResponse]:
        user_id = self.user_repo.get_id_by_auth_id(auth_id)
        if not user_id:
            raise HTTPException(status_code=404, detail="User not found")

        workouts = self.workout_repo.list_today()
        return [self._to_response(workout) for workout in workouts]

    async def get_workouts_for_exercise(self, auth_id: str, exercise_id: str) -> list[WorkoutResponse]:
        try:
            str(UUID(exercise_id))
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid exercise_id format")

        user_id = self.user_repo.get_id_by_auth_id(auth_id)
        if not user_id:
            raise HTTPException(status_code=404, detail="User not found")

        workouts = self.workout_repo.list_for_exercise(user_id, exercise_id)
        return [self._to_response(workout) for workout in workouts]

    async def log_workout(self, auth_id: str, data):
        user_id = self.user_repo.get_id_by_auth_id(auth_id)
        if not user_id:
            raise HTTPException(status_code=404, detail="User not found")

        exercise_exists = self.exercise_repo.get_by_id(data.exercise_id)
        if not exercise_exists:
            raise HTTPException(status_code=404, detail="Exercise not found")

        if len(data.reps) != len(data.weights):
            raise HTTPException(status_code=400, detail="Reps and weights lists must be the same length")

        workout = self.workout_repo.create(user_id, data.exercise_id, data.reps, data.weights)
        return {"message": "Workout logged successfully", "workout_id": workout.id}

    async def get_workouts(self) -> list[WorkoutResponse]:
        return [self._to_response(workout) for workout in self.workout_repo.list_all()]

    async def create_workout(self, data) -> WorkoutResponse:
        exercise = self.exercise_repo.get_by_id(data.exercise_id)
        if not exercise:
            raise HTTPException(status_code=400, detail="Exercise not found")

        workout = self.workout_repo.create_without_user(data.exercise_id, data.reps, data.weights)
        return self._to_response(workout)

    async def delete_workout(self, auth_id: str, workout_id: str):
        user_id = self.user_repo.get_id_by_auth_id(auth_id)
        if not user_id:
            raise HTTPException(status_code=404, detail="User not found")

        workout = self.workout_repo.get_for_user(workout_id, user_id)
        if not workout:
            raise HTTPException(status_code=404, detail="Workout not found")

        self.workout_repo.delete(workout)
        return {"message": "Workout deleted successfully"}
