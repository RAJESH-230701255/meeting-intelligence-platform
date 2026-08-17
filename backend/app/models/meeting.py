"""Meeting model."""

from datetime import datetime, timezone

from sqlalchemy import Column, Date, DateTime, ForeignKey, Integer, String, Text, Time
from sqlalchemy.orm import relationship

from app.database.base import Base


class Meeting(Base):
    __tablename__ = "meetings"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=True)
    meeting_type = Column(String(50), nullable=False, default="INTERNAL")  # INTERNAL, EXTERNAL
    host_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    room_id = Column(String(100), unique=True, nullable=True, index=True)
    meeting_date = Column(Date, nullable=True)
    start_time = Column(DateTime(timezone=True), nullable=True)
    end_time = Column(DateTime(timezone=True), nullable=True)
    status = Column(String(50), nullable=False, default="SCHEDULED")  # SCHEDULED, IN_PROGRESS, COMPLETED, CANCELLED
    source_type = Column(String(50), nullable=True)  # INTERNAL_AUDIO, UPLOADED_AUDIO, UPLOADED_TRANSCRIPT
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)

    # Relationships
    host = relationship("User", back_populates="hosted_meetings", foreign_keys=[host_id])
    participants = relationship("MeetingParticipant", back_populates="meeting", cascade="all, delete-orphan")
    transcript = relationship("Transcript", back_populates="meeting", uselist=False)
    summary = relationship("MeetingSummary", back_populates="meeting", uselist=False)
    decisions = relationship("Decision", back_populates="meeting", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="meeting")
