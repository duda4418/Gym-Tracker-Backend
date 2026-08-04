from datetime import datetime, timezone

from fastapi import HTTPException

from app.repositories.exercise_repository import ExerciseRepository
from app.repositories.split_repository import SplitRepository
from app.repositories.user_repository import UserRepository
from app.repositories.workout_repository import WorkoutRepository
from app.schemas.workouts import (
    ExerciseHistoryResponse,
    ExerciseHistorySetResponse,
    LastSetResponse,
    WorkoutExerciseResponse,
    WorkoutSessionResponse,
    WorkoutSessionSummaryResponse,
    WorkoutSetResponse,
)


class WorkoutService:
    def __init__(
        self,
        workout_repo: WorkoutRepository,
        user_repo: UserRepository,
        exercise_repo: ExerciseRepository,
        split_repo: SplitRepository,
    ) -> None:
        self.workout_repo = workout_repo
        self.user_repo = user_repo
        self.exercise_repo = exercise_repo
        self.split_repo = split_repo

    @staticmethod
    def _set_response(workout_set) -> WorkoutSetResponse:
        return WorkoutSetResponse.model_validate(workout_set)

    @classmethod
    def _exercise_response(cls, workout_exercise) -> WorkoutExerciseResponse:
        return WorkoutExerciseResponse(
            id=workout_exercise.id,
            exercise_id=workout_exercise.exercise_id,
            order_index=workout_exercise.order_index,
            superset_group_id=workout_exercise.superset_group_id,
            sets=[cls._set_response(workout_set) for workout_set in workout_exercise.sets],
        )

    @classmethod
    def _session_response(cls, workout_session) -> WorkoutSessionResponse:
        return WorkoutSessionResponse(
            id=workout_session.id,
            split_id=workout_session.split_id,
            started_at=workout_session.started_at,
            completed_at=workout_session.completed_at,
            notes=workout_session.notes,
            exercises=[cls._exercise_response(exercise) for exercise in workout_session.exercises],
        )

    @staticmethod
    def _summary_response(workout_session) -> WorkoutSessionSummaryResponse:
        return WorkoutSessionSummaryResponse.model_validate(workout_session)

    def _require_user(self, user_id):
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    def _require_session(self, user_id, session_id):
        workout_session = self.workout_repo.get_session_for_user(session_id, user_id)
        if not workout_session:
            raise HTTPException(status_code=404, detail="Workout session not found")
        return workout_session

    async def create_session(self, user_id, data) -> WorkoutSessionResponse:
        user = self._require_user(user_id)
        if data.split_id is not None and not self.split_repo.get_for_user(data.split_id, user.id):
            raise HTTPException(status_code=404, detail="Split not found")
        workout_session = self.workout_repo.create_session(user.id, data.split_id)
        return self._session_response(workout_session)

    async def list_sessions(self, user_id, limit: int, before: datetime | None) -> list[WorkoutSessionSummaryResponse]:
        user = self._require_user(user_id)
        sessions = self.workout_repo.list_sessions(user.id, limit, before)
        return [self._summary_response(session) for session in sessions]

    async def get_session(self, user_id, session_id) -> WorkoutSessionResponse:
        user = self._require_user(user_id)
        return self._session_response(self._require_session(user.id, session_id))

    async def update_session(self, user_id, session_id, data) -> WorkoutSessionResponse:
        user = self._require_user(user_id)
        workout_session = self._require_session(user.id, session_id)
        changes = data.model_dump(exclude_unset=True)
        started_at = changes.get("started_at", workout_session.started_at)
        completed_at = changes.get("completed_at", workout_session.completed_at)
        if started_at is None:
            raise HTTPException(status_code=400, detail="started_at cannot be null")
        if completed_at is not None and completed_at < started_at:
            raise HTTPException(status_code=400, detail="completed_at cannot be before started_at")
        updated = self.workout_repo.update_session(workout_session, changes)
        return self._session_response(updated)

    async def delete_session(self, user_id, session_id) -> None:
        user = self._require_user(user_id)
        self.workout_repo.delete_session(self._require_session(user.id, session_id))

    async def add_exercise(self, user_id, session_id, data) -> WorkoutExerciseResponse:
        user = self._require_user(user_id)
        self._require_session(user.id, session_id)
        if not self.exercise_repo.get_by_id(data.exercise_id):
            raise HTTPException(status_code=404, detail="Exercise not found")
        if self.workout_repo.order_index_exists(session_id, data.order_index):
            raise HTTPException(status_code=409, detail="order_index is already used in this session")
        workout_exercise = self.workout_repo.add_exercise(session_id, data.exercise_id, data.order_index)
        return self._exercise_response(workout_exercise)

    async def remove_exercise(self, user_id, session_id, workout_exercise_id) -> None:
        user = self._require_user(user_id)
        workout_exercise = self.workout_repo.get_workout_exercise_in_session(
            workout_exercise_id, session_id, user.id
        )
        if not workout_exercise:
            raise HTTPException(status_code=404, detail="Workout exercise not found")
        self.workout_repo.delete_exercise(workout_exercise)

    async def create_superset(self, user_id, session_id, data):
        user = self._require_user(user_id)
        self._require_session(user.id, session_id)
        workout_exercises = [
            self.workout_repo.get_workout_exercise_in_session(exercise_id, session_id, user.id)
            for exercise_id in data.workout_exercise_ids
        ]
        if any(exercise is None for exercise in workout_exercises):
            raise HTTPException(status_code=404, detail="Workout exercise not found in this session")
        group_id = self.workout_repo.next_superset_group_id(session_id)
        self.workout_repo.set_superset_group(workout_exercises, group_id)
        return {"superset_group_id": group_id}

    async def delete_superset(self, user_id, session_id, group_id: int) -> None:
        user = self._require_user(user_id)
        workout_exercises = self.workout_repo.get_superset_exercises(session_id, user.id, group_id)
        if not workout_exercises:
            raise HTTPException(status_code=404, detail="Superset not found")
        self.workout_repo.set_superset_group(workout_exercises, None)

    async def create_set(self, user_id, workout_exercise_id, data) -> WorkoutSetResponse:
        user = self._require_user(user_id)
        workout_exercise = self.workout_repo.get_workout_exercise_for_user(workout_exercise_id, user.id)
        if not workout_exercise:
            raise HTTPException(status_code=404, detail="Workout exercise not found")
        if self.workout_repo.set_number_exists(workout_exercise_id, data.set_number):
            raise HTTPException(status_code=409, detail="set_number is already used for this exercise")
        values = data.model_dump()
        values["completed_at"] = datetime.now(timezone.utc) if data.completed else None
        return self._set_response(self.workout_repo.create_set(workout_exercise_id, values))

    async def update_set(self, user_id, set_id, data) -> WorkoutSetResponse:
        user = self._require_user(user_id)
        workout_set = self.workout_repo.get_set_for_user(set_id, user.id)
        if not workout_set:
            raise HTTPException(status_code=404, detail="Set not found")
        changes = data.model_dump(exclude_unset=True)
        required_fields = {"set_number", "set_type", "completed"}
        if any(changes.get(field) is None for field in required_fields & changes.keys()):
            raise HTTPException(status_code=400, detail="set_number, set_type, and completed cannot be null")
        set_number = changes.get("set_number")
        if set_number is not None and self.workout_repo.set_number_exists(
            workout_set.workout_exercise_id, set_number, workout_set.id
        ):
            raise HTTPException(status_code=409, detail="set_number is already used for this exercise")
        if "completed" in changes:
            changes["completed_at"] = datetime.now(timezone.utc) if changes["completed"] else None
        return self._set_response(self.workout_repo.update_set(workout_set, changes))

    async def delete_set(self, user_id, set_id) -> None:
        user = self._require_user(user_id)
        workout_set = self.workout_repo.get_set_for_user(set_id, user.id)
        if not workout_set:
            raise HTTPException(status_code=404, detail="Set not found")
        self.workout_repo.delete_set(workout_set)

    async def get_exercise_history(self, user_id, exercise_id, limit: int, before: datetime | None):
        user = self._require_user(user_id)
        if not self.exercise_repo.get_by_id(exercise_id):
            raise HTTPException(status_code=404, detail="Exercise not found")
        workout_exercises = self.workout_repo.list_exercise_history(user.id, exercise_id, limit, before)
        return [
            ExerciseHistoryResponse(
                workout_session_id=item.workout_session_id,
                date=item.session.started_at,
                sets=[
                    ExerciseHistorySetResponse.model_validate(workout_set, from_attributes=True)
                    for workout_set in item.sets
                    if workout_set.completed
                ],
            )
            for item in workout_exercises
        ]

    async def get_last_set(self, user_id, exercise_id) -> LastSetResponse | None:
        user = self._require_user(user_id)
        if not self.exercise_repo.get_by_id(exercise_id):
            raise HTTPException(status_code=404, detail="Exercise not found")
        workout_set = self.workout_repo.get_last_completed_set(user.id, exercise_id)
        if workout_set is None:
            return None
        return LastSetResponse(
            actual_weight=workout_set.actual_weight,
            actual_reps=workout_set.actual_reps,
            actual_rir=workout_set.actual_rir,
            logged_at=workout_set.completed_at,
        )
