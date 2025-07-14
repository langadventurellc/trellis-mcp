# Trellis MCP Server – F-01 Scaffolding & CLI Feature Specification  (bootstrap only)

## 1 · Overview
The goal is to get a **runnable FastMCP skeleton** and a **basic Click-based CLI** into the repo so that
subsequent features (CRUD RPCs, directory layout, logging, etc.) have a solid foundation.

**Primary outcomes**

| ✔ | Outcome |
|---|---------|
| ✅ | Installable Python 3.12 package in `src/trellis_mcp/` |
| ✅ | `trellis-mcp init` – create *planning/* skeleton |
| ✅ | `trellis-mcp serve` – start FastMCP over STDIO (default) or optional `--http HOST:PORT` |
| ✅ | Hierarchical config loader (defaults → file → env → CLI) |
| ✅ | CI quality pipeline (uv, pre-commit, black, flake8, pyright, pytest) |

Estimated complexity **Medium**.

---

## 2 · Feature Components

| # | Component | Key Responsibilities |
|---|-----------|----------------------|
| **1** | **Project Structure & Package Setup** | src/ layout, `pyproject.toml`, version stub, `.gitignore` |
| **2** | **Development Tooling Integration** | uv, pre-commit, black, flake8, pyright, pytest |
| **3** | **Configuration Management** | Pydantic settings, load YAML/TOML, env overrides, CLI flags |
| **4** | **FastMCP Server Foundation** | Create `FastMCPApp`, add STDIO transport, optional HTTP transport |
| **5** | **Click CLI Interface** | Command group, `serve`, `init`, help/validation |

> **Out of scope (deferred features)**: directory hierarchy builder, logging/error framework, health endpoints, security hardening, integration/perf tests.

---

## 3 · Functional Requirements

### FR-1.x Project Structure & Package
- **FR-1.1** Create `src/trellis_mcp/` package, `__init__.py`
- **FR-1.2** Configure `pyproject.toml` (metadata, uv, pytest, black, flake8, click ≥ 8.1, fastmcp ≥ 0.7)
- **FR-1.3** `uv pip install -e .` succeeds

### FR-2.x Development Tooling
- **FR-2.1** Pre-commit hooks (black, flake8, pyright, pytest)
- **FR-2.2** CI target: `uv pip install -e . && pytest`

### FR-3.x Configuration
- **FR-3.1** `Settings` dataclass (defaults)
- **FR-3.2** YAML/TOML loader
- **FR-3.3** Env-var overrides (`MCP_` prefix)
- **FR-3.4** CLI flag overrides
- **FR-3.5** Validation errors raise rich messages

### FR-4.x FastMCP Server
- **FR-4.1** Build `FastMCPApp()` with service registry
- **FR-4.2** Attach STDIO transport (default)
- **FR-4.3** `--http HOST:PORT` flag adds HTTP transport
- **FR-4.4** Graceful shutdown on SIGINT/SIGTERM

### FR-5.x Click CLI
- **FR-5.1** `trellis-mcp --help` shows commands
- **FR-5.2** `trellis-mcp init [PATH]` creates minimal `planning/` tree
- **FR-5.3** `trellis-mcp serve [--http …]` starts server
- **FR-5.4** Error messages are actionable

---

## 4 · Acceptance Criteria
- New dev can `uv pip install -e . && trellis-mcp init && trellis-mcp serve` in < 5 min
- All pre-commit hooks and tests pass
- `serve` prints active transports at startup
- Config precedence obeys **defaults < file < env < CLI**

---

## 5 · Technical Considerations
- **Click vs argparse**: Click chosen (decided in spec v 1.1).
- **Transport choice**: STDIO default; HTTP via `--http`, uses FastMCP `HTTPTransport`.
- **Schema versioning**: no server-side object schemas yet—handled in later features.

---

## 6 · Non-Goals
Everything listed under Components 6-8 of the original spec (directory builder, logging, health, security, integration/perf tests).

