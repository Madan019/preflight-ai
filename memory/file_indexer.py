"""Index the project codebase → .preflight/file-index.json.

Walks the project tree, skipping ignored dirs, counting tokens per file,
detecting imports, and assigning files to modules.
"""

from __future__ import annotations

import json
import os
import re
import tempfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from rich.console import Console
from rich.progress import track

from core.constants import (
    IGNORED_DIRS,
    INDEXED_EXTENSIONS,
    PREFLIGHT_DIR,
    FILE_INDEX_FILE,
)
from core.token_counter import count_tokens

console = Console()

# ---------------------------------------------------------------------------
# Import detection patterns
# ---------------------------------------------------------------------------
_PY_IMPORT_RE = re.compile(
    r"^(?:from\s+([\w.]+)\s+import|import\s+([\w.]+))", re.MULTILINE
)
_JS_IMPORT_RE = re.compile(
    r"""(?:import\s+.*?from\s+['"](.*?)['"]|require\s*\(\s*['"](.*?)['"]\s*\))""",
    re.MULTILINE,
)
_PY_EXPORT_RE = re.compile(
    r"^(?:def\s+(\w+)|class\s+(\w+))", re.MULTILINE
)
_JS_EXPORT_RE = re.compile(
    r"(?:export\s+(?:default\s+)?(?:function|class|const|let|var)\s+(\w+))",
    re.MULTILINE,
)


class FileIndexer:
    """Walk a codebase and build a structured file index.

    Args:
        project_root: Path to the project root.
    """

    def __init__(self, project_root: Path) -> None:
        self._root = project_root
        self._dir = project_root / PREFLIGHT_DIR
        self._path = self._dir / FILE_INDEX_FILE

    def index(self) -> dict[str, Any]:
        """Index the full codebase and write file-index.json.

        Returns:
            The complete index dict.
        """
        files_data: dict[str, dict[str, Any]] = {}
        modules: dict[str, list[str]] = {}
        total_tokens = 0

        all_files = list(self._walk_files())
        for file_path in track(all_files, description="Indexing files...", console=console):
            rel = str(file_path.relative_to(self._root))
            try:
                content = file_path.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue

            tokens = count_tokens(content)
            total_tokens += tokens

            imports = self._detect_imports(content, file_path.suffix)
            exports = self._detect_exports(content, file_path.suffix)
            module = self._detect_module(rel)

            files_data[rel] = {
                "purpose": "",
                "module": module,
                "imports": imports,
                "exports": exports,
                "token_count": tokens,
                "last_modified": datetime.fromtimestamp(
                    file_path.stat().st_mtime, tz=timezone.utc
                ).isoformat(),
                "summary": "",
            }

            # Build module → files mapping
            if module:
                modules.setdefault(module, []).append(rel)

        index_data: dict[str, Any] = {
            "indexed_at": datetime.now(timezone.utc).isoformat(),
            "total_files": len(files_data),
            "total_tokens_if_full_read": total_tokens,
            "files": files_data,
            "modules": modules,
        }

        self._write_index(index_data)
        return index_data

    def load(self) -> dict[str, Any]:
        """Load the existing file index from disk.

        Returns:
            The index dict, or an empty default if missing.
        """
        if not self._path.exists():
            return {
                "indexed_at": "",
                "total_files": 0,
                "total_tokens_if_full_read": 0,
                "files": {},
                "modules": {},
            }
        try:
            return json.loads(self._path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            return {
                "indexed_at": "",
                "total_files": 0,
                "total_tokens_if_full_read": 0,
                "files": {},
                "modules": {},
            }

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _walk_files(self) -> list[Path]:
        """Yield all indexable files in the project tree."""
        results: list[Path] = []
        for dirpath, dirnames, filenames in os.walk(self._root):
            # Mutate in-place to skip ignored dirs
            dirnames[:] = [
                d for d in dirnames if d not in IGNORED_DIRS
            ]
            for fname in filenames:
                fpath = Path(dirpath) / fname
                if fpath.suffix.lower() in INDEXED_EXTENSIONS:
                    results.append(fpath)
        return results

    def _detect_imports(self, content: str, suffix: str) -> list[str]:
        """Extract import paths from file content."""
        imports: list[str] = []
        if suffix == ".py":
            for m in _PY_IMPORT_RE.finditer(content):
                imp = m.group(1) or m.group(2)
                if imp:
                    imports.append(imp)
        elif suffix in (".js", ".ts", ".jsx", ".tsx"):
            for m in _JS_IMPORT_RE.finditer(content):
                imp = m.group(1) or m.group(2)
                if imp:
                    imports.append(imp)
        return imports

    def _detect_exports(self, content: str, suffix: str) -> list[str]:
        """Extract exported names from file content."""
        exports: list[str] = []
        if suffix == ".py":
            for m in _PY_EXPORT_RE.finditer(content):
                name = m.group(1) or m.group(2)
                if name and not name.startswith("_"):
                    exports.append(name)
        elif suffix in (".js", ".ts", ".jsx", ".tsx"):
            for m in _JS_EXPORT_RE.finditer(content):
                if m.group(1):
                    exports.append(m.group(1))
        return exports

    def _detect_module(self, rel_path: str) -> str:
        """Infer a module name from the relative path.

        Uses the first directory under ``src/`` or the first directory
        in the path as the module name.
        """
        parts = Path(rel_path).parts
        if len(parts) < 2:
            return "root"
        # If the path starts with src/, use the next part
        if parts[0] == "src" and len(parts) >= 3:
            return parts[1]
        return parts[0]

    def _write_index(self, data: dict[str, Any]) -> None:
        """Atomically write the index to disk."""
        self._dir.mkdir(parents=True, exist_ok=True)
        fd, tmp_path = tempfile.mkstemp(
            dir=str(self._dir), suffix=".tmp", prefix="index_"
        )
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            os.replace(tmp_path, str(self._path))
        except Exception:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            raise
