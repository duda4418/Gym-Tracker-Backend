import json
from pathlib import Path

from app.scripts.seed_upload_data import discover_muscles, load_exercise_catalog


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

