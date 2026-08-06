from app.core.config import Settings


def test_database_url_uses_psycopg_driver_for_neon_url():
    settings = Settings(
        _env_file=None,
        DATABASE_URL=(
            "postgresql://app_user:password@example.neon.tech/app_db"
            "?sslmode=require&channel_binding=require"
        ),
    )

    assert settings.database_url == (
        "postgresql+psycopg://app_user:password@example.neon.tech/app_db"
        "?channel_binding=require&sslmode=require"
    )


def test_migration_database_url_prefers_direct_connection():
    settings = Settings(
        _env_file=None,
        DATABASE_URL="postgresql://app_user:password@example-pooler.neon.tech/app_db",
        MIGRATION_DATABASE_URL="postgresql://app_user:password@example.neon.tech/app_db",
    )

    assert settings.migration_database_url == (
        "postgresql+psycopg://app_user:password@example.neon.tech/app_db"
    )


def test_cors_origins_parses_comma_separated_hosts():
    settings = Settings(
        _env_file=None,
        CORS_ORIGINS="https://gym.example, http://localhost:3000",
    )

    assert settings.cors_origins == ["https://gym.example", "http://localhost:3000"]


def test_asset_url_uses_configured_frontend_origin():
    settings = Settings(_env_file=None, ASSET_BASE_URL="https://gym.example/")

    assert settings.asset_url("/uploads/muscles/Chest.png") == "https://gym.example/uploads/muscles/Chest.png"