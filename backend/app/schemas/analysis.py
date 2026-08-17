"""AI Analysis schemas — structured output from AI meeting intelligence."""

from typing import Optional

from pydantic import BaseModel, Field


class DecisionItem(BaseModel):
    decision: str
    context: Optional[str] = None


class ActionItem(BaseModel):
    title: str = Field(..., min_length=1)
    description: Optional[str] = None
    assignee_name: Optional[str] = None  # May be "unresolved"
    deadline: Optional[str] = None  # ISO date or relative like "Friday"
    priority: str = Field(default="MEDIUM", pattern="^(LOW|MEDIUM|HIGH|URGENT)$")
    source_text: Optional[str] = None
    confidence: float = Field(default=0.5, ge=0.0, le=1.0)


class MeetingAnalysis(BaseModel):
    """Validated structured output from the AI meeting intelligence pipeline."""
    summary: str
    key_points: list[str] = []
    decisions: list[DecisionItem] = []
    action_items: list[ActionItem] = []


class AnalysisResponse(BaseModel):
    meeting_id: int
    summary: str
    key_points: list[str] = []
    decisions: list[dict] = []
    action_items: list[dict] = []
    status: str = "completed"
