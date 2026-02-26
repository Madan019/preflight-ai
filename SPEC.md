# Preflight AI — Complete Production Specification

## Vision
A production-ready CLI tool that acts as an intelligent pre-flight layer
between developers and AI coding assistants (Claude Code + Gemini CLI).

Core promise:
- Generates perfectly optimized .claude/ and .gemini/ config folders
- Maintains local memory of every project so AI never re-reads what it already knows
- Reduces token usage by 85-95% on repeated and small changes
- Zero accuracy tradeoff — AI gets MORE context, not less, just compressed and targeted
- Works offline — no external memory APIs, everything stored locally in .preflight/

---

## The Two Modes

### Mode 1: SETUP
User runs `preflight setup` on a new or existing project.
Tool asks smart AI-powered questions, understands the full idea,
generates all config folders and files, indexes the codebase.

### Mode 2: CHANGE
User runs `preflight change` when they want to modify something.
Tool reads local memory, finds ONLY relevant files, builds minimal
context package, hands off to Claude or Gemini with surgical precision.

---

## Full Pipeline

### SETUP Pipeline
```
1. User runs: preflight setup
2. User describes idea or existing project in plain english
3. [Haiku] Parse idea → structured feature tags
4. [Haiku] Generate smart tailored follow-up questions
5. User answers questions (Rich interactive prompts)
6. [Haiku] Analyze all answers → detect gaps, contradictions, implicit needs
7. [Python] Assemble complete ProjectSpec dataclass
8. [Sonnet] Generate ALL config files in one call
9. [Python] Write .claude/ folder with all files
10. [Python] Write .gemini/ folder with all files
11. [Python] Create .preflight/memory.json (project brain)
12. [Python] Index existing codebase → .preflight/file-index.json
13. Show savings dashboard + next steps
```

### CHANGE Pipeline
```
1. User runs: preflight change
2. User describes what they want to change in plain english
3. [Haiku] Understand the change → identify affected modules
4. [Python] Read .preflight/memory.json → find relevant files
5. [Python] Load ONLY relevant files (not full codebase)
6. [Python] Build minimal context package (compressed)
7. [Python] Inject context into .claude/CLAUDE.md or .gemini/GEMINI.md
8. User runs: claude OR gemini
9. [PostHook] After AI finishes → update .preflight/memory.json
10. Show token savings: what was sent vs full codebase cost
```

---

## Project File Structure

```
preflight-ai/
├── main.py                    # Entry point, CLI commands
├── modes/
│   ├── setup_mode.py          # Full setup pipeline
│   └── change_mode.py         # Smart change pipeline
├── ai/
│   ├── idea_parser.py         # Haiku: parse plain english idea
│   ├── question_engine.py     # Haiku: generate tailored questions
│   ├── answer_analyzer.py     # Haiku: analyze answers for gaps
│   └── file_generator.py      # Sonnet: generate all config files
├── memory/
│   ├── memory_manager.py      # Read/write .preflight/memory.json
│   ├── file_indexer.py        # Index codebase → file-index.json
│   ├── context_finder.py      # Find relevant files for a change
│   └── memory_updater.py      # Update memory after AI runs
├── builders/
│   ├── claude_builder.py      # Write entire .claude/ folder
│   ├── gemini_builder.py      # Write entire .gemini/ folder
│   └── preflight_builder.py   # Write .preflight/ folder
├── core/
│   ├── compressor.py          # Strip verbose content post-generation
│   ├── token_counter.py       # Track usage + show savings
│   ├── spec_builder.py        # Assemble ProjectSpec dataclass
│   └── constants.py           # All models, costs, limits
├── templates/
│   ├── claude/
│   │   ├── CLAUDE.md.tmpl
│   │   ├── settings.json.tmpl
│   │   ├── rules/
│   │   │   ├── code-style.tmpl
│   │   │   ├── frontend.tmpl
│   │   │   ├── backend.tmpl
│   │   │   ├── database.tmpl
│   │   │   └── testing.tmpl
│   │   ├── agents.tmpl
│   │   ├── skills.tmpl
│   │   └── mcp.json.tmpl
│   └── gemini/
│       ├── GEMINI.md.tmpl
│       └── settings.json.tmpl
├── tests/
│   ├── test_idea_parser.py
│   ├── test_question_engine.py
│   ├── test_answer_analyzer.py
│   ├── test_memory_manager.py
│   ├── test_context_finder.py
│   └── test_file_generator.py
├── .claude/                   # This project's own Claude config
├── SPEC.md                    # This file
├── README.md
├── pyproject.toml             # Package config for pip install
├── setup.py
└── requirements.txt
```

---

## Local Memory System (.preflight/)

Every project gets a .preflight/ folder. This is the project brain.
No external APIs. Everything local. Git-ignorable or committable — user's choice.

### .preflight/memory.json
```json
{
  "project_name": "string",
  "created_at": "ISO datetime",
  "last_updated": "ISO datetime",
  "stack": {
    "language": "string",
    "frontend": "string or null",
    "backend": "string or null",
    "database": "string or null",
    "auth": "string or null",
    "hosting": "string or null"
  },
  "ai_target": "claude | gemini | both",
  "modules": {
    "module_name": {
      "status": "complete | in_progress | not_started",
      "files": ["relative/path/to/file.py"],
      "purpose": "one line description",
      "dependencies": ["other_module"]
    }
  },
  "decisions": [
    {
      "decision": "using bcrypt for password hashing",
      "reason": "industry standard, battle tested",
      "date": "ISO datetime",
      "affects": ["auth module", "user model"]
    }
  ],
  "change_history": [
    {
      "date": "ISO datetime",
      "description": "added rate limiting to login",
      "files_changed": ["src/auth/login.py"],
      "tokens_used": 340,
      "tokens_saved": 7800
    }
  ]
}
```

### .preflight/file-index.json
```json
{
  "indexed_at": "ISO datetime",
  "total_files": 42,
  "total_tokens_if_full_read": 84000,
  "files": {
    "src/auth/login.py": {
      "purpose": "handles user login, returns JWT token",
      "module": "auth",
      "imports": ["database.py", "jwt_utils.py", "models/user.py"],
      "exports": ["login_user", "verify_token"],
      "token_count": 320,
      "last_modified": "ISO datetime",
      "summary": "2 sentence compressed summary of what file does"
    }
  },
  "modules": {
    "auth": ["src/auth/login.py", "src/auth/register.py", "src/auth/jwt_utils.py"],
    "api": ["src/api/users.py", "src/api/products.py"]
  }
}
```

### .preflight/context-cache.json
```json
{
  "cached_contexts": {
    "auth_module": {
      "created_at": "ISO datetime",
      "token_count": 480,
      "content": "compressed summary of entire auth module"
    }
  }
}
```

---

## AI Stage Specifications

### Stage 1: Idea Parser (Haiku)
```
System: You are a software architect. Extract structured project requirements
        from plain english. Respond ONLY with valid JSON. No explanation.

Input:  Raw plain english string from user

Output Schema:
{
  "app_type": "web | mobile | cli | api | desktop | fullstack",
  "core_purpose": "one sentence",
  "features": ["auth", "payments", "realtime", "crud", ...],
  "integrations": ["github", "stripe", "slack", "twilio", ...],
  "complexity": "simple | moderate | complex | enterprise",
  "target_users": "description of who uses this",
  "suggested_stack": {
    "language": "python | javascript | typescript | go | ...",
    "frontend": "react | vue | next | flutter | none",
    "backend": "fastapi | express | django | none",
    "database": "postgres | mongo | sqlite | redis | none",
    "auth": "jwt | oauth | session | clerk | none"
  },
  "similar_to": "notion | github | shopify | slack | none",
  "implicit_requirements": [
    "email service (auth feature implies password reset)",
    "file storage (collaboration implies uploads)"
  ],
  "ai_target": "claude | gemini | both"
}

Max tokens: 600
Temperature: 0
Cache system prompt: yes
```

### Stage 2: Question Engine (Haiku)
```
System: You are a senior developer conducting a project requirements interview.
        Generate specific ordered questions based on parsed project tags.
        Each question must be relevant, non-obvious, and explain its impact.
        Respond ONLY with valid JSON. No explanation.

Input:  Parsed tags from Stage 1

Output Schema:
{
  "questions": [
    {
      "id": "q1",
      "question": "Will different users have different permission levels?",
      "why_asking": "Your collaboration feature requires role-based access control",
      "impacts": ["auth_complexity", "database_schema", "api_design"],
      "type": "choice | text | boolean | multi_choice",
      "options": ["admin/member only", "custom roles", "single role"],
      "default": "admin/member only",
      "required": true
    }
  ],
  "total_questions": 8,
  "estimated_minutes": 3
}

Rules:
- Generate 6-12 questions maximum
- Order from most impactful to least
- Skip obvious questions (dont ask stack if already clear from idea)
- Each question must directly affect what files get generated

Max tokens: 1500
Temperature: 0
Cache system prompt: yes
```

### Stage 3: Answer Analyzer (Haiku)
```
System: You are a software architect reviewing project requirements.
        Detect gaps, contradictions, implicit needs.
        Auto-resolve obvious gaps. Flag real contradictions.
        Respond ONLY with valid JSON. No explanation.

Input:  All questions + all user answers

Output Schema:
{
  "complete_spec": {
    "app_type": "string",
    "features": [],
    "stack": {},
    "auth": {},
    "database": {},
    "integrations": [],
    "deployment": {}
  },
  "gaps_auto_filled": [
    {
      "gap": "No error monitoring mentioned",
      "filled_with": "sentry",
      "reason": "Production app of this complexity needs error tracking"
    }
  ],
  "contradictions_resolved": [
    {
      "issue": "Said no auth but mentioned user profiles",
      "resolution": "Added JWT auth — required for user profiles to exist"
    }
  ],
  "implicit_requirements_added": [
    "rate_limiting (payments feature)",
    "email_service (auth feature requires password reset)",
    "file_storage (collaboration requires uploads)"
  ],
  "recommended_rules": ["code-style", "frontend", "backend", "database", "testing"],
  "recommended_agents": ["test-runner", "code-reviewer", "migration-runner"],
  "recommended_skills": ["run-tests", "deploy", "db-migrate"],
  "confidence_score": 0.95
}

Max tokens: 1000
Temperature: 0
Cache system prompt: yes
```

### Stage 4: File Generator (Sonnet)
```
System: You are an expert in Claude Code and Gemini CLI optimization.
        Generate compressed, token-efficient configuration files.
        Use shorthand AI understands. No verbose prose. No explanations.
        Every file must be as small as possible while being complete.
        Respond ONLY with valid JSON. No markdown fences.

Input:  Complete ProjectSpec from Stage 3

Output Schema:
{
  "claude": {
    "CLAUDE_md": "compressed content string",
    "settings_json": {},
    "rules": {
      "code_style": "string or null",
      "frontend": "string or null",
      "backend": "string or null",
      "database": "string or null",
      "testing": "string or null"
    },
    "agents_md": "string",
    "skills_md": "string",
    "hooks_json": {} or null,
    "mcp_json": {} or null
  },
  "gemini": {
    "GEMINI_md": "compressed content string",
    "settings_json": {}
  },
  "project": {
    "PLAN_md": "compressed build phases",
    "schema_json": {},
    "routes_json": [],
    "phases_json": []
  }
}

Max tokens: 8192
Temperature: 0
Cache system prompt: yes
```

### Change Mode: Change Analyzer (Haiku)
```
System: You are analyzing a code change request.
        Identify which modules and files are affected.
        Respond ONLY with valid JSON.

Input:  Change description + file-index.json summary

Output Schema:
{
  "change_type": "feature | bugfix | refactor | config | style",
  "affected_modules": ["auth", "api"],
  "affected_files": ["src/auth/login.py", "src/api/users.py"],
  "needs_new_files": true or false,
  "new_files_needed": ["src/auth/forgot_password.py"],
  "context_needed": ["auth module summary", "user model"],
  "estimated_complexity": "trivial | simple | moderate | complex",
  "token_estimate": 450
}

Max tokens: 512
Temperature: 0
```

---

## .claude/ Folder Generated (Per Project)

```
.claude/
├── CLAUDE.md                    # Compressed project instructions
├── CLAUDE.local.md              # Personal notes (gitignored)
├── settings.json                # Permissions + hooks + env
├── settings.local.json          # Personal API key overrides (gitignored)
├── agents/
│   └── agents.md                # Project-specific agent definitions
├── skills/
│   └── commands.md              # Slash commands for this project
├── hooks/
│   └── pre-tool-use.sh          # Preprocessing hooks (if needed)
├── rules/
│   ├── code-style.md            # Language + style rules
│   ├── frontend/
│   │   └── [framework].md       # e.g. react.md, vue.md
│   ├── backend/
│   │   └── [framework].md       # e.g. fastapi.md, express.md
│   ├── database/
│   │   └── [db].md              # e.g. postgres.md, mongo.md
│   └── testing/
│       └── [framework].md       # e.g. pytest.md, jest.md
└── .mcp.json                    # MCP server configs (if integrations)
```

---

## .gemini/ Folder Generated (Per Project)

```
.gemini/
├── GEMINI.md                    # Compressed project instructions
└── settings.json                # Gemini-specific settings
```

---

## Context Finder Logic (Change Mode)

When user describes a change, the tool must find the minimal context needed.

```python
Algorithm:
1. Parse change description with Haiku → get affected_modules + affected_files
2. Load file-index.json
3. For each affected file:
   a. Load the file itself
   b. Load its direct imports/dependencies (1 level deep only)
   c. Load relevant module summary from context-cache.json
4. Load relevant decisions from memory.json (filtered by affected modules)
5. Calculate total token count
6. If > TOKEN_THRESHOLD (2000): compress module summaries further
7. Return minimal context package

Result: AI gets exactly what it needs, nothing more.

Example:
Change: "add forgot password to login"
Affected: auth module
Files loaded: login.py (320 tokens) + email_service.py (180 tokens)
Decisions loaded: auth decisions only (120 tokens)
Total sent: 620 tokens
Full codebase would be: 84,000 tokens
Savings: 99.3%
```

---

## Token Optimization Rules (Non-Negotiable)

### Rule 1: AI Used Only Where Reasoning Needed
```
Parse idea          → Haiku    (free-form text needs understanding)
Generate questions  → Haiku    (context-aware question selection)
Analyze answers     → Haiku    (gap + contradiction detection)
Analyze change      → Haiku    (identify affected files)
Generate all files  → Sonnet   (complex, accuracy-critical)
Read/write memory   → Python   (structured data, no reasoning)
Find relevant files → Python   (index lookup, no reasoning)
Compress output     → Python   (pattern matching, no reasoning)
Write files to disk → Python   (I/O, no reasoning)
```

### Rule 2: One Call Per Stage
Never split a stage into multiple calls. Batch everything.

### Rule 3: Always Cache System Prompts
```python
system = [{"type": "text", "text": PROMPT, "cache_control": {"type": "ephemeral"}}]
```

### Rule 4: Always Enforce JSON Output
Append output schema to every prompt. Prevents reformatting follow-up calls.

### Rule 5: Explicit Max Tokens Every Call
```python
STAGE_TOKENS = {
    "parse": 600, "questions": 1500, "analysis": 1000,
    "change_analysis": 512, "generate": 8192
}
```

### Rule 6: Temperature = 0 Always
Deterministic output. No surprises. No token overruns.

### Rule 7: Compress After Generation
Let Sonnet generate accurately. Then strip verbose content in Python after.
Never constrain generation quality for token savings.

### Rule 8: Skills Over CLAUDE.md
Detailed workflow instructions go in skills/ (load on demand).
CLAUDE.md stays under 300 lines (loaded every session).

---

## Production Requirements

### Installation
```bash
pip install preflight-ai
# OR
pipx install preflight-ai
```

### CLI Commands
```bash
preflight setup              # Full setup for new or existing project
preflight change             # Smart change mode
preflight update             # Re-generate config files with new answers
preflight memory show        # Show .preflight/memory.json in readable format
preflight memory reset        # Clear memory and re-index
preflight index              # Re-index codebase (after big changes)
preflight savings            # Show token savings dashboard
preflight validate           # Check .claude/ and .gemini/ for issues
preflight --version          # Show version
preflight --help             # Show all commands
```

### Environment Variables
```bash
ANTHROPIC_API_KEY=sk-ant-...    # Required
PREFLIGHT_AI_TARGET=claude      # claude | gemini | both (default: both)
PREFLIGHT_DEFAULT_MODEL=sonnet  # sonnet | opus (default: sonnet)
PREFLIGHT_MEMORY_DIR=.preflight # default: .preflight
```

### Error Handling Requirements
- Every AI call wrapped in try/except with retry logic
- Rate limit errors: auto-retry after 60 seconds with Rich countdown
- JSON parse errors: retry once with explicit JSON reminder
- File write errors: clear user message with fix instructions
- Missing API key: immediate clear error with setup instructions
- Corrupt memory.json: auto-backup + rebuild from codebase

### Cross-Platform Requirements
- Works on macOS, Linux, Windows (WSL)
- Python 3.11+ required
- No platform-specific dependencies

---

## Model Constants
```python
SONNET = "claude-sonnet-4-5"
HAIKU  = "claude-haiku-4-5-20251001"

COSTS_PER_MILLION = {
    SONNET: {"input": 3.00,  "output": 15.00, "cache_read": 0.30,  "cache_write": 3.75},
    HAIKU:  {"input": 1.00,  "output": 5.00,  "cache_read": 0.10,  "cache_write": 1.25},
}

STAGE_CONFIG = {
    "parse":           {"model": HAIKU,  "max_tokens": 600,  "temperature": 0},
    "questions":       {"model": HAIKU,  "max_tokens": 1500, "temperature": 0},
    "analysis":        {"model": HAIKU,  "max_tokens": 1000, "temperature": 0},
    "change_analysis": {"model": HAIKU,  "max_tokens": 512,  "temperature": 0},
    "generate":        {"model": SONNET, "max_tokens": 8192, "temperature": 0},
}
```

---

## Rich Terminal UI Requirements

### Setup Mode Flow
```
┌─────────────────────────────────────────┐
│  🚀 Preflight AI — Project Setup        │
│  Generating optimal AI config files     │
└─────────────────────────────────────────┘

Step 1/7  Parsing your idea...        ⠸ (spinner)
Step 2/7  Generating questions...     ✅
Step 3/7  Collecting answers...

  ┌─ Question 1 of 8 ────────────────────┐
  │ Will users have different roles?     │
  │ (Why: collaboration implies roles)   │
  │                                      │
  │  1. Admin + Member only              │
  │  2. Custom roles                     │
  │  3. Single role for all              │
  └──────────────────────────────────────┘
  Your answer [1]: _

Step 4/7  Analyzing answers...        ✅
Step 5/7  Generating config files...  ⠸ (spinner)
Step 6/7  Writing files...            ✅
Step 7/7  Indexing codebase...        ✅

┌─────────────────────────────────────────┐
│  ✅ Setup Complete!                     │
├─────────────────────────────────────────┤
│  Files Created:                         │
│  .claude/  → 11 files                  │
│  .gemini/  →  4 files                  │
│  .preflight/ → 3 files                 │
├─────────────────────────────────────────┤
│  Estimated Savings Per Session:         │
│  Without Preflight: ~15,000 tokens      │
│  With Preflight:    ~2,100 tokens       │
│  Savings:           86% (~$0.038/day)   │
├─────────────────────────────────────────┤
│  Next Step:                             │
│  Run: claude  OR  gemini               │
└─────────────────────────────────────────┘
```

### Change Mode Flow
```
┌─────────────────────────────────────────┐
│  🔧 Preflight AI — Smart Change Mode    │
└─────────────────────────────────────────┘

What do you want to change?
> add forgot password feature

Analyzing change...          ✅
Finding relevant files...    ✅

┌─────────────────────────────────────────┐
│  📂 Context Loaded (Surgical Precision) │
├─────────────────────────────────────────┤
│  Files loaded:                          │
│  • src/auth/login.py        (320 tok)   │
│  • src/auth/email_service.py(180 tok)   │
│  • src/models/user.py       (140 tok)   │
├─────────────────────────────────────────┤
│  Token Usage:                           │
│  Sent to AI:        640 tokens          │
│  Full codebase:   8,400 tokens          │
│  Saved:           92% ($0.037)          │
└─────────────────────────────────────────┘

Context injected into .claude/CLAUDE.md
Run: claude
```

---

## Testing Requirements

### Unit Tests Required For
- idea_parser.py: mock Haiku response, test JSON parsing
- question_engine.py: mock Haiku, test question ordering
- answer_analyzer.py: mock Haiku, test gap detection
- memory_manager.py: test read/write/update operations
- file_indexer.py: test with sample Python/JS/TS projects
- context_finder.py: test minimal context selection logic
- compressor.py: test verbose content stripping
- token_counter.py: test cost calculations

### Integration Tests Required For
- Full setup pipeline (mocked AI calls)
- Full change pipeline (mocked AI calls)
- .claude/ folder generation validation
- .gemini/ folder generation validation
- Memory update after simulated AI run

### Test Command
```bash
pytest tests/ -v --cov=. --cov-report=term-missing
```

---

## Build Order for Claude Code

### Phase 1: Foundation
1. pyproject.toml + requirements.txt + setup.py
2. core/constants.py
3. core/spec_builder.py (ProjectSpec dataclass)
4. core/token_counter.py
5. core/compressor.py

### Phase 2: AI Layer
6. ai/idea_parser.py
7. ai/question_engine.py
8. ai/answer_analyzer.py
9. ai/file_generator.py

### Phase 3: Memory System
10. memory/memory_manager.py
11. memory/file_indexer.py
12. memory/context_finder.py
13. memory/memory_updater.py

### Phase 4: Builders
14. builders/claude_builder.py (with all templates)
15. builders/gemini_builder.py
16. builders/preflight_builder.py
17. templates/ (all .tmpl files)

### Phase 5: Modes + CLI
18. modes/setup_mode.py
19. modes/change_mode.py
20. main.py (Typer CLI with all commands)

### Phase 6: Tests + Polish
21. tests/ (all test files)
22. README.md
23. Validate pip install works end to end

---

## README Requirements

Must include:
- What it does (2 sentences)
- Installation instructions
- Quick start (setup + change mode example)
- How local memory works
- Supported AI tools (Claude Code, Gemini CLI)
- Token savings examples with real numbers
- Environment variable reference
- Full command reference

---

## Definition of Done (Production Ready)

- [ ] pip install preflight-ai works
- [ ] preflight setup works end to end on a real project
- [ ] preflight change works with real token savings
- [ ] .claude/ folder generated passes claude --doctor
- [ ] .gemini/ folder generated works with gemini CLI
- [ ] All tests pass (pytest tests/ -v)
- [ ] Test coverage > 80%
- [ ] Works on macOS + Linux + Windows WSL
- [ ] README complete with examples
- [ ] No hardcoded API keys anywhere
- [ ] Error messages are user friendly (not Python tracebacks)
- [ ] Rate limit handling works (tested manually)
- [ ] memory.json survives corrupt/partial writes (atomic writes)
