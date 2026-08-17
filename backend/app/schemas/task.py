"""Task schemas."""

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, Field


class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = None
    assigned_to: Optional[int] = None
    meeting_id: Optional[int] = None
    deadline: Optional[date] = None
    priority: str = Field(default="MEDIUM", pattern="^(LOW|MEDIUM|HIGH|URGENT)$")


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=500)
    description: Optional[str] = None
    assigned_to: Optional[int] = None
    deadline: Optional[date] = None
    priority: Optional[str] = Field(None, pattern="^(LOW|MEDIUM|HIGH|URGENT)$")
    status: Optional[str] = Field(None, pattern="^(PENDING_REVIEW|CONFIRMED|PENDING|IN_PROGRESS|COMPLETED|REJECTED)$")


class TaskResponse(BaseModel):
    id: int
    meeting_id: Optional[int] = None
    assigned_to: Optional[int] = None
    assignee_name: Optional[str] = None
    created_by: int
    creator_name: Optional[str] = None
    title: str
    description: Optional[str] = None
    deadline: Optional[date] = None
    priority: str
    status: str
    source_text: Optional[str] = None
    ai_confidence: Optional[float] = None
    source: str
    meeting_title: Optional[str] = None
    created_at: datetime
    updated_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class TaskListResponse(BaseModel):
    tasks: list[TaskResponse]
    total: int


class ConfirmActionItemRequest(BaseModel):
    """Confirm an AI-extracted action item, optionally overriding fields."""
    assigned_to: Optional[int] = None
    deadline: Optional[date] = None
    priority: Optional[str] = Field(None, pattern="^(LOW|MEDIUM|HIGH|URGENT)$")
    title: Optional[str] = None
    description: Optional[str] = None
