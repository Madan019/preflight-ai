"""Tests for ai/answer_analyzer.py — mock AI, test gap detection."""

from __future__ import annotations

import json
from unittest.mock import MagicMock, patch

import pytest

from ai.answer_analyzer import analyze_answers
from core.spec_builder import AnalysisResult, QuestionSet, Question


MOCK_QUESTIONS = QuestionSet(
    questions=[
        Question(
            id="q1",
            question="Will users have roles?",
            why_asking="Collaboration needs roles",
            impacts=["auth"],
            type="choice",
            options=["admin/member", "custom", "single"],
            default="admin/member",
        ),
        Question(
            id="q2",
            question="Need real-time?",
            why_asking="Realtime feature",
            impacts=["infra"],
            type="boolean",
        ),
    ],
    total_questions=2,
)

MOCK_ANSWERS = {"q1": "custom roles", "q2": "yes"}

MOCK_RESPONSE = {
    "complete_spec": {
        "app_type": "fullstack",
        "features": ["auth", "crud", "realtime", "rbac"],
        "stack": {"language": "typescript", "frontend": "react", "backend": "express"},
        "auth": {"method": "jwt", "roles": True},
        "database": {"type": "postgres"},
        "integrations": ["slack"],
        "deployment": {"provider": "vercel"},
    },
    "gaps_auto_filled": [
        {
            "gap": "No error monitoring",
            "filled_with": "sentry",
            "reason": "Production app needs error tracking",
        }
    ],
    "contradictions_resolved": [],
    "implicit_requirements_added": ["rate_limiting", "email_service"],
    "recommended_rules": ["code-style", "frontend", "backend", "testing"],
    "recommended_agents": ["test-runner"],
    "recommended_skills": ["run-tests", "deploy"],
    "confidence_score": 0.92,
}


class TestAnalyzeAnswers:
    """Tests for the analyze_answers function."""

    @patch("ai.answer_analyzer.call_ai")
    def test_returns_analysis_result(self, mock_call: MagicMock) -> None:
        """Test that a valid AnalysisResult is returned."""
        mock_call.return_value = MOCK_RESPONSE
        result = analyze_answers(MOCK_QUESTIONS, MOCK_ANSWERS, "{}")

        assert isinstance(result, AnalysisResult)
        assert result.confidence_score == 0.92

    @patch("ai.answer_analyzer.call_ai")
    def test_gap_detection(self, mock_call: MagicMock) -> None:
        """Test that auto-filled gaps are captured."""
        mock_call.return_value = MOCK_RESPONSE
        result = analyze_answers(MOCK_QUESTIONS, MOCK_ANSWERS, "{}")

        assert len(result.gaps_auto_filled) == 1
        assert result.gaps_auto_filled[0].filled_with == "sentry"

    @patch("ai.answer_analyzer.call_ai")
    def test_implicit_requirements(self, mock_call: MagicMock) -> None:
        """Test that implicit requirements are passed through."""
        mock_call.return_value = MOCK_RESPONSE
        result = analyze_answers(MOCK_QUESTIONS, MOCK_ANSWERS, "{}")

        assert "rate_limiting" in result.implicit_requirements_added

    @patch("ai.answer_analyzer.call_ai")
    def test_recommended_rules(self, mock_call: MagicMock) -> None:
        """Test that recommended rules are correct."""
        mock_call.return_value = MOCK_RESPONSE
        result = analyze_answers(MOCK_QUESTIONS, MOCK_ANSWERS, "{}")

        assert "code-style" in result.recommended_rules

    @patch("ai.answer_analyzer.call_ai")
    def test_complete_spec_stack(self, mock_call: MagicMock) -> None:
        """Test that complete_spec contains stack info."""
        mock_call.return_value = MOCK_RESPONSE
        result = analyze_answers(MOCK_QUESTIONS, MOCK_ANSWERS, "{}")

        assert result.complete_spec["stack"]["language"] == "typescript"

    @patch("ai.answer_analyzer.call_ai")
    def test_passes_provider_gemini(self, mock_call: MagicMock) -> None:
        """Test that provider='gemini' is forwarded."""
        mock_call.return_value = MOCK_RESPONSE
        analyze_answers(MOCK_QUESTIONS, MOCK_ANSWERS, "{}", provider="gemini")

        assert mock_call.call_args.kwargs["provider"] == "gemini"
