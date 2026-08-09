import json
from pathlib import Path
from types import SimpleNamespace
from uuid import uuid4

from app.scripts.seed_upload_data import (
    ExerciseSeed,
    _asset_code,
    _find_existing_exercise,
    _sync_secondary_muscle_links,
    discover_muscles,
    load_exercise_catalog,
)


LEGACY_CHEST_ID = "318783dd-51d9-4e7c-9ee9-7260cdfa8f1c"
LEGACY_TRICEPS_ID = "bf10e3bf-fbdf-470e-bfcf-52b069f58bfa"


def test_discover_muscles_reads_file_names(tmp_path: Path):
    muscles_dir = tmp_path / "muscles"
    muscles_dir.mkdir()
    (muscles_dir / "Chest.png").write_text("", encoding="utf-8")
    (muscles_dir / "Back.png").write_text("", encoding="utf-8")

    muscles = discover_muscles(muscles_dir)

    assert [muscle.name for muscle in muscles] == ["Back", "Chest"]
    assert [muscle.pic for muscle in muscles] == ["Back.png", "Chest.png"]


def test_load_exercise_catalog_maps_legacy_ids_to_names(tmp_path: Path):
    exercises_json = tmp_path / "exercises.json"
    exercises_json.write_text(
        json.dumps(
            [
                {
                    "name": "Bench Press",
                    "pic": "bench.mp4",
                    "tips": "",
                    "equipment": "Barbell",
                    "favourite": False,
                    "muscle_id": LEGACY_CHEST_ID,
                    "secondary_muscles": [LEGACY_TRICEPS_ID],
                }
            ]
        ),
        encoding="utf-8",
    )

    exercises, skipped = load_exercise_catalog(exercises_json)

    assert skipped == []
    assert len(exercises) == 1
    assert exercises[0].primary_muscle == "Chest"
    assert exercises[0].secondary_muscles == ["Triceps"]


def test_load_exercise_catalog_accepts_named_muscles(tmp_path: Path):
    muscles_dir = tmp_path / "muscles"
    muscles_dir.mkdir()
    for muscle_name in ["Glutes", "Hamstrings", "Lower Back"]:
        (muscles_dir / f"{muscle_name}.png").write_text("", encoding="utf-8")

    exercises_json = tmp_path / "exercises.json"
    exercises_json.write_text(
        json.dumps(
            [
                {
                    "name": "Hip Thrust",
                    "pic": "hip-thrust.mp4",
                    "tips": "",
                    "equipment": "Barbell",
                    "favourite": False,
                    "primary_muscle": "Glutes",
                    "secondary_muscles": ["Hamstrings", "Lower Back"],
                }
            ]
        ),
        encoding="utf-8",
    )

    exercises, skipped = load_exercise_catalog(exercises_json, muscles_dir=muscles_dir)

    assert skipped == []
    assert len(exercises) == 1
    assert exercises[0].primary_muscle == "Glutes"
    assert exercises[0].secondary_muscles == ["Hamstrings", "Lower Back"]


def test_load_exercise_catalog_accepts_external_schema(tmp_path: Path):
    exercises_json = tmp_path / "exercises.json"
    exercises_json.write_text(
        json.dumps(
            [
                {
                    "id": "A1B2C3D4",
                    "name": "Lever Chest Press",
                    "equipment": "machine",
                    "primary_muscle_group": "chest",
                    "secondary_muscle_groups": ["triceps"],
                    "thumbnail_url": "https://example.com/05771201-Machine-Chest-Press.jpg",
                    "video_url": "https://example.com/05771201-Machine-Chest-Press.mp4",
                }
            ]
        ),
        encoding="utf-8",
    )

    exercises, skipped = load_exercise_catalog(exercises_json)

    assert skipped == []
    assert exercises[0].catalog_id == "A1B2C3D4"
    assert exercises[0].name == "Machine Chest Press"
    assert exercises[0].equipment == "machine"
    assert exercises[0].primary_muscle == "Chest"
    assert exercises[0].secondary_muscles == ["Triceps"]
    assert exercises[0].pic == "https://example.com/05771201-Machine-Chest-Press.jpg"


def test_load_exercise_catalog_skips_unknown_muscle_ids(tmp_path: Path):
    exercises_json = tmp_path / "exercises.json"
    exercises_json.write_text(
        json.dumps(
            [
                {
                    "name": "Unknown Exercise",
                    "pic": "unknown.mp4",
                    "tips": "",
                    "equipment": "Machine",
                    "favourite": False,
                    "muscle_id": "missing-muscle-id",
                    "secondary_muscles": [],
                }
            ]
        ),
        encoding="utf-8",
    )

    exercises, skipped = load_exercise_catalog(exercises_json)

    assert exercises == []
    assert skipped == ["Unknown Exercise"]


def test_find_existing_exercise_falls_back_to_pic_match():
    existing = SimpleNamespace(name="Decline Bench Press (Dumbbell)", pic="13001201-Lever-Decline-Chest-Press_Chest-FIX.mp4")
    exercise_seed = ExerciseSeed(
        name="Lever Decline Chest Press",
        pic="13001201-Lever-Decline-Chest-Press_Chest-FIX_.mp4",
        tips="",
        equipment="Machine",
        favourite=False,
        primary_muscle="Chest",
        secondary_muscles=["Triceps"],
    )

    matched = _find_existing_exercise(
        exercise_seed,
        exercises_by_catalog_id={},
        exercises_by_name={existing.name: existing},
        exercises_by_pic={},
        exercises_by_asset_code={_asset_code(existing.pic): existing},
    )

    assert matched is existing


def test_catalog_uses_machine_instead_of_lever_names():
    exercises, skipped = load_exercise_catalog()

    assert skipped == []
    assert all("Lever" not in exercise.name for exercise in exercises)
    assert any("Machine" in exercise.name for exercise in exercises)


def test_sync_secondary_muscles_deduplicates_mapped_groups():
    exercise_id = uuid4()
    muscle_id = uuid4()
    session = SimpleNamespace(query=lambda _: SimpleNamespace(filter_by=lambda **_: SimpleNamespace(delete=lambda: None)))
    session.add = lambda link: links.append(link)
    links = []
    muscle = SimpleNamespace(id=muscle_id)

    _sync_secondary_muscle_links(session, SimpleNamespace(id=exercise_id), [muscle, muscle])

    assert len(links) == 1
    assert links[0].muscle_id == muscle_id


