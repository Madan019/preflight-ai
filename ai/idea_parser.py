"""Stage 1 — Parse plain-english idea into structured project requirements.

Uses the AI provider abstraction (Claude Haiku or Gemini Flash).
"""

from __future__ import annotations

from typing import Any

from rich.console import Console

from ai.provider import call_ai
from core.constants import PROVIDER_CLAUDE
from core.spec_builder import ParsedIdea

console = Console()

# ---------------------------------------------------------------------------
# System prompt (cached per SPEC Rule 3)
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = (
    "You are a software architect. Extract structured project requirements "
    "from plain english. Respond ONLY with valid JSON. No explanation."
)

# ---------------------------------------------------------------------------
# Output schema injected into the user message (SPEC Rule 4)
# ---------------------------------------------------------------------------
OUTPUT_SCHEMA = """{
  "app_type": "web | mobile | cli | api | desktop | fullstack",
  "core_purpose": "one sentence",
  "features": ["auth", "payments", "realtime", "crud"],
  "integrations": ["github", "stripe", "slack", "twilio"],
  "complexity": "simple | moderate | complex | enterprise",
  "target_users": "description of who uses this",
  "suggested_stack": {
    "language": "python | javascript | typescript | go",
    "frontend": "react | vue | next | flutter | none",
    "backend": "fastapi | express | django | none",
    "database": "postgres | mongo | sqlite | redis | none",
    "auth": "jwt | oauth | session | clerk | none"
  },
  "similar_to": "notion | github | shopify | slack | none",
  "implicit_requirements": [
    "email service (auth feature implies password reset)",
    "file storage (collaboration implies uploads)"
  ],
  "ai_target": "claude | gemini | both"
}"""


def parse_idea(
    raw_text: str,
    *,
    provider: str = PROVIDER_CLAUDE,
    client: Any = None,
) -> ParsedIdea:
    """Parse a plain-english project description into structured tags.

    Args:
        raw_text: The user's free-form project description.
        provider: AI provider to use (``"claude"`` or ``"gemini"``).
        client: Optional pre-configured SDK client (for testing).

    Returns:
        A populated :class:`ParsedIdea` dataclass.

    Raises:
        ValueError: If the AI response is not valid JSON after retry.
    """
    user_message = (
        f"{raw_text}\n\n"
        f"Respond ONLY with JSON matching this schema:\n{OUTPUT_SCHEMA}"
    )

    # First attempt
    data = call_ai(
        stage="parse",
        system_prompt=SYSTEM_PROMPT,
        user_message=user_message,
        provider=provider,
        client=client,
    )
    if data is not None:
        return ParsedIdea.from_dict(data)

    # Retry once with explicit JSON reminder (SPEC error handling)
    console.print("[yellow]⚠ JSON parse failed, retrying with explicit reminder...[/yellow]")
    user_message_retry = (
        f"{raw_text}\n\n"
        "CRITICAL: Your response MUST be valid JSON only. "
        "No markdown fences, no explanation, no text before or after the JSON.\n\n"
        f"Schema:\n{OUTPUT_SCHEMA}"
    )
    data = call_ai(
        stage="parse",
        system_prompt=SYSTEM_PROMPT,
        user_message=user_message_retry,
        provider=provider,
        client=client,
    )
    if data is not None:
        return ParsedIdea.from_dict(data)

    raise ValueError("Failed to parse AI response as JSON after retry.")
