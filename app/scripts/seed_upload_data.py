from __future__ import annotations

from collections import defaultdict
import json
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import urlparse
from uuid import uuid4

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from app.db.database import session_scope
from app.db.models.exercise_secondary_muscles import ExerciseSecondaryMuscle
from app.db.models.exercises import Exercise
from app.db.models.muscles import Muscle
from app.db.models.user_favourite_exercise import UserFavoriteExercise
from app.db.models.workout_exercises import WorkoutExercise

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

EXTERNAL_MUSCLE_IMAGE_FILENAMES = {
    "abdominals": "abdominals.png",
    "abductors": "abductors.png",
    "adductors": "adductors.png",
    "biceps": "biceps.png",
    "calves": "calves.png",
    "cardio": "cardio.png",
    "chest": "chest.png",
    "forearms": "forearms.png",
    "full_body": "full_body.png",
    "glutes": "glutes.png",
    "hamstrings": "hamstrings.png",
    "lats": "lats.png",
    "lower_back": "lower_back.png",
    "neck": "neck.png",
    "other": "other.png",
    "quadriceps": "quadriceps.png",
    "shoulders": "shoulders.png",
    "traps": "traps.png",
    "triceps": "triceps.png",
    "upper_back": "upper_back.png",
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
    catalog_id: str | None = None
    catalog_type: str | None = None
    thumbnail_url: str | None = None
    video_url: str | None = None


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


def _resolve_muscle_reference(reference: str | None, known_muscles: set[str]) -> str | None:
    if not reference:
        return None

    legacy_match = _map_legacy_muscle_id(reference)
    if legacy_match is not None:
        return legacy_match

    normalized_reference = reference.strip()
    if not normalized_reference:
        return None

    known_by_casefold = {muscle.casefold(): muscle for muscle in known_muscles}
    return known_by_casefold.get(normalized_reference.casefold())


def _resolve_external_muscle_group(reference: str | None) -> str | None:
    if not reference:
        return None
    normalized_reference = reference.strip().casefold()
    return normalized_reference or None


def _external_muscle_image_filename(muscle_name: str) -> str | None:
    return EXTERNAL_MUSCLE_IMAGE_FILENAMES.get(muscle_name)


def _normalize_pic_key(pic: str | None) -> str | None:
    if not pic:
        return None

    path = Path(urlparse(pic).path)
    normalized_stem = path.stem.rstrip("_-")
    return f"{normalized_stem}{path.suffix.lower()}"


def _asset_code(pic: str | None) -> str | None:
    if not pic:
        return None
    match = re.search(r"\b(\d{8})", Path(urlparse(pic).path).name)
    return match.group(1) if match else None


def _catalog_display_name(name: str, is_external_catalog: bool) -> str:
    return name.replace("Lever", "Machine") if is_external_catalog else name


def _exercise_type(catalog_type: str | None) -> str:
    return "weighted" if catalog_type in {"weight_reps", "bodyweight_weighted", "short_distance_weight"} else "body weight"


def _catalog_rest_time(name: str, primary_muscle: str) -> int:
    normalized_name = name.casefold()

    if primary_muscle == "abdominals":
        return 60

    isolation_terms = (
        "upright row",
        "straight arm pulldown",
        "glute ham raise",
        "nordic hamstrings",
        "back extension",
        "reverse hyperextension",
    )
    if any(term in normalized_name for term in isolation_terms):
        return 90

    lower_compound_terms = (
        "squat",
        "lunge",
        "deadlift",
        "hip thrust",
        "leg press",
        "step up",
        "good morning",
        "rack pull",
        "box jump",
        "frog jump",
        "burpee",
        "kettlebell swing",
        "sled push",
        "wall ball",
        "clean",
        "snatch",
        "thruster",
        "split jerk",
        "overhead squat",
    )
    if any(term in normalized_name for term in lower_compound_terms):
        return 180

    upper_compound_terms = (
        "bench press",
        "chest press",
        "floor press",
        "hex press",
        "squeeze press",
        "push up",
        "pushup",
        "dip",
        "pull up",
        "pullup",
        "chin up",
        "chinup",
        " row",
        "row (",
        "pulldown",
        "shoulder press",
        "overhead press",
        "military press",
        "push press",
        "handstand push",
        "pike push",
        "muscle up",
    )
    if any(term in normalized_name for term in upper_compound_terms):
        return 120

    return 90


def load_exercise_catalog(
    exercises_json: Path = EXERCISES_JSON,
    muscles_dir: Path = MUSCLES_DIR,
) -> tuple[list[ExerciseSeed], list[str]]:
    raw_items = json.loads(exercises_json.read_text(encoding="utf-8-sig"))
    known_muscles = {muscle.name for muscle in discover_muscles(muscles_dir)}
    exercises: list[ExerciseSeed] = []
    skipped: list[str] = []

    for item in raw_items:
        is_external_catalog = "primary_muscle_group" in item
        primary_reference = (
            item.get("primary_muscle_group")
            if is_external_catalog
            else item.get("primary_muscle") or item.get("muscle") or item.get("muscle_id")
        )
        secondary_references = item.get("secondary_muscle_groups", []) if is_external_catalog else item.get("secondary_muscles", [])
        if not isinstance(secondary_references, list):
            skipped.append(item["name"])
            continue

        resolve_muscle = _resolve_external_muscle_group if is_external_catalog else lambda reference: _resolve_muscle_reference(reference, known_muscles)
        primary_muscle = resolve_muscle(primary_reference)
        secondary_muscles = [resolve_muscle(reference) for reference in secondary_references]

        if not primary_muscle or any(name is None for name in secondary_muscles):
            skipped.append(item["name"])
            continue

        exercises.append(
            ExerciseSeed(
                name=_catalog_display_name(item["name"], is_external_catalog),
                pic=item.get("thumbnail_url") or item.get("video_url") if is_external_catalog else item.get("pic"),
                thumbnail_url=item.get("thumbnail_url") if is_external_catalog else None,
                video_url=item.get("video_url") if is_external_catalog else None,
                tips=item.get("tips"),
                equipment=item.get("equipment"),
                favourite=bool(item.get("favourite", False)),
                primary_muscle=primary_muscle,
                secondary_muscles=[name for name in secondary_muscles if name is not None],
                catalog_id=item.get("id") if is_external_catalog else None,
                catalog_type=item.get("type") if is_external_catalog else None,
            )
        )

    return exercises, skipped


def _find_existing_exercise(
    exercise_seed: ExerciseSeed,
    exercises_by_catalog_id: dict[str, Exercise],
    exercises_by_name: dict[str, Exercise],
    exercises_by_pic: dict[str, Exercise],
    exercises_by_asset_code: dict[str, Exercise],
) -> Exercise | None:
    if exercise_seed.catalog_id:
        return exercises_by_catalog_id.get(exercise_seed.catalog_id)

    exercise = exercises_by_name.get(exercise_seed.name)
    if exercise is not None:
        return exercise

    normalized_pic = _normalize_pic_key(exercise_seed.pic)
    if normalized_pic:
        exercise = exercises_by_pic.get(normalized_pic)
        if exercise is not None:
            return exercise

    asset_code = _asset_code(exercise_seed.pic)
    if asset_code:
        return exercises_by_asset_code.get(asset_code)

    return None


def _merge_duplicate_exercise(session, keeper: Exercise, duplicate: Exercise) -> None:
    session.query(WorkoutExercise).filter_by(exercise_id=duplicate.id).update(
        {WorkoutExercise.exercise_id: keeper.id},
        synchronize_session=False,
    )

    existing_favorites = {
        favorite.user_id
        for favorite in session.query(UserFavoriteExercise).filter_by(exercise_id=keeper.id).all()
    }
    for favorite in session.query(UserFavoriteExercise).filter_by(exercise_id=duplicate.id).all():
        if favorite.user_id in existing_favorites:
            session.delete(favorite)
            continue

        favorite.exercise_id = keeper.id
        existing_favorites.add(favorite.user_id)

    existing_secondary_muscles = {
        link.muscle_id
        for link in session.query(ExerciseSecondaryMuscle).filter_by(exercise_id=keeper.id).all()
    }
    for link in session.query(ExerciseSecondaryMuscle).filter_by(exercise_id=duplicate.id).all():
        if link.muscle_id in existing_secondary_muscles:
            session.delete(link)
            continue

        link.exercise_id = keeper.id
        existing_secondary_muscles.add(link.muscle_id)

    session.delete(duplicate)


def _deduplicate_existing_exercises(session, exercises_to_seed: list[ExerciseSeed]) -> None:
    preferred_names_by_pic = {
        _normalize_pic_key(exercise_seed.pic): exercise_seed.name
        for exercise_seed in exercises_to_seed
        if _normalize_pic_key(exercise_seed.pic)
    }
    exercises_grouped_by_pic: dict[str, list[Exercise]] = defaultdict(list)

    for exercise in session.query(Exercise).all():
        normalized_pic = _normalize_pic_key(exercise.pic)
        if normalized_pic:
            exercises_grouped_by_pic[normalized_pic].append(exercise)

    for pic, duplicates in exercises_grouped_by_pic.items():
        if len(duplicates) < 2:
            continue

        preferred_name = preferred_names_by_pic.get(pic)
        keeper = next((exercise for exercise in duplicates if exercise.name == preferred_name), duplicates[0])

        for duplicate in duplicates:
            if duplicate.id == keeper.id:
                continue
            _merge_duplicate_exercise(session, keeper, duplicate)


def _sync_muscles(session, muscles_to_seed: list[MuscleSeed]) -> tuple[dict[str, Muscle], int, int]:
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

    return muscles_by_name, muscles_created, muscles_updated


def _ensure_catalog_muscles(muscles_to_seed: list[MuscleSeed], exercises_to_seed: list[ExerciseSeed]) -> list[MuscleSeed]:
    seeds_by_name = {muscle.name: muscle for muscle in muscles_to_seed}
    for muscle_name in {
        muscle_name
        for exercise in exercises_to_seed
        for muscle_name in [exercise.primary_muscle, *exercise.secondary_muscles]
    }:
        seeds_by_name.setdefault(
            muscle_name,
            MuscleSeed(name=muscle_name, pic=_external_muscle_image_filename(muscle_name)),
        )
    return list(seeds_by_name.values())


def _upsert_exercise(
    session,
    exercise_seed: ExerciseSeed,
    primary_muscle: Muscle,
    exercises_by_catalog_id: dict[str, Exercise],
    exercises_by_name: dict[str, Exercise],
    exercises_by_pic: dict[str, Exercise],
    exercises_by_asset_code: dict[str, Exercise],
) -> tuple[Exercise, bool]:
    exercise = _find_existing_exercise(
        exercise_seed,
        exercises_by_catalog_id,
        exercises_by_name,
        exercises_by_pic,
        exercises_by_asset_code,
    )
    if exercise is None:
        exercise = Exercise(
            id=uuid4(),
            catalog_id=exercise_seed.catalog_id,
            catalog_type=exercise_seed.catalog_type,
            name=exercise_seed.name,
            pic=exercise_seed.pic,
            thumbnail_url=exercise_seed.thumbnail_url,
            video_url=exercise_seed.video_url,
            tips=exercise_seed.tips,
            equipment=exercise_seed.equipment,
            exercise_type=_exercise_type(exercise_seed.catalog_type),
            rest_time=_catalog_rest_time(exercise_seed.name, exercise_seed.primary_muscle),
            favourite=exercise_seed.favourite,
            muscle_id=primary_muscle.id,
        )
        session.add(exercise)
        session.flush()
        if exercise.catalog_id:
            exercises_by_catalog_id[exercise.catalog_id] = exercise
        exercises_by_name[exercise_seed.name] = exercise
        normalized_pic = _normalize_pic_key(exercise.pic)
        if normalized_pic:
            exercises_by_pic[normalized_pic] = exercise
        asset_code = _asset_code(exercise.pic)
        if asset_code:
            exercises_by_asset_code[asset_code] = exercise
        return exercise, True

    previous_name = exercise.name
    previous_pic = exercise.pic
    if exercise_seed.catalog_id:
        exercise.catalog_id = exercise_seed.catalog_id
        exercises_by_catalog_id[exercise.catalog_id] = exercise
    exercise.catalog_type = exercise_seed.catalog_type
    exercise.name = exercise_seed.name
    exercise.pic = exercise_seed.pic
    exercise.thumbnail_url = exercise_seed.thumbnail_url
    exercise.video_url = exercise_seed.video_url
    exercise.equipment = exercise_seed.equipment
    exercise.exercise_type = _exercise_type(exercise_seed.catalog_type)
    exercise.rest_time = _catalog_rest_time(exercise_seed.name, exercise_seed.primary_muscle)
    exercise.muscle_id = primary_muscle.id
    if previous_name != exercise.name:
        exercises_by_name.pop(previous_name, None)
    exercises_by_name[exercise.name] = exercise
    previous_pic_key = _normalize_pic_key(previous_pic)
    current_pic_key = _normalize_pic_key(exercise.pic)
    if previous_pic_key and previous_pic_key != current_pic_key:
        exercises_by_pic.pop(previous_pic_key, None)
    if current_pic_key:
        exercises_by_pic[current_pic_key] = exercise
    asset_code = _asset_code(exercise.pic)
    if asset_code:
        exercises_by_asset_code[asset_code] = exercise
    return exercise, False


def _sync_secondary_muscle_links(session, exercise: Exercise, secondary_muscles: list[Muscle | None]) -> None:
    session.query(ExerciseSecondaryMuscle).filter_by(exercise_id=exercise.id).delete()
    linked_muscle_ids = set()
    for secondary_muscle in secondary_muscles:
        if secondary_muscle is not None and secondary_muscle.id not in linked_muscle_ids:
            session.add(ExerciseSecondaryMuscle(exercise_id=exercise.id, muscle_id=secondary_muscle.id))
            linked_muscle_ids.add(secondary_muscle.id)


def _sync_exercises(
    session,
    exercises_to_seed: list[ExerciseSeed],
    muscles_by_name: dict[str, Muscle],
    skipped_exercises: list[str],
) -> tuple[int, int]:
    is_external_catalog = bool(exercises_to_seed) and all(
        exercise.catalog_id is not None for exercise in exercises_to_seed
    )
    if not is_external_catalog:
        _deduplicate_existing_exercises(session, exercises_to_seed)
        session.flush()

    existing_exercises = session.query(Exercise).all()
    exercises_by_catalog_id = {
        exercise.catalog_id: exercise
        for exercise in existing_exercises
        if exercise.catalog_id
    }
    exercises_by_name = {exercise.name: exercise for exercise in existing_exercises}
    exercises_by_pic = {
        normalized_pic: exercise
        for exercise in existing_exercises
        if (normalized_pic := _normalize_pic_key(exercise.pic)) is not None
    }
    asset_codes: dict[str, list[Exercise]] = defaultdict(list)
    for exercise in existing_exercises:
        if (asset_code := _asset_code(exercise.pic)) is not None:
            asset_codes[asset_code].append(exercise)
    exercises_by_asset_code = {
        asset_code: exercises[0]
        for asset_code, exercises in asset_codes.items()
        if len(exercises) == 1
    }
    exercises_created = 0
    exercises_updated = 0

    for exercise_seed in exercises_to_seed:
        primary_muscle = muscles_by_name.get(exercise_seed.primary_muscle)
        secondary_muscles = [muscles_by_name.get(name) for name in exercise_seed.secondary_muscles]
        if primary_muscle is None or any(muscle is None for muscle in secondary_muscles):
            skipped_exercises.append(exercise_seed.name)
            continue

        exercise, created = _upsert_exercise(
            session,
            exercise_seed,
            primary_muscle,
            exercises_by_catalog_id,
            exercises_by_name,
            exercises_by_pic,
            exercises_by_asset_code,
        )
        if created:
            exercises_created += 1
        else:
            exercises_updated += 1

        _sync_secondary_muscle_links(session, exercise, secondary_muscles)

    return exercises_created, exercises_updated


def seed_from_uploads() -> SeedSummary:
    exercises_to_seed, skipped_exercises = load_exercise_catalog()
    is_external_catalog = bool(exercises_to_seed) and all(
        exercise.catalog_id is not None for exercise in exercises_to_seed
    )
    initial_muscles = [] if is_external_catalog else discover_muscles()
    muscles_to_seed = _ensure_catalog_muscles(initial_muscles, exercises_to_seed)

    with session_scope() as session:
        muscles_by_name, muscles_created, muscles_updated = _sync_muscles(session, muscles_to_seed)
        exercises_created, exercises_updated = _sync_exercises(
            session,
            exercises_to_seed,
            muscles_by_name,
            skipped_exercises,
        )

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

