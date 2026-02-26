"""SETUP mode — full pipeline for new or existing project setup.

Pipeline:
1. User describes idea
2. [AI] Parse idea → structured tags
3. [AI] Generate follow-up questions
4. User answers questions (Rich interactive)
5. [AI] Analyze answers → detect gaps
6. [Python] Assemble ProjectSpec
7. [AI] Generate ALL config files
8. [Python] Write .claude/, .gemini/, .preflight/
9. Show savings dashboard
"""

from __future__ import annotations

import json
from pathlib import Path

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import SpinnerColumn, TextColumn, Progress

from ai.idea_parser import parse_idea
from ai.question_engine import generate_questions
from ai.answer_analyzer import analyze_answers
from ai.file_generator import generate_files
from ai.provider import call_ai
from builders.claude_builder import ClaudeBuilder
from builders.gemini_builder import GeminiBuilder
from builders.preflight_builder import PreflightBuilder
from core.constants import (
    PROVIDER_CLAUDE,
    PROVIDER_GEMINI,
    MODEL_OPTIONS,
    get_stage_config,
)
from core.spec_builder import ProjectSpec

console = Console()


def run_setup(
    project_root: Path | None = None,
    *,
    provider: str = PROVIDER_CLAUDE,
) -> None:
    """Run the full setup pipeline with Rich terminal UI.

    Args:
        project_root: Project directory. Defaults to cwd.
        provider: AI provider to use (``"claude"`` or ``"gemini"``).
    """
    if project_root is None:
        project_root = Path.cwd()

    # ── Header ──────────────────────────────────────────────
    console.print()
    console.print(
        Panel(
            "[bold cyan]🚀 Preflight AI — Project Setup[/bold cyan]\n"
            "[dim]Generating optimal AI config folders[/dim]",
            border_style="cyan",
        )
    )

    # ── Step 0: Interactive Selection ───────────────────────
    choices = [PROVIDER_CLAUDE, PROVIDER_GEMINI]
    provider = Prompt.ask(
        "Which [bold]AI Provider[/bold] do you want to use?",
        choices=choices,
        default=provider,
    )

    tiers = list(MODEL_OPTIONS[provider].keys())
    tier = Prompt.ask(
        f"Which [bold]{provider.capitalize()} Model Tier[/bold]?",
        choices=tiers,
        default=tiers[0],
    )

    # Apply selected models
    selected_models = MODEL_OPTIONS[provider][tier]
    if provider == PROVIDER_CLAUDE:
        import core.constants as const
        const.SONNET = selected_models["sonnet"]
        const.HAIKU = selected_models["haiku"]
        # Update stage config to reflect new constants
        const.CLAUDE_STAGE_CONFIG["parse"]["model"] = const.HAIKU
        const.CLAUDE_STAGE_CONFIG["questions"]["model"] = const.HAIKU
        const.CLAUDE_STAGE_CONFIG["analysis"]["model"] = const.HAIKU
        const.CLAUDE_STAGE_CONFIG["change_analysis"]["model"] = const.HAIKU
        const.CLAUDE_STAGE_CONFIG["generate"]["model"] = const.SONNET
    else:
        import core.constants as const
        const.GEMINI_PRO = selected_models["pro"]
        const.GEMINI_FLASH = selected_models["flash"]
        # Update stage config
        const.GEMINI_STAGE_CONFIG["parse"]["model"] = const.GEMINI_FLASH
        const.GEMINI_STAGE_CONFIG["questions"]["model"] = const.GEMINI_FLASH
        const.GEMINI_STAGE_CONFIG["analysis"]["model"] = const.GEMINI_FLASH
        const.GEMINI_STAGE_CONFIG["change_analysis"]["model"] = const.GEMINI_FLASH
        const.GEMINI_STAGE_CONFIG["generate"]["model"] = const.GEMINI_PRO

    provider_label = f"{provider.capitalize()} ({tier})"
    console.print(f"[dim]Provider set to: {provider_label}[/dim]\n")

    # ── Step 1: Get idea ────────────────────────────────────
    idea_text = Prompt.ask(
        "[bold]Describe your project idea[/bold]\n"
        "[dim](plain english, as detailed as you want)[/dim]"
    )
    if not idea_text.strip():
        console.print("[red]✗ No idea provided. Aborting.[/red]")
        return

    # ── Step 2: Parse idea ──────────────────────────────────
    with _spinner(f"Step 1/7  Parsing your idea ({provider_label})..."):
        parsed = parse_idea(idea_text, provider=provider)
    console.print("[green]Step 1/7  Parsed idea ✅[/green]")

    # ── Step 3: Generate questions ──────────────────────────
    with _spinner(f"Step 2/7  Generating questions ({provider_label})..."):
        questions = generate_questions(parsed, provider=provider)
    console.print("[green]Step 2/7  Generated questions ✅[/green]")

    # ── Step 4: Collect answers (Interactive) ───────────────
    console.print("[bold]Step 3/7  Collecting answers...[/bold]")
    answers: dict[str, str] = {}
    total_q = len(questions.questions)

    for i, q in enumerate(questions.questions, 1):
        console.print()
        panel_content = f"[bold]{q.question}[/bold]\n[dim]{q.why_asking}[/dim]"

        if q.type == "choice" and q.options:
            options_text = "\n".join(
                f"  [cyan]{j}.[/cyan] {opt}" for j, opt in enumerate(q.options, 1)
            )
            panel_content += f"\n\n{options_text}"

        console.print(
            Panel(
                panel_content,
                title=f"Question {i} of {total_q}",
                border_style="blue",
            )
        )

        if q.type == "boolean":
            answer = "yes" if Confirm.ask("Your answer", default=True) else "no"
        elif q.type == "choice" and q.options:
            default_idx = "1"
            if q.default:
                for j, opt in enumerate(q.options, 1):
                    if opt == q.default:
                        default_idx = str(j)
                        break
            choice = Prompt.ask(
                f"Your answer [1-{len(q.options)}]",
                default=default_idx,
            )
            try:
                idx = int(choice) - 1
                answer = q.options[idx] if 0 <= idx < len(q.options) else choice
            except (ValueError, IndexError):
                answer = choice
        else:
            answer = Prompt.ask("Your answer", default=q.default or "")

        answers[q.id] = answer

    console.print("[green]Step 3/7  Answers collected ✅[/green]")

    # ── Step 5: Analyze answers ─────────────────────────────
    parsed_json = json.dumps(
        {
            "app_type": parsed.app_type,
            "core_purpose": parsed.core_purpose,
            "features": parsed.features,
            "integrations": parsed.integrations,
            "complexity": parsed.complexity,
            "target_users": parsed.target_users,
            "suggested_stack": parsed.suggested_stack,
            "similar_to": parsed.similar_to,
            "implicit_requirements": parsed.implicit_requirements,
            "ai_target": parsed.ai_target,
        },
        indent=2,
    )

    with _spinner(f"Step 4/7  Analyzing answers ({provider_label})..."):
        analysis = analyze_answers(questions, answers, parsed_json, provider=provider)
    console.print("[green]Step 4/7  Analysis complete ✅[/green]")

    # Show auto-filled gaps if any
    if analysis.gaps_auto_filled:
        console.print("\n[yellow]Auto-filled gaps:[/yellow]")
        for gap in analysis.gaps_auto_filled:
            console.print(f"  • {gap.gap} → [cyan]{gap.filled_with}[/cyan] ({gap.reason})")
    if analysis.contradictions_resolved:
        console.print("\n[yellow]Resolved contradictions:[/yellow]")
        for c in analysis.contradictions_resolved:
            console.print(f"  • {c.issue} → [cyan]{c.resolution}[/cyan]")

    # ── Step 6: Assemble spec + Generate files ──────────────
    spec = ProjectSpec.from_stages(parsed, answers, analysis)

    with _spinner(f"Step 5/7  Generating config files ({provider_label})..."):
        generated = generate_files(spec, provider=provider)
    console.print("[green]Step 5/7  Files generated ✅[/green]")

    # ── Step 7: Write all folders ───────────────────────────
    with _spinner("Step 6/7  Writing files..."):
        claude_count = ClaudeBuilder(project_root).build(generated)
        gemini_count = GeminiBuilder(project_root).build(generated)
    console.print("[green]Step 6/7  Files written ✅[/green]")

    with _spinner("Step 7/7  Indexing codebase..."):
        preflight_count = PreflightBuilder(project_root).build(spec)
    console.print("[green]Step 7/7  Codebase indexed ✅[/green]")

    # ── Summary ─────────────────────────────────────────────
    total_files = claude_count + gemini_count + preflight_count

    ai_target = spec.ai_target
    next_cmd = "claude  OR  gemini" if ai_target == "both" else ai_target

    console.print()
    console.print(
        Panel(
            f"[bold green]✅ Setup Complete![/bold green]\n\n"
            f"[bold]Provider:[/bold] {provider_label}\n"
            f"[bold]Files Created:[/bold]\n"
            f"  .claude/    → {claude_count} files\n"
            f"  .gemini/    → {gemini_count} files\n"
            f"  .preflight/ → {preflight_count} files\n\n"
            f"[bold]Confidence Score:[/bold] {analysis.confidence_score:.0%}\n\n"
            f"[bold]Next Step:[/bold]\n"
            f"  Run: [cyan]{next_cmd}[/cyan]",
            border_style="green",
        )
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
