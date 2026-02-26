"""Write the .preflight/ folder — project brain storage.

Creates memory.json, file-index.json, context-cache.json.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rich.console import Console

from core.constants import PREFLIGHT_DIR, CONTEXT_CACHE_FILE
from core.spec_builder import ProjectSpec
from memory.memory_manager import MemoryManager
from memory.file_indexer import FileIndexer

console = Console()


class PreflightBuilder:
    """Build the .preflight/ folder with initial memory and index.

    Args:
        project_root: Path to the project root directory.
    """

    def __init__(self, project_root: Path) -> None:
        self._root = project_root
        self._dir = project_root / PREFLIGHT_DIR

    def build(self, spec: ProjectSpec) -> int:
        """Initialize .preflight/ folder with memory, index, and cache.

        Args:
            spec: Complete project specification.

        Returns:
            Number of files written.
        """
        self._dir.mkdir(parents=True, exist_ok=True)
        files_written = 0

        # 1. memory.json
        memory = MemoryManager(self._root)
        data = memory.load()
        data["project_name"] = spec.core_purpose[:50] if spec.core_purpose else self._root.name
        data["stack"] = {
            "language": spec.stack.language,
            "frontend": spec.stack.frontend,
            "backend": spec.stack.backend,
            "database": spec.stack.database,
            "auth": spec.stack.auth,
            "hosting": spec.stack.hosting,
        }
        data["ai_target"] = spec.ai_target
        memory.save(data)
        files_written += 1

        # 2. file-index.json
        indexer = FileIndexer(self._root)
        indexer.index()
        files_written += 1

        # 3. context-cache.json (empty initial)
        cache_path = self._dir / CONTEXT_CACHE_FILE
        if not cache_path.exists():
            cache_data: dict[str, Any] = {
                "cached_contexts": {},
            }
            cache_path.write_text(
                json.dumps(cache_data, indent=2) + "\n",
                encoding="utf-8",
            )
        files_written += 1

        console.print(
            f"[green]✅ .preflight/ → {files_written} files written[/green]"
        )
        return files_written
