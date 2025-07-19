# Trellis MCP

File-backed MCP server for hierarchical project management (Projects → Epics → Features → Tasks).

## Overview

Trellis MCP implements the **"Trellis MCP v 1.1"** specification, providing a structured approach to project planning and task management. The server stores all state as Markdown files with YAML front-matter in a nested tree structure:

```
planning/projects/P-…/epics/E-…/features/F-…/tasks-open/T-….md
```

### Key Features

- **Hierarchical project structure**: Projects → Epics → Features → Tasks
- **Optional parent relationships**: Tasks can be standalone or hierarchy-based (v1.1)
- **Type-safe operations**: Enhanced type system with type guards and generic support
- **File-backed storage**: Human-readable Markdown files with YAML front-matter
- **MCP server integration**: JSON-RPC API for programmatic access
- **Validation and security**: Comprehensive validation with cycle detection

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
uvx task-trellis-mcp serve
# 3) optional – HTTP transport on port 8545
uvx task-trellis-mcp serve --http 0.0.0.0:8545
```

### 2 · Zero‑install from GitHub

```bash
uvx --from git+https://github.com/langadventurellc/trellis-mcp.git task-trellis-mcp serve
```

Add `--http` to expose HTTP.

### 3 · Local development workflow (editable clone)

1. **Initialize a new planning structure:**
   ```bash
   uv run task-trellis-mcp init
   ```

2. **Start the MCP server:**
   ```bash
   # STDIO transport (default)
   uv run task-trellis-mcp serve

   # HTTP transport
   uv run task-trellis-mcp serve --http localhost:8000
   ```

3. **Create objects with priority fields and optional parent relationships:**
   ```yaml
   # Hierarchy-based task (traditional)
   kind: task
   id: T-setup-auth
   parent: F-user-management
   title: Set up authentication system
   priority: high
   status: open
   
   # Standalone task (new in v1.1)
   kind: task
   id: T-urgent-bugfix
   parent: null
   title: Fix critical security issue
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
   npx @modelcontextprotocol/inspector node -e "require('child_process').spawn('task-trellis-mcp', ['serve'], {stdio: 'inherit'})"
   
   # Or test with CLI mode to call getNextReviewableTask
   npx @modelcontextprotocol/inspector --cli task-trellis-mcp serve --method tools/call --tool-name getNextReviewableTask --tool-arg projectRoot=.
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
   task-trellis-mcp delete task T-001
   
   # Delete a feature with confirmation prompt
   task-trellis-mcp delete feature F-user-management
   # Output: ⚠️  Delete Feature F-user-management and 5 descendants? [y/N]
   
   # Delete an epic and all its children
   task-trellis-mcp delete epic E-auth
   # Output: ⚠️  Delete Epic E-auth and 12 descendants? [y/N]
   
   # Force delete even if children have protected status (in-progress/review)
   task-trellis-mcp delete project P-001 --force
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

6. Run from test.pypi.org:

```bash
uvx \
  --prerelease allow \
  --index-url https://test.pypi.org/simple/ \
  --extra-index-url https://pypi.org/simple/ \
  task-trellis-mcp==1.0.0rc1 serve
```

```bash
claude mcp add task-trellis-test \
  -- uvx --prerelease allow \
         --index-url https://test.pypi.org/simple/ \
         --extra-index-url https://pypi.org/simple/ \
         task-trellis-mcp==1.0.0rc1 serve
```

```json
{
  "mcpServers": {
    "trellis-test": {
      "type": "stdio",
      "command": "uvx",
      "args": [
        "--prerelease", "allow",
        "--index-url", "https://test.pypi.org/simple/",
        "--extra-index-url", "https://pypi.org/simple/",
        "task-trellis-mcp==1.0.0rc1",
        "serve"
      ]
    }
  }
}
```

## Cross-System Prerequisites

Trellis MCP supports cross-system prerequisites, enabling tasks to depend on components across different parts of your project hierarchy or external systems. This powerful feature allows you to create complex dependency relationships while maintaining clear validation and security.

### Overview

Cross-system prerequisites allow you to:
- **Mix hierarchy and standalone tasks**: Standalone tasks can depend on hierarchy-based tasks and vice versa
- **Create complex dependency networks**: Build sophisticated dependency relationships across different project areas
- **Maintain validation integrity**: All prerequisites are validated with comprehensive security checks and cycle detection

### Practical Examples

#### 1. Standalone Task with Hierarchy Prerequisites

Create a standalone urgent task that depends on hierarchy-based components:

```bash
# Create a feature in your project hierarchy
uv run task-trellis-mcp createObject feature "User Authentication System" \
  --project-root . --parent E-core-features --id F-user-auth

# Create a task within that feature  
uv run task-trellis-mcp createObject task "Implement JWT tokens" \
  --project-root . --parent F-user-auth --id T-jwt-implementation

# Create a standalone urgent task that depends on the hierarchy task
uv run task-trellis-mcp createObject task "Deploy security hotfix" \
  --project-root . --id T-security-hotfix --priority high \
  --prerequisites T-jwt-implementation
```

#### 2. Complex Multi-Level Mixed Dependencies

Build sophisticated dependency networks spanning multiple systems:

```bash
# Create hierarchy tasks
uv run task-trellis-mcp createObject task "Database migration" \
  --project-root . --parent F-data-layer --id T-db-migration

uv run task-trellis-mcp createObject task "API endpoints" \
  --project-root . --parent F-api-layer --id T-api-endpoints \
  --prerequisites T-db-migration

# Create standalone tasks that integrate with hierarchy
uv run task-trellis-mcp createObject task "Performance monitoring setup" \
  --project-root . --id T-monitoring --priority normal \
  --prerequisites T-api-endpoints

uv run task-trellis-mcp createObject task "Production deployment" \
  --project-root . --id T-deploy --priority high \
  --prerequisites T-monitoring,T-security-hotfix
```

#### 3. Checking Cross-System Dependencies

Validate and monitor your cross-system prerequisites:

```bash
# List tasks and their cross-system dependencies
uv run task-trellis-mcp listBacklog --project-root . --status open

# Claim next available task (respects cross-system prerequisites)
uv run task-trellis-mcp claimNextTask --project-root .

# Check specific task dependencies
uv run task-trellis-mcp getObject task T-deploy --project-root .
```

Example output showing cross-system dependency validation:
```json
{
  "yaml": {
    "id": "T-deploy",
    "title": "Production deployment", 
    "prerequisites": ["T-monitoring", "T-security-hotfix"],
    "status": "open",
    "priority": "high"
  },
  "validation": {
    "prerequisites_valid": true,
    "cross_system_resolved": true,
    "ready_to_claim": false,
    "blocking_prerequisites": ["T-monitoring"]
  }
}
```

### Quick Troubleshooting

**Common Issues & Solutions:**

| Issue | Quick Fix | When to Check Docs |
|-------|-----------|-------------------|
| "Prerequisites not found" | Verify task IDs exist with `getObject` | [Architecture docs](docs/cross-system-prerequisites/architecture.md) for resolution details |
| "Circular dependency detected" | Check dependency chain with `listBacklog` | [Troubleshooting guide](docs/cross-system-prerequisites/troubleshooting.md#cycle-detection) |
| "Performance slow with many prerequisites" | Use `--priority high` for critical paths | [Performance guidelines](docs/cross-system-prerequisites/performance.md) |
| "Task claiming fails" | Ensure prerequisites are completed (`status: done`) | [Examples](docs/cross-system-prerequisites/examples/) for dependency patterns |

**Debug Commands:**
```bash
# Check all objects for dependency issues
uv run task-trellis-mcp listBacklog --project-root . --priority high

# Validate specific task's prerequisites  
uv run task-trellis-mcp getObject task T-problematic-task --project-root .

# Check for circular dependencies
uv run task-trellis-mcp createObject task "test-cycle" --project-root . \
  --prerequisites T-existing-task  # Will validate for cycles
```

### Performance Considerations

For large projects with complex cross-system dependencies:
- **Keep prerequisite lists focused** (1-10 items per task)
- **Use priority levels** to optimize critical paths
- **Monitor validation performance** with timing checks
- **Consider breaking large dependency chains** into smaller segments

### Detailed Documentation

For comprehensive information on cross-system prerequisites:

- **📋 [Architecture](docs/cross-system-prerequisites/architecture.md)** - System design and technical details
- **📚 [Examples](docs/cross-system-prerequisites/examples/)** - Real-world implementation patterns  
- **🔧 [Troubleshooting](docs/cross-system-prerequisites/troubleshooting.md)** - Debugging and problem resolution
- **⚡ [Performance](docs/cross-system-prerequisites/performance.md)** - Optimization strategies and benchmarks

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