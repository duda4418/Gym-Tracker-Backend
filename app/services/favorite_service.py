from fastapi import HTTPException

from app.schemas.exercises import ExerciseResponse
from app.repositories.exercise_repository import ExerciseRepository
from app.repositories.favorite_repository import FavoriteRepository
from app.repositories.muscle_repository import MuscleRepository
from app.repositories.user_repository import UserRepository


class FavoriteService:
    def __init__(
        self,
        favorite_repo: FavoriteRepository,
        exercise_repo: ExerciseRepository,
        muscle_repo: MuscleRepository,
        user_repo: UserRepository,
    ) -> None:
        self.favorite_repo = favorite_repo
        self.exercise_repo = exercise_repo
        self.muscle_repo = muscle_repo
        self.user_repo = user_repo

    def _fetch_exercises_by_muscle(self, muscle_id, user_id):
        muscle = self.muscle_repo.get_by_id(muscle_id)
        if not muscle:
            raise HTTPException(status_code=404, detail="Muscle not found")

        exercises = self.exercise_repo.list_by_primary_muscle(muscle_id)
        favorite_exercise_ids = {fav.exercise_id for fav in self.favorite_repo.list_for_user(user_id)}
        sorted_exercises = sorted(exercises, key=lambda x: x.id not in favorite_exercise_ids)

        return [
            ExerciseResponse(
                id=exercise.id,
                name=exercise.name,
                pic=f"/uploads/exercises/{exercise.pic}" if exercise.pic else None,
                tips=exercise.tips,
                equipment=exercise.equipment,
                favourite=(exercise.id in favorite_exercise_ids),
                primary_muscle=muscle.name,
                secondary_muscles=[
                    self.muscle_repo.get_name_by_id(sm.muscle_id)
                    for sm in exercise.secondary_muscles
                ],
            )
            for exercise in sorted_exercises
        ]

    async def add_favorite(self, auth_id: str, exercise_id):
        user = self.user_repo.get_by_auth_id(auth_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found in database")

        exercise = self.exercise_repo.get_by_id(exercise_id)
        if not exercise:
            raise HTTPException(status_code=404, detail="Exercise not found")

        existing = self.favorite_repo.get_by_user_and_exercise(user.id, exercise_id)
        if existing:
            raise HTTPException(status_code=400, detail="Exercise is already in favorites")

        self.favorite_repo.create(user.id, exercise_id)
        return self._fetch_exercises_by_muscle(exercise.muscle_id, user.id)

    async def remove_favorite(self, auth_id: str, exercise_id):
        user = self.user_repo.get_by_auth_id(auth_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found in database")

        favorite = self.favorite_repo.get_by_user_and_exercise(user.id, exercise_id)
        if not favorite:
            raise HTTPException(status_code=404, detail="Favorite not found")

        self.favorite_repo.delete(favorite)

        exercise = self.exercise_repo.get_by_id(exercise_id)
        return self._fetch_exercises_by_muscle(exercise.muscle_id, user.id)

    async def get_favorites(self, auth_id: str):
        user = self.user_repo.get_by_auth_id(auth_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found in database")

        favorites = self.favorite_repo.list_for_user(user.id)
        return {"favorite_exercises": [fav.exercise_id for fav in favorites]}
