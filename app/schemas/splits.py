from uuid import UUID
from typing import List, Optional
from pydantic import BaseModel

class MuscleResponse(BaseModel):
    id: UUID
    name: str
    pic: Optional[str]  # ✅ Include full muscle details

class SplitMuscleCreate(BaseModel):
    muscle_id: UUID  # ✅ This is used in the request body
    nr_of_exercises: int

class SplitMuscleResponse(BaseModel):
    id: UUID  # ✅ Return muscle ID directly in the response
    name: str
    pic: Optional[str]
    nr_of_exercises: int  # ✅ Now at the same level as muscle details
    nr_of_exercises_done_today: int

class SplitMuscleResponse2(BaseModel):
    id: UUID  # ✅ Return muscle ID directly in the response
    name: str
    pic: Optional[str]
    nr_of_exercises: int  # ✅ Now at the same level as muscle details


class SplitCreate(BaseModel):
    name: str
    pic: Optional[str] = ""
    muscles: List[SplitMuscleCreate]  # ✅ Ensure request accepts `muscle_id`

class SplitResponse(BaseModel):
    id: UUID
    name: str
    pic: Optional[str]
    description: str
    muscles: List[SplitMuscleResponse]  # ✅ Ensure response returns full muscle details


class SplitResponse2(BaseModel):
    id: UUID
    name: str
    pic: Optional[str]
    description: str
    muscles: List[SplitMuscleResponse2]  # ✅ Ensure response returns full muscle details
