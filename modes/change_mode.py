"""CHANGE mode — smart context injection for code changes.

Pipeline:
1. User describes what they want to change
2. [AI] Understand change → identify affected modules/files
3. [Python] Read memory → find relevant files
4. [Python] Load ONLY relevant files (not full codebase)
5. [Python] Build minimal context package (compressed)
6. [Python] Inject context into CLAUDE.md / GEMINI.md
7. Show token savings
"""

from __future__ import annotations

import os
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt
from rich.progress import SpinnerColumn, TextColumn, Progress
from rich.table import Table

from builders.claude_builder import ClaudeBuilder
from builders.gemini_builder import GeminiBuilder
from core.constants import HAIKU, GEMINI_FLASH, PROVIDER_CLAUDE, PROVIDER_GEMINI, PREFLIGHT_DIR
from core.token_counter import count_tokens, format_savings
from memory.context_finder import ContextFinder
from memory.file_indexer import FileIndexer
from memory.memory_updater import MemoryUpdater

console = Console()


def run_change(
    project_root: Path | None = None,
    *,
    provider: str = PROVIDER_CLAUDE,
) -> None:
    """Run the smart change pipeline.

    Args:
        project_root: Project directory. Defaults to cwd.
        provider: AI provider to use (``"claude"`` or ``"gemini"``).
    """
    if project_root is None:
        project_root = Path.cwd()

    # Validate .preflight/ exists
    preflight_dir = project_root / PREFLIGHT_DIR
    if not preflight_dir.exists():
        console.print(
            "[red]✗ No .preflight/ found. Run [bold]preflight setup[/bold] first.[/red]"
        )
        return

    provider_label = provider.capitalize()

    # ── Header ──────────────────────────────────────────────
    console.print()
    console.print(
        Panel(
            f"[bold cyan]🔧 Preflight AI — Smart Change Mode[/bold cyan]\n"
            f"[dim]Provider: {provider_label}[/dim]",
            border_style="cyan",
        )
    )
    console.print()

    # ── Get change description ──────────────────────────────
    change_desc = Prompt.ask("[bold]What do you want to change?[/bold]")
    if not change_desc.strip():
        console.print("[red]✗ No change described. Aborting.[/red]")
        return

    # ── Analyze change ──────────────────────────────────────
    finder = ContextFinder(project_root)

    with _spinner(f"Analyzing change ({provider_label})..."):
        analysis = finder.analyze_change(change_desc, provider=provider)
    console.print("[green]Analyzing change ✅[/green]")

    # ── Build context ───────────────────────────────────────
    with _spinner("Finding relevant files..."):
        context = finder.build_context(analysis)
    console.print("[green]Finding relevant files ✅[/green]")

    # ── Show loaded files ───────────────────────────────────
    file_table = Table(title="📂 Context Loaded (Surgical Precision)", border_style="blue")
    file_table.add_column("File", style="cyan")
    file_table.add_column("Tokens", justify="right")

    for fpath, content in context.files.items():
        tokens = count_tokens(content)
        file_table.add_row(fpath, f"{tokens:,}")

    console.print(file_table)

    # ── Get full codebase token count ───────────────────────
    indexer = FileIndexer(project_root)
    index = indexer.load()
    full_tokens = index.get("total_tokens_if_full_read", 0)

    # ── Show savings ────────────────────────────────────────
    cost_model = GEMINI_FLASH if provider == PROVIDER_GEMINI else HAIKU
    savings_table = format_savings(context.total_tokens, full_tokens, cost_model)
    console.print(savings_table)

    # ── Inject context ──────────────────────────────────────
    ai_target = os.environ.get("PREFLIGHT_AI_TARGET", "both")
    injection_text = context.to_injection_text()

    if ai_target in ("claude", "both"):
        ClaudeBuilder(project_root).inject_context(injection_text)
    if ai_target in ("gemini", "both"):
        GeminiBuilder(project_root).inject_context(injection_text)

    # ── Next step ───────────────────────────────────────────
    next_cmd = "claude  OR  gemini" if ai_target == "both" else ai_target
    console.print(f"\nRun: [bold cyan]{next_cmd}[/bold cyan]")

    # ── Update memory ───────────────────────────────────────
    updater = MemoryUpdater(project_root)
    updater.update_after_change(
        change_description=change_desc,
        analysis=analysis,
        tokens_used=context.total_tokens,
        full_codebase_tokens=full_tokens,
    )


def _spinner(message: str) -> "_SpinnerContext":
    """Create a Rich progress spinner context manager."""
    progress = Progress(
        SpinnerColumn(),
        TextColumn(f"[bold]{message}[/bold]"),
        console=console,
        transient=True,
    )
    return _SpinnerContext(progress, message)


class _SpinnerContext:
    """Context manager that shows a spinner while work happens."""

    def __init__(self, progress: Progress, message: str) -> None:
        self._progress = progress
        self._message = message

    def __enter__(self) -> Progress:
        self._progress.start()
        self._task_id = self._progress.add_task(self._message)
        return self._progress

    def __exit__(self, *args: object) -> None:
        self._progress.stop()
