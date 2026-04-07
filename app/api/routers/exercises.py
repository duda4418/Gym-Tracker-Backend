from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user, get_exercise_service
from app.schemas.exercises import ExerciseCreate, ExerciseResponse, ExerciseBulkCreate
from app.services.exercise_service import ExerciseService

exercises_router = APIRouter(tags=["Exercises"])


@exercises_router.get("/exercises", response_model=List[ExerciseResponse])
async def get_exercises(exercise_service: ExerciseService = Depends(get_exercise_service)):
    return await exercise_service.list_exercises()


@exercises_router.get("/exercises/by-muscle/{muscle_id}", response_model=List[ExerciseResponse])
async def get_exercises_by_primary_muscle(
    muscle_id: UUID,
    current_user=Depends(get_current_user),
    exercise_service: ExerciseService = Depends(get_exercise_service),
):
    return await exercise_service.list_exercises_by_muscle(muscle_id, current_user.id)


@exercises_router.post("/exercises", response_model=ExerciseResponse, status_code=201)
async def create_exercise(data: ExerciseCreate, exercise_service: ExerciseService = Depends(get_exercise_service)):
    return await exercise_service.create_exercise(data)


@exercises_router.post("/exercises/bulk", response_model=List[ExerciseResponse], status_code=201)
async def create_exercises_bulk(
    data: ExerciseBulkCreate,
    exercise_service: ExerciseService = Depends(get_exercise_service),
):
    return await exercise_service.create_bulk(data)
