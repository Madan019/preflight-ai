"""Tests for core/token_counter.py — test cost calculations."""

from __future__ import annotations

import pytest

from core.token_counter import count_tokens, estimate_cost, format_savings
from core.constants import HAIKU, SONNET


class TestCountTokens:
    """Tests for the count_tokens function."""

    def test_empty_string(self) -> None:
        assert count_tokens("") == 0

    def test_simple_text(self) -> None:
        tokens = count_tokens("Hello, world!")
        assert tokens > 0
        assert tokens < 10

    def test_longer_text(self) -> None:
        text = "The quick brown fox jumps over the lazy dog. " * 10
        tokens = count_tokens(text)
        assert tokens > 50

    def test_code_counting(self) -> None:
        code = "def hello():\n    return 'world'\n"
        tokens = count_tokens(code)
        assert tokens > 5


class TestEstimateCost:
    """Tests for the estimate_cost function."""

    def test_haiku_cost(self) -> None:
        cost = estimate_cost(1_000_000, 0, HAIKU)
        assert cost == pytest.approx(1.00, abs=0.01)

    def test_sonnet_cost(self) -> None:
        cost = estimate_cost(1_000_000, 0, SONNET)
        assert cost == pytest.approx(3.00, abs=0.01)

    def test_output_cost(self) -> None:
        cost = estimate_cost(0, 1_000_000, HAIKU)
        assert cost == pytest.approx(5.00, abs=0.01)

    def test_cached_input(self) -> None:
        cost = estimate_cost(0, 0, HAIKU, cached_input_tokens=1_000_000)
        assert cost == pytest.approx(0.10, abs=0.01)

    def test_unknown_model(self) -> None:
        cost = estimate_cost(1000, 1000, "unknown-model")
        assert cost == 0.0

    def test_zero_tokens(self) -> None:
        cost = estimate_cost(0, 0, HAIKU)
        assert cost == 0.0


class TestFormatSavings:
    """Tests for the format_savings function."""

    def test_returns_table(self) -> None:
        from rich.table import Table

        table = format_savings(1000, 10000, HAIKU)
        assert isinstance(table, Table)

    def test_zero_full_codebase(self) -> None:
        """Should not crash on zero full codebase."""
        table = format_savings(0, 0, HAIKU)
        assert table is not None
