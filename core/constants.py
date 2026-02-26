"""Model constants, cost tables, and stage configurations."""

from typing import Final

# ---------------------------------------------------------------------------
# Provider names
# ---------------------------------------------------------------------------
PROVIDER_CLAUDE: Final[str] = "claude"
PROVIDER_GEMINI: Final[str] = "gemini"

# ---------------------------------------------------------------------------
# Claude model identifiers
# ---------------------------------------------------------------------------
SONNET: Final[str] = "claude-sonnet-4-5"
HAIKU: Final[str] = "claude-haiku-4-5-20251001"

# ---------------------------------------------------------------------------
# Gemini model identifiers
# ---------------------------------------------------------------------------
import os
GEMINI_PRO: Final[str] = os.environ.get("PREFLIGHT_GEMINI_PRO_MODEL", "gemini-1.5-pro")
GEMINI_FLASH: Final[str] = os.environ.get("PREFLIGHT_GEMINI_FLASH_MODEL", "gemini-1.5-flash")

# ---------------------------------------------------------------------------
# Cost per 1 M tokens (USD)
# ---------------------------------------------------------------------------
COSTS_PER_MILLION: Final[dict[str, dict[str, float]]] = {
    SONNET: {
        "input": 3.00,
        "output": 15.00,
        "cache_read": 0.30,
        "cache_write": 3.75,
    },
    HAIKU: {
        "input": 1.00,
        "output": 5.00,
        "cache_read": 0.10,
        "cache_write": 1.25,
    },
    "gemini-1.5-pro": {
        "input": 1.25,
        "output": 5.00,
        "cache_read": 0.315,
        "cache_write": 1.25,
    },
    "gemini-1.5-flash": {
        "input": 0.075,
        "output": 0.30,
        "cache_read": 0.018,
        "cache_write": 0.075,
    },
    GEMINI_PRO: { "input": 1.25, "output": 10.00, "cache_read": 0.315, "cache_write": 1.25 },
    GEMINI_FLASH: { "input": 0.15, "output": 0.60, "cache_read": 0.0375, "cache_write": 0.15 },
}


# ---------------------------------------------------------------------------
# Per-stage configuration — Claude  (model, max_tokens, temperature)
# ---------------------------------------------------------------------------
CLAUDE_STAGE_CONFIG: Final[dict[str, dict]] = {
    "parse": {"model": HAIKU, "max_tokens": 600, "temperature": 0},
    "questions": {"model": HAIKU, "max_tokens": 1500, "temperature": 0},
    "analysis": {"model": HAIKU, "max_tokens": 1000, "temperature": 0},
    "change_analysis": {"model": HAIKU, "max_tokens": 512, "temperature": 0},
    "generate": {"model": SONNET, "max_tokens": 8192, "temperature": 0},
}

# Alias for backward compat — existing code that imports STAGE_CONFIG
STAGE_CONFIG = CLAUDE_STAGE_CONFIG

# ---------------------------------------------------------------------------
# Per-stage configuration — Gemini  (Flash for stages 1-3, Pro for stage 4)
# ---------------------------------------------------------------------------
GEMINI_STAGE_CONFIG: Final[dict[str, dict]] = {
    "parse": {"model": GEMINI_FLASH, "max_tokens": 600, "temperature": 0},
    "questions": {"model": GEMINI_FLASH, "max_tokens": 1500, "temperature": 0},
    "analysis": {"model": GEMINI_FLASH, "max_tokens": 1000, "temperature": 0},
    "change_analysis": {"model": GEMINI_FLASH, "max_tokens": 512, "temperature": 0},
    "generate": {"model": GEMINI_PRO, "max_tokens": 8192, "temperature": 0},
}


def get_stage_config(provider: str = PROVIDER_CLAUDE) -> dict[str, dict]:
    """Return the stage config dict for the given provider.

    Args:
        provider: ``"claude"`` or ``"gemini"``.

    Returns:
        Stage configuration dict.
    """
    if provider == PROVIDER_GEMINI:
        return GEMINI_STAGE_CONFIG
    return CLAUDE_STAGE_CONFIG

# ---------------------------------------------------------------------------
# Token thresholds
# ---------------------------------------------------------------------------
CONTEXT_TOKEN_THRESHOLD: Final[int] = 2000
MAX_CLAUDE_MD_LINES: Final[int] = 300

# ---------------------------------------------------------------------------
# File indexer defaults
# ---------------------------------------------------------------------------
IGNORED_DIRS: Final[set[str]] = {
    ".git",
    ".svn",
    "node_modules",
    "venv",
    ".venv",
    "env",
    "__pycache__",
    ".preflight",
    ".claude",
    ".gemini",
    "dist",
    "build",
    ".eggs",
    ".tox",
    ".mypy_cache",
    ".pytest_cache",
}

INDEXED_EXTENSIONS: Final[set[str]] = {
    ".py",
    ".js",
    ".ts",
    ".jsx",
    ".tsx",
    ".go",
    ".rs",
    ".java",
    ".rb",
    ".php",
    ".swift",
    ".kt",
    ".c",
    ".cpp",
    ".h",
    ".css",
    ".scss",
    ".html",
    ".vue",
    ".svelte",
    ".sql",
    ".graphql",
    ".proto",
    ".yaml",
    ".yml",
    ".toml",
    ".json",
    ".md",
    ".txt",
    ".env",
    ".sh",
    ".bash",
    ".zsh",
    ".dockerfile",
}

# ---------------------------------------------------------------------------
# Preflight directory name
# ---------------------------------------------------------------------------
PREFLIGHT_DIR: Final[str] = ".preflight"
MEMORY_FILE: Final[str] = "memory.json"
FILE_INDEX_FILE: Final[str] = "file-index.json"
CONTEXT_CACHE_FILE: Final[str] = "context-cache.json"
