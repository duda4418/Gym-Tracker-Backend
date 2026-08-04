import uuid

from sqlalchemy import Boolean, Column, DateTime, Enum, Float, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.database import Base
from app.utils.enums.workouts import SetType


class WorkoutSet(Base):
    __tablename__ = "workout_sets"
    __table_args__ = (
        UniqueConstraint("workout_exercise_id", "set_number", name="uq_workout_set_number"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    workout_exercise_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workout_exercises.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    set_number = Column(Integer, nullable=False)
    set_type = Column(Enum(SetType, name="workout_set_type", values_callable=lambda enum: [item.value for item in enum]), nullable=False)
    target_weight = Column(Float, nullable=True)
    target_reps = Column(Integer, nullable=True)
    target_rir = Column(Integer, nullable=True)
    actual_weight = Column(Float, nullable=True)
    actual_reps = Column(Integer, nullable=True)
    actual_rir = Column(Integer, nullable=True)
    completed = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)

    workout_exercise = relationship("WorkoutExercise", back_populates="sets")