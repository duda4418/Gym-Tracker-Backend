from fastapi import HTTPException

from app.core.config import get_settings
from app.schemas.exercises import ExerciseBulkCreate, ExerciseCreate, ExerciseResponse, ExerciseUpdate
from app.repositories.exercise_repository import ExerciseRepository
from app.repositories.favorite_repository import FavoriteRepository
from app.repositories.muscle_repository import MuscleRepository
from app.repositories.user_repository import UserRepository

settings = get_settings()


class ExerciseService:
    def __init__(
        self,
        exercise_repo: ExerciseRepository,
        muscle_repo: MuscleRepository,
        user_repo: UserRepository,
        favorite_repo: FavoriteRepository,
    ) -> None:
        self.exercise_repo = exercise_repo
        self.muscle_repo = muscle_repo
        self.user_repo = user_repo
        self.favorite_repo = favorite_repo

    def _to_response(self, exercise, primary_muscle_name: str, favourite: bool | None = None) -> ExerciseResponse:
        secondary_names = [
            self.muscle_repo.get_name_by_id(sm.muscle_id)
            for sm in self.exercise_repo.list_secondary_links(exercise.id)
        ]
        return ExerciseResponse(
            id=exercise.id,
            name=exercise.name,
            muscle_id=exercise.muscle_id,
            pic=settings.asset_url(f"/uploads/exercises/{exercise.pic}") if exercise.pic else None,
            tips=exercise.tips,
            equipment=exercise.equipment,
            exercise_type=exercise.exercise_type,
            favourite=exercise.favourite if favourite is None else favourite,
            primary_muscle=primary_muscle_name,
            secondary_muscles=secondary_names,
        )

    async def list_exercises(self) -> list[ExerciseResponse]:
        exercises = self.exercise_repo.list_all()
        return [
            self._to_response(exercise, self.muscle_repo.get_name_by_id(exercise.muscle_id))
            for exercise in exercises
        ]

    async def list_exercises_by_muscle(self, muscle_id, user_id) -> list[ExerciseResponse]:
        user = self.user_repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found in database")

        muscle = self.muscle_repo.get_by_id(muscle_id)
        if not muscle:
            raise HTTPException(status_code=404, detail="Muscle not found")

        exercises = self.exercise_repo.list_by_primary_muscle(muscle_id)
        favorite_exercise_ids = {fav.exercise_id for fav in self.favorite_repo.list_for_user(user.id)}
        sorted_exercises = sorted(exercises, key=lambda item: item.id not in favorite_exercise_ids)

        return [
            self._to_response(exercise, muscle.name, favourite=exercise.id in favorite_exercise_ids)
            for exercise in sorted_exercises
        ]

    async def create_exercise(self, data: ExerciseCreate) -> ExerciseResponse:
        primary_muscle = self.muscle_repo.get_by_id(data.muscle_id)
        if not primary_muscle:
            raise HTTPException(status_code=400, detail="Primary muscle not found")

        if self.exercise_repo.get_by_name(data.name):
            raise HTTPException(status_code=400, detail="Exercise already exists")

        exercise = self.exercise_repo.create(data)

        for muscle_id in data.secondary_muscles:
            secondary_muscle = self.muscle_repo.get_by_id(muscle_id)
            if not secondary_muscle:
                raise HTTPException(status_code=400, detail=f"Secondary muscle with ID {muscle_id} not found")
            self.exercise_repo.add_secondary_muscle(exercise.id, muscle_id)

        self.exercise_repo.session.commit()
        return self._to_response(exercise, primary_muscle.name)

    async def update_exercise(self, exercise_id, data: ExerciseUpdate) -> ExerciseResponse:
        exercise = self.exercise_repo.get_by_id(exercise_id)
        if not exercise:
            raise HTTPException(status_code=404, detail="Exercise not found")

        changes = data.model_dump(exclude_unset=True, exclude={"secondary_muscles"})
        for required_field in ("name", "exercise_type", "favourite", "muscle_id"):
            if required_field in changes and changes[required_field] is None:
                raise HTTPException(status_code=400, detail=f"{required_field} cannot be null")

        if "name" in changes:
            duplicate = self.exercise_repo.get_by_name(changes["name"])
            if duplicate and duplicate.id != exercise.id:
                raise HTTPException(status_code=400, detail="Exercise already exists")

        primary_muscle_id = changes.get("muscle_id", exercise.muscle_id)
        primary_muscle = self.muscle_repo.get_by_id(primary_muscle_id)
        if not primary_muscle:
            raise HTTPException(status_code=400, detail="Primary muscle not found")

        secondary_muscle_ids = data.secondary_muscles
        if "secondary_muscles" in data.model_fields_set:
            if secondary_muscle_ids is None:
                raise HTTPException(status_code=400, detail="secondary_muscles cannot be null")
            for muscle_id in secondary_muscle_ids:
                if not self.muscle_repo.get_by_id(muscle_id):
                    raise HTTPException(status_code=400, detail=f"Secondary muscle with ID {muscle_id} not found")

        self.exercise_repo.update(exercise, changes)
        if secondary_muscle_ids is not None:
            self.exercise_repo.replace_secondary_muscles(exercise.id, secondary_muscle_ids)
        self.exercise_repo.session.commit()
        return self._to_response(exercise, primary_muscle.name)

    async def create_bulk(self, data: ExerciseBulkCreate) -> list[ExerciseResponse]:
        created: list[ExerciseResponse] = []

        for item in data.exercises:
            primary_muscle = self.muscle_repo.get_by_id(item.muscle_id)
            if not primary_muscle:
                raise HTTPException(status_code=400, detail=f"Primary muscle {item.muscle_id} not found")

            if self.exercise_repo.get_by_name(item.name):
                continue

            exercise = self.exercise_repo.create(item)
            for muscle_id in item.secondary_muscles:
                secondary_muscle = self.muscle_repo.get_by_id(muscle_id)
                if not secondary_muscle:
                    raise HTTPException(status_code=400, detail=f"Secondary muscle {muscle_id} not found")
                self.exercise_repo.add_secondary_muscle(exercise.id, muscle_id)

            created.append(self._to_response(exercise, primary_muscle.name))

        self.exercise_repo.session.commit()
        return created
