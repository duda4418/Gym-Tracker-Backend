from fastapi import HTTPException

from app.repositories.exercise_repository import ExerciseRepository
from app.repositories.favorite_repository import FavoriteRepository
from app.repositories.user_repository import UserRepository


class FavoriteService:
    def __init__(
        self,
        favorite_repo: FavoriteRepository,
        exercise_repo: ExerciseRepository,
        user_repo: UserRepository,
    ) -> None:
        self.favorite_repo = favorite_repo
        self.exercise_repo = exercise_repo
        self.user_repo = user_repo

    async def add_favorite(self, user_id, exercise_id):
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found in database")

        exercise = self.exercise_repo.get_by_id(exercise_id)
        if not exercise:
            raise HTTPException(status_code=404, detail="Exercise not found")

        existing = self.favorite_repo.get_by_user_and_exercise(user.id, exercise_id)
        if existing:
            raise HTTPException(status_code=409, detail="Exercise is already in favorites")

        self.favorite_repo.create(user.id, exercise_id)

    async def remove_favorite(self, user_id, exercise_id):
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found in database")

        favorite = self.favorite_repo.get_by_user_and_exercise(user.id, exercise_id)
        if not favorite:
            raise HTTPException(status_code=404, detail="Favorite not found")

        self.favorite_repo.delete(favorite)

    async def get_favorites(self, user_id):
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found in database")

        favorites = self.favorite_repo.list_for_user(user.id)
        return {"favorite_exercises": [fav.exercise_id for fav in favorites]}
