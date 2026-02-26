"""Unified AI provider abstraction — Claude (Anthropic) + Gemini (Google).

Provides a single `call_ai()` function that routes to the correct provider
based on the provider name. Both providers enforce JSON output and cache
system prompts where supported.
"""

from __future__ import annotations

import json
import time
from abc import ABC, abstractmethod
from typing import Any

from rich.console import Console

from core.constants import (
    PROVIDER_CLAUDE,
    PROVIDER_GEMINI,
    get_stage_config,
)

console = Console()


class AIProvider(ABC):
    """Abstract base class for AI providers."""

    @abstractmethod
    def call(
        self,
        *,
        stage: str,
        system_prompt: str,
        user_message: str,
        provider_name: str,
    ) -> dict[str, Any] | None:
        """Make an AI call and return parsed JSON, or None on parse failure.

        Args:
            stage: Stage name (``parse``, ``questions``, ``analysis``, etc.).
            system_prompt: System-level instruction text.
            user_message: User-level prompt text.
            provider_name: Provider identifier for stage config lookup.

        Returns:
            Parsed JSON dict, or ``None`` if JSON parsing fails.
        """


class AnthropicProvider(AIProvider):
    """Anthropic (Claude) provider using the Anthropic SDK."""

    def __init__(self, client: Any = None) -> None:
        self._client = client

    def _get_client(self) -> Any:
        """Lazy-init the Anthropic client."""
        if self._client is None:
            import anthropic

            self._client = anthropic.Anthropic()
        return self._client

    def call(
        self,
        *,
        stage: str,
        system_prompt: str,
        user_message: str,
        provider_name: str = PROVIDER_CLAUDE,
    ) -> dict[str, Any] | None:
        """Make a Claude API call with cached system prompt and JSON output."""
        import anthropic

        client = self._get_client()
        cfg = get_stage_config(provider_name)[stage]

        try:
            response = client.messages.create(
                model=cfg["model"],
                max_tokens=cfg["max_tokens"],
                temperature=cfg["temperature"],
                system=[
                    {
                        "type": "text",
                        "text": system_prompt,
                        "cache_control": {"type": "ephemeral"},
                    }
                ],
                messages=[{"role": "user", "content": user_message}],
            )
            raw = response.content[0].text
            return json.loads(raw)
        except json.JSONDecodeError:
            return None
        except anthropic.RateLimitError:
            _handle_rate_limit()
            return self.call(
                stage=stage,
                system_prompt=system_prompt,
                user_message=user_message,
                provider_name=provider_name,
            )


class GeminiProvider(AIProvider):
    """Google Gemini provider using the google-genai SDK."""

    def __init__(self, client: Any = None) -> None:
        self._client = client

    def _get_client(self) -> Any:
        """Lazy-init the Gemini client."""
        if self._client is None:
            from google import genai

            self._client = genai.Client()
        return self._client

    def call(
        self,
        *,
        stage: str,
        system_prompt: str,
        user_message: str,
        provider_name: str = PROVIDER_GEMINI,
    ) -> dict[str, Any] | None:
        """Make a Gemini API call with JSON output mode."""
        from google import genai
        from google.genai import types

        client = self._get_client()
        cfg = get_stage_config(provider_name)[stage]

        try:
            response = client.models.generate_content(
                model=cfg["model"],
                contents=user_message,
                config=types.GenerateContentConfig(
                    system_instruction=system_prompt,
                    max_output_tokens=cfg["max_tokens"],
                    temperature=cfg["temperature"],
                    response_mime_type="application/json",
                ),
            )
            raw = response.text
            return json.loads(raw)
        except json.JSONDecodeError:
            return None
        except Exception as exc:
            # Handle rate limiting from Gemini
            exc_str = str(exc).lower()
            if "429" in exc_str or "rate" in exc_str or "quota" in exc_str:
                _handle_rate_limit()
                return self.call(
                    stage=stage,
                    system_prompt=system_prompt,
                    user_message=user_message,
                    provider_name=provider_name,
                )
            raise


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------
def get_provider(name: str = PROVIDER_CLAUDE, *, client: Any = None) -> AIProvider:
    """Return the correct AI provider instance.

    Args:
        name: ``"claude"`` or ``"gemini"``.
        client: Optional pre-configured SDK client (useful for testing).

    Returns:
        An :class:`AIProvider` instance.
    """
    if name == PROVIDER_GEMINI:
        return GeminiProvider(client=client)
    return AnthropicProvider(client=client)


# ---------------------------------------------------------------------------
# Convenience wrapper — used by all AI modules
# ---------------------------------------------------------------------------
def call_ai(
    *,
    stage: str,
    system_prompt: str,
    user_message: str,
    provider: str = PROVIDER_CLAUDE,
    client: Any = None,
) -> dict[str, Any] | None:
    """High-level AI call with provider routing.

    Calls the correct provider, returns parsed JSON dict or None.

    Args:
        stage: Stage name for config lookup.
        system_prompt: System prompt text.
        user_message: User prompt text.
        provider: ``"claude"`` or ``"gemini"``.
        client: Optional pre-configured client for testing.

    Returns:
        Parsed JSON dict, or ``None`` on JSON decode failure.
    """
    p = get_provider(provider, client=client)
    return p.call(
        stage=stage,
        system_prompt=system_prompt,
        user_message=user_message,
        provider_name=provider,
    )


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------
def _handle_rate_limit() -> None:
    """Wait 60 seconds with a Rich countdown on rate-limit errors."""
    for remaining in range(60, 0, -1):
        console.print(
            f"\r[yellow]Rate limited — retrying in {remaining}s...[/yellow]",
            end="",
        )
        time.sleep(1)
    console.print()
