from __future__ import annotations

import json
import re
from collections import Counter
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent
EXERCISES_DIR = BASE_DIR / "exercises"
MUSCLES_DIR = BASE_DIR / "muscles"
OUTPUT_JSON = BASE_DIR / "exercises.json"

CANONICAL_MUSCLES = {
    muscle_path.stem
    for muscle_path in MUSCLES_DIR.iterdir()
    if muscle_path.is_file()
}

BODY_REGION_ALIASES = {
    "back": "Back",
    "calves": "Calves",
    "chest": "Chest",
    "forearm": "Forearms",
    "forearms": "Forearms",
    "hips": "Hips",
    "plyometrics": "Plyometrics",
    "shoulder": "Shoulders",
    "shoulders": "Shoulders",
    "stretching": "Stretching",
    "thighs": "Thighs",
    "upper arms": "Upper Arms",
    "waist": "Waist",
}

NAME_FIXUPS = {
    "Revers": "Reverse",
    "revers": "Reverse",
    "Flys": "Flys",
}

LOWERCASE_WORDS = {"a", "an", "and", "for", "in", "of", "on", "the", "to", "up", "with", "without"}
ACRONYM_WORDS = {"EZ", "II", "III", "IV", "JM", "T", "V"}
PUSH_UP_TERM = "push up"
CHIN_UP_TERM = "chin up"
PRESS_TERMS = ("press", PUSH_UP_TERM, "dip")
ROW_TERMS = ("row", "pull", CHIN_UP_TERM, "shrug", "pullover")
CORE_TERMS = ("crunch", "leg raise", "russian twist", "l sit", "plank")


def strip_numeric_prefix(stem: str) -> str:
    return re.sub(r"^\d+-", "", stem)


def clean_stem(stem: str) -> str:
    cleaned = re.sub(r"_small$", "", stem, flags=re.IGNORECASE)
    return cleaned.rstrip("_-")


def normalize_body_region(region: str | None) -> str | None:
    if not region:
        return None

    normalized = region.strip("_-")
    normalized = re.sub(r"[-_]?fix$", "", normalized, flags=re.IGNORECASE)
    normalized = normalized.strip("_-")
    normalized = normalized.replace("-", " ").replace("_", " ").strip().lower()
    return BODY_REGION_ALIASES.get(normalized)


def split_name_and_region(file_name: str) -> tuple[str, str | None]:
    stem = clean_stem(Path(file_name).stem)
    stem = strip_numeric_prefix(stem)
    parts = [part for part in stem.split("_") if part]
    if len(parts) >= 2:
        region = normalize_body_region(parts[-1])
        if region is not None:
            return "_".join(parts[:-1]), region
    return stem, None


def normalize_word(word: str, is_first: bool) -> str:
    if not word:
        return word
    if word.upper() in ACRONYM_WORDS:
        return word.upper()

    lowered = word.lower()
    if not is_first and lowered in LOWERCASE_WORDS:
        return lowered
    return NAME_FIXUPS.get(word, NAME_FIXUPS.get(lowered, word.capitalize()))


def humanize_slug(slug: str) -> str:
    normalized = slug.replace("_", " ")
    normalized = normalized.replace("(", " (").replace(")", ") ")
    normalized = normalized.replace("-", " ")
    normalized = re.sub(r"\s+", " ", normalized).strip()

    words = normalized.split(" ")
    titled = [normalize_word(word, index == 0) for index, word in enumerate(words)]
    title = " ".join(titled).replace("( ", "(").replace(" )", ")")
    title = re.sub(r"\bm\b", "", title, flags=re.IGNORECASE)
    title = re.sub(r"\s+", " ", title).strip()
    title = title.replace("Captains", "Captain's")
    return title.strip()


def infer_equipment(slug: str) -> str:
    lowered = slug.lower()
    if lowered.startswith(("barbell-", "ez-barbell-", "trap-bar-")):
        return "Barbell"
    if lowered.startswith("dumbbell-"):
        return "Dumbbell"
    if lowered.startswith(("cable-", "lever-", "smith-", "assisted-", "sled-")):
        return "Machine"
    if lowered.startswith("band-"):
        return "Band"
    return "None"


def _infer_upper_arms_primary(lowered_name: str) -> str | None:
    if any(token in lowered_name for token in ("tricep", "pushdown", "extension", "kickback", "skull", "jm bench", "close grip")):
        return "Triceps"
    if any(token in lowered_name for token in ("curl", CHIN_UP_TERM)):
        return "Biceps"
    if "dip" in lowered_name:
        return "Triceps"
    return None


def _infer_forearms_primary(lowered_name: str) -> str | None:
    if any(token in lowered_name for token in ("wrist curl", "reverse curl", "hammer curl")):
        return "Forearms"
    return None


def _infer_waist_primary(lowered_name: str) -> str:
    if any(token in lowered_name for token in ("deadlift", "back extension", "hyperextension")):
        return "Lower Back"
    return "Abs"


def _infer_thighs_primary(lowered_name: str) -> str | None:
    if any(token in lowered_name for token in ("leg curl", "glute ham")):
        return "Hamstrings"
    return "Quadriceps"


def _infer_hips_primary(lowered_name: str) -> str | None:
    if any(token in lowered_name for token in CORE_TERMS):
        return "Abs"
    if any(token in lowered_name for token in ("deadlift", "hyperextension")):
        return "Lower Back"
    if any(token in lowered_name for token in ("hip thrust", "rear kick")):
        return "Glutes"
    return "Quadriceps"


def _infer_back_primary(lowered_name: str) -> str:
    if "shrug" in lowered_name:
        return "Traps"
    if any(token in lowered_name for token in ("pull up", "chin up", "pulldown", "pullover")):
        return "Lats"
    return "Back"


def _infer_primary_from_region(lowered_name: str, region: str | None) -> str | None:
    direct_map = {"Chest": "Chest", "Shoulders": "Shoulders", "Calves": "Calves"}
    if region in direct_map:
        return direct_map[region]
    if region == "Back":
        return _infer_back_primary(lowered_name)
    if region == "Upper Arms":
        return _infer_upper_arms_primary(lowered_name)
    if region == "Forearms":
        return _infer_forearms_primary(lowered_name)
    if region == "Waist":
        return _infer_waist_primary(lowered_name)
    if region == "Thighs":
        return _infer_thighs_primary(lowered_name)
    if region == "Hips":
        return _infer_hips_primary(lowered_name)
    return None


def _infer_primary_from_name(lowered_name: str) -> str | None:
    if PUSH_UP_TERM in lowered_name:
        return "Chest"
    if "shrug" in lowered_name:
        return "Traps"
    if any(token in lowered_name for token in (CHIN_UP_TERM, "pull up", "pulldown", "pullover")):
        return "Lats"
    if "row" in lowered_name:
        return "Back"
    if any(token in lowered_name for token in CORE_TERMS):
        return "Abs"
    if any(token in lowered_name for token in ("wrist curl", "hammer curl", "reverse curl")):
        return "Forearms"
    if any(token in lowered_name for token in ("hip thrust", "rear kick")):
        return "Glutes"
    return None


def infer_primary_muscle(name: str, region: str | None) -> str | None:
    lowered = name.lower()
    if region in {"Stretching", "Plyometrics"}:
        return None

    return _infer_primary_from_region(lowered, region) or _infer_primary_from_name(lowered)


def _infer_chest_secondaries(lowered_name: str) -> list[str]:
    secondary: list[str] = []
    if any(term in lowered_name for term in PRESS_TERMS):
        secondary.append("Triceps")
    if any(term in lowered_name for term in ("bench press", "chest press", "push up")):
        secondary.append("Shoulders")
    if "pullover" in lowered_name:
        secondary.append("Lats")
    return secondary


def _infer_back_secondaries(lowered_name: str) -> list[str]:
    secondary: list[str] = []
    if any(term in lowered_name for term in ROW_TERMS):
        secondary.append("Biceps")
    return secondary


def _infer_lats_secondaries(_: str) -> list[str]:
    return ["Biceps"]


def _infer_shoulder_secondaries(lowered_name: str) -> list[str]:
    secondary: list[str] = []
    if any(term in lowered_name for term in ("press", "upright row")):
        secondary.append("Triceps")
    if "upright row" in lowered_name:
        secondary.append("Traps")
    return secondary


def _infer_forearm_secondaries(lowered_name: str) -> list[str]:
    secondary: list[str] = []
    if any(term in lowered_name for term in ("reverse curl", "hammer curl")):
        secondary.append("Biceps")
    return secondary


def _infer_hamstring_secondaries(lowered_name: str) -> list[str]:
    secondary: list[str] = []
    if "glute ham" in lowered_name:
        secondary.append("Glutes")
    return secondary


def _infer_glute_secondaries(_: str) -> list[str]:
    return ["Hamstrings"]


def _infer_lower_back_secondaries(lowered_name: str) -> list[str]:
    secondary: list[str] = []
    if any(term in lowered_name for term in ("deadlift", "hyperextension")):
        secondary.extend(["Glutes", "Hamstrings"])
    return secondary


def _infer_triceps_secondaries(lowered_name: str) -> list[str]:
    secondary: list[str] = []
    if any(term in lowered_name for term in ("dip", "close grip bench press", "jm bench")):
        secondary.append("Chest")
    if "overhead" in lowered_name:
        secondary.append("Shoulders")
    return secondary


def infer_secondary_muscles(name: str, primary_muscle: str) -> list[str]:
    lowered = name.lower()
    secondary_by_primary = {
        "Chest": _infer_chest_secondaries,
        "Back": _infer_back_secondaries,
        "Lats": _infer_lats_secondaries,
        "Shoulders": _infer_shoulder_secondaries,
        "Forearms": _infer_forearm_secondaries,
        "Hamstrings": _infer_hamstring_secondaries,
        "Glutes": _infer_glute_secondaries,
        "Lower Back": _infer_lower_back_secondaries,
        "Triceps": _infer_triceps_secondaries,
    }
    secondary = secondary_by_primary.get(primary_muscle, lambda _: [])(lowered)
    return [muscle for muscle in secondary if muscle != primary_muscle]


def score_asset(path: Path) -> tuple[int, int, str]:
    extension_score = 2 if path.suffix.lower() == ".mp4" else 1
    size_score = 0 if "small" in path.stem.lower() else 1
    return extension_score, size_score, path.name.lower()


def build_record(path: Path) -> dict[str, object] | None:
    slug, region = split_name_and_region(path.name)
    name = humanize_slug(slug)
    primary_muscle = infer_primary_muscle(name, region)
    if primary_muscle is None:
        return None

    secondary_muscles = infer_secondary_muscles(name, primary_muscle)
    if primary_muscle not in CANONICAL_MUSCLES or any(muscle not in CANONICAL_MUSCLES for muscle in secondary_muscles):
        return None

    return {
        "name": name,
        "pic": path.name,
        "tips": "",
        "equipment": infer_equipment(slug),
        "favourite": False,
        "primary_muscle": primary_muscle,
        "secondary_muscles": secondary_muscles,
    }


def build_exercise_catalog(exercises_dir: Path = EXERCISES_DIR) -> tuple[list[dict[str, object]], list[str]]:
    generated = {}
    skipped: list[str] = []

    for path in sorted(exercises_dir.iterdir()):
        if not path.is_file():
            continue

        record = build_record(path)
        if record is None:
            skipped.append(path.name)
            continue

        key = str(record["name"])
        candidate = (score_asset(path), record)
        current = generated.get(key)
        if current is None or candidate[0] > current[0]:
            generated[key] = candidate

    catalog = [item[1] for item in sorted(generated.values(), key=lambda value: str(value[1]["name"]))]
    return catalog, skipped


def write_catalog(output_path: Path = OUTPUT_JSON, exercises_dir: Path = EXERCISES_DIR) -> tuple[Path, list[dict[str, object]], list[str]]:
    catalog, skipped = build_exercise_catalog(exercises_dir)
    output_path.write_text(json.dumps(catalog, indent=2), encoding="utf-8")
    return output_path, catalog, skipped


def main() -> None:
    output_path, catalog, skipped = write_catalog()
    primary_counts = Counter(str(item["primary_muscle"]) for item in catalog)

    print(f"Wrote {len(catalog)} exercises to {output_path}")
    print(f"Primary muscle distribution: {dict(sorted(primary_counts.items()))}")
    if skipped:
        print(f"Skipped {len(skipped)} unsupported assets.")


if __name__ == "__main__":
    main()
