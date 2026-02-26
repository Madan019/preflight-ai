"""Update .preflight/memory.json after AI finishes a change.

Re-indexes changed files, records the change in history, and
updates module statuses.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from rich.console import Console

from core.token_counter import count_tokens
from memory.memory_manager import MemoryManager
from memory.file_indexer import FileIndexer
from memory.context_finder import ChangeAnalysis

console = Console()


class MemoryUpdater:
    """Post-AI-run memory updater.

    Args:
        project_root: Project root directory.
    """

    def __init__(self, project_root: Path) -> None:
        self._root = project_root
        self._memory = MemoryManager(project_root)
        self._indexer = FileIndexer(project_root)

    def update_after_change(
        self,
        change_description: str,
        analysis: ChangeAnalysis,
        tokens_used: int,
        full_codebase_tokens: int,
    ) -> None:
        """Update memory after an AI-assisted change completes.

        Args:
            change_description: What the user asked to change.
            analysis: The change analysis from context_finder.
            tokens_used: Actual tokens sent to AI.
            full_codebase_tokens: What full codebase would have cost.
        """
        self._memory.load()

        # Record the change
        tokens_saved = max(0, full_codebase_tokens - tokens_used)
        self._memory.add_change(
            description=change_description,
            files_changed=analysis.affected_files,
            tokens_used=tokens_used,
            tokens_saved=tokens_saved,
        )

        # Update module statuses
        for mod_name in analysis.affected_modules:
            mod = self._memory.get_module(mod_name)
            if mod is not None:
                mod["status"] = "in_progress"

        # Save
        self._memory.save()

        # Re-index changed files
        console.print("[dim]Re-indexing changed files...[/dim]")
        self._reindex_files(analysis.affected_files)

    def update_stack(self, stack: dict[str, Any]) -> None:
        """Update the stack information in memory.

        Args:
            stack: Stack dict with language, frontend, backend, etc.
        """
        self._memory.load()
        self._memory.data["stack"] = stack
        self._memory.save()

    def _reindex_files(self, file_paths: list[str]) -> None:
        """Re-index only the specified files in file-index.json.

        Args:
            file_paths: Relative paths of files to re-index.
        """
        index = self._indexer.load()
        files_data = index.get("files", {})

        for rel_path in file_paths:
            full_path = self._root / rel_path
            if not full_path.exists():
                # File was deleted — remove from index
                files_data.pop(rel_path, None)
                continue

            try:
                content = full_path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue

            tokens = count_tokens(content)
            existing = files_data.get(rel_path, {})
            existing["token_count"] = tokens
            files_data[rel_path] = existing

        # Recalculate total tokens
        index["total_tokens_if_full_read"] = sum(
            f.get("token_count", 0) for f in files_data.values()
        )
        index["total_files"] = len(files_data)
        index["files"] = files_data

        # Write updated index (reuse indexer's atomic write)
        self._indexer._write_index(index)
