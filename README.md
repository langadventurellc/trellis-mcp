# Trellis MCP

File-backed MCP server for hierarchical project management (Projects → Epics → Features → Tasks).

## Overview

Trellis MCP implements the **"Trellis MCP v 1.0"** specification, providing a structured approach to project planning and task management. The server stores all state as Markdown files with YAML front-matter in a nested tree structure:

```
planning/projects/P-…/epics/E-…/features/F-…/tasks-open/T-….md
```

## Installation

Install the package in development mode:

```bash
uv pip install -e .
```

## Quick Start

### 1 · Zero‑install (run directly from PyPI)

```bash
# 1) install uv once
curl -LsSf https://astral.sh/uv/install.sh | sh
# 2) run the server (STDIO transport)
uvx trellis-mcp serve
# 3) optional – HTTP transport on port 8545
uvx trellis-mcp serve --http 0.0.0.0:8545
```

### 2 · Zero‑install from GitHub

```bash
uvx --from git+https://github.com/langadventurellc/trellis-mcp.git trellis-mcp serve
```

Add `--http` to expose HTTP.

### 3 · Local development workflow (editable clone)

1. **Initialize a new planning structure:**
   ```bash
   trellis-mcp init
   ```

2. **Start the MCP server:**
   ```bash
   # STDIO transport (default)
   trellis-mcp serve
   
   # HTTP transport
   trellis-mcp serve --http localhost:8000
   ```

3. **Create objects with priority fields:**
   ```yaml
   # Task with high priority
   kind: task
   id: T-setup-auth
   title: Set up authentication system
   priority: high
   status: open
   
   # Feature with normal priority (default)
   kind: feature  
   id: F-user-management
   title: User management system
   priority: normal
   status: open
   ```

4. **Test RPC methods with mcp-inspector:**
   ```bash
   # Start mcp-inspector to test your server
   npx @modelcontextprotocol/inspector node -e "require('child_process').spawn('trellis-mcp', ['serve'], {stdio: 'inherit'})"
   
   # Or test with CLI mode to call getNextReviewableTask
   npx @modelcontextprotocol/inspector --cli trellis-mcp serve --method tools/call --tool-name getNextReviewableTask --tool-arg projectRoot=.
   ```
   
   Example output when reviewable task found:
   ```json
   {
     "task": {
       "id": "implement-auth",
       "title": "Implement authentication system", 
       "status": "review",
       "priority": "high",
       "parent": "F-user-management",
       "file_path": "./planning/projects/P-app/epics/E-auth/features/F-user-management/tasks-open/T-implement-auth.md",
       "created": "2025-01-15T10:00:00Z",
       "updated": "2025-01-15T14:30:00Z"
     }
   }
   ```
   
   Example output when no reviewable tasks exist:
   ```json
   {
     "task": null
   }
   ```

5. **Delete objects with cascade deletion:**
   ```bash
   # Delete a task (no children to cascade)
   trellis-mcp delete task T-001
   
   # Delete a feature with confirmation prompt
   trellis-mcp delete feature F-user-management
   # Output: ⚠️  Delete Feature F-user-management and 5 descendants? [y/N]
   
   # Delete an epic and all its children
   trellis-mcp delete epic E-auth
   # Output: ⚠️  Delete Epic E-auth and 12 descendants? [y/N]
   
   # Force delete even if children have protected status (in-progress/review)
   trellis-mcp delete project P-001 --force
   ```
   
   Example output after successful deletion:
   ```
   ✓ Deleted epic E-auth
     Cascade deleted 12 items:
       - planning/projects/P-001/epics/E-auth/epic.md
       - planning/projects/P-001/epics/E-auth/features/F-login/feature.md
       - planning/projects/P-001/epics/E-auth/features/F-login/tasks-open/T-login-form.md
       - planning/projects/P-001/epics/E-auth/features/F-login/tasks-done/2025-01-15T10:30:00-T-setup-db.md
       - ... (and 8 more files)
   ```

## Requirements

- Python 3.12+
- Click >= 8.1
- FastMCP >= 0.7

## Development

Install development dependencies:

```bash
uv pip install -r requirements.dev.txt
pre-commit install
```

Run quality checks:

```bash
pre-commit run --all-files
pytest -q
```

## License

MIT License - See LICENSE file for details.

## Repository

[https://github.com/langadventurellc/trellis-mcp](https://github.com/langadventurellc/trellis-mcp)