"""Token counting and cost estimation utilities."""

from __future__ import annotations

import tiktoken
from rich.table import Table
from rich.console import Console

from core.constants import COSTS_PER_MILLION

# ---------------------------------------------------------------------------
# Encoding singleton
# ---------------------------------------------------------------------------
_ENCODING: tiktoken.Encoding | None = None


def _get_encoding() -> tiktoken.Encoding:
    """Return a cached cl100k_base encoding (used by Claude models)."""
    global _ENCODING  # noqa: PLW0603
    if _ENCODING is None:
        _ENCODING = tiktoken.get_encoding("cl100k_base")
    return _ENCODING


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def count_tokens(text: str) -> int:
    """Count the number of tokens in *text* using cl100k_base encoding.

    Args:
        text: The string to tokenise.

    Returns:
        Token count.
    """
    return len(_get_encoding().encode(text))


def estimate_cost(
    input_tokens: int,
    output_tokens: int,
    model: str,
    *,
    cached_input_tokens: int = 0,
) -> float:
    """Estimate the USD cost for a single API call.

    Args:
        input_tokens: Non-cached input tokens.
        output_tokens: Output tokens generated.
        model: Model identifier (must be a key in ``COSTS_PER_MILLION``).
        cached_input_tokens: Input tokens served from cache.

    Returns:
        Estimated cost in USD.
    """
    costs = COSTS_PER_MILLION.get(model)
    if costs is None:
        return 0.0

    cost = (
        (input_tokens / 1_000_000) * costs["input"]
        + (output_tokens / 1_000_000) * costs["output"]
        + (cached_input_tokens / 1_000_000) * costs["cache_read"]
    )
    return round(cost, 6)


def format_savings(
    tokens_sent: int,
    full_codebase_tokens: int,
    model: str,
) -> Table:
    """Build a Rich table showing token savings vs reading the full codebase.

    Args:
        tokens_sent: Actual tokens sent to the AI.
        full_codebase_tokens: Hypothetical tokens if full codebase was sent.
        model: Model identifier for cost calculation.

    Returns:
        A ``rich.table.Table`` ready for ``console.print()``.
    """
    saved = full_codebase_tokens - tokens_sent
    pct = (saved / full_codebase_tokens * 100) if full_codebase_tokens > 0 else 0.0
    cost_full = estimate_cost(full_codebase_tokens, 0, model)
    cost_actual = estimate_cost(tokens_sent, 0, model)
    cost_saved = cost_full - cost_actual

    table = Table(title="Token Savings", show_header=False, border_style="green")
    table.add_column("Metric", style="bold")
    table.add_column("Value", justify="right")

    table.add_row("Sent to AI", f"{tokens_sent:,} tokens")
    table.add_row("Full codebase", f"{full_codebase_tokens:,} tokens")
    table.add_row("Saved", f"{pct:.0f}% ({saved:,} tokens)")
    table.add_row("Cost (full)", f"${cost_full:.4f}")
    table.add_row("Cost (actual)", f"${cost_actual:.4f}")
    table.add_row("Money saved", f"${cost_saved:.4f}")

    return table


def print_savings(
    tokens_sent: int,
    full_codebase_tokens: int,
    model: str,
) -> None:
    """Print the token savings table to the console.

    Args:
        tokens_sent: Actual tokens sent.
        full_codebase_tokens: Full codebase tokens.
        model: Model identifier.
    """
    console = Console()
    table = format_savings(tokens_sent, full_codebase_tokens, model)
    console.print(table)
