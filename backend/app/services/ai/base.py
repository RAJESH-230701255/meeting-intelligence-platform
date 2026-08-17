"""AI Service — Abstract base class for meeting intelligence providers."""

from abc import ABC, abstractmethod

from app.schemas.analysis import MeetingAnalysis


class AIService(ABC):
    """Abstract base class for AI meeting intelligence providers."""

    @abstractmethod
    def analyze_transcript(self, transcript: str) -> MeetingAnalysis:
        """Analyze a meeting transcript and return structured intelligence.

        Args:
            transcript: The full text of the meeting transcript.

        Returns:
            MeetingAnalysis: Validated structured output containing summary,
            key points, decisions, and action items.
        """
        pass
