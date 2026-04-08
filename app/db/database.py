from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from contextlib import contextmanager
from app.core.config import get_settings

# Initialize the database connection
settings = get_settings()
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"connect_timeout": settings.POSTGRES_CONNECT_TIMEOUT_SECONDS},
    pool_timeout=settings.POSTGRES_POOL_TIMEOUT_SECONDS,
    pool_pre_ping=True,
)

# Base Model
Base = declarative_base()

# ORM Session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ✅ Import models to ensure tables are registered on Base.metadata
import app.db.models  # noqa: F401

# ✅ Fix: Add session_scope to manage database transactions
@contextmanager
def session_scope():
    """Provides a transactional scope around a series of operations."""
    session = SessionLocal()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        raise e
    finally:
        session.close()
