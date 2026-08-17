"""Transcript model."""

from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship

from app.database.base import Base


class Transcript(Base):
    __tablename__ = "transcripts"

    id = Column(Integer, primary_key=True, index=True)
    meeting_id = Column(Integer, ForeignKey("meetings.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)
    source = Column(String(50), nullable=False)  # AUTO_RECORDED, UPLOADED_AUDIO, UPLOADED_FILE
    content = Column(Text, nullable=False)
    language = Column(String(20), nullable=True, default="en")
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    processed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    meeting = relationship("Meeting", back_populates="transcript")
