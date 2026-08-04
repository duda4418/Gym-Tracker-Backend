from typing import List
from uuid import UUID

from datetime import datetime

from fastapi import APIRouter, Depends, Query, Response

from app.api.dependencies import get_current_user, get_exercise_service, get_workout_service
from app.schemas.exercises import ExerciseCreate, ExerciseResponse, ExerciseBulkCreate
from app.schemas.users import AuthenticatedUser
from app.schemas.workouts import ExerciseHistoryResponse, LastSetResponse
from app.services.exercise_service import ExerciseService
from app.services.workout_service import WorkoutService

exercises_router = APIRouter(tags=["Exercises"], dependencies=[Depends(get_current_user)])


@exercises_router.get("/exercises", response_model=List[ExerciseResponse])
async def get_exercises(
    muscle_id: UUID | None = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
    exercise_service: ExerciseService = Depends(get_exercise_service),
):
    if muscle_id is not None:
        return await exercise_service.list_exercises_by_muscle(muscle_id, current_user.id)
    return await exercise_service.list_exercises()


@exercises_router.get("/exercises/{exercise_id}/history", response_model=list[ExerciseHistoryResponse])
async def get_exercise_history(
    exercise_id: UUID,
    limit: int = Query(default=20, ge=1, le=100),
    before: datetime | None = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
    workout_service: WorkoutService = Depends(get_workout_service),
):
    return await workout_service.get_exercise_history(current_user.id, exercise_id, limit, before)


@exercises_router.get(
    "/exercises/{exercise_id}/last-set",
    response_model=LastSetResponse,
    responses={204: {"description": "No logged set exists"}},
)
async def get_last_exercise_set(
    exercise_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    workout_service: WorkoutService = Depends(get_workout_service),
):
    workout_set = await workout_service.get_last_set(current_user.id, exercise_id)
    if workout_set is None:
        return Response(status_code=204)
    return workout_set


@exercises_router.post("/exercises", response_model=ExerciseResponse, status_code=201)
async def create_exercise(data: ExerciseCreate, exercise_service: ExerciseService = Depends(get_exercise_service)):
    return await exercise_service.create_exercise(data)


@exercises_router.post("/exercises/bulk", response_model=List[ExerciseResponse], status_code=201)
async def create_exercises_bulk(
    data: ExerciseBulkCreate,
    exercise_service: ExerciseService = Depends(get_exercise_service),
):
    return await exercise_service.create_bulk(data)
