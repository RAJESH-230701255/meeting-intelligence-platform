"""Transcript schemas."""

from datetime import datetime
from typing import Optional

from pydantic import BaseModel


class TranscriptResponse(BaseModel):
    id: int
    meeting_id: int
    source: str
    content: str
    language: Optional[str] = "en"
    created_at: datetime
    processed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TranscriptUpload(BaseModel):
    content: str
    source: str = "UPLOADED_FILE"
    language: Optional[str] = "en"
