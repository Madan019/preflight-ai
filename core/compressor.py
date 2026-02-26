"""Post-generation content compression utilities.

Rule 7 from SPEC: let Sonnet generate accurately, then strip verbose
content in Python. Never constrain generation quality for token savings.
"""

from __future__ import annotations

import re
from pathlib import Path

from core.token_counter import count_tokens


# ---------------------------------------------------------------------------
# Patterns to strip
# ---------------------------------------------------------------------------
_BLOCK_COMMENT_RE = re.compile(
    r'("""[\s\S]*?"""|\'\'\'[\s\S]*?\'\'\')', re.MULTILINE
)
_LINE_COMMENT_RE = re.compile(r"#[^\n]*")
_JS_LINE_COMMENT_RE = re.compile(r"//[^\n]*")
_JS_BLOCK_COMMENT_RE = re.compile(r"/\*[\s\S]*?\*/")
_BLANK_LINES_RE = re.compile(r"\n{3,}")


def compress_content(text: str, *, aggressive: bool = False) -> str:
    """Strip verbose content from generated text to reduce token count.

    Works on any text — code, markdown, config files.

    Args:
        text: Raw text to compress.
        aggressive: When ``True``, also strip single-line comments and
            collapse all runs of blank lines to a single newline.

    Returns:
        Compressed text.
    """
    result = text

    # Always strip multi-line docstrings / block comments
    result = _BLOCK_COMMENT_RE.sub("", result)
    result = _JS_BLOCK_COMMENT_RE.sub("", result)

    if aggressive:
        result = _LINE_COMMENT_RE.sub("", result)
        result = _JS_LINE_COMMENT_RE.sub("", result)

    # Collapse excessive blank lines → max 2
    result = _BLANK_LINES_RE.sub("\n\n", result)

    return result.strip() + "\n"


def compress_file(path: Path, *, aggressive: bool = False) -> str:
    """Read a file and return its compressed content.

    Args:
        path: Filesystem path to the file.
        aggressive: Forward to :func:`compress_content`.

    Returns:
        Compressed file content.
    """
    content = path.read_text(encoding="utf-8", errors="replace")
    return compress_content(content, aggressive=aggressive)


def compress_file_summary(path: Path) -> str:
    """Generate a 2-sentence summary of a source file.

    This is a *local* summarisation (no AI call) — it reads the first
    meaningful lines and the export-level names.

    Args:
        path: Path to the file.

    Returns:
        A short summary string.
    """
    try:
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return f"Could not read {path.name}."

    lines = [l.strip() for l in content.splitlines() if l.strip()]
    if not lines:
        return f"{path.name} is empty."

    # Grab the first non-blank, non-comment line as purpose hint
    purpose_line = ""
    for line in lines:
        if not line.startswith(("#", "//", "/*", "'''", '"""', "import", "from")):
            purpose_line = line[:120]
            break

    tokens = count_tokens(content)
    return f"{path.name} ({tokens} tokens). {purpose_line}"


def should_compress(token_count: int, threshold: int) -> bool:
    """Return ``True`` if the token count exceeds the compression threshold.

    Args:
        token_count: Current token count.
        threshold: Maximum tokens before compression kicks in.

    Returns:
        Whether compression should be applied.
    """
    return token_count > threshold
