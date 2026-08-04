import uuid
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship

from app.db.database import Base


class WorkoutSession(Base):
    __tablename__ = "workout_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4, index=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    split_id = Column(UUID(as_uuid=True), ForeignKey("splits.id", ondelete="SET NULL"), nullable=True)
    started_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    notes = Column(String, nullable=True)

    split = relationship("Split")
    user = relationship("User", back_populates="workout_sessions")
    exercises = relationship(
        "WorkoutExercise",
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="WorkoutExercise.order_index",
    )
