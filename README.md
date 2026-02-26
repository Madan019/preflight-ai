# 🚀 Preflight AI

**The intelligent pre-flight layer for AI coding assistants.**

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Supported Models](https://img.shields.io/badge/AI-Claude_%7C_Gemini-8e44ad.svg)](#-dual-provider-precision)

Preflight AI acts as a sophisticated buffer between you and your AI agents (Claude Code & Gemini CLI). It manages project memory, indexes your codebase, and—most importantly—injects **surgical context** to reduce token usage by **85-95%**.

---

## 📉 The Problem: Context Bloat
AI coding assistants are powerful, but sending your entire codebase on every turn is:
1. **Expensive**: Burns thousands of unnecessary tokens.
2. **Confusing**: Leads to "context drift" where the AI loses track of the core task.
3. **Slow**: Large context windows increase latency.

## ✨ The Solution: Surgical Context
Preflight AI analyzes your change request *before* you talk to your main agent. It identifies the exact files, modules, and architectural decisions needed for that specific task and injects them into your assistant's system instructions.

---

## 🛠 Features

- 🧠 **Local Project Memory**: Maintains a `memory.json` of your stack and architectural decisions.
- 🎯 **Surgical Injection**: Automatically identifies and loads only relevant files for a specific change.
- ⚡ **Dual Provider Precision**: Switch between **Anthropic (Claude)** and **Google (Gemini)** with a single flag.
- ✂️ **Smart Compression**: Strips comments, docstrings, and boilerplate to maximize token efficiency.
- 📊 **Savings Dashboard**: Track exactly how many tokens (and dollars) you've saved.
- 📁 **Config Generator**: Scaffolds optimized `.claude/` and `.gemini/` folders tailored to your specific stack.

---

## 🚀 Quick Start

### 1. Installation
Install directly via pip:
```bash
pip install git+https://github.com/Madan019/preflight-ai.git
```

### 2. Set API Keys
```bash
# Set at least one to get started
export ANTHROPIC_API_KEY=sk-ant-...
export GEMINI_API_KEY=your-google-api-key
```

### 3. Initialize a Project
Run this in any new or existing project root:
```bash
preflight setup --provider claude
```

---

## 📖 Core Workflow

### The "Change" Loop
This is where the magic happens. When you want to make a modification to your code:

1. **Tell Preflight what you want to do**:
   ```bash
   preflight change "Add a Stripe checkout webhook to the billing module"
   ```
2. **Preflight analyzes the request**: It finds `billing.py`, `models.py`, and your API routes.
3. **Context Injection**: It injects compressed versions of those files into `.claude/CLAUDE.md`.
4. **Launch Your Agent**:
   ```bash
   claude
   ```
   Claude now has the exact context it needs—no more, no less.

---

## 🤖 Dual Provider Support

Preflight uses a tiered model approach to maximize quality while minimizing cost. We use the absolute latest "Next" and "Preview" models from each provider:

| Feature | Claude Mode | Gemini Mode |
| :--- | :--- | :--- |
| **Parsing & Analysis** | Claude 3.5 Haiku | Gemini 2.5 Flash |
| **File Generation** | Claude 4.5 Sonnet | Gemini 2.5 Pro |
| **Change Discovery** | Claude 3.5 Haiku | Gemini 2.5 Flash |

Switch providers anytime:
```bash
preflight setup --provider gemini
preflight change --provider claude
```

---

## 📋 Commands Reference

| Command | Description |
| :--- | :--- |
| `setup` | Full project initialization and config generation. |
| `change` | **Main Workflow**: surgical context discovery and injection. |
| `update` | Sync local memory back to your AI config files. |
| `index` | Force a re-index of the codebase (useful after big refactors). |
| `savings` | View your cumulative token and cost savings. |
| `validate` | Check your `.claude` and `.gemini` folders for health issues. |
| `memory show` | Display the project's architectural memory. |

---

## ⚙️ Configuration & Templates
Preflight AI uses Jinja2 templates to generate your rules. You can customize the look and feel of your generated `.claude/rules` by modifying the templates in the `templates/` directory of the source.

---

## 🛡 License
Distributed under the MIT License. See `LICENSE` for more information.

---
**Build smarter, spend less. Happy coding!** 🚀
