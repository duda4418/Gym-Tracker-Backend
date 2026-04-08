from fastapi import APIRouter, Depends

from app.api.dependencies import get_current_user, get_muscle_service
from app.schemas.muscles import MuscleCreate, MuscleResponse
from app.services.muscle_service import MuscleService

muscles_router = APIRouter(tags=["Muscles"], dependencies=[Depends(get_current_user)])

@muscles_router.get("/muscles", response_model=list[MuscleResponse])
async def get_muscles(muscle_service: MuscleService = Depends(get_muscle_service)):
    return await muscle_service.get_muscles()

@muscles_router.post("/muscles", response_model=MuscleResponse, status_code=201)
async def create_muscle(data: MuscleCreate, muscle_service: MuscleService = Depends(get_muscle_service)):
    return await muscle_service.create_muscle(data)
