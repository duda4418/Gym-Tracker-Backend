from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user, get_workout_session_service
from app.schemas.workout_sessions import WorkoutSessionCreate, WorkoutSessionResponse
from app.schemas.users import AuthenticatedUser
from app.services.workout_session_service import WorkoutSessionService

workout_sessions_router = APIRouter(tags=["Workout Sessions"], dependencies=[Depends(get_current_user)])

@workout_sessions_router.get("/workout_sessions", response_model=list[WorkoutSessionResponse])
async def get_workout_sessions(
    current_user: AuthenticatedUser = Depends(get_current_user),
    workout_session_service: WorkoutSessionService = Depends(get_workout_session_service),
):
    return await workout_session_service.get_workout_sessions(current_user.id)

@workout_sessions_router.post("/workout_sessions", response_model=WorkoutSessionResponse, status_code=201)
async def create_workout_session(
    data: WorkoutSessionCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    workout_session_service: WorkoutSessionService = Depends(get_workout_session_service),
):
    return await workout_session_service.create_workout_session(current_user.id, data)
