"""OpenAI AI Provider — real meeting intelligence using configurable models."""

import json
import logging

from app.core.config import get_settings
from app.schemas.analysis import MeetingAnalysis
from app.services.ai.base import AIService

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an AI meeting intelligence assistant. Analyze the meeting transcript and extract structured information.

Return ONLY valid JSON in this exact format:
{
  "summary": "A concise summary of the meeting",
  "key_points": ["Point 1", "Point 2"],
  "decisions": [
    {"decision": "What was decided", "context": "Why or how it was decided"}
  ],
  "action_items": [
    {
      "title": "Short task title",
      "description": "Detailed task description",
      "assignee_name": "Person name or 'unresolved'",
      "deadline": "YYYY-MM-DD or null if unclear",
      "priority": "LOW|MEDIUM|HIGH|URGENT",
      "source_text": "The exact quote from the transcript",
      "confidence": 0.0 to 1.0
    }
  ]
}

Rules:
- Only extract ACTIONABLE tasks, not general discussion.
- Do NOT invent information. If assignee is unclear, use "unresolved".
- If deadline is unclear, set it to null.
- Include the source_text verbatim from the transcript.
- Confidence should reflect how certain you are this is an actionable task.
- Distinguish between decisions, suggestions, questions, and actual tasks.
"""


class OpenAIService(AIService):
    """Real AI meeting intelligence using OpenAI-compatible APIs."""

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.OPENAI_API_KEY
        self.model = settings.AI_MODEL

        if not self.api_key or self.api_key.startswith("YOUR_"):
            raise ValueError(
                "OpenAI API key not configured. Set OPENAI_API_KEY in .env "
                "or use AI_PROVIDER=mock for development."
            )

    def analyze_transcript(self, transcript: str) -> MeetingAnalysis:
        """Analyze transcript using OpenAI API."""
        try:
            import openai

            client = openai.OpenAI(api_key=self.api_key)

            response = client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": f"Analyze this meeting transcript:\n\n{transcript}"},
                ],
                temperature=0.3,
                response_format={"type": "json_object"},
            )

            content = response.choices[0].message.content
            data = json.loads(content)

            # Validate through Pydantic
            return MeetingAnalysis(**data)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            raise ValueError(f"AI returned invalid JSON: {e}")
        except Exception as e:
            logger.error(f"OpenAI API error: {e}")
            raise
