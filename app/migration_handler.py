from pathlib import Path

from alembic import command
from alembic.config import Config

from app.scripts.seed_upload_data import seed_from_uploads


def handler(_, __):
    project_root = Path(__file__).resolve().parents[1]
    alembic_config = Config(project_root / "alembic.ini")
    migration_dir = project_root / "db_migrations"
    if not migration_dir.exists():
        migration_dir = project_root / "alembic"
    alembic_config.set_main_option("script_location", str(migration_dir))
    command.upgrade(alembic_config, "head")
    summary = seed_from_uploads()
    return {
        "muscles_created": summary.muscles_created,
        "muscles_updated": summary.muscles_updated,
        "exercises_created": summary.exercises_created,
        "exercises_updated": summary.exercises_updated,
        "exercises_skipped": summary.exercises_skipped,
    }