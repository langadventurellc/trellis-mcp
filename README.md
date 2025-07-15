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

## Quick Start

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