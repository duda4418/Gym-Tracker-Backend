"""Application settings and environment configuration."""
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import URL, make_url


class Settings(BaseSettings):
    """Pydantic settings for application configuration."""

    DEBUG: bool = False
    CORS_ORIGINS: str = "http://localhost:3000"
    CORS_ORIGIN_REGEX: str | None = None
    ASSET_BASE_URL: str = ""
    SERVE_LOCAL_UPLOADS: bool = True
    METRICS_ENABLED: bool = True
    OTEL_ENABLED: bool = False
    OTEL_SERVICE_NAME: str = "gym-tracker-backend"
    OTEL_SERVICE_VERSION: str = "1.0.0"
    OTEL_ENVIRONMENT: str = "development"
    OTEL_EXPORTER_OTLP_TRACES_ENDPOINT: str = "http://localhost:4318/v1/traces"
    OTEL_EXPORTER_TIMEOUT_SECONDS: int = 10
    OTEL_TRACES_SAMPLER_RATIO: float = 1.0

    PYROSCOPE_ENABLED: bool = False
    PYROSCOPE_SERVER_ADDRESS: str = "http://localhost:4040"
    PYROSCOPE_APPLICATION_NAME: str = "gym-tracker-backend"
    PYROSCOPE_SAMPLE_RATE: int = 100
    PYROSCOPE_GIL_ONLY: bool = True
    PYROSCOPE_ENABLE_LOGGING: bool = False

    LOG_LEVEL: str = "INFO"
    LOG_TO_FILE: bool = True
    LOGS_DIR: str = "app/logs"
    LOG_FILE_NAME: str = "backend.log"

    POSTGRES_USER: str = "app_user"
    POSTGRES_PASSWORD: str = "app_password"
    POSTGRES_DB: str = "app_db"
    POSTGRES_HOST: str = "localhost"
    POSTGRES_PORT: int = 5432
    DATABASE_URL: str | None = None
    MIGRATION_DATABASE_URL: str | None = None

    POSTGRES_CONNECT_TIMEOUT_SECONDS: int = 5
    POSTGRES_POOL_TIMEOUT_SECONDS: int = 5
    DATABASE_POOL_SIZE: int = 1
    DATABASE_MAX_OVERFLOW: int = 0
    DATABASE_POOL_RECYCLE_SECONDS: int = 300
    POLICY_EXPIRY_CHECK_INTERVAL_SECONDS: int = 600

    JWT_SECRET_KEY: str = "secret-dev-jwt-secret-key-min-32-bytes-long"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 14 * 24 * 60
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    UPLOADS_DIR: str = "app/uploads"

    @property
    def database_url(self) -> str:
        """Return a psycopg SQLAlchemy URL from DATABASE_URL or Postgres fields."""
        if self.DATABASE_URL:
            url = make_url(self.DATABASE_URL)
            if url.drivername == "postgresql":
                url = url.set(drivername="postgresql+psycopg")
            return url.render_as_string(hide_password=False)

        return URL.create(
            drivername="postgresql+psycopg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_HOST,
            port=self.POSTGRES_PORT,
            database=self.POSTGRES_DB,
        ).render_as_string(hide_password=False)

    @property
    def migration_database_url(self) -> str:
        if not self.MIGRATION_DATABASE_URL:
            return self.database_url

        url = make_url(self.MIGRATION_DATABASE_URL)
        if url.drivername == "postgresql":
            url = url.set(drivername="postgresql+psycopg")
        return url.render_as_string(hide_password=False)

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        """Build the async SQLAlchemy database URL from settings."""
        return self.database_url

    @property
    def cors_origins(self) -> list[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]

    def asset_url(self, path: str) -> str:
        return f"{self.ASSET_BASE_URL.rstrip('/')}/{path.lstrip('/')}"

    model_config = SettingsConfigDict(
        env_file=Path(__file__).resolve().parents[2] / ".env",
        extra="ignore",
    )


@lru_cache
def get_settings() -> Settings:
    """Get cached application settings."""
    return Settings()
