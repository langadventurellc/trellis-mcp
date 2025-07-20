# Trellis MCP Server - Specification v 1.0 & MVP Implementation Plan

## 0 · Purpose

A lightweight, file‑backed MCP server that lets planning/developer agents manage **Projects → Epics → Features → Tasks** in a Git repo, while keeping context windows small and human files readable.

---

## 1 · Repository Layout (v 1.0)

```
repo-root/
└─ planning/
└─ projects/
└─ P-.../
├─ project.md
└─ epics/
└─ E-.../
├─ epic.md
└─ features/
└─ F-.../
├─ feature.md
├─ tasks-open/ # one <id>.md, status≠done
└─ tasks-done/ # <ISO-datetime>-<id>.md, status=done
```

- The nested tree ensures **deleting a parent** (feature/epic/project) automatically removes its child files → no orphan state.
- **IDs** remain human‑readable *P‑ / E‑ / F‑ / T‑* slugs.

---

## 2 · YAML Front‑Matter Schema (`schema: 1.1`)

```yaml
kind: task | feature | epic | project
id: T-refresh-token
parent: F-auth-layer # backlink; absent for projects, optional for tasks
status: open | in-progress | review | done | draft
title: Implement token refresh
priority: high | normal | low # default = normal
prerequisites: [T-jwt-decode] # allowed on tasks **and** features/epics
worktree: null # optional; filled by dev agent if desired
created: 2025-07-13T19:12:00-05:00
updated: 2025-07-13T19:12:00-05:00
schema: 1.1
```

- `prerequisites` **MUST NOT form cycles** (server rejects on create/update).
- While *dependencies* and *prerequisites* were used interchangeably, the schema sticks to \`\` for all kinds.

Each Markdown body contains:

- Free‑form **Description** (the planning agent must supply context).
- `### Log` - append‑only human/agent notes.

### 2.1 · Optional Parent Field for Tasks (v 1.1)

**Tasks** can now be created with or without a parent, supporting both:

1. **Hierarchy-based tasks**: `parent: F-feature-id` (traditional workflow)
2. **Standalone tasks**: `parent: null` or omitted (new in v 1.1)

This change introduces a flexible task system where tasks can exist independently of the project hierarchy while maintaining backward compatibility with existing hierarchical workflows.

**Examples:**

```yaml
# Hierarchy-based task (traditional)
kind: task
id: T-implement-login
parent: F-authentication
status: open
title: Implement login endpoint
schema: 1.1
```

```yaml
# Standalone task (new in v 1.1)
kind: task
id: T-standalone-bugfix
parent: null
status: open
title: Fix critical security issue
schema: 1.1
```

**Parent field rules:**
- **Projects**: Must have `parent: null` (no parent)
- **Epics**: Must have valid project parent ID
- **Features**: Must have valid epic parent ID
- **Tasks**: May have feature parent ID or be standalone (`parent: null`)

**Type System Enhancements:**
- All parent parameters now use `str | None` type annotations
- Type guard functions distinguish between standalone and hierarchy tasks
- Runtime validation ensures proper parent constraints for each object type
- MCP tool handlers properly handle `None` parent values for standalone tasks

---

## 2.2 · Type System Enhancements (v 1.1)

The type system has been significantly enhanced to support optional parent relationships and provide better type safety:

**Core Type Annotations:**
- All parent parameters now use `str | None` type annotations instead of empty strings
- Type guard functions provide runtime type checking and type narrowing
- Generic type variables support enhanced type safety for task operations

**Type Guard Functions:**
- `is_standalone_task()` - Identifies tasks with no parent (standalone tasks)  
- `is_hierarchy_task()` - Identifies tasks with a parent (hierarchy tasks)
- `is_project_object()`, `is_epic_object()`, `is_feature_object()`, `is_task_object()` - Object type identification

**Generic Type Support:**
- Template functions for processing tasks while preserving type information
- Factory functions for creating typed task objects with parent constraints
- Type-safe validation functions for parent-child relationships

**Runtime Validation:**
- Enhanced validation logic that properly handles `None` parent values
- Contextual error messages that distinguish between standalone and hierarchy tasks
- Security validation for standalone tasks to prevent unauthorized access

**MCP Tool Integration:**
- All MCP tool handlers properly handle optional parent fields
- Return types correctly reflect `str | None` for parent fields
- Documentation includes examples of both standalone and hierarchy task usage

---

## 3 · Lifecycle States (unchanged)

| Kind | Allowed Transitions |
| ------- | ------------------------------------------------------------------------- |
| Task | `open → in‑progress → review → done`, `open → done`, `in‑progress → done` |
| Feature | `draft → in‑progress → done` |
| Epic | `draft → in‑progress → done` |
| Project | `draft → in‑progress → done` |

No rejection/abandon states in v 1.

---

## 4 · Concurrency Rules

1. Reservation is implicit: \`\` flips the picked task's status → `in‑progress` in main before any branching.
2. Agents must pull main before calling `claimNextTask` to avoid duplicates.
3. No timed locks; manual workflow handles long‑running tasks.

---

## 5 · JSON‑RPC Method Surface (v 1.0)

All methods include an explicit `projectRoot` so one Trellis MCP instance can serve many working directories.

| Method | Purpose / Side‑effect |
| ------------------------- | ---------------------------------------------------------------------------------------------------------------------- |
| **createObject** | Write a new Project/Epic/Feature/Task file. |
| **getObject** | Fetch object with automatic kind inference from ID prefix (P-, E-, F-, T-). |
| **updateObject** | Patch YAML/body with automatic kind inference; also used to mark non‑task objects `done`. |
| **claimNextTask** | Atomically select highest‑priority `open` task (all prereqs done), set `status=in‑progress`, fill optional `worktree`. |
| **getNextReviewableTask** | Pure query: return oldest `review` task. |
| **completeTask** | Move file to *tasks-done/*, set `status=done`, append `filesChanged[]` to `### Log`. |
| **listBacklog** | List tasks filtered by scope (feature/epic/project) & optional status/priority filters. |

Batch and graph queries are deferred to **v 1.2**.

---

## 6 · Priority Ordering

`high → 1`, `normal → 2`, `low → 3` (internal). Missing field = `normal`.

---

## 7 · Validation Rules (new)

1. **Acyclic prerequisites** - server rejects objects that would introduce cycles.
2. **Parent existence** - `parent` must exist; deletion of a parent recursively removes children.

---

## 8 · System Logs

Unchanged: JSONL per day under server‑home, pruned after 30 days.

---

## 9 · Versioning & Linting

Objects now carry `schema: 1.1`. Linter (`mcp lint`) postponed to v 1.2.

---

# MVP Implementation Plan (v 1.0)

The MVP is broken into **12 features** comprising **44 atomic tasks**. Each task is sized to be claimed and completed by a single developer‑agent in one session.

| ID | Feature | Purpose | Tasks |
| -------- | --------------------------- | ------------------------------------------------------------ | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| **F‑01** | **Scaffolding & CLI** | Provide a runnable FastMCP skeleton and directory bootstrap. | S‑01 create project package · S‑02 `Trellis MCP serve` entrypoint · S‑03 `Trellis MCP init` that creates `planning/` tree · S‑04 unit tests |
| **F‑02** | **Path & ID Management** | Resolve object → file and generate collision‑safe slugs. | P‑01 path resolver util · P‑02 slug generator · P‑03 unit tests |
| **F‑03** | **YAML Schema Loader** | Parse / render front‑matter blocks. | Y‑01 schema constants · Y‑02 loader → dataclass · Y‑03 writer · Y‑04 round‑trip unit tests |
| **F‑04** | **CRUD Objects RPC** | JSON‑RPC methods: create/get/update. | C‑01 `createObject` impl · C‑02 `getObject` impl · C‑03 `updateObject` impl (yaml + body patch) · C‑04 validation: parent‑exists · C‑05 unit tests |
| **F‑05** | **Priority Handling** | Map enum → sortable int, expose helper. | PR‑01 enum definition · PR‑02 sort util · PR‑03 unit tests |
| **F‑06** | **Task Claim Logic** | Select next task, enforce prereqs. | CL‑01 build dependency graph for tasks · CL‑02 select highest‑priority open task w/ prereqs done · CL‑03 mutate status → in‑progress & write file · CL‑04 optionally stamp `worktree` · CL‑05 integration test (two competing tasks) |
| **F‑07** | **Task Completion Flow** | Move to *tasks-done/* and log summary. | CO‑01 timestamp‑prefix move util · CO‑02 append `filesChanged[]` to `### Log` · CO‑03 set status=done · CO‑04 integration test |
| **F‑08** | **Review Query** | Surface tasks in `review`. | R‑01 `getNextReviewableTask` impl · R‑02 unit test |
| **F‑09** | **Backlog Listing** | Filtered task listing for planners. | B‑01 `listBacklog` with scope param · B‑02 support status & priority filters · B‑03 unit tests |
| **F‑10** | **Acyclic Validation** | Enforce no cycles in prerequisites. | A‑01 graph builder · A‑02 DFS cycle detect · A‑03 hook into create/update · A‑04 unit tests |
| **F‑11** | **Parent Deletion Cascade** | Recursive delete to avoid orphans. | DPC‑01 `deleteObject` RPC (projects+epics+features) · DPC‑02 recursive file removal util · DPC‑03 unit tests |
| **F‑12** | **System Logging & Prune** | JSONL log + 30‑day rotation. | SL‑01 event logger wrapper · SL‑02 daily file writer · SL‑03 prune job · SL‑04 unit tests |

> **Total:** 12 features · 44 tasks (task IDs prefixed by feature code, e.g. *CL‑02*).

### Task ID Glossary

| Task ID | One‑liner | Size |
| ------- | ------------------------------------------------------------- | ---- |
| S‑01 | Create Python package skeleton `Trellis MCP/` with `__init__.py`. | XS |
| S‑02 | Implement `Trellis MCP serve` CLI using FastMCP server runner. | S |
| S‑03 | Implement `Trellis MCP init` that writes nested `planning/` dirs. | S |
| S‑04 | Unit tests for CLI scaffold commands. | XS |
| P‑01 | Implement util `path_for_object(kind,id,projectRoot)`. | XS |
| P‑02 | Implement `generate_slug(kind,title)` with collision check. | S |
| P‑03 | Unit tests for path + slug utilities. | XS |
| Y‑01 | Define `SchemaV11` dataclass with pydantic‑like validation. | S |
| Y‑02 | Loader reads front‑matter → dataclass instance. | S |
| Y‑03 | Writer serializes dataclass back to Markdown file. | S |
| Y‑04 | Round‑trip tests (load→write→load). | XS |
| C‑01 | Implement RPC `createObject` with validation & file write. | M |
| C‑02 | Implement RPC `getObject`. | XS |
| C‑03 | Implement RPC `updateObject` with YAML patch support. | M |
| C‑04 | Validate parent existence on create/update. | XS |
| C‑05 | Unit tests for CRUD flows. | S |
| PR‑01 | Enum + int map (`high=1`,...). | XS |
| PR‑02 | Sorting helper `sorted_tasks(tasks)`. | XS |
| PR‑03 | Tests for priority ordering. | XS |
| CL‑01 | Build in‑memory graph of `prerequisites`. | S |
| CL‑02 | Implement selection algorithm for next task. | M |
| CL‑03 | Update YAML: status to `in-progress`, `updated` timestamp. | XS |
| CL‑04 | Stamp optional `worktree`. | XS |
| CL‑05 | Integration test: two tasks, ensure right one claimed. | S |
| CO‑01 | Move file to `tasks-done/` with ISO prefix util. | XS |
| CO‑02 | Append `filesChanged[]` to `### Log`. | XS |
| CO‑03 | Set `status=done`, touch `updated`. | XS |
| CO‑04 | Integration test complete path. | S |
| R‑01 | Implement `getNextReviewableTask`. | XS |
| R‑02 | Unit test review query. | XS |
| B‑01 | Implement `listBacklog` scoped by feature/epic/project. | M |
| B‑02 | Add status & priority filters. | XS |
| B‑03 | Unit tests backlog filter combos. | S |
| A‑01 | Build adjacency list from all objects. | S |
| A‑02 | Cycle detection (DFS). | S |
| A‑03 | Reject create/update with cycle error. | XS |
| A‑04 | Tests for cycle detection. | S |
| DPC‑01 | Implement `deleteObject` RPC with recursive deletion. | M |
| DPC‑02 | Utility to remove nested dirs safely. | XS |
| DPC‑03 | Unit tests cascade delete. | S |
| SL‑01 | Implement logger util `log_event(level,msg,details)`. | XS |
| SL‑02 | Daily JSONL file writer. | XS |
| SL‑03 | Prune files older than 30 days. | XS |
| SL‑04 | Unit tests for log rotation. | XS |

Size legend: **XS <1 h · S 1-2 h · M 2-4 h**

