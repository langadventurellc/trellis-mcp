# CLAUDE.md – System Prompt for Trellis MCP Coding Agents

> **Server purpose:** File‑backed MCP server implementing the **“Trellis MCP v 1.0”** specification (Projects → Epics → Features → Tasks).

---

## 🗺️ Project Overview

Trellis MCP is a **Python 3.12** JSON‑RPC server built on **FastMCP**.\
It stores all state as Markdown files with YAML front‑matter in a nested tree:

```
planning/projects/P‑…/epics/E‑…/features/F‑…/tasks-open/T‑….md
```

## 🚦 Quality Gate — “GREEN or STOP 🚫”

**Mandatory** - Run **all** checks before committing:

```bash
uv run poe quality                   # isort, black, flake8, pyright
uv run pre-commit run --all-files    # Alternative: run checks on git-staged files only
```

Any ❌ = block. Fix → re‑run → commit. Repeat until all checks pass.

---

## 🔄 Workflow (Research → Plan → Implement)

1. **Research**  – Browse code & spec. Ask questions if requirements are fuzzy.
2. **Plan**      – Draft a concise step list; confirm interfaces, files, tests.
3. **Implement** – Code & tests → run quality gate → update task `### Log` with a one‑paragraph summary + `filesChanged[]` → call `completeTask` → **STOP**.

---

## 🔧 Common Commands

| Goal | Command |
| ---- | ------- |
| Install dependencies    | `uv sync` |
| Install for development | `uv pip install -e .` |
| All quality checks      | `uv run poe quality` |
| Run unit tests          | `uv run pytest -q` |

## CLI Commands

See [docs/api/cli-commands.md](docs/api/cli-commands.md) for a full list of CLI commands.

---

## 📑 Coding Standards

- **flake8/black** decide style—no bikeshedding.
- Functions ≤ 40 LOC; classes ≤ 200 LOC; refactor otherwise.
- Prefer composition over inheritance.
- One logical concept per file.
- See Clean‑Code Charter below.

### Type Checking

- Prefer built-in types (`list`, `dict`, etc.) over `typing.List`, `typing.Dict` unless necessary
- Use union operator for optional types (e.g., `str | None` instead of `Optional[str]`)

---

## Clean‑Code Charter

> **Purpose**  Guide large‑language‑model (LLM) coding agents toward the simplest **working** solution, written in the style of seasoned engineers (Kent Beck, Robert Martin, et al.).
> The charter is language‑agnostic but assumes most code is authored in **Python**.

### 1  Guiding Maxims (agents must echo these before coding)

| Maxim | Practical test |
|-------|----------------|
| **KISS** – *Keep It Super Simple* | Could a junior dev explain the design to a peer in ≤ 2 min? |
| **YAGNI** – *You Aren’t Gonna Need It* | Is the abstraction used < 3 times? If so, inline it. |
| **SRP / small units** | One concept per function; ≤ 20 logical LOC; cyclomatic ≤ 5. |
| **DRY** – *Don’t Repeat Yourself* | Is the code repeated in ≥ 2 places? If so, extract it. |
| **Simplicity** | Is the code simpler than the alternative? If not, refactor it. |
| **Explicit is better than implicit** | Is the code self‑documenting? If not, add comments. |
| **Fail fast** | Does the code handle errors gracefully? If not, add error handling. |

## 2  Architecture Heuristics

#### 2.1 File‑ & package‑level
* **≤ 400 LOC per file** (logical lines).
* No **“util” or “helpers” dumping grounds** – every module owns a domain noun/verb.

#### 2.2 Module decomposition & dependency rules *(new)*
1. **Domain‑oriented modules.** Each module encapsulates **one** coherent business concept (noun) or service (verb).
2. **Explicit public surface.** Export `__all__` only what callers need; everything else is private.
3. **Acyclic dependency graph.** Imports must not form cycles; prefer dependency‑inversion interfaces to break loops.
4. **Shallow import depth ≤ 3.** Deep chains signal hidden coupling.
5. **Rule of three for new layers.** Add a new package level only after three modules share the same concern.
6. **Composition over inheritance** unless ≥ 2 concrete subclasses are already required.
7. **Ports & Adapters pattern** for I/O: keep domain logic free of external frameworks (DB, HTTP, UI).
8. **Naming convention:** *package/module = noun*, *class = noun*, *function = verb + noun*.

### 3  Testing Policy
* **Goldilocks rule.** Exactly **one** happy‑path unit test per public function *unless* complexity > 5.
* **Integration tests only at seams.** Use fakes/mocks internally.
* **Performance tests gated.** Only generate when the target class/function bears a `@perf_test` attribute.

### 4  Agent Self‑Review Checklist (before emitting code)
1. Could this be **one function simpler**?
2. Did I introduce an abstraction used **only once**?
3. Did I write a **performance test without** a `@perf_test` attribute?
4. Can a junior dev grok each file in **< 5 min**?

---

## 🤔 When You’re Unsure

1. **Stop** and ask a clear, single question.
2. Offer options (A / B / C) if helpful.
3. Wait for user guidance before proceeding.

## Troubleshooting

If you encounter issues:

- Check the documentation in `docs/`
- Use the context7 MCP tool for up-to-date library documentation
- Use web for research (the current year is 2025)
- If you need clarification, ask specific questions with options
