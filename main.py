"""Preflight AI — CLI entry point.

Commands:
  preflight setup          Full setup for new/existing project
  preflight change         Smart change mode
  preflight update         Re-generate config files
  preflight memory show    Show .preflight/memory.json
  preflight memory reset   Clear memory and re-index
  preflight index          Re-index codebase
  preflight savings        Show token savings dashboard
  preflight validate       Check .claude/ and .gemini/ for issues
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from core.constants import PREFLIGHT_DIR, PROVIDER_CLAUDE, PROVIDER_GEMINI

console = Console()

app = typer.Typer(
    name="preflight",
    help="🚀 Intelligent pre-flight layer for AI coding assistants",
    add_completion=False,
    no_args_is_help=True,
)

memory_app = typer.Typer(
    name="memory",
    help="Manage .preflight/memory.json",
    no_args_is_help=True,
)
app.add_typer(memory_app, name="memory")


def _version_callback(value: bool) -> None:
    """Print version and exit."""
    if value:
        console.print("[bold cyan]preflight-ai[/bold cyan] v0.1.0")
        raise typer.Exit()


def _default_provider() -> str:
    """Get default provider from env var or fall back to claude."""
    return os.environ.get("PREFLIGHT_PROVIDER", PROVIDER_CLAUDE)


@app.callback()
def main(
    version: bool = typer.Option(
        False,
        "--version",
        "-v",
        help="Show version and exit",
        callback=_version_callback,
        is_eager=True,
    ),
) -> None:
    """Preflight AI — optimize your AI coding sessions."""


# ---------------------------------------------------------------------------
# setup
# ---------------------------------------------------------------------------
@app.command()
def setup(
    path: str = typer.Argument(
        ".",
        help="Project directory (default: current directory)",
    ),
    provider: str = typer.Option(
        _default_provider(),
        "--provider",
        "-p",
        help="AI provider: claude or gemini",
    ),
) -> None:
    """Run full setup for a new or existing project."""
    from modes.setup_mode import run_setup

    provider = _validate_provider(provider)
    project_root = Path(path).resolve()
    if not project_root.is_dir():
        console.print(f"[red]✗ {project_root} is not a directory[/red]")
        raise typer.Exit(1)

    run_setup(project_root, provider=provider)


# ---------------------------------------------------------------------------
# change
# ---------------------------------------------------------------------------
@app.command()
def change(
    path: str = typer.Argument(
        ".",
        help="Project directory (default: current directory)",
    ),
    provider: str = typer.Option(
        _default_provider(),
        "--provider",
        "-p",
        help="AI provider: claude or gemini",
    ),
) -> None:
    """Smart change mode — surgical context injection."""
    from modes.change_mode import run_change

    provider = _validate_provider(provider)
    project_root = Path(path).resolve()
    if not project_root.is_dir():
        console.print(f"[red]✗ {project_root} is not a directory[/red]")
        raise typer.Exit(1)

    run_change(project_root, provider=provider)


# ---------------------------------------------------------------------------
# update
# ---------------------------------------------------------------------------
@app.command()
def update(
    path: str = typer.Argument(
        ".",
        help="Project directory (default: current directory)",
    ),
    provider: str = typer.Option(
        _default_provider(),
        "--provider",
        "-p",
        help="AI provider: claude or gemini",
    ),
) -> None:
    """Re-generate config files with current memory."""
    provider = _validate_provider(provider)
    project_root = Path(path).resolve()
    preflight_dir = project_root / PREFLIGHT_DIR

    if not preflight_dir.exists():
        console.print(
            "[red]✗ No .preflight/ found. Run [bold]preflight setup[/bold] first.[/red]"
        )
        raise typer.Exit(1)

    console.print(f"[yellow]Re-generating config files (provider: {provider})...[/yellow]")

    from memory.memory_manager import MemoryManager
    from core.spec_builder import ProjectSpec, StackSpec
    from ai.file_generator import generate_files
    from builders.claude_builder import ClaudeBuilder
    from builders.gemini_builder import GeminiBuilder

    memory = MemoryManager(project_root)
    data = memory.load()

    # Build a minimal spec from memory
    stack_data = data.get("stack", {})
    stack = StackSpec(
        language=stack_data.get("language", ""),
        frontend=stack_data.get("frontend"),
        backend=stack_data.get("backend"),
        database=stack_data.get("database"),
        auth=stack_data.get("auth"),
        hosting=stack_data.get("hosting"),
    )

    spec = ProjectSpec(
        core_purpose=data.get("project_name", ""),
        ai_target=data.get("ai_target", "both"),
        stack=stack,
    )

    generated = generate_files(spec, provider=provider)
    ClaudeBuilder(project_root).build(generated)
    GeminiBuilder(project_root).build(generated)

    console.print("[green]✅ Config files regenerated[/green]")


# ---------------------------------------------------------------------------
# memory show
# ---------------------------------------------------------------------------
@memory_app.command("show")
def memory_show(
    path: str = typer.Argument(
        ".",
        help="Project directory (default: current directory)",
    ),
) -> None:
    """Show .preflight/memory.json in readable format."""
    project_root = Path(path).resolve()

    from memory.memory_manager import MemoryManager

    memory = MemoryManager(project_root)
    data = memory.load()

    syntax = Syntax(
        json.dumps(data, indent=2),
        "json",
        theme="monokai",
        line_numbers=True,
    )
    console.print(
        Panel(syntax, title=".preflight/memory.json", border_style="blue")
    )


# ---------------------------------------------------------------------------
# memory reset
# ---------------------------------------------------------------------------
@memory_app.command("reset")
def memory_reset(
    path: str = typer.Argument(
        ".",
        help="Project directory (default: current directory)",
    ),
) -> None:
    """Clear memory and re-index codebase."""
    from rich.prompt import Confirm

    project_root = Path(path).resolve()

    if not Confirm.ask("[yellow]Reset all memory? This cannot be undone[/yellow]"):
        console.print("[dim]Cancelled.[/dim]")
        raise typer.Exit()

    import shutil

    preflight_dir = project_root / PREFLIGHT_DIR
    if preflight_dir.exists():
        shutil.rmtree(preflight_dir)
        console.print("[green]✅ .preflight/ cleared[/green]")

    # Re-index
    from memory.file_indexer import FileIndexer

    indexer = FileIndexer(project_root)
    indexer.index()
    console.print("[green]✅ Codebase re-indexed[/green]")


# ---------------------------------------------------------------------------
# index
# ---------------------------------------------------------------------------
@app.command()
def index(
    path: str = typer.Argument(
        ".",
        help="Project directory (default: current directory)",
    ),
) -> None:
    """Re-index codebase (use after big changes)."""
    project_root = Path(path).resolve()

    from memory.file_indexer import FileIndexer

    indexer = FileIndexer(project_root)
    result = indexer.index()
    console.print(
        f"[green]✅ Indexed {result['total_files']} files "
        f"({result['total_tokens_if_full_read']:,} tokens)[/green]"
    )


# ---------------------------------------------------------------------------
# savings
# ---------------------------------------------------------------------------
@app.command()
def savings(
    path: str = typer.Argument(
        ".",
        help="Project directory (default: current directory)",
    ),
) -> None:
    """Show token savings dashboard."""
    project_root = Path(path).resolve()

    from memory.memory_manager import MemoryManager

    memory = MemoryManager(project_root)
    data = memory.load()

    changes = data.get("change_history", [])
    if not changes:
        console.print("[yellow]No changes recorded yet. Run [bold]preflight change[/bold] first.[/yellow]")
        raise typer.Exit()

    total_used = sum(c.get("tokens_used", 0) for c in changes)
    total_saved = sum(c.get("tokens_saved", 0) for c in changes)
    total_full = total_used + total_saved

    console.print(
        Panel(
            f"[bold]Token Savings (All Sessions)[/bold]\n\n"
            f"Total changes: {len(changes)}\n"
            f"Tokens used:   {total_used:,}\n"
            f"Tokens saved:  {total_saved:,}\n"
            f"Total (full):  {total_full:,}\n"
            f"Savings:       {total_saved / total_full * 100:.0f}%" if total_full > 0 else "N/A",
            border_style="green",
            title="💰 Savings Dashboard",
        )
    )


# ---------------------------------------------------------------------------
# validate
# ---------------------------------------------------------------------------
@app.command()
def validate(
    path: str = typer.Argument(
        ".",
        help="Project directory (default: current directory)",
    ),
) -> None:
    """Check .claude/ and .gemini/ for issues."""
    project_root = Path(path).resolve()
    issues: list[str] = []

    # Check .claude/
    claude_dir = project_root / ".claude"
    if not claude_dir.exists():
        issues.append("❌ .claude/ directory not found")
    else:
        claude_md = claude_dir / "CLAUDE.md"
        if not claude_md.exists():
            issues.append("❌ .claude/CLAUDE.md not found")
        else:
            content = claude_md.read_text()
            lines = content.splitlines()
            if len(lines) > 300:
                issues.append(f"⚠️  CLAUDE.md has {len(lines)} lines (max recommended: 300)")

    # Check .gemini/
    gemini_dir = project_root / ".gemini"
    if not gemini_dir.exists():
        issues.append("❌ .gemini/ directory not found")
    else:
        gemini_md = gemini_dir / "GEMINI.md"
        if not gemini_md.exists():
            issues.append("❌ .gemini/GEMINI.md not found")

    # Check .preflight/
    preflight_dir = project_root / PREFLIGHT_DIR
    if not preflight_dir.exists():
        issues.append("❌ .preflight/ directory not found")
    else:
        for required in ["memory.json", "file-index.json"]:
            if not (preflight_dir / required).exists():
                issues.append(f"❌ .preflight/{required} not found")

    # Check for API keys
    has_claude_key = bool(os.environ.get("ANTHROPIC_API_KEY"))
    has_gemini_key = bool(os.environ.get("GEMINI_API_KEY"))
    if not has_claude_key and not has_gemini_key:
        issues.append("⚠️  No API key found. Set ANTHROPIC_API_KEY or GEMINI_API_KEY")
    elif not has_claude_key:
        issues.append("ℹ️  ANTHROPIC_API_KEY not set (Claude provider unavailable)")
    elif not has_gemini_key:
        issues.append("ℹ️  GEMINI_API_KEY not set (Gemini provider unavailable)")

    if issues:
        console.print("[bold red]Validation Issues:[/bold red]")
        for issue in issues:
            console.print(f"  {issue}")
    else:
        console.print("[bold green]✅ All checks passed![/bold green]")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _validate_provider(provider: str) -> str:
    """Validate and normalize provider name."""
    provider = provider.lower().strip()
    if provider not in (PROVIDER_CLAUDE, PROVIDER_GEMINI):
        console.print(
            f"[red]✗ Invalid provider '{provider}'. Use 'claude' or 'gemini'.[/red]"
        )
        raise typer.Exit(1)
    return provider


if __name__ == "__main__":
    app()
