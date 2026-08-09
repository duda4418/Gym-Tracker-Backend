import uuid
from sqlalchemy import Boolean, CheckConstraint, Column, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db.database import Base
from app.utils.enums.exercises import ExerciseType

class Exercise(Base):
    __tablename__ = "exercises"
    __table_args__ = (
        CheckConstraint(
            "exercise_type IN ('body weight', 'weighted', 'negative')",
            name="ck_exercises_exercise_type",
        ),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    catalog_id = Column(String, unique=True, nullable=True, index=True)
    catalog_type = Column("type", String, nullable=True)
    name = Column(String, unique=True, nullable=False)
    pic = Column(String, nullable=True)
    thumbnail_url = Column(String, nullable=True)
    video_url = Column(String, nullable=True)
    tips = Column(String, nullable=True)
    equipment = Column(String, nullable=True)
    exercise_type = Column(String, nullable=False, default=ExerciseType.WEIGHTED.value)
    rest_time = Column(Integer, nullable=False, default=90)
    favourite = Column(Boolean, default=False)

    muscle_id = Column(UUID(as_uuid=True), ForeignKey("muscles.id"), nullable=False)

    muscle = relationship("Muscle", back_populates="exercises")
    workout_exercises = relationship("WorkoutExercise", back_populates="exercise")
    secondary_muscles = relationship("ExerciseSecondaryMuscle", back_populates="exercise", cascade="all, delete-orphan")
    favorited_by = relationship("UserFavoriteExercise", back_populates="exercise", cascade="all, delete-orphan")
