"""Tests for ai/idea_parser.py — mock AI providers, test JSON parsing."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from ai.idea_parser import parse_idea
from core.spec_builder import ParsedIdea


MOCK_RESPONSE = {
    "app_type": "fullstack",
    "core_purpose": "A task management app with team collaboration",
    "features": ["auth", "crud", "realtime", "collaboration"],
    "integrations": ["slack"],
    "complexity": "moderate",
    "target_users": "Small to medium development teams",
    "suggested_stack": {
        "language": "typescript",
        "frontend": "react",
        "backend": "express",
        "database": "postgres",
        "auth": "jwt",
    },
    "similar_to": "notion",
    "implicit_requirements": [
        "email service (auth implies password reset)",
        "file storage (collaboration implies uploads)",
    ],
    "ai_target": "both",
}


class TestParseIdea:
    """Tests for the parse_idea function."""

    @patch("ai.idea_parser.call_ai")
    def test_parse_valid_idea(self, mock_call: MagicMock) -> None:
        """Test parsing a valid idea returns correct ParsedIdea."""
        mock_call.return_value = MOCK_RESPONSE
        result = parse_idea("I want a task management app for teams")

        assert isinstance(result, ParsedIdea)
        assert result.app_type == "fullstack"
        assert result.complexity == "moderate"
        assert "auth" in result.features
        assert result.ai_target == "both"

    @patch("ai.idea_parser.call_ai")
    def test_parse_preserves_features(self, mock_call: MagicMock) -> None:
        """Test that all features are preserved from AI response."""
        mock_call.return_value = MOCK_RESPONSE
        result = parse_idea("task app")

        assert len(result.features) == 4
        assert "realtime" in result.features

    @patch("ai.idea_parser.call_ai")
    def test_parse_preserves_stack(self, mock_call: MagicMock) -> None:
        """Test that suggested stack is preserved."""
        mock_call.return_value = MOCK_RESPONSE
        result = parse_idea("task app")

        assert result.suggested_stack["language"] == "typescript"
        assert result.suggested_stack["frontend"] == "react"

    @patch("ai.idea_parser.call_ai")
    def test_parse_retries_on_invalid_json(self, mock_call: MagicMock) -> None:
        """Test that parse_idea retries once on None response (JSON failure)."""
        mock_call.side_effect = [None, MOCK_RESPONSE]
        result = parse_idea("task app")

        assert isinstance(result, ParsedIdea)
        assert mock_call.call_count == 2

    @patch("ai.idea_parser.call_ai")
    def test_parse_raises_on_persistent_failure(self, mock_call: MagicMock) -> None:
        """Test that parse_idea raises ValueError after two failed attempts."""
        mock_call.return_value = None
        with pytest.raises(ValueError, match="Failed to parse"):
            parse_idea("task app")

    @patch("ai.idea_parser.call_ai")
    def test_parse_passes_provider_claude(self, mock_call: MagicMock) -> None:
        """Test that provider='claude' is passed to call_ai."""
        mock_call.return_value = MOCK_RESPONSE
        parse_idea("task app", provider="claude")

        call_kwargs = mock_call.call_args
        assert call_kwargs.kwargs["provider"] == "claude"
        assert call_kwargs.kwargs["stage"] == "parse"

    @patch("ai.idea_parser.call_ai")
    def test_parse_passes_provider_gemini(self, mock_call: MagicMock) -> None:
        """Test that provider='gemini' is passed to call_ai."""
        mock_call.return_value = MOCK_RESPONSE
        parse_idea("task app", provider="gemini")

        call_kwargs = mock_call.call_args
        assert call_kwargs.kwargs["provider"] == "gemini"
