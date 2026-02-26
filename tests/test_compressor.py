"""Tests for core/compressor.py — test verbose content stripping."""

from __future__ import annotations

import pytest

from core.compressor import compress_content, compress_file_summary, should_compress
from pathlib import Path


class TestCompressContent:
    """Tests for the compress_content function."""

    def test_strips_python_docstrings(self) -> None:
        """Test that triple-quoted docstrings are removed."""
        code = '''def foo():\n    """This is a docstring."""\n    return 1\n'''
        result = compress_content(code)
        assert '"""' not in result
        assert "return 1" in result

    def test_strips_js_block_comments(self) -> None:
        """Test that /* */ comments are removed."""
        code = "/* This is a comment */\nconst x = 1;\n"
        result = compress_content(code)
        assert "/*" not in result
        assert "const x = 1" in result

    def test_collapses_blank_lines(self) -> None:
        """Test that excessive blank lines are collapsed."""
        text = "line1\n\n\n\n\nline2\n"
        result = compress_content(text)
        assert "\n\n\n" not in result
        assert "line1" in result
        assert "line2" in result

    def test_aggressive_strips_line_comments(self) -> None:
        """Test that aggressive mode strips single-line comments."""
        code = "x = 1  # set x\ny = 2\n"
        result = compress_content(code, aggressive=True)
        assert "# set x" not in result
        assert "x = 1" in result

    def test_not_aggressive_keeps_line_comments(self) -> None:
        """Test that non-aggressive mode keeps single-line comments."""
        code = "x = 1  # set x\n"
        result = compress_content(code, aggressive=False)
        assert "# set x" in result

    def test_returns_trailing_newline(self) -> None:
        """Test that result always ends with newline."""
        result = compress_content("hello")
        assert result.endswith("\n")


class TestCompressFileSummary:
    """Tests for the compress_file_summary function."""

    def test_summary_of_valid_file(self, tmp_path: Path) -> None:
        """Test summary generation from a real file."""
        f = tmp_path / "example.py"
        f.write_text("def hello():\n    return 'world'\n")
        summary = compress_file_summary(f)
        assert "example.py" in summary
        assert "tokens" in summary

    def test_summary_of_empty_file(self, tmp_path: Path) -> None:
        """Test summary of an empty file."""
        f = tmp_path / "empty.py"
        f.write_text("")
        summary = compress_file_summary(f)
        assert "empty" in summary.lower()

    def test_summary_of_missing_file(self, tmp_path: Path) -> None:
        """Test summary when file doesn't exist."""
        f = tmp_path / "nope.py"
        summary = compress_file_summary(f)
        assert "Could not read" in summary


class TestShouldCompress:
    """Tests for the should_compress function."""

    def test_above_threshold(self) -> None:
        assert should_compress(3000, 2000) is True

    def test_below_threshold(self) -> None:
        assert should_compress(1000, 2000) is False

    def test_at_threshold(self) -> None:
        assert should_compress(2000, 2000) is False
