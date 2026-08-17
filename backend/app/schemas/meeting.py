"""Meeting schemas."""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class MeetingCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    meeting_type: str = Field(default="INTERNAL", pattern="^(INTERNAL|EXTERNAL)$")
    meeting_date: Optional[date] = None
    participant_ids: Optional[list[int]] = None


class MeetingUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(SCHEDULED|IN_PROGRESS|COMPLETED|CANCELLED)$")
    meeting_date: Optional[date] = None


class ParticipantInfo(BaseModel):
    id: int
    user_id: int
    user_name: str
    user_email: str
    role_in_meeting: str
    joined_at: Optional[datetime] = None
    left_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class MeetingResponse(BaseModel):
    id: int
    title: str
    description: Optional[str] = None
    meeting_type: str
    host_id: int
    host_name: Optional[str] = None
    room_id: Optional[str] = None
    meeting_date: Optional[date] = None
    start_time: Optional[datetime] = None
    end_time: Optional[datetime] = None
    status: str
    source_type: Optional[str] = None
    created_at: datetime
    participants: list[ParticipantInfo] = []
    has_transcript: bool = False
    has_summary: bool = False
    task_count: int = 0

    class Config:
        from_attributes = True


class MeetingListResponse(BaseModel):
    meetings: list[MeetingResponse]
    total: int


class AddParticipantsRequest(BaseModel):
    user_ids: list[int]


class StartMeetingRequest(BaseModel):
    """Sent when a host starts the meeting."""
    pass


class EndMeetingRequest(BaseModel):
    """Sent when a host ends the meeting."""
    pass
