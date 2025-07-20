# Trellis MCP

A powerful file-backed MCP (Model Context Protocol) server that implements hierarchical project management for software development teams. Organize your work with a clear structure: Projects → Epics → Features → Tasks.

## Why Trellis MCP?

Trellis MCP transforms project management by providing:

- **Structured Workflow**: Break down complex projects into manageable, hierarchical components
- **Developer-First**: Built for software teams with file-based storage that integrates seamlessly with your existing tools
- **AI-Native**: Designed specifically for AI coding assistants like Claude, enabling intelligent task management
- **Dependency Management**: Support for cross-system prerequisites with cycle detection and validation
- **Human-Readable**: All data stored as Markdown files with YAML front-matter - no proprietary formats
- **Flexible Architecture**: Support both hierarchical tasks (within project structure) and standalone tasks for urgent work

Perfect for teams who want to maintain project structure while enabling AI assistants to understand context, claim tasks, and track progress automatically.

## Features

- **Hierarchical project structure**: Projects → Epics → Features → Tasks
- **Cross-system task support**: Mix hierarchical and standalone tasks with prerequisites spanning both systems
- **File-backed storage**: Human-readable Markdown files with YAML front-matter
- **MCP server integration**: JSON-RPC API for programmatic access by AI assistants
- **Comprehensive validation**: Cycle detection, prerequisite validation, and type safety
- **Atomic operations**: Task claiming, completion, and status transitions with integrity guarantees

## Installation

### Using uv (Fast Python Package Manager)

```bash
# Install with uv
uv add task-trellis-mcp

# Or run directly without installation
uvx task-trellis-mcp serve
```

### Development Installation

For development or to install from source:

```bash
# Clone the repository
git clone https://github.com/langadventurellc/trellis-mcp.git
cd trellis-mcp

# Install development dependencies
uv sync

# Install in editable mode
uv pip install -e .
```

### Claude Code Configuration

Add Trellis MCP to your Claude Code MCP configuration:

```bash
# Add to Claude Code
claude mcp add task-trellis \
  -- uvx task-trellis-mcp serve

# Or specify a custom project root
claude mcp add task-trellis \
  -- uvx task-trellis-mcp --project-root /path/to/project serve
```

Configuration in `~/.config/claude/mcp_servers.json`:

```json
{
  "mcpServers": {
    "task-trellis": {
      "type": "stdio",
      "command": "uvx",
      "args": [
        "task-trellis-mcp",
        "serve"
      ]
    }
  }
}
```

### VS Code with Claude Extension

Add to your VS Code settings:

```json
{
  "claude.mcpServers": {
    "task-trellis": {
      "command": "uvx",
      "args": ["task-trellis-mcp", "serve"]
    }
  }
}
```

### Other MCP Clients

For other MCP-compatible tools, use the command:

```bash
uvx task-trellis-mcp serve
```

Or with HTTP transport:

```bash
uvx task-trellis-mcp serve --http localhost:8545
```

## Usage

### MCP Tool Integration

Trellis MCP provides a comprehensive set of tools for AI assistants to manage hierarchical project structures. Once configured with your MCP client, these tools enable intelligent project planning and task management.

#### Core MCP Tools

- **`createObject`** - Create projects, epics, features, or tasks with validation
- **`getObject`** - Retrieve detailed object information with automatic type detection
- **`updateObject`** - Modify object properties with atomic updates
- **`listBacklog`** - Query and filter tasks across the project hierarchy
- **`claimNextTask`** - Automatically claim highest-priority available task with optional scope filtering
- **`completeTask`** - Mark tasks complete with logging and file tracking

#### Creating Project Hierarchies

Start by creating a project and breaking it down into manageable components:

```javascript
// Create a new project
await mcp.call('createObject', {
  kind: 'project',
  title: 'E-commerce Platform Redesign',
  priority: 'high',
  projectRoot: '.',
  description: 'Comprehensive redesign of the e-commerce platform...'
});

// Create an epic within the project
await mcp.call('createObject', {
  kind: 'epic',
  title: 'User Authentication System',
  parent: 'P-ecommerce-platform-redesign',
  priority: 'high',
  projectRoot: '.'
});

// Create features within the epic
await mcp.call('createObject', {
  kind: 'feature',
  title: 'User Registration',
  parent: 'E-user-authentication-system',
  priority: 'high',
  projectRoot: '.'
});

// Create implementable tasks
await mcp.call('createObject', {
  kind: 'task',
  title: 'Create user database model',
  parent: 'F-user-registration',
  priority: 'high',
  projectRoot: '.',
  prerequisites: ['T-setup-database-schema']
});
```

#### Task Management Workflow

Use the task management tools to claim, track, and complete work:

```javascript
// List available tasks
const backlog = await mcp.call('listBacklog', {
  projectRoot: '.',
  status: 'open',
  priority: 'high',
  sortByPriority: true
});

// Claim the next highest-priority task (any scope)
const claimedTask = await mcp.call('claimNextTask', {
  projectRoot: '.',
  worktree: 'feature/user-auth'
});

// Claim task within specific project scope
const projectTask = await mcp.call('claimNextTask', {
  projectRoot: '.',
  scope: 'P-ecommerce-platform',
  worktree: 'feature/ecommerce'
});

// Claim task within specific epic scope
const epicTask = await mcp.call('claimNextTask', {
  projectRoot: '.',
  scope: 'E-user-authentication',
  worktree: 'feature/auth'
});

// Claim task within specific feature scope
const featureTask = await mcp.call('claimNextTask', {
  projectRoot: '.',
  scope: 'F-login-functionality',
  worktree: 'feature/login'
});

// Update task progress
await mcp.call('updateObject', {
  id: 'T-create-user-model',
  projectRoot: '.',
  yamlPatch: {
    status: 'review'
  }
});

// Complete the task with summary
await mcp.call('completeTask', {
  projectRoot: '.',
  taskId: 'T-create-user-model',
  summary: 'Implemented user model with validation and security features',
  filesChanged: ['src/models/User.js', 'tests/models/User.test.js']
});
```

#### Cross-System Prerequisites

Trellis supports complex dependency relationships across different parts of your project:

```javascript
// Create a standalone urgent task that depends on hierarchy tasks
await mcp.call('createObject', {
  kind: 'task',
  title: 'Security hotfix deployment',
  projectRoot: '.',
  priority: 'high',
  prerequisites: ['T-auth-implementation', 'T-validation-update'],
  // No parent - this is a standalone task
});
```

#### Querying and Filtering

Use flexible querying to understand project status:

```javascript
// Get all open tasks for a specific feature
const featureTasks = await mcp.call('listBacklog', {
  projectRoot: '.',
  scope: 'F-user-registration',
  status: 'open'
});

// Get high-priority tasks across the entire project
const urgentTasks = await mcp.call('listBacklog', {
  projectRoot: '.',
  priority: 'high',
  sortByPriority: true
});

// Get task details with prerequisites
const taskDetails = await mcp.call('getObject', {
  id: 'T-create-user-model',
  projectRoot: '.'
});
```

### Working with AI Assistants

When using Trellis MCP with AI coding assistants, you can request natural language operations that use these tools behind the scenes:

- "Create a new project for inventory management and break it down into epics"
- "Claim the next highest priority task and implement it"
- "Claim a task from the user authentication epic"
- "Show me all open tasks that are ready to work on"
- "Show me tasks in the frontend development epic"
- "Complete the current task and provide a summary of what was implemented"
- "Claim a task from the login feature specifically"

#### Natural Language Scope Claiming

AI assistants can interpret scope-focused requests:

```javascript
// "Work on user authentication epic"
const authTask = await mcp.call('claimNextTask', {
  projectRoot: './planning',
  scope: 'E-user-authentication'
});

// "Focus on login functionality feature"
const loginTask = await mcp.call('claimNextTask', {
  projectRoot: './planning', 
  scope: 'F-login-functionality'
});

// "Claim any task from the mobile app project"
const mobileTask = await mcp.call('claimNextTask', {
  projectRoot: './planning',
  scope: 'P-mobile-app-redesign'
});
```

### Sample Commands

For examples of how to create comprehensive AI assistant commands that leverage these MCP tools, see the [sample commands](docs/sample-commands/) directory. These examples show how to build complex workflows that combine multiple MCP tool calls for project planning and task implementation.

### Direct CLI Usage

You can also use Trellis MCP directly from the command line for manual operations:

```bash
# Initialize a new project structure
task-trellis-mcp init

# Start the MCP server
task-trellis-mcp serve
```

## Requirements

- Python 3.12+
- Click >= 8.1
- FastMCP >= 0.7

## Developer Guidelines

### Code Quality Standards

This project follows strict quality standards enforced by automated tools. All changes must pass the quality gate before being committed.

#### Quality Gate

Run **all** checks before committing - any failure blocks the commit:

```bash
uv run poe quality   # flake8, black, pyright, unit tests
```

#### Code Style

- **Formatting**: `black` and `flake8` enforce code style automatically
- **Type Checking**: `pyright` ensures type safety with strict settings
- **Line Limits**: Functions ≤ 40 LOC, classes ≤ 200 LOC
- **Import Organization**: One logical concept per file
- **Modern Python**: Use built-in types (`list`, `dict`) over `typing` equivalents
- **Union Types**: Use `str | None` instead of `Optional[str]`

#### Architecture Principles

- **Single Responsibility**: Each module/class/function has one clear purpose
- **Minimal Coupling**: Components interact through clean interfaces
- **High Cohesion**: Related functionality grouped together
- **Dependency Injection**: Avoid tight coupling between components
- **No Circular Dependencies**: Maintain clear dependency flow

#### Security Requirements

- **Input Validation**: Validate ALL user inputs
- **Parameterized Queries**: Never concatenate user data into queries
- **Secure Defaults**: Fail closed, not open
- **Least Privilege**: Request minimum permissions needed
- **No Hardcoded Secrets**: Use environment variables and configuration

#### Testing Standards

- **Comprehensive Coverage**: Write tests alongside implementation
- **Test Pyramid**: Unit tests > integration tests > end-to-end tests
- **Fast Feedback**: Unit tests must run quickly (< 5 seconds total)
- **Clear Test Names**: Test names describe behavior being verified
- **Isolated Tests**: No dependencies between test cases

### Development Workflow

#### Setup

```bash
# Clone repository
git clone https://github.com/langadventurellc/trellis-mcp.git
cd trellis-mcp

# Install dependencies
uv sync

# Install pre-commit hooks
uv run pre-commit install

# Install in editable mode
uv pip install -e .
```

#### Daily Development

```bash
# Format code
uv run black src/

# Lint code
uv run flake8 src/

# Type check
uv run pyright src/

# Run unit tests
uv run pytest -q

# Run all quality checks
uv run poe quality
```

#### Common Commands

| Goal                    | Command                                          |
| ----------------------- | ------------------------------------------------ |
| Install dependencies    | `uv sync`                                        |
| Start server (STDIO)    | `uv run task-trellis-mcp serve`                  |
| Start server (HTTP)     | `uv run task-trellis-mcp serve --http localhost:8000` |
| Initialize planning     | `uv run task-trellis-mcp init`                   |
| All quality checks      | `uv run poe quality`                             |
| Run formatter           | `uv run black src/`                              |
| Run linter              | `uv run flake8 src/`                             |
| Type check              | `uv run pyright src/`                            |
| Run unit tests          | `uv run pytest -q`                               |

### Task-Centric Development

This project uses its own task management system for development:

#### Working with Tasks

```bash
# Claim next available task
uv run task-trellis-mcp claim-task

# List available tasks
uv run task-trellis-mcp list tasks --status open

# Complete a task with summary
uv run task-trellis-mcp complete T-task-id \
  --summary "Implemented feature with comprehensive tests" \
  --files-changed src/module.py,tests/test_module.py
```

### Contributing Guidelines

#### Before Starting

- Check existing issues and discussions
- Understand the Trellis MCP specification
- Review existing code patterns
- Set up development environment properly

#### Making Changes

- Create feature branch from `main`
- Ensure all quality checks pass
- Keep commits focused and atomic

#### Pull Request Process

- Provide clear description of changes
- Include test coverage information
- Document any breaking changes
- Link to relevant issues or discussions
- Ensure CI passes completely

### Performance Considerations

- **File Operations**: Use efficient file I/O patterns
- **Validation**: Cache validation results when appropriate
- **Dependencies**: Minimize external dependencies
- **Memory Usage**: Clean up resources properly
- **Cross-System Operations**: Optimize for common access patterns

## License

MIT License - See LICENSE file for details.

## Repository

[https://github.com/langadventurellc/trellis-mcp](https://github.com/langadventurellc/trellis-mcp)