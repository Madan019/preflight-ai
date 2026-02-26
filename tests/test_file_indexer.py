"""Tests for memory/file_indexer.py — test with sample project structures."""

from __future__ import annotations

from pathlib import Path

import pytest

from memory.file_indexer import FileIndexer


@pytest.fixture()
def sample_project(tmp_path: Path) -> Path:
    """Create a sample project structure for indexing."""
    # Python files
    src = tmp_path / "src" / "auth"
    src.mkdir(parents=True)
    (src / "login.py").write_text(
        'from database import get_user\n\ndef login_user(email, password):\n    """Login user."""\n    pass\n'
    )
    (src / "register.py").write_text(
        'from database import create_user\n\ndef register_user(email, password):\n    pass\n'
    )

    api = tmp_path / "src" / "api"
    api.mkdir(parents=True)
    (api / "users.py").write_text(
        'from auth.login import login_user\n\ndef get_users():\n    pass\n'
    )

    # JS file
    (tmp_path / "app.js").write_text(
        'import { Router } from "express";\nconst app = Router();\nexport default app;\n'
    )

    # Ignored dir
    node_modules = tmp_path / "node_modules" / "pkg"
    node_modules.mkdir(parents=True)
    (node_modules / "index.js").write_text("module.exports = {};")

    return tmp_path


class TestFileIndexer:
    """Tests for the FileIndexer class."""

    def test_index_counts_files(self, sample_project: Path) -> None:
        """Test that index counts correct number of files."""
        indexer = FileIndexer(sample_project)
        result = indexer.index()

        # Should find 4 files (login.py, register.py, users.py, app.js)
        # node_modules should be skipped
        assert result["total_files"] == 4

    def test_index_skips_ignored_dirs(self, sample_project: Path) -> None:
        """Test that node_modules is skipped."""
        indexer = FileIndexer(sample_project)
        result = indexer.index()

        files = result["files"]
        for path in files:
            assert "node_modules" not in path

    def test_index_detects_python_imports(self, sample_project: Path) -> None:
        """Test that Python imports are detected."""
        indexer = FileIndexer(sample_project)
        result = indexer.index()

        login_file = None
        for path, info in result["files"].items():
            if "login.py" in path:
                login_file = info
                break

        assert login_file is not None
        assert "database" in login_file["imports"]

    def test_index_detects_python_exports(self, sample_project: Path) -> None:
        """Test that Python function names are detected as exports."""
        indexer = FileIndexer(sample_project)
        result = indexer.index()

        login_file = None
        for path, info in result["files"].items():
            if "login.py" in path:
                login_file = info
                break

        assert login_file is not None
        assert "login_user" in login_file["exports"]

    def test_index_assigns_modules(self, sample_project: Path) -> None:
        """Test that files are assigned to modules."""
        indexer = FileIndexer(sample_project)
        result = indexer.index()

        modules = result["modules"]
        assert "auth" in modules or "src" in modules

    def test_index_counts_tokens(self, sample_project: Path) -> None:
        """Test that total token count is > 0."""
        indexer = FileIndexer(sample_project)
        result = indexer.index()

        assert result["total_tokens_if_full_read"] > 0

    def test_index_writes_file(self, sample_project: Path) -> None:
        """Test that file-index.json is written."""
        indexer = FileIndexer(sample_project)
        indexer.index()

        index_path = sample_project / ".preflight" / "file-index.json"
        assert index_path.exists()

    def test_load_existing_index(self, sample_project: Path) -> None:
        """Test loading a previously written index."""
        indexer = FileIndexer(sample_project)
        indexer.index()

        indexer2 = FileIndexer(sample_project)
        result = indexer2.load()
        assert result["total_files"] == 4

    def test_load_missing_index(self, tmp_path: Path) -> None:
        """Test loading when no index exists."""
        indexer = FileIndexer(tmp_path)
        result = indexer.load()
        assert result["total_files"] == 0
