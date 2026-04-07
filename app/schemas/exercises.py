from uuid import UUID
from typing import List, Optional
from pydantic import BaseModel

class ExerciseCreate(BaseModel):
    name: str
    pic: Optional[str]
    tips: Optional[str]
    equipment: Optional[str]
    favourite: bool = False
    muscle_id: UUID  # ✅ Primary muscle
    secondary_muscles: List[UUID] = []  # ✅ List of secondary muscle IDs

class ExerciseResponse(BaseModel):
    id: UUID
    name: str
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

