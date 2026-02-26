"""Integration tests — full setup + change pipelines with mocked AI calls."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from core.spec_builder import ProjectSpec, StackSpec
from ai.file_generator import GeneratedFiles
from builders.claude_builder import ClaudeBuilder
from builders.gemini_builder import GeminiBuilder
from builders.preflight_builder import PreflightBuilder
from memory.memory_manager import MemoryManager
from memory.file_indexer import FileIndexer


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture()
def empty_project(tmp_path: Path) -> Path:
    """Create an empty project directory with one source file."""
    (tmp_path / "app.py").write_text("print('hello')\n")
    return tmp_path


@pytest.fixture()
def sample_spec() -> ProjectSpec:
    """Create a sample ProjectSpec for testing."""
    return ProjectSpec(
        app_type="web",
        core_purpose="A simple web app",
        features=["auth", "crud"],
        complexity="simple",
        ai_target="both",
        stack=StackSpec(
            language="python",
            frontend="none",
            backend="fastapi",
            database="postgres",
        ),
        recommended_rules=["code-style", "backend", "testing"],
    )


@pytest.fixture()
def sample_generated() -> GeneratedFiles:
    """Create sample generated files."""
    return GeneratedFiles(
        claude={
            "CLAUDE_md": "# Test Project\nPython + FastAPI + Postgres\n",
            "settings_json": {"permissions": {"allow": ["Read files"]}},
            "rules": {
                "code_style": "# Code Style\n- Use type hints\n",
                "backend": "# Backend\n- Use FastAPI patterns\n",
            },
            "agents_md": "# Agents\n## test-runner\nRuns tests\n",
            "skills_md": "# Skills\n## /run-tests\nRun pytest\n",
        },
        gemini={
            "GEMINI_md": "# Test Project\nPython + FastAPI\n",
            "settings_json": {"project": "test"},
        },
        project={
            "PLAN_md": "# Build Plan\n1. Setup\n2. Build\n",
        },
    )


# ---------------------------------------------------------------------------
# Integration: .claude/ folder generation
# ---------------------------------------------------------------------------
class TestClaudeFolderGeneration:
    """Test full .claude/ folder generation."""

    def test_builds_complete_folder(
        self, empty_project: Path, sample_generated: GeneratedFiles
    ) -> None:
        """Test that ClaudeBuilder creates all expected files."""
        builder = ClaudeBuilder(empty_project)
        count = builder.build(sample_generated)

        assert count >= 4  # CLAUDE.md, settings.json, rules, agents/skills
        assert (empty_project / ".claude" / "CLAUDE.md").exists()
        assert (empty_project / ".claude" / "settings.json").exists()
        assert (empty_project / ".claude" / "rules" / "code-style.md").exists()

    def test_claude_md_content(
        self, empty_project: Path, sample_generated: GeneratedFiles
    ) -> None:
        """Test CLAUDE.md has correct content."""
        ClaudeBuilder(empty_project).build(sample_generated)
        content = (empty_project / ".claude" / "CLAUDE.md").read_text()
        assert "Test Project" in content


# ---------------------------------------------------------------------------
# Integration: .gemini/ folder generation
# ---------------------------------------------------------------------------
class TestGeminiFolderGeneration:
    """Test full .gemini/ folder generation."""

    def test_builds_gemini_folder(
        self, empty_project: Path, sample_generated: GeneratedFiles
    ) -> None:
        """Test that GeminiBuilder creates all expected files."""
        builder = GeminiBuilder(empty_project)
        count = builder.build(sample_generated)

        assert count == 2
        assert (empty_project / ".gemini" / "GEMINI.md").exists()
        assert (empty_project / ".gemini" / "settings.json").exists()


# ---------------------------------------------------------------------------
# Integration: .preflight/ folder
# ---------------------------------------------------------------------------
class TestPreflightFolderGeneration:
    """Test .preflight/ folder creation and population."""

    def test_builds_preflight_folder(
        self, empty_project: Path, sample_spec: ProjectSpec
    ) -> None:
        """Test that PreflightBuilder creates memory + index + cache."""
        builder = PreflightBuilder(empty_project)
        count = builder.build(sample_spec)

        assert count == 3
        assert (empty_project / ".preflight" / "memory.json").exists()
        assert (empty_project / ".preflight" / "file-index.json").exists()
        assert (empty_project / ".preflight" / "context-cache.json").exists()

    def test_memory_contains_stack(
        self, empty_project: Path, sample_spec: ProjectSpec
    ) -> None:
        """Test that memory.json contains the project stack."""
        PreflightBuilder(empty_project).build(sample_spec)

        mm = MemoryManager(empty_project)
        data = mm.load()
        assert data["stack"]["language"] == "python"
        assert data["stack"]["backend"] == "fastapi"


# ---------------------------------------------------------------------------
# Integration: Context injection
# ---------------------------------------------------------------------------
class TestContextInjection:
    """Test context injection into existing config files."""

    def test_claude_context_injection(
        self, empty_project: Path, sample_generated: GeneratedFiles
    ) -> None:
        """Test injecting change context into CLAUDE.md."""
        builder = ClaudeBuilder(empty_project)
        builder.build(sample_generated)
        builder.inject_context("## Auth Changes\nModified login flow")

        content = (empty_project / ".claude" / "CLAUDE.md").read_text()
        assert "PREFLIGHT CONTEXT START" in content
        assert "Auth Changes" in content

    def test_context_replacement(
        self, empty_project: Path, sample_generated: GeneratedFiles
    ) -> None:
        """Test that re-injection replaces old context."""
        builder = ClaudeBuilder(empty_project)
        builder.build(sample_generated)
        builder.inject_context("First context")
        builder.inject_context("Second context")

        content = (empty_project / ".claude" / "CLAUDE.md").read_text()
        assert "First context" not in content
        assert "Second context" in content

    def test_gemini_context_injection(
        self, empty_project: Path, sample_generated: GeneratedFiles
    ) -> None:
        """Test injecting context into GEMINI.md."""
        GeminiBuilder(empty_project).build(sample_generated)
        GeminiBuilder(empty_project).inject_context("Change context here")

        content = (empty_project / ".gemini" / "GEMINI.md").read_text()
        assert "Change context here" in content


# ---------------------------------------------------------------------------
# Integration: Memory update after change
# ---------------------------------------------------------------------------
class TestMemoryUpdateAfterChange:
    """Test that memory is properly updated after changes."""

    def test_change_recorded_in_history(self, empty_project: Path) -> None:
        """Test that a change is recorded in change_history."""
        mm = MemoryManager(empty_project)
        mm.load()
        mm.add_change("Added login", ["auth/login.py"], 300, 5000)
        mm.save()

        mm2 = MemoryManager(empty_project)
        data = mm2.load()
        assert len(data["change_history"]) == 1
        assert data["change_history"][0]["tokens_saved"] == 5000
