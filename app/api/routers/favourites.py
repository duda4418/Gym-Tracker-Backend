from uuid import UUID

from fastapi import APIRouter, Depends, Response

from app.api.dependencies import get_current_user, get_favorite_service
from app.schemas.exercises import FavoriteCreate
from app.schemas.users import AuthenticatedUser
from app.services.favorite_service import FavoriteService

favorites_router = APIRouter(tags=["Favorites"], dependencies=[Depends(get_current_user)])


@favorites_router.post("/favorites", status_code=204)
async def add_favorite(
    data: FavoriteCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    favorite_service: FavoriteService = Depends(get_favorite_service),
):
    await favorite_service.add_favorite(current_user.id, data.exercise_id)
    return Response(status_code=204)


@favorites_router.delete("/favorites/{exercise_id}", status_code=204)
async def remove_favorite(
    exercise_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    favorite_service: FavoriteService = Depends(get_favorite_service),
):
    await favorite_service.remove_favorite(current_user.id, exercise_id)
    return Response(status_code=204)


@favorites_router.get("/favorites", status_code=200)
async def get_favorites(
    current_user: AuthenticatedUser = Depends(get_current_user),
    favorite_service: FavoriteService = Depends(get_favorite_service),
):
    return await favorite_service.get_favorites(current_user.id)
