from typing import List
from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user, get_workout_service
from app.schemas.workouts import WorkoutCreate, WorkoutResponse
from app.services.workout_service import WorkoutService

workouts_router = APIRouter(tags=["Workouts"])

@workouts_router.get("/workouts/today", response_model=List[WorkoutResponse])
async def get_todays_workouts(
    current_user=Depends(get_current_user),
    workout_service: WorkoutService = Depends(get_workout_service),
):
    return await workout_service.get_todays_workouts(current_user.id)


@workouts_router.get("/workouts/by-exercise", response_model=list[WorkoutResponse])
async def get_all_workouts_for_exercise(
    exercise_id: str,
    current_user=Depends(get_current_user),
    workout_service: WorkoutService = Depends(get_workout_service),
):
    return await workout_service.get_workouts_for_exercise(current_user.id, exercise_id)


@workouts_router.post("/log-workout", status_code=201)
async def log_workout(
    data: WorkoutCreate,
    current_user=Depends(get_current_user),
    workout_service: WorkoutService = Depends(get_workout_service),
):
    return await workout_service.log_workout(current_user.id, data)

@workouts_router.get("/workouts", response_model=list[WorkoutResponse])
async def get_workouts(workout_service: WorkoutService = Depends(get_workout_service)):
    return await workout_service.get_workouts()

@workouts_router.post("/workouts", response_model=WorkoutResponse, status_code=201)
async def create_workout(data: WorkoutCreate, workout_service: WorkoutService = Depends(get_workout_service)):
    return await workout_service.create_workout(data)


@workouts_router.delete("/workouts", status_code=204)
async def delete_workout(
    workout_id: str,
    current_user=Depends(get_current_user),
    workout_service: WorkoutService = Depends(get_workout_service),
):
    await workout_service.delete_workout(current_user.id, workout_id)
    return None

