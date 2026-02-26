"""Tests for ai/question_engine.py — mock AI, test question ordering."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from ai.question_engine import generate_questions
from core.spec_builder import ParsedIdea, QuestionSet


MOCK_PARSED = ParsedIdea(
    app_type="fullstack",
    core_purpose="Task management with collaboration",
    features=["auth", "crud", "realtime"],
    integrations=["slack"],
    complexity="moderate",
    target_users="Dev teams",
    suggested_stack={"language": "typescript", "frontend": "react"},
    ai_target="both",
)

MOCK_RESPONSE = {
    "questions": [
        {
            "id": "q1",
            "question": "Will users have different roles?",
            "why_asking": "Collaboration requires role-based access",
            "impacts": ["auth_complexity", "database_schema"],
            "type": "choice",
            "options": ["admin/member only", "custom roles", "single role"],
            "default": "admin/member only",
            "required": True,
        },
        {
            "id": "q2",
            "question": "Do you need real-time notifications?",
            "why_asking": "Realtime feature implies WebSocket setup",
            "impacts": ["infrastructure", "frontend"],
            "type": "boolean",
            "options": [],
            "default": "yes",
            "required": True,
        },
    ],
    "total_questions": 2,
    "estimated_minutes": 1,
}


class TestGenerateQuestions:
    """Tests for the generate_questions function."""

    @patch("ai.question_engine.call_ai")
    def test_generates_question_set(self, mock_call: MagicMock) -> None:
        """Test that a valid QuestionSet is returned."""
        mock_call.return_value = MOCK_RESPONSE
        result = generate_questions(MOCK_PARSED)

        assert isinstance(result, QuestionSet)
        assert len(result.questions) == 2
        assert result.total_questions == 2

    @patch("ai.question_engine.call_ai")
    def test_question_fields(self, mock_call: MagicMock) -> None:
        """Test that question fields are correctly populated."""
        mock_call.return_value = MOCK_RESPONSE
        result = generate_questions(MOCK_PARSED)

        q1 = result.questions[0]
        assert q1.id == "q1"
        assert q1.type == "choice"
        assert len(q1.options) == 3
        assert q1.required is True

    @patch("ai.question_engine.call_ai")
    def test_question_ordering(self, mock_call: MagicMock) -> None:
        """Test that questions maintain their order."""
        mock_call.return_value = MOCK_RESPONSE
        result = generate_questions(MOCK_PARSED)

        assert result.questions[0].id == "q1"
        assert result.questions[1].id == "q2"

    @patch("ai.question_engine.call_ai")
    def test_passes_provider(self, mock_call: MagicMock) -> None:
        """Test model selection via provider parameter."""
        mock_call.return_value = MOCK_RESPONSE
        generate_questions(MOCK_PARSED, provider="gemini")

        assert mock_call.call_args.kwargs["provider"] == "gemini"
        assert mock_call.call_args.kwargs["stage"] == "questions"

    @patch("ai.question_engine.call_ai")
    def test_retry_on_json_failure(self, mock_call: MagicMock) -> None:
        """Test retry on None response (JSON failure)."""
        mock_call.side_effect = [None, MOCK_RESPONSE]
        result = generate_questions(MOCK_PARSED)
        assert isinstance(result, QuestionSet)
        assert mock_call.call_count == 2
