from __future__ import annotations

import json
import sys
from dataclasses import dataclass
from pathlib import Path
from uuid import uuid4

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.db.database import session_scope
from app.db.models.exercise_secondary_muscles import ExerciseSecondaryMuscle
from app.db.models.exercises import Exercise
from app.db.models.muscles import Muscle

BASE_DIR = Path(__file__).resolve().parents[1]
UPLOADS_DIR = BASE_DIR / "uploads"
MUSCLES_DIR = UPLOADS_DIR / "muscles"
EXERCISES_JSON = UPLOADS_DIR / "exercises.json"

LEGACY_MUSCLE_ID_TO_NAME = {
    "03632f9c-8581-4a5e-b3da-3451ccb4b2bf": "Back",
    "318783dd-51d9-4e7c-9ee9-7260cdfa8f1c": "Chest",
    "5becb596-87a2-4a0e-91b2-d793dc0949ed": "Abs",
    "6d5c28cc-2706-4d2b-9a01-41da76b14068": "Biceps",
    "9917f5db-9aa4-42b4-948f-fe393fc10f05": "Calves",
    "b43eeed8-f177-46a1-94ca-16d59096fa29": "Quadriceps",
    "bf10e3bf-fbdf-470e-bfcf-52b069f58bfa": "Triceps",
    "e1595911-ce98-478f-a556-5d8961e2c7db": "Shoulders",
}


@dataclass(frozen=True)
class MuscleSeed:
    name: str
    pic: str | None


@dataclass(frozen=True)
class ExerciseSeed:
    name: str
    pic: str | None
    tips: str | None
    equipment: str | None
    favourite: bool
    primary_muscle: str
    secondary_muscles: list[str]


@dataclass(frozen=True)
class SeedSummary:
    muscles_created: int
    muscles_updated: int
    exercises_created: int
    exercises_updated: int
    exercises_skipped: int


def discover_muscles(muscles_dir: Path = MUSCLES_DIR) -> list[MuscleSeed]:
    return [
        MuscleSeed(name=muscle_file.stem, pic=muscle_file.name)
        for muscle_file in sorted(muscles_dir.iterdir())
        if muscle_file.is_file()
    ]


def _map_legacy_muscle_id(legacy_id: str) -> str | None:
    return LEGACY_MUSCLE_ID_TO_NAME.get(legacy_id)


def load_exercise_catalog(exercises_json: Path = EXERCISES_JSON) -> tuple[list[ExerciseSeed], list[str]]:
    raw_items = json.loads(exercises_json.read_text(encoding="utf-8"))
    exercises: list[ExerciseSeed] = []
    skipped: list[str] = []

    for item in raw_items:
        primary_muscle = _map_legacy_muscle_id(item["muscle_id"])
        secondary_muscles = [_map_legacy_muscle_id(muscle_id) for muscle_id in item.get("secondary_muscles", [])]

        if not primary_muscle or any(name is None for name in secondary_muscles):
            skipped.append(item["name"])
            continue

        exercises.append(
            ExerciseSeed(
                name=item["name"],
                pic=item.get("pic"),
                tips=item.get("tips"),
                equipment=item.get("equipment"),
                favourite=bool(item.get("favourite", False)),
                primary_muscle=primary_muscle,
                secondary_muscles=[name for name in secondary_muscles if name is not None],
            )
        )

    return exercises, skipped


def seed_from_uploads() -> SeedSummary:
    muscles_to_seed = discover_muscles()
    exercises_to_seed, skipped_exercises = load_exercise_catalog()

    with session_scope() as session:
        muscles_by_name = {muscle.name: muscle for muscle in session.query(Muscle).all()}
        muscles_created = 0
        muscles_updated = 0

        for muscle_seed in muscles_to_seed:
            muscle = muscles_by_name.get(muscle_seed.name)
            if muscle is None:
                muscle = Muscle(id=uuid4(), name=muscle_seed.name, pic=muscle_seed.pic)
                session.add(muscle)
                session.flush()
                muscles_by_name[muscle_seed.name] = muscle
                muscles_created += 1
            elif muscle.pic != muscle_seed.pic:
                muscle.pic = muscle_seed.pic
                muscles_updated += 1

        exercises_by_name = {exercise.name: exercise for exercise in session.query(Exercise).all()}
        exercises_created = 0
        exercises_updated = 0

        for exercise_seed in exercises_to_seed:
            primary_muscle = muscles_by_name.get(exercise_seed.primary_muscle)
            secondary_muscles = [muscles_by_name.get(name) for name in exercise_seed.secondary_muscles]
            if primary_muscle is None or any(muscle is None for muscle in secondary_muscles):
                skipped_exercises.append(exercise_seed.name)
                continue

            exercise = exercises_by_name.get(exercise_seed.name)
            if exercise is None:
                exercise = Exercise(
                    id=uuid4(),
                    name=exercise_seed.name,
                    pic=exercise_seed.pic,
                    tips=exercise_seed.tips,
                    equipment=exercise_seed.equipment,
                    favourite=exercise_seed.favourite,
                    muscle_id=primary_muscle.id,
                )
                session.add(exercise)
                session.flush()
                exercises_by_name[exercise_seed.name] = exercise
                exercises_created += 1
            else:
                exercise.pic = exercise_seed.pic
                exercise.tips = exercise_seed.tips
                exercise.equipment = exercise_seed.equipment
                exercise.favourite = exercise_seed.favourite
                exercise.muscle_id = primary_muscle.id
                exercises_updated += 1

            session.query(ExerciseSecondaryMuscle).filter_by(exercise_id=exercise.id).delete()
            for secondary_muscle in secondary_muscles:
                session.add(ExerciseSecondaryMuscle(exercise_id=exercise.id, muscle_id=secondary_muscle.id))

    return SeedSummary(
        muscles_created=muscles_created,
        muscles_updated=muscles_updated,
        exercises_created=exercises_created,
        exercises_updated=exercises_updated,
        exercises_skipped=len(skipped_exercises),
    )


def main() -> None:
    summary = seed_from_uploads()
    print("Seed completed successfully.")
    print(f"Muscles created: {summary.muscles_created}")
    print(f"Muscles updated: {summary.muscles_updated}")
    print(f"Exercises created: {summary.exercises_created}")
    print(f"Exercises updated: {summary.exercises_updated}")
    print(f"Exercises skipped: {summary.exercises_skipped}")


if __name__ == "__main__":
    main()

