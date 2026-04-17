import importlib.util
import json
from pathlib import Path

from app.scripts.seed_upload_data import load_exercise_catalog


GENERATOR_PATH = Path(__file__).resolve().parents[1] / "uploads" / "generate exercises.py"


def _load_generator_module():
    spec = importlib.util.spec_from_file_location("generate_exercises", GENERATOR_PATH)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_build_record_infers_supported_muscles_and_secondaries():
    generator = _load_generator_module()

    chest = generator.build_record(Path("00251201-Barbell-Bench-Press_Chest.mp4"))
    biceps = generator.build_record(Path("02941201-Dumbbell-Biceps-Curl_Upper-Arms.mp4"))
    triceps = generator.build_record(Path("00191201-Assisted-Triceps-Dip-(kneeling)_Upper-Arms.mp4"))
    abs_record = generator.build_record(Path("05951201-Lever-Seated-Crunch-(chest-pad).mp4"))
    quads = generator.build_record(Path("05851201-Lever-Leg-Extension_Thighs.mp4"))
    forearms = generator.build_record(Path("00791201-Barbell-Revers-Wrist-Curl-II_Forearms.mp4"))
    lats = generator.build_record(Path("00171201-Assisted-Pull-up_Back.mp4"))
    traps = generator.build_record(Path("00951201-Barbell-Shrug_Back.mp4"))
    hamstrings = generator.build_record(Path("05861201-Lever-Lying-Leg-Curl_Thighs.mp4"))
    glutes = generator.build_record(Path("21461201-Lever-Hip-Thrust_Hips.mp4"))
    lower_back = generator.build_record(Path("05731201-Lever-Back-Extension_Waist.mp4"))
    military_press = generator.build_record(Path("11651201-Barbell-Standing-Military-Press-(without-rack)_Shoulders.mp4"))

    assert chest is not None
    assert chest["name"] == "Barbell Bench Press"
    assert chest["equipment"] == "Barbell"
    assert chest["secondary_muscles"] == ["Triceps", "Shoulders"]

    assert biceps is not None
    assert biceps["primary_muscle"] == "Biceps"

    assert triceps is not None
    assert triceps["primary_muscle"] == "Triceps"
    assert triceps["secondary_muscles"] == ["Chest"]

    assert abs_record is not None
    assert abs_record["primary_muscle"] == "Abs"

    assert quads is not None
    assert quads["primary_muscle"] == "Quadriceps"

    assert forearms is not None
    assert forearms["primary_muscle"] == "Forearms"

    assert lats is not None
    assert lats["primary_muscle"] == "Lats"
    assert lats["secondary_muscles"] == ["Biceps"]

    assert traps is not None
    assert traps["primary_muscle"] == "Traps"

    assert hamstrings is not None
    assert hamstrings["primary_muscle"] == "Hamstrings"

    assert glutes is not None
    assert glutes["primary_muscle"] == "Glutes"
    assert glutes["secondary_muscles"] == ["Hamstrings"]

    assert lower_back is not None
    assert lower_back["primary_muscle"] == "Lower Back"

    assert military_press is not None
    assert military_press["name"] == "Barbell Standing Military Press (without Rack)"


def test_build_exercise_catalog_deduplicates_and_skips_unsupported_assets(tmp_path: Path):
    generator = _load_generator_module()
    exercises_dir = tmp_path / "exercises"
    exercises_dir.mkdir()

    for name in [
        "02921201-Dumbbell-Bent-over-Row_Back.mp4",
        "02931201-Dumbbell-Bent-Over-Row_Back.mp4",
        "02941201-Dumbbell-Biceps-Curl_Upper-Arms.mp4",
        "02941201-Dumbbell-Biceps-Curl_Upper-Arms_small.jpg",
        "05851201-Lever-Leg-Extension_Thighs.mp4",
        "50551101-Dead-Hang-Stretch_Stretching_small.jpg",
    ]:
        (exercises_dir / name).write_text("", encoding="utf-8")

    catalog, skipped = generator.build_exercise_catalog(exercises_dir)

    names = [item["name"] for item in catalog]
    assert names == ["Dumbbell Bent Over Row", "Dumbbell Biceps Curl", "Lever Leg Extension"]
    assert next(item for item in catalog if item["name"] == "Dumbbell Biceps Curl")["pic"].endswith(".mp4")
    assert skipped == ["50551101-Dead-Hang-Stretch_Stretching_small.jpg"]


def test_write_catalog_output_stays_compatible_with_seed_loader(tmp_path: Path):
    generator = _load_generator_module()
    exercises_dir = tmp_path / "exercises"
    exercises_dir.mkdir()
    muscles_dir = tmp_path / "muscles"
    muscles_dir.mkdir()

    for muscle_name in [
        "Abs",
        "Biceps",
        "Chest",
        "Forearms",
        "Glutes",
        "Hamstrings",
        "Lats",
        "Lower Back",
        "Quadriceps",
        "Shoulders",
        "Triceps",
    ]:
        (muscles_dir / f"{muscle_name}.png").write_text("", encoding="utf-8")

    for name in [
        "00251201-Barbell-Bench-Press_Chest.mp4",
        "00171201-Assisted-Pull-up_Back.mp4",
        "02941201-Dumbbell-Biceps-Curl_Upper-Arms.mp4",
        "00191201-Assisted-Triceps-Dip-(kneeling)_Upper-Arms.mp4",
        "05851201-Lever-Leg-Extension_Thighs.mp4",
        "05951201-Lever-Seated-Crunch-(chest-pad).mp4",
        "00791201-Barbell-Revers-Wrist-Curl-II_Forearms.mp4",
        "21461201-Lever-Hip-Thrust_Hips.mp4",
        "05861201-Lever-Lying-Leg-Curl_Thighs.mp4",
        "05731201-Lever-Back-Extension_Waist.mp4",
    ]:
        (exercises_dir / name).write_text("", encoding="utf-8")

    output_path = tmp_path / "exercises.json"
    written_path, catalog, skipped = generator.write_catalog(output_path, exercises_dir)

    assert written_path == output_path
    assert skipped == []

    persisted = json.loads(output_path.read_text(encoding="utf-8"))
    assert persisted == catalog

    exercises, seed_skipped = load_exercise_catalog(output_path, muscles_dir=muscles_dir)
    assert seed_skipped == []
    assert {exercise.primary_muscle for exercise in exercises} == {
        "Abs",
        "Biceps",
        "Chest",
        "Forearms",
        "Glutes",
        "Hamstrings",
        "Lats",
        "Lower Back",
        "Quadriceps",
        "Triceps",
    }

