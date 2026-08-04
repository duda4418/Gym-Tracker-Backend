from uuid import UUID
from typing import List, Optional
from pydantic import BaseModel, Field

class ExerciseCreate(BaseModel):
    name: str
    pic: Optional[str]
    tips: Optional[str]
    equipment: Optional[str]
    favourite: bool = False
    muscle_id: UUID  # ✅ Primary muscle
    secondary_muscles: List[UUID] = Field(default_factory=list)

class ExerciseResponse(BaseModel):
    id: UUID
    name: str
    muscle_id: UUID
    pic: Optional[str]
    tips: Optional[str]
    equipment: Optional[str]
    favourite: bool
    primary_muscle: str  # ✅ Returns primary muscle name
    secondary_muscles: List[str]  # ✅ Returns secondary muscle names

class ExerciseBulkCreate(BaseModel):
    exercises: List[ExerciseCreate]  # ✅ Accepts a list of exercises

class ExerciseSecondaryMuscleResponse(BaseModel):
    muscle_id: UUID
    name: str


class FavoriteCreate(BaseModel):
    exercise_id: UUID

