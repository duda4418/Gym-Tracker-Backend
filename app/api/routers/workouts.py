from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response

from app.api.dependencies import get_current_user, get_workout_service
from app.schemas.users import AuthenticatedUser
from app.schemas.workouts import (
    SupersetCreate,
    SupersetResponse,
    WorkoutExerciseCreate,
    WorkoutExerciseResponse,
    WorkoutSessionCreate,
    WorkoutSessionResponse,
    WorkoutSessionSummaryResponse,
    WorkoutSessionUpdate,
    WorkoutSetCreate,
    WorkoutSetResponse,
    WorkoutSetUpdate,
)
from app.services.workout_service import WorkoutService

workouts_router = APIRouter(tags=["Workouts"], dependencies=[Depends(get_current_user)])

@workouts_router.post("/workouts", response_model=WorkoutSessionResponse, status_code=201)
async def create_workout_session(
    data: WorkoutSessionCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    workout_service: WorkoutService = Depends(get_workout_service),
):
    return await workout_service.create_session(current_user.id, data)


@workouts_router.get("/workouts", response_model=list[WorkoutSessionSummaryResponse])
async def get_workout_sessions(
    limit: int = Query(default=20, ge=1, le=100),
    before: datetime | None = None,
    current_user: AuthenticatedUser = Depends(get_current_user),
    workout_service: WorkoutService = Depends(get_workout_service),
):
    return await workout_service.list_sessions(current_user.id, limit, before)


@workouts_router.get("/workouts/{session_id}", response_model=WorkoutSessionResponse)
async def get_workout_session(
    session_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    workout_service: WorkoutService = Depends(get_workout_service),
):
    return await workout_service.get_session(current_user.id, session_id)


@workouts_router.patch("/workouts/{session_id}", response_model=WorkoutSessionResponse)
async def update_workout_session(
    session_id: UUID,
    data: WorkoutSessionUpdate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    workout_service: WorkoutService = Depends(get_workout_service),
):
    return await workout_service.update_session(current_user.id, session_id, data)


@workouts_router.delete("/workouts/{session_id}", status_code=204)
async def delete_workout_session(
    session_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    workout_service: WorkoutService = Depends(get_workout_service),
):
    await workout_service.delete_session(current_user.id, session_id)
    return Response(status_code=204)


@workouts_router.post("/workouts/{session_id}/exercises", response_model=WorkoutExerciseResponse, status_code=201)
async def add_workout_exercise(
    session_id: UUID,
    data: WorkoutExerciseCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    workout_service: WorkoutService = Depends(get_workout_service),
):
    return await workout_service.add_exercise(current_user.id, session_id, data)


@workouts_router.delete("/workouts/{session_id}/exercises/{workout_exercise_id}", status_code=204)
async def remove_workout_exercise(
    session_id: UUID,
    workout_exercise_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    workout_service: WorkoutService = Depends(get_workout_service),
):
    await workout_service.remove_exercise(current_user.id, session_id, workout_exercise_id)
    return Response(status_code=204)


@workouts_router.post("/workouts/{session_id}/supersets", response_model=SupersetResponse)
async def create_superset(
    session_id: UUID,
    data: SupersetCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    workout_service: WorkoutService = Depends(get_workout_service),
):
    return await workout_service.create_superset(current_user.id, session_id, data)


@workouts_router.delete("/workouts/{session_id}/supersets/{superset_group_id}", status_code=204)
async def delete_superset(
    session_id: UUID,
    superset_group_id: int,
    current_user: AuthenticatedUser = Depends(get_current_user),
    workout_service: WorkoutService = Depends(get_workout_service),
):
    await workout_service.delete_superset(current_user.id, session_id, superset_group_id)
    return Response(status_code=204)


@workouts_router.post("/workout-exercises/{workout_exercise_id}/sets", response_model=WorkoutSetResponse, status_code=201)
async def create_workout_set(
    workout_exercise_id: UUID,
    data: WorkoutSetCreate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    workout_service: WorkoutService = Depends(get_workout_service),
):
    return await workout_service.create_set(current_user.id, workout_exercise_id, data)


@workouts_router.patch("/sets/{set_id}", response_model=WorkoutSetResponse)
async def update_workout_set(
    set_id: UUID,
    data: WorkoutSetUpdate,
    current_user: AuthenticatedUser = Depends(get_current_user),
    workout_service: WorkoutService = Depends(get_workout_service),
):
    return await workout_service.update_set(current_user.id, set_id, data)


@workouts_router.delete("/sets/{set_id}", status_code=204)
async def delete_workout_set(
    set_id: UUID,
    current_user: AuthenticatedUser = Depends(get_current_user),
    workout_service: WorkoutService = Depends(get_workout_service),
):
    await workout_service.delete_set(current_user.id, set_id)
    return Response(status_code=204)

