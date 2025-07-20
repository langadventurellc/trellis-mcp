# MCP Tools API Reference

Complete API reference for all Trellis MCP tools. This document provides detailed parameter specifications, response formats, and error codes for programmatic integration.

## Tool Overview

| Tool | Purpose | Enhanced Features |
|------|---------|-------------------|
| `claimNextTask` | Claim available tasks | Scope filtering, direct claiming |
| `createObject` | Create project objects | Cross-system prerequisites |
| `getObject` | Retrieve object details | Automatic kind inference, children discovery |
| `updateObject` | Modify object properties | Atomic updates, validation |
| `listBacklog` | Query task collections | Cross-system discovery, filtering |
| `completeTask` | Mark tasks complete | Logging, file tracking |
| `healthCheck` | Server status | Server info, diagnostics |

## claimNextTask

### Enhanced Parameters

```typescript
interface ClaimNextTaskParams {
  projectRoot: string;          // Required: Planning structure root
  worktree?: string;           // Optional: Worktree identifier
  scope?: string;              // Optional: Hierarchical scope (P-, E-, F-)
  taskId?: string;             // Optional: Direct task ID claiming
}
```

### Parameter Validation Rules

| Parameter | Format | Validation |
|-----------|--------|------------|
| `projectRoot` | string | Non-empty, valid path |
| `scope` | string | Must match `^(P\|E\|F)-[a-zA-Z0-9_-]+$` |
| `taskId` | string | T- prefix for hierarchical, or standalone format |

### Mutual Exclusivity

- **scope** and **taskId** cannot be used together
- If both provided, returns `INVALID_FIELD` error

### Response Format

```typescript
interface ClaimNextTaskResponse {
  task: {
    id: string;                // Clean task ID
    title: string;             // Task title
    status: "in-progress";     // Always in-progress after claiming
    priority: string;          // Task priority level
    parent: string | null;     // Parent feature ID (null for standalone)
    file_path: string;         // Path to task markdown file
    created: string;           // ISO timestamp
    updated: string;           // ISO timestamp
  };
  claimed_status: "in-progress";
  worktree: string;            // Worktree identifier if provided
  file_path: string;           // Path to claimed task file
}
```

### Direct Claiming Parameters

#### Task ID Formats

- **Hierarchical**: `T-<task-identifier>`
  - Example: `T-implement-authentication`
  - Example: `T-create-user-model`

- **Standalone**: `task-<task-identifier>`
  - Example: `task-security-audit`
  - Example: `task-database-migration`

#### Direct Claiming Behavior

```typescript
// Direct claiming bypasses priority-based selection
await mcp.call('claimNextTask', {
  projectRoot: './planning',
  taskId: 'T-specific-task'  // Claims this exact task
});

// Scope parameter ignored when taskId provided
await mcp.call('claimNextTask', {
  projectRoot: './planning',
  scope: 'P-project',        // Ignored
  taskId: 'T-specific-task'  // This takes precedence
});
```

### Error Codes

| Code | Condition | Description |
|------|-----------|-------------|
| `MISSING_REQUIRED_FIELD` | Empty projectRoot | Project root parameter required |
| `INVALID_FIELD` | Invalid scope format | Scope must be P-, E-, or F- prefixed |
| `INVALID_FIELD` | Invalid taskId format | Task ID format validation failed |
| `INVALID_FIELD` | Conflicting parameters | Cannot use scope + taskId together |
| `INVALID_FIELD` | Task not found | Specified task ID doesn't exist |
| `INVALID_FIELD` | Task not available | Task status prevents claiming |
| `CROSS_SYSTEM_PREREQUISITE_INVALID` | Prerequisites incomplete | Cross-system dependencies not met |

### Examples

#### Priority-Based Claiming

```javascript
const response = await mcp.call('claimNextTask', {
  projectRoot: './planning'
});
// Claims highest priority available task
```

#### Scope-Based Claiming

```javascript
const response = await mcp.call('claimNextTask', {
  projectRoot: './planning',
  scope: 'E-user-authentication'
});
// Claims from authentication epic only
```

#### Direct Task Claiming

```javascript
// Hierarchical task
const response = await mcp.call('claimNextTask', {
  projectRoot: './planning',
  taskId: 'T-implement-login-form'
});

// Standalone task
const response = await mcp.call('claimNextTask', {
  projectRoot: './planning', 
  taskId: 'task-security-audit'
});
```

## createObject

### Enhanced Prerequisites

```typescript
interface CreateObjectParams {
  kind: 'project' | 'epic' | 'feature' | 'task';
  title: string;
  projectRoot: string;
  id?: string;                    // Auto-generated if empty
  parent?: string;                // Required for epics/features
  status?: string;                // Default based on kind
  priority?: string;              // Default: 'normal'
  prerequisites?: string[];       // Cross-system support
  description?: string;           // Optional body content
}
```

### Cross-System Prerequisites

```javascript
// Task with mixed prerequisites
await mcp.call('createObject', {
  kind: 'task',
  title: 'Deploy user authentication',
  projectRoot: './planning',
  parent: 'F-user-auth',
  prerequisites: [
    'T-auth-implementation',    // Hierarchical task
    'task-database-setup',      // Standalone task
    'T-validation-update'       // Another hierarchical task
  ]
});
```

## getObject

### Automatic Kind Inference

```typescript
interface GetObjectParams {
  id: string;                     // Object ID (auto-detects type)
  projectRoot: string;
}

interface GetObjectResponse {
  yaml: Record<string, any>;      // YAML front-matter
  body: string;                   // Markdown content
  kind: string;                   // Inferred object type
  id: string;                     // Clean object ID
  children: Array<{               // Immediate children only
    id: string;
    title: string;
    status: string;
    kind: string;
    created: string;
  }>;
}
```

### Children Discovery

```javascript
// Get project with immediate epics
const project = await mcp.call('getObject', {
  id: 'P-ecommerce-platform',
  projectRoot: './planning'
});

console.log('Epics:', project.children);
// Returns immediate child epics only
```

## updateObject

### Atomic Updates

```typescript
interface UpdateObjectParams {
  id: string;                     // Object ID with prefix
  projectRoot: string;
  yamlPatch?: Record<string, any>; // YAML fields to update
  bodyPatch?: string;             // Replace entire body
  force?: boolean;                // Bypass safeguards
}
```

### Cross-System Prerequisite Updates

```javascript
// Update task prerequisites across systems
await mcp.call('updateObject', {
  id: 'T-user-registration',
  projectRoot: './planning',
  yamlPatch: {
    prerequisites: [
      'T-auth-setup',           // Hierarchical
      'task-database-init',     // Standalone
      'T-validation-rules'      // Hierarchical
    ]
  }
});
```

## listBacklog

### Cross-System Discovery

```typescript
interface ListBacklogParams {
  projectRoot: string;
  scope?: string;                 // Optional hierarchical scope
  status?: string;                // Filter by status
  priority?: string;              // Filter by priority
  sortByPriority?: boolean;       // Default: true
}

interface ListBacklogResponse {
  tasks: Array<{
    id: string;                   // Task ID (hierarchical or standalone)
    title: string;
    status: string;
    priority: string;
    parent: string | null;        // null for standalone tasks
    file_path: string;            // Full path to task file
    created: string;
    updated: string;
  }>;
}
```

### Mixed Task Discovery

```javascript
// Get all open tasks (hierarchical + standalone)
const allTasks = await mcp.call('listBacklog', {
  projectRoot: './planning',
  status: 'open'
});
// Returns tasks from both systems

// Get tasks within specific scope (hierarchical only)
const epicTasks = await mcp.call('listBacklog', {
  projectRoot: './planning',
  scope: 'E-user-management',
  status: 'open'
});
// Returns only hierarchical tasks within scope
```

## completeTask

### Enhanced Logging

```typescript
interface CompleteTaskParams {
  projectRoot: string;
  taskId: string;                 // Hierarchical or standalone
  summary?: string;               // Work summary
  filesChanged?: string[];        // List of modified files
}
```

### Cross-System Completion

```javascript
// Complete hierarchical task
await mcp.call('completeTask', {
  projectRoot: './planning',
  taskId: 'T-implement-auth',
  summary: 'Implemented authentication with JWT tokens and password hashing',
  filesChanged: ['src/auth.js', 'tests/auth.test.js']
});

// Complete standalone task
await mcp.call('completeTask', {
  projectRoot: './planning',
  taskId: 'task-security-audit',
  summary: 'Completed security audit, found no critical vulnerabilities',
  filesChanged: ['docs/security-report.md']
});
```

## Error Handling

### Standard Error Format

```typescript
interface TrellisError {
  errors: string[];               // Human-readable error messages
  error_codes: string[];          // Machine-readable error codes
  context: Record<string, any>;   // Additional error context
  object_kind?: string;           // Object type if applicable
}
```

### Common Error Patterns

#### Validation Errors

```javascript
try {
  await mcp.call('claimNextTask', {
    projectRoot: './planning',
    scope: 'invalid-scope'        // Missing P-, E-, F- prefix
  });
} catch (error) {
  // error.error_codes: ['INVALID_FIELD']
  // error.context.field: 'scope'
}
```

#### Cross-System Errors

```javascript
try {
  await mcp.call('claimNextTask', {
    projectRoot: './planning',
    taskId: 'T-task-with-broken-prereqs'
  });
} catch (error) {
  // error.error_codes: ['CROSS_SYSTEM_PREREQUISITE_INVALID']
  // error.context: { invalid_prerequisites: ['task-missing'] }
}
```

#### Parameter Conflicts

```javascript
try {
  await mcp.call('claimNextTask', {
    projectRoot: './planning',
    scope: 'P-project',
    taskId: 'T-specific-task'     // Cannot use both
  });
} catch (error) {
  // error.error_codes: ['INVALID_FIELD']
  // error.errors: ['Cannot specify both scope and taskId parameters']
}
```

## Performance Characteristics

### Caching and Optimization

| Operation | Cold Cache | Warm Cache | Notes |
|-----------|------------|------------|-------|
| Cross-system validation | 50-200ms | 1-5ms | Multi-layer caching |
| Kind inference | 10-50ms | <1ms | LRU cache |
| Task discovery | 100-500ms | 5-20ms | Scope-dependent |
| Direct claiming | 20-100ms | 2-10ms | Single file operation |

### Scalability Limits

- **Task count**: Optimized for 1,000-10,000 tasks per project
- **Prerequisite depth**: Validated for chains up to 20 levels
- **Cross-system references**: Efficient with mixed environments
- **Concurrent operations**: Atomic file operations prevent conflicts

## Integration Patterns

### Batch Operations

```javascript
// Claim multiple tasks with different strategies
const tasks = await Promise.all([
  mcp.call('claimNextTask', { projectRoot: './planning', scope: 'E-backend' }),
  mcp.call('claimNextTask', { projectRoot: './planning', scope: 'E-frontend' }),
  mcp.call('claimNextTask', { projectRoot: './planning', taskId: 'T-urgent-fix' })
]);
```

### Error Recovery

```javascript
async function robustTaskClaiming(options) {
  const strategies = [
    () => mcp.call('claimNextTask', { ...options, taskId: options.preferredTask }),
    () => mcp.call('claimNextTask', { ...options, scope: options.fallbackScope }),
    () => mcp.call('claimNextTask', { projectRoot: options.projectRoot })
  ];
  
  for (const strategy of strategies) {
    try {
      return await strategy();
    } catch (error) {
      console.log(`Strategy failed: ${error.message}`);
    }
  }
  throw new Error('All claiming strategies failed');
}
```

## Version Compatibility

### API Versioning

- **Current Version**: 1.1
- **Backward Compatibility**: All 1.0 APIs supported
- **Deprecation Policy**: 6-month notice for breaking changes

### Feature Detection

```javascript
// Check for direct claiming support
const healthInfo = await mcp.call('healthCheck', {});
if (healthInfo.schema_version >= '1.1') {
  // Direct claiming available
  const task = await mcp.call('claimNextTask', {
    projectRoot: './planning',
    taskId: 'T-specific-task'
  });
}
```

## See Also

- [claimNextTask Tool Documentation](../tools/claim-next-task.md)
- [Task Claiming Workflows](../workflows/task-claiming.md)
- [Cross-System Prerequisites](../cross-system-prerequisites/)
- [Error Handling Guide](../troubleshooting/error-handling.md)