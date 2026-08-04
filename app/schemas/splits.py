from uuid import UUID
from pydantic import BaseModel, Field


class SplitMuscleCreate(BaseModel):
    muscle_id: UUID
    nr_of_exercises: int = Field(ge=1)


class SplitMuscleResponse(BaseModel):
    muscle_id: UUID
    nr_of_exercises: int


class SplitCreate(BaseModel):
    name: str = Field(min_length=1)
    pic: str | None = None
    muscles: list[SplitMuscleCreate]

    @property
    def muscle_ids(self) -> list[UUID]:
        return [muscle.muscle_id for muscle in self.muscles]


class SplitResponse(BaseModel):
    id: UUID
    name: str
    pic: str | None
    muscles: list[SplitMuscleResponse]
