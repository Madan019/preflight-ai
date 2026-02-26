"""Read/write .preflight/memory.json — the project brain.

All writes are atomic (write temp → rename) to survive corrupt/partial writes.
"""

from __future__ import annotations

import json
import os
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rich.console import Console

from core.constants import PREFLIGHT_DIR, MEMORY_FILE

console = Console()


class MemoryManager:
    """Manages the .preflight/memory.json file.

    Args:
        project_root: Path to the project root directory.
    """

    def __init__(self, project_root: Path) -> None:
        self._root = project_root
        self._dir = project_root / PREFLIGHT_DIR
        self._path = self._dir / MEMORY_FILE
        self._data: dict[str, Any] = {}

    # ------------------------------------------------------------------
    # Core I/O
    # ------------------------------------------------------------------

    def load(self) -> dict[str, Any]:
        """Load memory from disk. Creates default if missing or corrupt.

        Returns:
            The full memory dict.
        """
        if not self._path.exists():
            self._data = self._default_memory()
            return self._data

        try:
            raw = self._path.read_text(encoding="utf-8")
            self._data = json.loads(raw)
        except (json.JSONDecodeError, OSError) as exc:
            console.print(
                f"[yellow]⚠ memory.json is corrupt ({exc}), rebuilding...[/yellow]"
            )
            self._backup_corrupt()
            self._data = self._default_memory()

        return self._data

    def save(self, data: dict[str, Any] | None = None) -> None:
        """Atomically write memory to disk (temp file → rename).

        Args:
            data: Optional dict to save. If ``None``, saves current in-memory data.
        """
        if data is not None:
            self._data = data

        self._data["last_updated"] = datetime.now(timezone.utc).isoformat()
        self._dir.mkdir(parents=True, exist_ok=True)

        # Atomic write: write to temp in same dir → rename
        fd, tmp_path = tempfile.mkstemp(
            dir=str(self._dir), suffix=".tmp", prefix="memory_"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(self._data, f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, str(self._path))
        except Exception:
            # Clean up temp file on failure
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise

    @property
    def data(self) -> dict[str, Any]:
        """Return the current in-memory data."""
        return self._data

    # ------------------------------------------------------------------
    # Accessors
    # ------------------------------------------------------------------

    def get_module(self, name: str) -> dict[str, Any] | None:
        """Return a module entry by name.

        Args:
            name: Module name.

        Returns:
            Module dict or ``None``.
        """
        return self._data.get("modules", {}).get(name)

    def get_modules_for_files(self, file_paths: list[str]) -> list[str]:
        """Return module names that contain any of the given files.

        Args:
            file_paths: List of relative file paths.

        Returns:
            List of matching module names.
        """
        modules = self._data.get("modules", {})
        result: list[str] = []
        for mod_name, mod_info in modules.items():
            mod_files = set(mod_info.get("files", []))
            if mod_files & set(file_paths):
                result.append(mod_name)
        return result

    def get_decisions_for_modules(self, module_names: list[str]) -> list[dict]:
        """Return decisions that affect any of the given modules.

        Args:
            module_names: Modules to filter by.

        Returns:
            Filtered decision list.
        """
        decisions = self._data.get("decisions", [])
        module_set = set(module_names)
        return [
            d
            for d in decisions
            if module_set & set(d.get("affects", []))
        ]

    # ------------------------------------------------------------------
    # Mutators
    # ------------------------------------------------------------------

    def set_module(
        self,
        name: str,
        *,
        status: str = "not_started",
        files: list[str] | None = None,
        purpose: str = "",
        dependencies: list[str] | None = None,
    ) -> None:
        """Add or update a module entry.

        Args:
            name: Module name.
            status: ``complete``, ``in_progress``, or ``not_started``.
            files: Relative file paths in this module.
            purpose: One-line description.
            dependencies: Other module names this depends on.
        """
        if "modules" not in self._data:
            self._data["modules"] = {}
        self._data["modules"][name] = {
            "status": status,
            "files": files or [],
            "purpose": purpose,
            "dependencies": dependencies or [],
        }

    def add_decision(
        self,
        decision: str,
        reason: str,
        affects: list[str],
    ) -> None:
        """Record an architectural decision.

        Args:
            decision: What was decided.
            reason: Why.
            affects: Which modules are affected.
        """
        if "decisions" not in self._data:
            self._data["decisions"] = []
        self._data["decisions"].append(
            {
                "decision": decision,
                "reason": reason,
                "date": datetime.now(timezone.utc).isoformat(),
                "affects": affects,
            }
        )

    def add_change(
        self,
        description: str,
        files_changed: list[str],
        tokens_used: int = 0,
        tokens_saved: int = 0,
    ) -> None:
        """Record a change in the history.

        Args:
            description: What changed.
            files_changed: Relative paths of files modified.
            tokens_used: Tokens consumed by this change.
            tokens_saved: Tokens saved vs full codebase read.
        """
        if "change_history" not in self._data:
            self._data["change_history"] = []
        self._data["change_history"].append(
            {
                "date": datetime.now(timezone.utc).isoformat(),
                "description": description,
                "files_changed": files_changed,
                "tokens_used": tokens_used,
                "tokens_saved": tokens_saved,
            }
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _default_memory(self) -> dict[str, Any]:
        """Return a blank memory structure."""
        now = datetime.now(timezone.utc).isoformat()
        return {
            "project_name": self._root.name,
            "created_at": now,
            "last_updated": now,
            "stack": {
                "language": "",
                "frontend": None,
                "backend": None,
                "database": None,
                "auth": None,
                "hosting": None,
            },
            "ai_target": "both",
            "modules": {},
            "decisions": [],
            "change_history": [],
        }

    def _backup_corrupt(self) -> None:
        """Rename the corrupt memory.json to .bak."""
        if self._path.exists():
            bak_path = self._path.with_suffix(".json.bak")
            try:
                self._path.rename(bak_path)
                console.print(f"[dim]Backed up corrupt file → {bak_path.name}[/dim]")
            except OSError:
                pass
