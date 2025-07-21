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
| `force_claim` | boolean | No | Bypass validation when claiming specific task (only with `taskId`) |

## Enhanced Parameter Validation

The `claimNextTask` tool implements comprehensive parameter validation with mutual exclusivity rules and parameter combination logic to ensure correct usage and provide clear error guidance.

### Parameter Combination Rules

#### Valid Combinations

```javascript
// Basic claiming (default behavior)
{ projectRoot: './planning' }

// Legacy pattern with worktree
{ projectRoot: './planning', worktree: 'feature/auth' }

// Scope-based claiming
{ projectRoot: './planning', scope: 'P-ecommerce-platform' }
{ projectRoot: './planning', scope: 'E-user-authentication' }
{ projectRoot: './planning', scope: 'F-login-functionality' }

// Scope-based claiming with worktree
{ projectRoot: './planning', scope: 'P-project', worktree: 'feature/epic' }

// Direct task claiming
{ projectRoot: './planning', taskId: 'T-implement-auth' }
{ projectRoot: './planning', taskId: 'task-standalone-setup' }

// Direct claiming with worktree
{ projectRoot: './planning', taskId: 'T-urgent-fix', worktree: 'hotfix/critical' }

// Force claiming (bypasses prerequisites and status validation)
{ projectRoot: './planning', taskId: 'T-blocked-task', force_claim: true }
{ projectRoot: './planning', taskId: 'T-in-progress-task', force_claim: true, worktree: 'reassign/urgent' }
```

#### Invalid Combinations

```javascript
// ❌ Mutual exclusivity violation
{ projectRoot: './planning', scope: 'P-project', taskId: 'T-task' }
// Error: "Cannot specify both scope and taskId parameters"

// ❌ Force claim without task ID
{ projectRoot: './planning', force_claim: true }
// Error: "force_claim parameter requires taskId to be specified"

// ❌ Force claim with scope (not supported)
{ projectRoot: './planning', scope: 'P-project', force_claim: true }
// Error: "Cannot use force_claim with scope parameter"
```

### Parameter Format Validation

#### Project Root Validation
- **Required**: Cannot be empty or null
- **Format**: Valid file system path
- **Examples**: `./planning`, `/path/to/planning`, `../project/planning`

#### Scope ID Validation
- **Format**: Must use P-, E-, or F- prefix followed by alphanumeric, hyphen, or underscore characters
- **Pattern**: `^[PEF]-[A-Za-z0-9_-]+$`
- **Valid Examples**: `P-ecommerce-platform`, `E-user-auth`, `F-login-form`
- **Invalid Examples**: `project-name`, `P_invalid`, `Epic-name`

#### Task ID Validation
- **Hierarchical Tasks**: Must use T- prefix (e.g., `T-implement-auth`, `T-create-user-model`)
- **Standalone Tasks**: Valid standalone format (e.g., `task-security-audit`, `task-database-setup`)
- **Pattern Validation**: Automatically detected and validated based on ID format

#### Force Claim Validation
- **Type**: Boolean only (true/false)
- **Scope**: Only valid when `taskId` is specified
- **Purpose**: Bypasses prerequisite validation and status restrictions
- **Default**: `false` (maintains standard claiming behavior)

### Parameter Interaction Rules

- **Mutual Exclusivity**: `scope` and `taskId` cannot be used together
  - Use `scope` for filtering tasks within project boundaries
  - Use `taskId` for direct claiming of specific tasks
- **Force Claim Scope**: `force_claim=true` only applies when `taskId` is specified
  - Cannot be used with scope-based claiming
  - Enables claiming tasks regardless of prerequisites or status
- **Priority Override**: When `taskId` is provided, priority-based selection is bypassed
- **Backward Compatibility**: Omitting enhanced parameters maintains existing priority-based behavior

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

### Force Claiming

```javascript
// Force claim task with incomplete prerequisites
const blockedTask = await mcp.call('claimNextTask', {
  projectRoot: './planning',
  taskId: 'T-blocked-by-dependencies',
  force_claim: true
});

// Force claim in-progress task for reassignment
const inProgressTask = await mcp.call('claimNextTask', {
  projectRoot: './planning',
  taskId: 'T-currently-in-progress',
  force_claim: true,
  worktree: 'reassign/urgent-priority'
});

// Force claim completed task for reopening
const completedTask = await mcp.call('claimNextTask', {
  projectRoot: './planning',
  taskId: 'T-completed-task',
  force_claim: true,
  worktree: 'reopen/bug-found'
});

// Force claim task in review status
const reviewTask = await mcp.call('claimNextTask', {
  projectRoot: './planning',
  taskId: 'T-task-under-review',
  force_claim: true
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

### Parameter Validation Errors

#### Empty Project Root

```javascript
try {
  await mcp.call('claimNextTask', {
    projectRoot: ''  // Empty string
  });
} catch (error) {
  // Error: "Project root parameter cannot be empty or None"
  // Solution: Provide valid path like './planning' or '/path/to/planning'
}
```

#### Invalid Scope Format

```javascript
try {
  await mcp.call('claimNextTask', {
    projectRoot: './planning',
    scope: 'invalid-scope'  // Missing P-, E-, F- prefix
  });
} catch (error) {
  // Error: "Invalid scope ID format: 'invalid-scope'. Must use P-, E-, or F- prefix"
  // Solution: Use P-project-name, E-epic-name, or F-feature-name
}
```

#### Invalid Task ID Format

```javascript
try {
  await mcp.call('claimNextTask', {
    projectRoot: './planning',
    taskId: 'invalid-task-id'  // Invalid format
  });
} catch (error) {
  // Error: "Invalid task ID format: 'invalid-task-id'"
  // Solution: Use T-task-name for hierarchical or task-name for standalone
}
```

#### Mutual Exclusivity Violation

```javascript
try {
  await mcp.call('claimNextTask', {
    projectRoot: './planning',
    scope: 'P-project',
    taskId: 'T-specific-task'  // Cannot use both
  });
} catch (error) {
  // Error: "Cannot specify both scope 'P-project' and taskId 'T-specific-task' parameters"
  // Solution: Use either scope for filtering OR taskId for direct claiming
}
```

#### Force Claim Without Task ID

```javascript
try {
  await mcp.call('claimNextTask', {
    projectRoot: './planning',
    force_claim: true  // Missing taskId
  });
} catch (error) {
  // Error: "force_claim parameter requires taskId to be specified"
  // Solution: Provide taskId when using force_claim=true
}
```

#### Force Claim With Scope

```javascript
try {
  await mcp.call('claimNextTask', {
    projectRoot: './planning',
    scope: 'P-project',
    force_claim: true  // Not compatible with scope
  });
} catch (error) {
  // Error: "Cannot use force_claim with scope parameter"
  // Solution: Use force_claim only with direct task claiming (taskId)
}
```

### Task State and Availability Errors

#### Task Not Found

```javascript
try {
  await mcp.call('claimNextTask', {
    projectRoot: './planning',
    taskId: 'T-nonexistent-task'
  });
} catch (error) {
  // Error: "Task not found: T-nonexistent-task"
  // Solution: Verify task ID using getObject or listBacklog
}
```

#### Task Not Available (Status)

```javascript
try {
  await mcp.call('claimNextTask', {
    projectRoot: './planning',
    taskId: 'T-in-progress-task'  // Without force_claim
  });
} catch (error) {
  // Error: "Task T-in-progress-task is not available for claiming (status: in-progress)"
  // Solutions: 
  // 1. Wait for task completion 
  // 2. Use force_claim=true to override status restriction
}
```

#### Prerequisites Not Complete

```javascript
try {
  await mcp.call('claimNextTask', {
    projectRoot: './planning',
    taskId: 'T-blocked-task'  // Without force_claim
  });
} catch (error) {
  // Error: "Task T-blocked-task has incomplete prerequisites: [T-setup-database, T-create-schema]"
  // Solutions:
  // 1. Complete prerequisite tasks first
  // 2. Use force_claim=true to bypass prerequisite validation
}
```

#### Scope Object Not Found

```javascript
try {
  await mcp.call('claimNextTask', {
    projectRoot: './planning',
    scope: 'P-nonexistent-project'
  });
} catch (error) {
  // Error: "Specified scope object not found: P-nonexistent-project"
  // Solution: Verify scope ID exists using getObject
}
```

#### No Tasks Available in Scope

```javascript
try {
  await mcp.call('claimNextTask', {
    projectRoot: './planning',
    scope: 'F-completed-feature'
  });
} catch (error) {
  // Error: "No eligible tasks available within scope boundaries"
  // Solution: Check scope for open tasks or use broader scope
}
```

### Comprehensive Error Reference

| Error Type | Error Code | Description | Solution |
|------------|------------|-------------|----------|
| **Parameter Validation** |
| Empty project root | `MISSING_REQUIRED_FIELD` | Project root cannot be empty | Provide valid path to planning directory |
| Invalid scope format | `INVALID_FIELD` | Scope must use P-, E-, F- prefix | Use correct format: P-name, E-name, F-name |
| Invalid task ID format | `INVALID_FIELD` | Task ID format validation failed | Use T- prefix for hierarchical or valid standalone format |
| Mutual exclusivity | `INVALID_FIELD` | Cannot use scope + taskId together | Choose either scope OR taskId parameter |
| Force claim scope error | `INVALID_FIELD` | force_claim requires taskId | Use force_claim only with direct task claiming |
| **Task Availability** |
| Task not found | `INVALID_FIELD` | Task ID doesn't exist | Verify task ID using getObject or listBacklog |
| Invalid task status | `INVALID_FIELD` | Task not in claimable status | Use force_claim=true to override or wait for task |
| Prerequisites incomplete | `CROSS_SYSTEM_PREREQUISITE_INVALID` | Dependent tasks not completed | Complete prerequisites or use force_claim=true |
| Scope not found | `INVALID_FIELD` | Scope object doesn't exist | Verify scope ID exists in planning structure |
| No available tasks | `INVALID_FIELD` | No eligible tasks in scope | Check scope for open tasks or broaden scope |

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

4. **Use force claiming when**:
   - Emergency task reassignment is needed
   - Reopening completed tasks due to discovered issues
   - Overriding prerequisite blocking in exceptional circumstances
   - Taking over abandoned in-progress tasks

### Parameter Validation Best Practices

1. **Validate parameters locally** before calling the tool when possible
2. **Handle validation errors gracefully** with user-friendly messages
3. **Use specific error codes** for programmatic error handling
4. **Provide clear feedback** about parameter format requirements
5. **Test parameter combinations** in development environments first

### Force Claim Security Considerations

- **Audit Logging**: All force claim operations are logged with original status, target status, and worktree context
- **Use Sparingly**: Reserve force claiming for exceptional circumstances only
- **Review Process**: Consider implementing review processes for force claim operations
- **Documentation**: Document the reason for force claiming in commit messages or task logs

## Migration Guide

### Backward Compatibility

The enhanced parameter validation system is **fully backward compatible** with existing claimNextTask usage patterns. All previous parameter combinations continue to work without changes.

#### Legacy Usage (Still Supported)

```javascript
// Basic claiming - no changes needed
await mcp.call('claimNextTask', {
  projectRoot: './planning'
});

// With worktree - no changes needed  
await mcp.call('claimNextTask', {
  projectRoot: './planning',
  worktree: 'feature/my-branch'
});
```

#### Migrating to Enhanced Parameters

**Before (Legacy):**
```javascript
// Manual task selection after claiming
const task = await mcp.call('claimNextTask', { projectRoot: './planning' });
if (task.task.id !== 'T-desired-task') {
  // Manual workaround needed
}
```

**After (Enhanced):**
```javascript
// Direct task claiming
const task = await mcp.call('claimNextTask', {
  projectRoot: './planning',
  taskId: 'T-desired-task'
});
```

**Before (No scope filtering):**
```javascript
// Claimed tasks from entire project
const task = await mcp.call('claimNextTask', { projectRoot: './planning' });
// Had to manually filter or check task scope
```

**After (With scope filtering):**
```javascript
// Claim only from specific epic
const task = await mcp.call('claimNextTask', {
  projectRoot: './planning',
  scope: 'E-user-authentication'
});
```

### Adoption Strategy

#### Phase 1: Update Error Handling
Update your error handling to recognize the new validation error messages:

```javascript
try {
  await mcp.call('claimNextTask', params);
} catch (error) {
  if (error.message.includes('Cannot specify both scope and taskId')) {
    // Handle mutual exclusivity error
    console.error('Invalid parameter combination:', error.message);
  } else if (error.message.includes('force_claim parameter requires taskId')) {
    // Handle force claim validation error
    console.error('Force claim usage error:', error.message);
  } else {
    // Handle other errors
    console.error('Claiming failed:', error.message);
  }
}
```

#### Phase 2: Adopt Enhanced Parameters
Gradually adopt the new parameter capabilities:

```javascript
// Add scope filtering for team-based workflows
const teamTask = await mcp.call('claimNextTask', {
  projectRoot: './planning',
  scope: 'E-my-team-epic',
  worktree: 'team/feature-branch'
});

// Use direct claiming for specific issues
const bugfixTask = await mcp.call('claimNextTask', {
  projectRoot: './planning', 
  taskId: 'T-fix-critical-bug',
  worktree: 'hotfix/issue-123'
});
```

#### Phase 3: Advanced Features
Implement advanced features like force claiming for specific workflows:

```javascript
// Emergency reassignment workflow
async function emergencyReassign(taskId, newWorktree) {
  try {
    return await mcp.call('claimNextTask', {
      projectRoot: './planning',
      taskId: taskId,
      force_claim: true,
      worktree: newWorktree
    });
  } catch (error) {
    console.error('Emergency reassignment failed:', error.message);
    throw error;
  }
}
```

### Breaking Changes

**None.** The enhanced parameter validation system maintains full backward compatibility. All existing code will continue to work without modifications.

### New Validation Errors

Be prepared to handle these new validation error scenarios:

- **Parameter format validation errors** (invalid scope/task ID formats)
- **Parameter combination errors** (mutual exclusivity violations)
- **Force claim validation errors** (incorrect force_claim usage)

Update your error handling to provide user-friendly messages for these new error types.

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