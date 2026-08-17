"""AuditLog model."""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import relationship

from app.database.base import Base


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    action = Column(String(100), nullable=False)  # e.g., CREATE_MEETING, CONFIRM_TASK, LOGIN
    entity_type = Column(String(50), nullable=True)  # e.g., meeting, task, user
    entity_id = Column(Integer, nullable=True)
    timestamp = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    metadata_ = Column("metadata", JSON, nullable=True)

    # Relationships
    user = relationship("User", back_populates="audit_logs")
