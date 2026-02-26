"""Write the entire .claude/ folder for a project.

Creates CLAUDE.md, settings.json, rules/, agents/, skills/, hooks/, .mcp.json
based on generated file content from Stage 4.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rich.console import Console

from ai.file_generator import GeneratedFiles

console = Console()


class ClaudeBuilder:
    """Build the .claude/ configuration folder.

    Args:
        project_root: Path to the project root directory.
    """

    def __init__(self, project_root: Path) -> None:
        self._root = project_root
        self._claude_dir = project_root / ".claude"

    def build(self, generated: GeneratedFiles) -> int:
        """Write all .claude/ files from generated content.

        Args:
            generated: Output from Stage 4 file generator.

        Returns:
            Number of files written.
        """
        claude = generated.claude
        if not claude:
            console.print("[yellow]⚠ No Claude config content generated[/yellow]")
            return 0

        files_written = 0

        # CLAUDE.md
        if claude.get("CLAUDE_md"):
            self._write_file("CLAUDE.md", claude["CLAUDE_md"])
            files_written += 1

        # settings.json
        if claude.get("settings_json"):
            self._write_json("settings.json", claude["settings_json"])
            files_written += 1

        # rules/
        rules = claude.get("rules", {})
        if rules:
            rules_dir = self._claude_dir / "rules"
            rules_dir.mkdir(parents=True, exist_ok=True)

            rule_mapping = {
                "code_style": "code-style.md",
                "frontend": "frontend.md",
                "backend": "backend.md",
                "database": "database.md",
                "testing": "testing.md",
            }
            for key, filename in rule_mapping.items():
                content = rules.get(key)
                if content:
                    self._write_file(f"rules/{filename}", content)
                    files_written += 1

        # agents/
        if claude.get("agents_md"):
            (self._claude_dir / "agents").mkdir(parents=True, exist_ok=True)
            self._write_file("agents/agents.md", claude["agents_md"])
            files_written += 1

        # skills/
        if claude.get("skills_md"):
            (self._claude_dir / "skills").mkdir(parents=True, exist_ok=True)
            self._write_file("skills/commands.md", claude["skills_md"])
            files_written += 1

        # hooks/
        hooks = claude.get("hooks_json")
        if hooks:
            (self._claude_dir / "hooks").mkdir(parents=True, exist_ok=True)
            # If it's a dict with shell commands, write as shell script
            if isinstance(hooks, dict):
                self._write_json("hooks/hooks.json", hooks)
            else:
                self._write_file("hooks/pre-tool-use.sh", str(hooks))
            files_written += 1

        # .mcp.json
        mcp = claude.get("mcp_json")
        if mcp:
            self._write_json(".mcp.json", mcp)
            files_written += 1

        console.print(
            f"[green]✅ .claude/ → {files_written} files written[/green]"
        )
        return files_written

    def inject_context(self, context_text: str) -> None:
        """Inject change-mode context into CLAUDE.md.

        Appends a context section at the end of CLAUDE.md that AI will
        read on its next session.

        Args:
            context_text: Formatted context package text.
        """
        claude_md = self._claude_dir / "CLAUDE.md"
        if not claude_md.exists():
            console.print("[red]✗ .claude/CLAUDE.md not found[/red]")
            return

        content = claude_md.read_text(encoding="utf-8")

        # Remove any previous context injection
        marker_start = "<!-- PREFLIGHT CONTEXT START -->"
        marker_end = "<!-- PREFLIGHT CONTEXT END -->"
        if marker_start in content:
            before = content[: content.index(marker_start)]
            after_idx = content.find(marker_end)
            after = content[after_idx + len(marker_end) :] if after_idx >= 0 else ""
            content = before + after

        # Append new context
        injection = (
            f"\n\n{marker_start}\n"
            f"# Current Change Context (Auto-injected by Preflight)\n\n"
            f"{context_text}\n"
            f"{marker_end}\n"
        )
        content = content.rstrip() + injection

        claude_md.write_text(content, encoding="utf-8")
        console.print("[green]✅ Context injected into .claude/CLAUDE.md[/green]")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _write_file(self, relative_path: str, content: str) -> None:
        """Write a text file under .claude/."""
        path = self._claude_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _write_json(self, relative_path: str, data: Any) -> None:
        """Write a JSON file under .claude/."""
        path = self._claude_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
