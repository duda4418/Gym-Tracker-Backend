from fastapi import HTTPException

from app.schemas.muscles import MuscleCreate, MuscleResponse
from app.repositories.muscle_repository import MuscleRepository


class MuscleService:
    def __init__(self, repo: MuscleRepository) -> None:
        self.repo = repo

    async def get_muscles(self) -> list[MuscleResponse]:
        muscles = self.repo.list_all()
        return [
            MuscleResponse(
                id=muscle.id,
                name=muscle.name,
                pic=f"/uploads/muscles/{muscle.pic}" if muscle.pic else None,
            )
            for muscle in muscles
        ]

    async def create_muscle(self, data: MuscleCreate) -> MuscleResponse:
        existing = self.repo.get_by_name(data.name)
        if existing:
            raise HTTPException(status_code=400, detail="Muscle already exists")

        muscle = self.repo.create(data.name, data.pic)
        return MuscleResponse(id=muscle.id, name=muscle.name, pic=muscle.pic)
