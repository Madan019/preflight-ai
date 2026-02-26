"""Write the .gemini/ folder for a project.

Creates GEMINI.md and settings.json.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from rich.console import Console

from ai.file_generator import GeneratedFiles

console = Console()


class GeminiBuilder:
    """Build the .gemini/ configuration folder.

    Args:
        project_root: Path to the project root directory.
    """

    def __init__(self, project_root: Path) -> None:
        self._root = project_root
        self._gemini_dir = project_root / ".gemini"

    def build(self, generated: GeneratedFiles) -> int:
        """Write all .gemini/ files from generated content.

        Args:
            generated: Output from Stage 4 file generator.

        Returns:
            Number of files written.
        """
        gemini = generated.gemini
        if not gemini:
            console.print("[yellow]⚠ No Gemini config content generated[/yellow]")
            return 0

        files_written = 0

        # GEMINI.md
        if gemini.get("GEMINI_md"):
            self._write_file("GEMINI.md", gemini["GEMINI_md"])
            files_written += 1

        # settings.json
        if gemini.get("settings_json"):
            self._write_json("settings.json", gemini["settings_json"])
            files_written += 1

        console.print(
            f"[green]✅ .gemini/ → {files_written} files written[/green]"
        )
        return files_written

    def inject_context(self, context_text: str) -> None:
        """Inject change-mode context into GEMINI.md.

        Args:
            context_text: Formatted context package text.
        """
        gemini_md = self._gemini_dir / "GEMINI.md"
        if not gemini_md.exists():
            console.print("[red]✗ .gemini/GEMINI.md not found[/red]")
            return

        content = gemini_md.read_text(encoding="utf-8")

        marker_start = "<!-- PREFLIGHT CONTEXT START -->"
        marker_end = "<!-- PREFLIGHT CONTEXT END -->"
        if marker_start in content:
            before = content[: content.index(marker_start)]
            after_idx = content.find(marker_end)
            after = content[after_idx + len(marker_end) :] if after_idx >= 0 else ""
            content = before + after

        injection = (
            f"\n\n{marker_start}\n"
            f"# Current Change Context (Auto-injected by Preflight)\n\n"
            f"{context_text}\n"
            f"{marker_end}\n"
        )
        content = content.rstrip() + injection
        gemini_md.write_text(content, encoding="utf-8")
        console.print("[green]✅ Context injected into .gemini/GEMINI.md[/green]")

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _write_file(self, relative_path: str, content: str) -> None:
        """Write a text file under .gemini/."""
        path = self._gemini_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    def _write_json(self, relative_path: str, data: Any) -> None:
        """Write a JSON file under .gemini/."""
        path = self._gemini_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False) + "\n",
            encoding="utf-8",
        )
