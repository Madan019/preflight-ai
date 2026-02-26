"""Tests for memory/context_finder.py — test minimal context selection."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from memory.context_finder import ContextFinder, ChangeAnalysis, ContextPackage


@pytest.fixture()
def project_with_index(tmp_path: Path) -> Path:
    """Create a project with pre-built index and memory."""
    # Source files
    auth = tmp_path / "src" / "auth"
    auth.mkdir(parents=True)
    (auth / "login.py").write_text("def login(): pass")
    (auth / "register.py").write_text("def register(): pass")

    api = tmp_path / "src" / "api"
    api.mkdir(parents=True)
    (api / "users.py").write_text("from auth.login import login\ndef get_users(): pass")

    # Pre-built index
    preflight = tmp_path / ".preflight"
    preflight.mkdir()
    index = {
        "indexed_at": "2024-01-01T00:00:00",
        "total_files": 3,
        "total_tokens_if_full_read": 100,
        "files": {
            "src/auth/login.py": {
                "purpose": "User login",
                "module": "auth",
                "imports": [],
                "exports": ["login"],
                "token_count": 30,
            },
            "src/auth/register.py": {
                "purpose": "User registration",
                "module": "auth",
                "imports": [],
                "exports": ["register"],
                "token_count": 30,
            },
            "src/api/users.py": {
                "purpose": "User API",
                "module": "api",
                "imports": ["auth.login"],
                "exports": ["get_users"],
                "token_count": 40,
            },
        },
        "modules": {
            "auth": ["src/auth/login.py", "src/auth/register.py"],
            "api": ["src/api/users.py"],
        },
    }
    (preflight / "file-index.json").write_text(json.dumps(index))
    (preflight / "memory.json").write_text(json.dumps({
        "project_name": "test",
        "created_at": "2024-01-01",
        "last_updated": "2024-01-01",
        "stack": {},
        "ai_target": "both",
        "modules": {},
        "decisions": [
            {"decision": "Use JWT", "reason": "Standard", "date": "2024-01-01", "affects": ["auth"]},
        ],
        "change_history": [],
    }))

    return tmp_path


class TestChangeAnalysis:
    """Tests for the ChangeAnalysis dataclass."""

    def test_from_dict(self) -> None:
        """Test creating ChangeAnalysis from dict."""
        data = {
            "change_type": "feature",
            "affected_modules": ["auth"],
            "affected_files": ["src/auth/login.py"],
            "needs_new_files": True,
            "new_files_needed": ["src/auth/forgot.py"],
            "estimated_complexity": "moderate",
        }
        analysis = ChangeAnalysis.from_dict(data)
        assert analysis.change_type == "feature"
        assert "auth" in analysis.affected_modules
        assert analysis.needs_new_files is True


class TestContextPackage:
    """Tests for the ContextPackage dataclass."""

    def test_to_injection_text(self) -> None:
        """Test that injection text is properly formatted."""
        package = ContextPackage(
            files={"login.py": "def login(): pass"},
            decisions=[{"decision": "Use JWT", "reason": "Standard"}],
            module_summaries={"auth": "Auth module files"},
            total_tokens=100,
        )
        text = package.to_injection_text()
        assert "login.py" in text
        assert "Use JWT" in text
        assert "Auth module files" in text


class TestContextFinder:
    """Tests for the ContextFinder class."""

    def test_build_context_loads_affected_files(
        self, project_with_index: Path
    ) -> None:
        """Test that build_context loads only affected files."""
        finder = ContextFinder(project_with_index)
        analysis = ChangeAnalysis(
            affected_modules=["auth"],
            affected_files=["src/auth/login.py"],
        )
        context = finder.build_context(analysis)

        assert "src/auth/login.py" in context.files
        assert context.total_tokens > 0

    def test_build_context_loads_decisions(
        self, project_with_index: Path
    ) -> None:
        """Test that relevant decisions are loaded."""
        finder = ContextFinder(project_with_index)
        analysis = ChangeAnalysis(
            affected_modules=["auth"],
            affected_files=["src/auth/login.py"],
        )
        context = finder.build_context(analysis)

        assert len(context.decisions) == 1
        assert context.decisions[0]["decision"] == "Use JWT"

    def test_build_context_includes_module_summary(
        self, project_with_index: Path
    ) -> None:
        """Test that module summaries are included."""
        finder = ContextFinder(project_with_index)
        analysis = ChangeAnalysis(
            affected_modules=["auth"],
            affected_files=["src/auth/login.py"],
        )
        context = finder.build_context(analysis)

        assert "auth" in context.module_summaries

    @patch("memory.context_finder.call_ai")
    def test_analyze_change_passes_provider(
        self, mock_call: MagicMock, project_with_index: Path
    ) -> None:
        """Test that analyze_change forwards the provider parameter."""
        mock_call.return_value = {
            "change_type": "feature",
            "affected_modules": ["auth"],
            "affected_files": ["src/auth/login.py"],
        }
        finder = ContextFinder(project_with_index)
        finder.analyze_change("add forgot password", provider="gemini")

        assert mock_call.call_args.kwargs["provider"] == "gemini"
