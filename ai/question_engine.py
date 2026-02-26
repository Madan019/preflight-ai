"""Stage 2 — Generate smart tailored follow-up questions.

Uses the AI provider abstraction (Claude Haiku or Gemini Flash).
"""

from __future__ import annotations

import json
from typing import Any

from rich.console import Console

from ai.provider import call_ai
from core.constants import PROVIDER_CLAUDE
from core.spec_builder import ParsedIdea, QuestionSet

console = Console()

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = (
    "You are a senior developer conducting a project requirements interview. "
    "Generate specific ordered questions based on parsed project tags. "
    "Each question must be relevant, non-obvious, and explain its impact. "
    "Respond ONLY with valid JSON. No explanation."
)

# ---------------------------------------------------------------------------
# Output schema
# ---------------------------------------------------------------------------
OUTPUT_SCHEMA = """{
  "questions": [
    {
      "id": "q1",
      "question": "Will different users have different permission levels?",
      "why_asking": "Your collaboration feature requires role-based access control",
      "impacts": ["auth_complexity", "database_schema", "api_design"],
      "type": "choice | text | boolean | multi_choice",
      "options": ["admin/member only", "custom roles", "single role"],
      "default": "admin/member only",
      "required": true
    }
  ],
  "total_questions": 8,
  "estimated_minutes": 3
}

Rules:
- Generate 6-12 questions maximum
- Order from most impactful to least
- Skip obvious questions (don't ask stack if already clear from idea)
- Each question must directly affect what files get generated"""


def generate_questions(
    parsed_idea: ParsedIdea,
    *,
    provider: str = PROVIDER_CLAUDE,
    client: Any = None,
) -> QuestionSet:
    """Generate tailored follow-up questions from the parsed idea.

    Args:
        parsed_idea: Output from Stage 1 (idea parser).
        provider: AI provider to use (``"claude"`` or ``"gemini"``).
        client: Optional pre-configured SDK client.

    Returns:
        A :class:`QuestionSet` with ordered questions.

    Raises:
        ValueError: If the AI response is not valid JSON after retry.
    """
    idea_json = json.dumps(
        {
            "app_type": parsed_idea.app_type,
            "core_purpose": parsed_idea.core_purpose,
            "features": parsed_idea.features,
            "integrations": parsed_idea.integrations,
            "complexity": parsed_idea.complexity,
            "target_users": parsed_idea.target_users,
            "suggested_stack": parsed_idea.suggested_stack,
            "similar_to": parsed_idea.similar_to,
            "implicit_requirements": parsed_idea.implicit_requirements,
            "ai_target": parsed_idea.ai_target,
        },
        indent=2,
    )

    user_message = (
        f"Parsed project tags:\n{idea_json}\n\n"
        f"Respond ONLY with JSON matching this schema:\n{OUTPUT_SCHEMA}"
    )

    data = call_ai(
        stage="questions",
        system_prompt=SYSTEM_PROMPT,
        user_message=user_message,
        provider=provider,
        client=client,
    )
    if data is not None:
        return QuestionSet.from_dict(data)

    # Retry once
    console.print("[yellow]⚠ JSON parse failed, retrying...[/yellow]")
    user_message_retry = (
        f"Parsed project tags:\n{idea_json}\n\n"
        "CRITICAL: Your response MUST be valid JSON only. "
        "No markdown fences, no explanation.\n\n"
        f"Schema:\n{OUTPUT_SCHEMA}"
    )
    data = call_ai(
        stage="questions",
        system_prompt=SYSTEM_PROMPT,
        user_message=user_message_retry,
        provider=provider,
        client=client,
    )
    if data is not None:
        return QuestionSet.from_dict(data)

    raise ValueError("Failed to parse question engine response as JSON after retry.")
