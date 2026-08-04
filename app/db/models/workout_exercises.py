import uuid

from sqlalchemy import Column, ForeignKey, Integer, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.database import Base


class WorkoutExercise(Base):
    __tablename__ = "workout_exercises"
    __table_args__ = (
        UniqueConstraint("workout_session_id", "order_index", name="uq_workout_exercise_order"),
    )

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    workout_session_id = Column(
        UUID(as_uuid=True),
        ForeignKey("workout_sessions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    exercise_id = Column(
        UUID(as_uuid=True),
        ForeignKey("exercises.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    order_index = Column(Integer, nullable=False)
    superset_group_id = Column(Integer, nullable=True)

    session = relationship("WorkoutSession", back_populates="exercises")
    exercise = relationship("Exercise", back_populates="workout_exercises")
    sets = relationship(
        "WorkoutSet",
        back_populates="workout_exercise",
        cascade="all, delete-orphan",
        order_by="WorkoutSet.set_number",
    )