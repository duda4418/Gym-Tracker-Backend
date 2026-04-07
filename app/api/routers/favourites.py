from typing import List

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user, get_favorite_service
from app.schemas.exercises import ExerciseResponse
from app.services.favorite_service import FavoriteService
from uuid import UUID

favorites_router = APIRouter(tags=["Favorites"])


# ✅ Function to add an exercise to user's favorites
@favorites_router.post("/favorites/add", response_model=List[ExerciseResponse])
async def add_favorite(
    exercise_id: UUID,
    current_user=Depends(get_current_user),
    favorite_service: FavoriteService = Depends(get_favorite_service),
):
    return await favorite_service.add_favorite(current_user.id, exercise_id)


# ✅ Function to remove an exercise from user's favorites
@favorites_router.delete("/favorites/remove", response_model=List[ExerciseResponse])
async def remove_favorite(
    exercise_id: UUID,
    current_user=Depends(get_current_user),
    favorite_service: FavoriteService = Depends(get_favorite_service),
):
    return await favorite_service.remove_favorite(current_user.id, exercise_id)


# ✅ Function to get all favorite exercises for a user
@favorites_router.get("/favorites", status_code=200)
async def get_favorites(
    current_user=Depends(get_current_user),
    favorite_service: FavoriteService = Depends(get_favorite_service),
):
    return await favorite_service.get_favorites(current_user.id)
