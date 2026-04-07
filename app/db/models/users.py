import uuid
from sqlalchemy import Column, String, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.database import Base

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    auth_id = Column(String, unique=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=True)
    qr_code = Column(String, nullable=True)
    password_hash = Column(String, nullable=False)

    workout_sessions = relationship("WorkoutSession", back_populates="user")
    workouts = relationship("Workout", back_populates="user", cascade="all, delete-orphan")
    splits = relationship("Split", back_populates="user", cascade="all, delete-orphan")
    favorite_exercises = relationship("UserFavoriteExercise", back_populates="user", cascade="all, delete-orphan")
