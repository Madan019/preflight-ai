# 🚀 Preflight AI

Intelligent pre-flight layer between developers and AI coding assistants.
Generates optimized `.claude/` and `.gemini/` config folders, maintains local memory, and reduces token usage by **85-95%** on repeated sessions.

## Installation

```bash
pip install preflight-ai
# OR
pipx install preflight-ai
```

## Quick Start

### Setup Mode
Run once on a new or existing project:

```bash
cd your-project/
preflight setup
```

This will:
1. Ask you to describe your project in plain english
2. Generate smart follow-up questions
3. Analyze your answers for gaps and contradictions
4. Generate optimized `.claude/`, `.gemini/`, and `.preflight/` folders
5. Index your codebase for future token savings

### Change Mode
Run when you want to modify something:

```bash
preflight change
```
## 🚀 Quick Start

1.  **Set your API Keys**:
    ```bash
    export ANTHROPIC_API_KEY=sk-ant-...  # For Claude
    export GEMINI_API_KEY=your-key        # For Gemini
    ```

2.  **Install the tool**:
    ```bash
    pip install .
    ```

3.  **Initialize a project**:
    ```bash
    preflight setup --provider gemini
    ```

---

## 🛠 Working with Existing Projects

Preflight AI isn't just for new projects—it's most powerful when used to maintain existing ones.

### 1. The Initial Sync
Run `preflight setup` in any existing project. Preflight will:
- Walk your directory tree and index every file.
- Detect imports/exports to map your project's internal dependencies.
- Create a `memory.json` that acts as the "source of truth" for AI assistants.

### 2. Surgical Context Injection (The `change` command)
Instead of giving an AI assistant your whole project (expensive and confusing), use:
```bash
preflight change "Refactor the user authentication to use JWT instead of sessions"
```

Preflight will:
1. Use a cheap model (Haiku/Flash) to identify *exactly* which 3-5 files need to change.
2. Load those files + their direct imports.
3. Strip comments/docstrings to save tokens.
4. Inject this "Context Package" into your `.claude/CLAUDE.md` or `.gemini/GEMINI.md`.

### 3. Re-indexing
After making significant manual changes or adding many files, run:
```bash
preflight index
```

---

---

## 🌍 Sharing & Distribution

### 1. Push to GitHub
To share this tool, push it to a public GitHub repository. Ensure your `.gitignore` is active so you don't leak API keys or local memory.

### 2. Installation for others
Other developers can install your tool directly from GitHub:
```bash
pip install git+https://github.com/your-username/preflight-ai.git
```

### 3. Future Step: PyPI
If you want to make it an "official" package (installable via `pip install preflight-ai`), you can publish it to [PyPI](https://pypi.org/).

## 💡 Next Steps
- [ ] Initialize Git and push to GitHub.
- [ ] Add your first project decision to `memory.json` using `preflight change`.
- [ ] Try a complex refactor on an existing app and monitor the savings dashboard!

No external APIs. Everything stored locally. Git-ignorable or committable — your choice.

## Token Savings Example

```
Change: "add forgot password to login"
Affected: auth module

Files loaded:
  • src/auth/login.py         (320 tokens)
  • src/auth/email_service.py  (180 tokens)
  • src/models/user.py         (140 tokens)

Total sent:       640 tokens
Full codebase:  84,000 tokens
Saved:          99.3% ($0.037)
```

## Supported AI Tools

- **Claude Code** — generates full `.claude/` folder (CLAUDE.md, settings.json, rules/, agents/, skills/, hooks/, .mcp.json)
- **Gemini CLI** — generates `.gemini/` folder (GEMINI.md, settings.json)

## Commands

| Command | Description |
|---------|-------------|
| `preflight setup` | Full setup for new/existing project |
| `preflight change` | Smart change mode with minimal context |
| `preflight update` | Re-generate config files |
| `preflight memory show` | Show memory.json in readable format |
| `preflight memory reset` | Clear memory and re-index |
| `preflight index` | Re-index codebase after big changes |
| `preflight savings` | Show token savings dashboard |
| `preflight validate` | Check config folders for issues |
| `preflight --version` | Show version |

## Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `ANTHROPIC_API_KEY` | *(required)* | Your Anthropic API key |
| `PREFLIGHT_AI_TARGET` | `both` | `claude`, `gemini`, or `both` |
| `PREFLIGHT_DEFAULT_MODEL` | `sonnet` | `sonnet` or `opus` |
| `PREFLIGHT_MEMORY_DIR` | `.preflight` | Memory directory name |

## Development

```bash
# Install in dev mode
pip install -e ".[dev]"

# Run tests
pytest tests/ -v --cov=. --cov-report=term-missing
```

## Requirements

- Python 3.11+
- Works on macOS, Linux, Windows (WSL)

## License

MIT
