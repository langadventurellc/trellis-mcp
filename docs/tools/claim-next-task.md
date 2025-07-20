# claimNextTask Tool

The `claimNextTask` tool automatically claims the next highest-priority open task with all prerequisites completed, setting its status to 'in-progress'. Enhanced with scope-based filtering and direct task claiming capabilities.

## Overview

The `claimNextTask` tool provides three claiming modes:

1. **Priority-Based Claiming** (default) - Claims highest priority available task
2. **Scope-Based Claiming** - Claims tasks within specific project boundaries  
3. **Direct Task Claiming** - Claims a specific task by ID

## Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `projectRoot` | string | Yes | Root directory for the planning structure |
| `worktree` | string | No | Optional worktree identifier to stamp on claimed task |
| `scope` | string | No | Hierarchical scope for task filtering (P-, E-, F- prefixed) |
| `taskId` | string | No | Specific task ID to claim directly |

### Parameter Interaction Rules

- **Mutual Exclusivity**: `scope` and `taskId` cannot be used together
- **Priority Override**: When `taskId` is provided, priority-based selection is bypassed
- **Backward Compatibility**: Omitting both maintains existing priority-based behavior

## Usage Examples

### Priority-Based Claiming (Default)

```javascript
// Claim highest priority task from anywhere
const task = await mcp.call('claimNextTask', {
  projectRoot: './planning'
});
```

### Scope-Based Claiming

```javascript
// Claim task within project scope
const projectTask = await mcp.call('claimNextTask', {
  projectRoot: './planning',
  scope: 'P-ecommerce-platform'
});

// Claim task within epic scope
const epicTask = await mcp.call('claimNextTask', {
  projectRoot: './planning', 
  scope: 'E-user-authentication'
});

// Claim task within feature scope
const featureTask = await mcp.call('claimNextTask', {
  projectRoot: './planning',
  scope: 'F-login-functionality'
});
```

### Direct Task Claiming

```javascript
// Claim specific hierarchical task by ID
const specificTask = await mcp.call('claimNextTask', {
  projectRoot: './planning',
  taskId: 'T-implement-user-auth'
});

// Claim specific standalone task by ID
const standaloneTask = await mcp.call('claimNextTask', {
  projectRoot: './planning',
  taskId: 'task-security-audit'
});
```

### With Worktree Assignment

```javascript
// Direct claiming with worktree
const taskWithWorktree = await mcp.call('claimNextTask', {
  projectRoot: './planning',
  taskId: 'T-create-login-form',
  worktree: 'feature/auth-forms'
});
```

## Response Format

```javascript
{
  "task": {
    "id": "T-implement-user-auth",
    "title": "Implement user authentication system",
    "status": "in-progress",
    "priority": "high", 
    "parent": "F-user-management",
    "file_path": "/path/to/task/file.md",
    "created": "2025-07-20T10:00:00.000Z",
    "updated": "2025-07-20T14:30:00.000Z"
  },
  "claimed_status": "in-progress",
  "worktree": "feature/auth",
  "file_path": "/path/to/task/file.md"
}
```

## Direct Task Claiming

### Supported Task ID Formats

- **Hierarchical Tasks**: `T-<task-name>` (e.g., `T-implement-auth`, `T-create-user-model`)
- **Standalone Tasks**: `task-<task-name>` (e.g., `task-security-audit`, `task-database-setup`)

### Prerequisites and Validation

When claiming a task directly:

1. **Task Existence**: Verifies task exists in either hierarchical or standalone systems
2. **Status Check**: Ensures task has `status='open'` 
3. **Prerequisite Validation**: Confirms all prerequisites have `status='done'`
4. **Cross-System Support**: Prerequisites can span hierarchical and standalone tasks

### Direct Claiming vs Priority-Based

| Aspect | Priority-Based | Direct Claiming |
|--------|----------------|-----------------|
| Selection | Highest priority available | Specific task by ID |
| Prerequisites | Must be complete | Must be complete |
| Status | Must be 'open' | Must be 'open' |
| Scope Filtering | Respects scope parameter | Ignores scope parameter |
| Use Case | Normal workflow | Specific task needed |

## Error Handling

### Common Error Scenarios

#### Invalid Task ID

```javascript
try {
  await mcp.call('claimNextTask', {
    projectRoot: './planning',
    taskId: 'T-nonexistent-task'
  });
} catch (error) {
  // Error: "Task not found: T-nonexistent-task"
}
```

#### Task Already Claimed

```javascript
try {
  await mcp.call('claimNextTask', {
    projectRoot: './planning', 
    taskId: 'T-in-progress-task'
  });
} catch (error) {
  // Error: "Task T-in-progress-task is not available for claiming (status: in-progress)"
}
```

#### Prerequisites Not Complete

```javascript
try {
  await mcp.call('claimNextTask', {
    projectRoot: './planning',
    taskId: 'T-blocked-task'
  });
} catch (error) {
  // Error: "Task T-blocked-task has incomplete prerequisites: [T-setup-database]"
}
```

#### Conflicting Parameters

```javascript
try {
  await mcp.call('claimNextTask', {
    projectRoot: './planning',
    scope: 'P-project',
    taskId: 'T-specific-task'  // Not allowed together
  });
} catch (error) {
  // Error: "Cannot specify both scope and taskId parameters"
}
```

### Error Reference

| Error Type | Description | Solution |
|------------|-------------|----------|
| Task not found | Task ID doesn't exist | Verify task ID using `getObject` or `listBacklog` |
| Invalid status | Task not in 'open' status | Check task status, wait for completion if in-progress |
| Prerequisites incomplete | Dependent tasks not done | Complete prerequisite tasks first |
| Invalid format | Task ID format incorrect | Use T- prefix for hierarchical, valid format for standalone |
| Parameter conflict | scope + taskId together | Use either scope OR taskId, not both |

## Performance Considerations

### Direct Claiming Performance

- **Task Resolution**: O(1) lookup using task ID
- **Prerequisite Checking**: Cached cross-system validation (1-5ms warm cache)
- **File Operations**: Single file read/write for claiming operation
- **Optimal Use**: When you know specific task to work on

### Best Practices

1. **Use direct claiming when**:
   - Working on specific reported issues
   - Following up on code review feedback
   - Implementing specific feature requirements
   - Resuming interrupted work

2. **Use scope-based claiming when**:
   - Working within team boundaries
   - Focusing on specific project areas
   - Coordinating parallel development

3. **Use priority-based claiming when**:
   - Starting new work session
   - No specific task preferences
   - Following normal development workflow

## Integration Patterns

### With Git Worktrees

```javascript
// Create worktree and claim specific task
const result = await mcp.call('claimNextTask', {
  projectRoot: './planning',
  taskId: 'T-implement-payment-flow',
  worktree: 'feature/payment-integration'
});

// Use returned worktree info for git operations
console.log(`Working in: ${result.worktree}`);
```

### With AI Assistant Workflows

Direct claiming enables natural language task assignment:

```javascript
// AI can interpret: "Work on the user authentication task"
const authTask = await mcp.call('claimNextTask', {
  projectRoot: './planning',
  taskId: 'T-user-authentication'
});

// "Continue work on the login form implementation"
const loginTask = await mcp.call('claimNextTask', {
  projectRoot: './planning', 
  taskId: 'T-create-login-form'
});
```

### With Issue Tracking

```javascript
// Map GitHub issue to specific task
const issueTask = await mcp.call('claimNextTask', {
  projectRoot: './planning',
  taskId: 'T-fix-login-validation',  // Links to GitHub issue #123
  worktree: 'bugfix/login-validation'
});
```

## See Also

- [Scope-Based Task Claiming](../scope-based-task-claiming.md)
- [Task Management Workflows](../workflows/task-claiming.md)
- [Cross-System Prerequisites](../cross-system-prerequisites/)
- [MCP Tools API Reference](../api/mcp-tools.md)