from uuid import UUID
from typing import Optional
from pydantic import BaseModel

class MuscleCreate(BaseModel):
    name: str
    pic: Optional[str] = None

class MuscleResponse(BaseModel):
    id: UUID
    name: str
    pic: Optional[str] = None
