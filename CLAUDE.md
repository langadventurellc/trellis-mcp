# CLAUDE.md – System Prompt for Trellis MCP Coding Agents

> **Repository:** [https://github.com/langadventurellc/trellis-mcp](https://github.com/langadventurellc/trellis-mcp)\
> **Server purpose:** File‑backed MCP server implementing the **“Trellis MCP v 1.0”** specification (Projects → Epics → Features → Tasks).

---

## 🗺️ Project Overview

Trellis MCP is a **Python 3.12** JSON‑RPC server built on **FastMCP**.\
It stores all state as Markdown files with YAML front‑matter in a nested tree:

```
planning/projects/P‑…/epics/E‑…/features/F‑…/tasks-open/T‑….md
```

Consult `` (v 1.0) for schema & lifecycles.

## 🚦 Quality Gate — “GREEN or STOP 🚫”

Run **all** checks before committing:

```bash
pre-commit run --all-files   # flake8, black, pyright, etc.
pytest -q                    # unit tests
```

Any ❌ = block. Fix → re‑run → commit.

---

## 🔄 Workflow (Research → Plan → Implement)

1. **Research**  – Browse code & spec. Ask questions if requirements are fuzzy.
2. **Plan**      – Draft a concise step list; confirm interfaces, files, tests.
3. **Implement** – Code & tests → run quality gate → update task `### Log` with a one‑paragraph summary + `filesChanged[]` → call `completeTask` → **STOP**.

---

## 🔧 Common Commands

| Goal               | Command                                        |
| ------------------ | ---------------------------------------------- |
| Start server (dev) | `uv pip install -e . && python -m trellis_mcp` |
| Run unit tests     | `uv run pytest -q`                             |
| Lint & format      | `uv run pre-commit run --all-files`            |
| Type check         | `uv run pyright src/`                          |
| Generate docs      | `uv run mkdocs serve`                          |

---

## 📑 Coding Standards

- **Type hints everywhere** (`from __future__ import annotations`).
- **flake8/black** decide style—no bikeshedding.
- Functions ≤ 40 LOC; classes ≤ 200 LOC; refactor otherwise.
- Prefer composition over inheritance.
- One logical concept per file.
- Delete dead code immediately—no `*_old.py`.

---

## 🛰️ Task‑Centric Etiquette

| When                      | Action                                                |
| ------------------------- | ----------------------------------------------------- |
| Need a new hierarchy node | `createObject` via Trellis MCP                        |
| Starting dev work         | `claimNextTask` (auto‑sets `in-progress`)             |
| Task ready for PR         | Push branch → set `status=review` (or reviewer flips) |
| Merging to main           | Run gate → `completeTask`                             |

Other metadata edits use `updateObject`.

---

## 🤔 When You’re Unsure

1. **Stop** and ask a clear, single question.
2. Offer options (A / B / C) if helpful.
3. Wait for user guidance before proceeding.

## Troubleshooting

If you encounter issues:

- Check the documentation in `docs/`
- Use the context7 MCP tool for up-to-date library documentation
- Use web for research
- Get a second opinion from Gemini CLI by executing bash`gemini -p "<explanation of problem or question>"` for quick useful insights
- If you need clarification, ask specific questions with options

---

Happy coding! Keep it clean, typed, and green. 🛠️✅

