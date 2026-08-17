"""Anthropic AI Provider — real meeting intelligence using Claude."""

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
      "confidence": 0.9
    }
  ]
}

Rules:
- Only extract ACTIONABLE tasks, not general discussion.
- Do NOT invent information. If assignee is unclear, use "unresolved".
- If deadline is unclear, set it to null.
- Include the source_text verbatim from the transcript.
- Confidence should reflect how certain you are this is an actionable task (0.0 to 1.0).
- Distinguish between decisions, suggestions, questions, and actual tasks.
- Do not output markdown code blocks like ```json ... ```. Output raw JSON ONLY.
"""

class AnthropicService(AIService):
    """Real AI meeting intelligence using Anthropic APIs."""

    def __init__(self):
        settings = get_settings()
        self.api_key = settings.ANTHROPIC_API_KEY
        self.model = settings.AI_MODEL if settings.AI_MODEL and "claude" in settings.AI_MODEL.lower() else "claude-3-haiku-20240307"

        if not self.api_key or self.api_key.startswith("YOUR_"):
            raise ValueError(
                "Anthropic API key not configured. Set ANTHROPIC_API_KEY in .env "
                "or use AI_PROVIDER=mock for development."
            )

    def analyze_transcript(self, transcript: str) -> MeetingAnalysis:
        """Analyze transcript using Anthropic API."""
        try:
            import anthropic

            client = anthropic.Anthropic(api_key=self.api_key)

            response = client.messages.create(
                model=self.model,
                max_tokens=2048,
                temperature=0.3,
                system=SYSTEM_PROMPT,
                messages=[
                    {"role": "user", "content": f"Analyze this meeting transcript and output JSON ONLY without markdown:\n\n{transcript}"},
                ],
            )

            # Anthropic returns a list of text blocks
            content = response.content[0].text.strip()
            
            # Handle potential markdown formatting from Claude
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            data = json.loads(content)

            # Validate through Pydantic
            return MeetingAnalysis(**data)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI response as JSON: {e}")
            raise ValueError(f"AI returned invalid JSON: {e}")
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise
