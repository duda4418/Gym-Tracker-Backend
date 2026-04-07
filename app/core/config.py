"""Application settings and environment configuration."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Pydantic settings for application configuration."""

    DEBUG: bool = False

    POSTGRES_USER: str = "app_user"
    POSTGRES_PASSWORD: str = "app_password"
    POSTGRES_DB: str = "app_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432

    POSTGRES_CONNECT_TIMEOUT_SECONDS: int = 5
    POSTGRES_POOL_TIMEOUT_SECONDS: int = 5
    POLICY_EXPIRY_CHECK_INTERVAL_SECONDS: int = 600

    JWT_SECRET_KEY: str = "secret-dev-jwt-secret-key-min-32-bytes-long"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    UPLOADS_DIR: str = "app/uploads"

    @property
    def DATABASE_URL(self) -> str:
        """Build the sync SQLAlchemy database URL from settings."""
        return (
            f"postgresql+psycopg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_HOST}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        """Build the async SQLAlchemy database URL from settings."""
        return self.DATABASE_URL

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
