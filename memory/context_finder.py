"""Find the minimal context needed for a code change.

Algorithm (from SPEC):
1. Parse change → get affected modules + files
2. Load file-index.json
3. For each affected file: load it + 1-level imports + module summary
4. Load relevant decisions from memory.json
5. Calculate total tokens
6. If > TOKEN_THRESHOLD: compress further
7. Return minimal context package
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from rich.console import Console

from ai.provider import call_ai
from core.constants import CONTEXT_TOKEN_THRESHOLD, PROVIDER_CLAUDE
from core.compressor import compress_content
from core.token_counter import count_tokens
from memory.file_indexer import FileIndexer
from memory.memory_manager import MemoryManager

console = Console()

# ---------------------------------------------------------------------------
# Change analysis prompt
# ---------------------------------------------------------------------------
SYSTEM_PROMPT = (
    "You are analyzing a code change request. "
    "Identify which modules and files are affected. "
    "Respond ONLY with valid JSON."
)

CHANGE_SCHEMA = """{
  "change_type": "feature | bugfix | refactor | config | style",
  "affected_modules": ["auth", "api"],
  "affected_files": ["src/auth/login.py", "src/api/users.py"],
  "needs_new_files": true,
  "new_files_needed": ["src/auth/forgot_password.py"],
  "context_needed": ["auth module summary", "user model"],
  "estimated_complexity": "trivial | simple | moderate | complex",
  "token_estimate": 450
}"""


@dataclass
class ChangeAnalysis:
    """Result of analysing a change request."""

    change_type: str = "feature"
    affected_modules: list[str] = field(default_factory=list)
    affected_files: list[str] = field(default_factory=list)
    needs_new_files: bool = False
    new_files_needed: list[str] = field(default_factory=list)
    context_needed: list[str] = field(default_factory=list)
    estimated_complexity: str = "simple"
    token_estimate: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ChangeAnalysis:
        """Create from a JSON-decoded dict."""
        return cls(
            change_type=data.get("change_type", "feature"),
            affected_modules=data.get("affected_modules", []),
            affected_files=data.get("affected_files", []),
            needs_new_files=data.get("needs_new_files", False),
            new_files_needed=data.get("new_files_needed", []),
            context_needed=data.get("context_needed", []),
            estimated_complexity=data.get("estimated_complexity", "simple"),
            token_estimate=data.get("token_estimate", 0),
        )


@dataclass
class ContextPackage:
    """Minimal context package ready for injection."""

    files: dict[str, str] = field(default_factory=dict)
    decisions: list[dict] = field(default_factory=list)
    module_summaries: dict[str, str] = field(default_factory=dict)
    total_tokens: int = 0
    analysis: ChangeAnalysis = field(default_factory=ChangeAnalysis)

    def to_injection_text(self) -> str:
        """Format the context package for injection into CLAUDE.md / GEMINI.md."""
        parts: list[str] = []

        if self.module_summaries:
            parts.append("## Relevant Modules")
            for mod, summary in self.module_summaries.items():
                parts.append(f"### {mod}\n{summary}")

        if self.files:
            parts.append("## Relevant Files")
            for path, content in self.files.items():
                parts.append(f"### {path}\n```\n{content}\n```")

        if self.decisions:
            parts.append("## Relevant Decisions")
            for d in self.decisions:
                parts.append(f"- {d['decision']} ({d['reason']})")

        return "\n\n".join(parts)


class ContextFinder:
    """Find minimal context for a code change.

    Args:
        project_root: Project root directory.
    """

    def __init__(self, project_root: Path) -> None:
        self._root = project_root
        self._indexer = FileIndexer(project_root)
        self._memory = MemoryManager(project_root)

    def analyze_change(
        self,
        description: str,
        *,
        provider: str = PROVIDER_CLAUDE,
        client: Any = None,
    ) -> ChangeAnalysis:
        """Use AI to understand which modules/files a change affects.

        Args:
            description: Plain-english change description.
            provider: AI provider to use (``"claude"`` or ``"gemini"``).
            client: Optional pre-configured SDK client.

        Returns:
            A :class:`ChangeAnalysis` with affected modules and files.
        """
        index = self._indexer.load()

        # Build a summary of available modules/files
        index_summary = json.dumps(
            {
                "modules": index.get("modules", {}),
                "files": {
                    k: {"purpose": v.get("purpose", ""), "module": v.get("module", "")}
                    for k, v in index.get("files", {}).items()
                },
            },
            indent=2,
        )

        user_message = (
            f"Change request: {description}\n\n"
            f"Available project structure:\n{index_summary}\n\n"
            f"Respond ONLY with JSON matching this schema:\n{CHANGE_SCHEMA}"
        )

        data = call_ai(
            stage="change_analysis",
            system_prompt=SYSTEM_PROMPT,
            user_message=user_message,
            provider=provider,
            client=client,
        )
        if data is not None:
            return ChangeAnalysis.from_dict(data)

        # Retry
        user_message_retry = (
            f"Change request: {description}\n\n"
            f"Available project structure:\n{index_summary}\n\n"
            "CRITICAL: Valid JSON only, no markdown.\n\n"
            f"Schema:\n{CHANGE_SCHEMA}"
        )
        data = call_ai(
            stage="change_analysis",
            system_prompt=SYSTEM_PROMPT,
            user_message=user_message_retry,
            provider=provider,
            client=client,
        )
        if data is not None:
            return ChangeAnalysis.from_dict(data)

        raise ValueError("Failed to parse change analysis as JSON after retry.")

    def build_context(self, analysis: ChangeAnalysis) -> ContextPackage:
        """Build the minimal context package from a change analysis.

        Args:
            analysis: Output from :meth:`analyze_change`.

        Returns:
            A :class:`ContextPackage` ready for injection.
        """
        index = self._indexer.load()
        self._memory.load()

        files_content: dict[str, str] = {}
        module_summaries: dict[str, str] = {}
        total_tokens = 0

        # Load affected files + 1-level imports
        files_in_index = index.get("files", {})
        files_to_load: set[str] = set(analysis.affected_files)

        # Add direct imports (1 level deep)
        for fpath in list(files_to_load):
            if fpath in files_in_index:
                imports = files_in_index[fpath].get("imports", [])
                for imp in imports:
                    for idx_path in files_in_index:
                        if imp.replace(".", "/") in idx_path or imp in idx_path:
                            files_to_load.add(idx_path)
                            break

        # Load file contents
        for fpath in files_to_load:
            full_path = self._root / fpath
            if full_path.exists():
                try:
                    content = full_path.read_text(encoding="utf-8", errors="replace")
                    tokens = count_tokens(content)
                    total_tokens += tokens
                    files_content[fpath] = content
                except OSError:
                    continue

        # Load module summaries
        for mod_name in analysis.affected_modules:
            mod_files = index.get("modules", {}).get(mod_name, [])
            summary_parts = []
            for mf in mod_files:
                info = files_in_index.get(mf, {})
                summary_parts.append(
                    f"- {mf}: {info.get('purpose', 'no description')} "
                    f"({info.get('token_count', 0)} tokens)"
                )
            module_summaries[mod_name] = "\n".join(summary_parts) if summary_parts else "no files"

        # Load relevant decisions
        decisions = self._memory.get_decisions_for_modules(analysis.affected_modules)

        # Compress if over threshold
        if total_tokens > CONTEXT_TOKEN_THRESHOLD:
            files_content = {
                k: compress_content(v, aggressive=True)
                for k, v in files_content.items()
            }
            total_tokens = sum(count_tokens(v) for v in files_content.values())

        return ContextPackage(
            files=files_content,
            decisions=decisions,
            module_summaries=module_summaries,
            total_tokens=total_tokens,
            analysis=analysis,
        )
