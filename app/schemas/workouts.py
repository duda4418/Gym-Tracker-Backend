from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.utils.enums.workouts import SetType


class WorkoutSessionCreate(BaseModel):
    split_id: UUID | None = None


class WorkoutSessionUpdate(BaseModel):
    started_at: datetime | None = None
    completed_at: datetime | None = None
    notes: str | None = None


class WorkoutExerciseCreate(BaseModel):
    exercise_id: UUID
    order_index: int = Field(ge=0)


class SupersetCreate(BaseModel):
    workout_exercise_ids: list[UUID] = Field(min_length=2)

    @model_validator(mode="after")
    def exercise_ids_must_be_unique(self):
        if len(set(self.workout_exercise_ids)) != len(self.workout_exercise_ids):
            raise ValueError("workout_exercise_ids must be unique")
        return self


class SupersetResponse(BaseModel):
    superset_group_id: int


class WorkoutSetCreate(BaseModel):
    set_number: int = Field(ge=1)
    set_type: SetType = SetType.STANDARD
    target_weight: float | None = Field(default=None, ge=0)
    target_reps: int | None = Field(default=None, ge=0)
    target_rir: int | None = Field(default=None, ge=0)
    actual_weight: float | None = Field(default=None, ge=0)
    actual_reps: int | None = Field(default=None, ge=0)
    actual_rir: int | None = Field(default=None, ge=0)
    completed: bool = False


class WorkoutSetUpdate(BaseModel):
    set_number: int | None = Field(default=None, ge=1)
    set_type: SetType | None = None
    target_weight: float | None = Field(default=None, ge=0)
    target_reps: int | None = Field(default=None, ge=0)
    target_rir: int | None = Field(default=None, ge=0)
    actual_weight: float | None = Field(default=None, ge=0)
    actual_reps: int | None = Field(default=None, ge=0)
    actual_rir: int | None = Field(default=None, ge=0)
    completed: bool | None = None


class WorkoutSetResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    set_number: int
    set_type: SetType
    target_weight: float | None
    target_reps: int | None
    target_rir: int | None
    actual_weight: float | None
    actual_reps: int | None
    actual_rir: int | None
    completed: bool
    completed_at: datetime | None


class WorkoutExerciseResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    exercise_id: UUID
    order_index: int
    superset_group_id: int | None
    sets: list[WorkoutSetResponse]


class WorkoutSessionSummaryResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    split_id: UUID | None
    started_at: datetime
    completed_at: datetime | None
    notes: str | None


class WorkoutSessionResponse(WorkoutSessionSummaryResponse):
    exercises: list[WorkoutExerciseResponse]


class ExerciseHistorySetResponse(BaseModel):
    set_number: int
    set_type: SetType
    actual_weight: float | None
    actual_reps: int | None
    actual_rir: int | None


class ExerciseHistoryResponse(BaseModel):
    workout_session_id: UUID
    date: datetime
    sets: list[ExerciseHistorySetResponse]


class LastSetResponse(BaseModel):
    actual_weight: float | None
    actual_reps: int | None
    actual_rir: int | None
    logged_at: datetime
