import asyncio
from types import SimpleNamespace
from uuid import uuid4

from app.schemas.exercises import ExerciseUpdate
from app.services.exercise_service import ExerciseService


class SessionStub:
    def __init__(self):
        self.committed = False

    def commit(self):
        self.committed = True


class ExerciseRepositoryStub:
    def __init__(self, exercise, secondary_muscle_ids):
        self.exercise = exercise
        self.secondary_muscle_ids = secondary_muscle_ids
        self.session = SessionStub()

    def get_by_id(self, _):
        return self.exercise

    def get_by_name(self, _):
        return None

    def update(self, exercise, changes):
        for field, value in changes.items():
            setattr(exercise, field, value)
        return exercise

    def replace_secondary_muscles(self, _, muscle_ids):
        self.secondary_muscle_ids = list(dict.fromkeys(muscle_ids))

    def list_secondary_links(self, _):
        return [SimpleNamespace(muscle_id=muscle_id) for muscle_id in self.secondary_muscle_ids]


class MuscleRepositoryStub:
    def __init__(self, muscles):
        self.muscles = muscles

    def get_by_id(self, muscle_id):
        return self.muscles.get(muscle_id)

    def get_name_by_id(self, muscle_id):
        return self.muscles[muscle_id].name


def test_update_exercise_replaces_supplied_secondary_muscles():
    exercise_id = uuid4()
    primary_muscle_id = uuid4()
    secondary_muscle_id = uuid4()
    exercise = SimpleNamespace(
        id=exercise_id,
        name="Oddly Named Press",
        muscle_id=primary_muscle_id,
        pic=None,
        tips=None,
        equipment="barbell",
        exercise_type="weighted",
        favourite=False,
    )
    muscles = {
        primary_muscle_id: SimpleNamespace(id=primary_muscle_id, name="Chest"),
        secondary_muscle_id: SimpleNamespace(id=secondary_muscle_id, name="Triceps"),
    }
    exercise_repo = ExerciseRepositoryStub(exercise, [])
    service = ExerciseService(
        exercise_repo,
        MuscleRepositoryStub(muscles),
        SimpleNamespace(),
        SimpleNamespace(),
    )

    response = asyncio.run(
        service.update_exercise(
            exercise_id,
            ExerciseUpdate(
                name="Incline Press",
                exercise_type="negative",
                secondary_muscles=[secondary_muscle_id, secondary_muscle_id],
            ),
        )
    )

    assert response.name == "Incline Press"
    assert response.exercise_type == "negative"
    assert response.secondary_muscles == ["Triceps"]
    assert exercise_repo.secondary_muscle_ids == [secondary_muscle_id]
    assert exercise_repo.session.committed is True