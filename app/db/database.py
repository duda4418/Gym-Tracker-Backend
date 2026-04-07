from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from contextlib import contextmanager
from app.core.config import get_settings

# Initialize the database connection
settings = get_settings()
engine = create_engine(settings.DATABASE_URL)

# Base Model
Base = declarative_base()

# ORM Session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# ✅ Import models to ensure tables are created
from app.db.models.muscles import Muscle
from app.db.models.exercises import Exercise
from app.db.models.splits import Split
from app.db.models.split_muscle import SplitMuscle
from app.db.models.workouts import Workout
from app.db.models.workout_sessions import WorkoutSession
from app.db.models.workout_session_muscle import WorkoutSessionMuscle

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
