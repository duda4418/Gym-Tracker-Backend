from uuid import UUID
from typing import Optional, List
from pydantic import BaseModel
from datetime import datetime

class WorkoutSessionCreate(BaseModel):
    split_id: UUID
    muscles: List[dict]  # ✅ List of { muscle_id, nr_of_exercises }

class WorkoutSessionResponse(BaseModel):
    id: UUID
    date: datetime
    split_id: UUID
    muscles: List[dict]  # ✅ List of { muscle_id, nr_of_exercises }
