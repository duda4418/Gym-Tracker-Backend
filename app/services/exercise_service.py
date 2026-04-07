from fastapi import HTTPException

from app.schemas.exercises import ExerciseBulkCreate, ExerciseCreate, ExerciseResponse
from app.repositories.exercise_repository import ExerciseRepository
from app.repositories.favorite_repository import FavoriteRepository
from app.repositories.muscle_repository import MuscleRepository
from app.repositories.user_repository import UserRepository


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
            pic=f"/uploads/exercises/{exercise.pic}" if exercise.pic else None,
            tips=exercise.tips,
            equipment=exercise.equipment,
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

    async def list_exercises_by_muscle(self, muscle_id, auth_id: str) -> list[ExerciseResponse]:
        user = self.user_repo.get_by_auth_id(auth_id)
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
