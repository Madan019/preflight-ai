"""Tests for memory/memory_manager.py — read/write/update operations."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from memory.memory_manager import MemoryManager


@pytest.fixture()
def tmp_project(tmp_path: Path) -> Path:
    """Create a temporary project directory."""
    return tmp_path


class TestMemoryManager:
    """Tests for the MemoryManager class."""

    def test_load_creates_default(self, tmp_project: Path) -> None:
        """Test that load creates default memory when file is missing."""
        mm = MemoryManager(tmp_project)
        data = mm.load()

        assert data["project_name"] == tmp_project.name
        assert "modules" in data
        assert "decisions" in data
        assert "change_history" in data

    def test_save_and_load_roundtrip(self, tmp_project: Path) -> None:
        """Test that data survives a save/load cycle."""
        mm = MemoryManager(tmp_project)
        mm.load()
        mm.set_module("auth", status="complete", files=["auth.py"], purpose="Auth")
        mm.save()

        # Load in a new instance
        mm2 = MemoryManager(tmp_project)
        data = mm2.load()
        assert data["modules"]["auth"]["status"] == "complete"
        assert "auth.py" in data["modules"]["auth"]["files"]

    def test_atomic_write(self, tmp_project: Path) -> None:
        """Test that save uses atomic write (file exists after save)."""
        mm = MemoryManager(tmp_project)
        mm.load()
        mm.save()

        memory_path = tmp_project / ".preflight" / "memory.json"
        assert memory_path.exists()

        # Verify it's valid JSON
        data = json.loads(memory_path.read_text())
        assert "project_name" in data

    def test_corrupt_file_recovery(self, tmp_project: Path) -> None:
        """Test that corrupt memory.json is backed up and rebuilt."""
        preflight_dir = tmp_project / ".preflight"
        preflight_dir.mkdir()
        (preflight_dir / "memory.json").write_text("{{not valid json}}")

        mm = MemoryManager(tmp_project)
        data = mm.load()

        # Should have recovered with default data
        assert "project_name" in data
        # Backup should exist
        assert (preflight_dir / "memory.json.bak").exists()

    def test_add_decision(self, tmp_project: Path) -> None:
        """Test adding a decision to memory."""
        mm = MemoryManager(tmp_project)
        mm.load()
        mm.add_decision(
            decision="Use bcrypt",
            reason="Industry standard",
            affects=["auth"],
        )

        assert len(mm.data["decisions"]) == 1
        assert mm.data["decisions"][0]["decision"] == "Use bcrypt"

    def test_add_change(self, tmp_project: Path) -> None:
        """Test recording a change."""
        mm = MemoryManager(tmp_project)
        mm.load()
        mm.add_change(
            description="Added login",
            files_changed=["auth/login.py"],
            tokens_used=300,
            tokens_saved=5000,
        )

        assert len(mm.data["change_history"]) == 1
        assert mm.data["change_history"][0]["tokens_saved"] == 5000

    def test_get_module(self, tmp_project: Path) -> None:
        """Test getting a module by name."""
        mm = MemoryManager(tmp_project)
        mm.load()
        mm.set_module("api", status="in_progress", purpose="REST API")

        mod = mm.get_module("api")
        assert mod is not None
        assert mod["status"] == "in_progress"
        assert mm.get_module("nonexistent") is None

    def test_get_decisions_for_modules(self, tmp_project: Path) -> None:
        """Test filtering decisions by module."""
        mm = MemoryManager(tmp_project)
        mm.load()
        mm.add_decision("Use JWT", "Standard", affects=["auth"])
        mm.add_decision("Use REST", "Simple", affects=["api"])

        auth_decisions = mm.get_decisions_for_modules(["auth"])
        assert len(auth_decisions) == 1
        assert auth_decisions[0]["decision"] == "Use JWT"

    def test_get_modules_for_files(self, tmp_project: Path) -> None:
        """Test finding modules that contain given files."""
        mm = MemoryManager(tmp_project)
        mm.load()
        mm.set_module("auth", files=["src/auth/login.py", "src/auth/register.py"])
        mm.set_module("api", files=["src/api/users.py"])

        result = mm.get_modules_for_files(["src/auth/login.py"])
        assert "auth" in result
        assert "api" not in result
