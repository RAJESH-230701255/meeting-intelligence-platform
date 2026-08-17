"""Mock AI Provider — deterministic results for development/testing."""

import re
from datetime import date, timedelta

from app.schemas.analysis import ActionItem, DecisionItem, MeetingAnalysis
from app.services.ai.base import AIService


class MockAIService(AIService):
    """Mock AI service returning deterministic meeting intelligence.

    When transcript content matches known patterns, returns contextual results.
    For unknown transcripts, performs basic keyword extraction.
    """

    # The canonical sample transcript from the project specification
    SAMPLE_KEYWORDS = ["rajesh", "priya", "report", "friday", "monday", "testing"]

    def analyze_transcript(self, transcript: str) -> MeetingAnalysis:
        """Analyze transcript with deterministic mock intelligence."""
        transcript_lower = transcript.lower()

        # Check if this matches the canonical sample
        matches = sum(1 for kw in self.SAMPLE_KEYWORDS if kw in transcript_lower)

        if matches >= 3:
            return self._canonical_response()
        else:
            return self._generic_response(transcript)

    def _canonical_response(self) -> MeetingAnalysis:
        """Return the canonical response matching the project specification."""
        today = date.today()
        # Calculate next Friday and next Monday
        days_until_friday = (4 - today.weekday()) % 7
        if days_until_friday == 0:
            days_until_friday = 7
        next_friday = today + timedelta(days=days_until_friday)

        days_until_monday = (0 - today.weekday()) % 7
        if days_until_monday == 0:
            days_until_monday = 7
        next_monday = today + timedelta(days=days_until_monday)

        return MeetingAnalysis(
            summary="The team discussed project reporting, review responsibilities and testing completion.",
            key_points=[
                "Rajesh will prepare the project report",
                "Priya will review the project report",
                "Testing must be completed before the next meeting",
            ],
            decisions=[
                DecisionItem(
                    decision="Testing must be completed before the next meeting.",
                    context="The team agreed on a testing deadline to ensure quality before the next review cycle.",
                ),
            ],
            action_items=[
                ActionItem(
                    title="Prepare project report",
                    description="Prepare and submit the project report",
                    assignee_name="Rajesh",
                    deadline=next_friday.isoformat(),
                    priority="MEDIUM",
                    source_text="Rajesh will prepare the project report by Friday.",
                    confidence=0.91,
                ),
                ActionItem(
                    title="Review project report",
                    description="Review the project report prepared by Rajesh",
                    assignee_name="Priya",
                    deadline=next_monday.isoformat(),
                    priority="MEDIUM",
                    source_text="Priya will review the report on Monday.",
                    confidence=0.89,
                ),
            ],
        )

    def _generic_response(self, transcript: str) -> MeetingAnalysis:
        """Generate a basic response for non-canonical transcripts."""
        # Simple sentence splitting
        sentences = [s.strip() for s in re.split(r'[.!?]+', transcript) if s.strip()]

        # Build summary from first few sentences
        summary_sentences = sentences[:3] if len(sentences) >= 3 else sentences
        summary = ". ".join(summary_sentences) + "." if summary_sentences else "Meeting discussion recorded."

        # Extract key points (up to 5 non-trivial sentences)
        key_points = [s for s in sentences if len(s.split()) >= 4][:5]
        if not key_points:
            key_points = ["General discussion took place."]

        # Look for action-like patterns
        action_items = []
        action_patterns = [
            r"(?:please|will|should|must|need to)\s+(.+)",
            r"(\w+)\s+(?:will|should|must)\s+(.+)",
        ]

        for sentence in sentences:
            for pattern in action_patterns:
                match = re.search(pattern, sentence, re.IGNORECASE)
                if match:
                    action_items.append(
                        ActionItem(
                            title=sentence[:100],
                            description=sentence,
                            assignee_name="unresolved",
                            deadline=None,
                            priority="MEDIUM",
                            source_text=sentence,
                            confidence=0.65,
                        )
                    )
                    break
            if len(action_items) >= 5:
                break

        return MeetingAnalysis(
            summary=summary,
            key_points=key_points,
            decisions=[],
            action_items=action_items,
        )
