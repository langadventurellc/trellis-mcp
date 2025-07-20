# Scope-Based Task Claiming

Enhanced task claiming functionality that enables focused work within specific project boundaries using the `claimNextTask` tool's scope parameter.

## Overview

Scope-based task claiming allows developers and AI assistants to claim tasks within defined hierarchical boundaries, enabling focused development work while maintaining the priority-based claiming logic. This feature supports three scope types: Project, Epic, and Feature levels.

## Scope Types and Behavior

### Project Scope (P-*)

**Format**: `P-<project-id>`  
**Boundary**: Entire project hierarchy plus standalone tasks  
**Use Case**: Working on any part of a specific project

```javascript
// Claim any task within the e-commerce project
await mcp.call('claimNextTask', {
  projectRoot: './planning',
  scope: 'P-ecommerce-platform'
});
```

**Includes**:
- All epics within the project
- All features within project epics  
- All tasks within project features
- Standalone tasks (not tied to hierarchy)

**Best for**: Project-focused development, mixed team environments

### Epic Scope (E-*)

**Format**: `E-<epic-id>`  
**Boundary**: Epic and its child features (hierarchical only)  
**Use Case**: Working on a specific major work stream

```javascript
// Claim tasks only from user authentication epic
await mcp.call('claimNextTask', {
  projectRoot: './planning', 
  scope: 'E-user-authentication-system'
});
```

**Includes**:
- All features within the epic
- All tasks within epic's features

**Excludes**:
- Standalone tasks (not part of hierarchy)
- Tasks from other epics

**Best for**: Epic-focused development, specialized teams

### Feature Scope (F-*)

**Format**: `F-<feature-id>`  
**Boundary**: Feature and its direct child tasks only  
**Use Case**: Working on specific functionality

```javascript
// Claim tasks only from login functionality feature  
await mcp.call('claimNextTask', {
  projectRoot: './planning',
  scope: 'F-login-functionality'
});
```

**Includes**:
- Tasks directly within the feature

**Excludes**:
- Tasks from other features
- Standalone tasks
- Tasks from sibling features

**Best for**: Feature-focused development, tight iteration loops

## Usage Examples

### Basic Scope Claiming

```javascript
// No scope - claim any available task (default behavior)
const anyTask = await mcp.call('claimNextTask', {
  projectRoot: './planning'
});

// Project scope - include entire project + standalone tasks
const projectTask = await mcp.call('claimNextTask', {
  projectRoot: './planning',
  scope: 'P-mobile-app-redesign'
});

// Epic scope - only epic's features and tasks
const epicTask = await mcp.call('claimNextTask', {
  projectRoot: './planning', 
  scope: 'E-payment-processing'
});

// Feature scope - only feature's direct tasks
const featureTask = await mcp.call('claimNextTask', {
  projectRoot: './planning',
  scope: 'F-checkout-workflow'
});
```

### Integration with Worktrees

```javascript
// Claim feature-scoped task with git worktree assignment
const result = await mcp.call('claimNextTask', {
  projectRoot: './planning',
  scope: 'F-user-registration',
  worktree: 'feature/user-registration'
});

console.log(`Claimed ${result.task.title} in worktree ${result.worktree}`);
```

### Cross-System Prerequisites

Scope filtering works seamlessly with cross-system prerequisites:

```javascript
// This will only claim tasks where ALL prerequisites are complete,
// even if prerequisites span hierarchical and standalone systems
const task = await mcp.call('claimNextTask', {
  projectRoot: './planning',
  scope: 'E-frontend-development'
});

// The claimed task might depend on:
// - Other tasks within the epic (hierarchical prerequisites)  
// - Standalone infrastructure tasks (cross-system prerequisites)
```

## Error Handling and Troubleshooting

### Common Error Scenarios

#### Invalid Scope Format

```javascript
// ❌ Invalid - missing prefix
scope: 'invalid-project-name'

// ❌ Invalid - wrong prefix
scope: 'T-task-id' 

// ❌ Invalid - special characters
scope: 'P-project@name#'

// ✅ Valid formats
scope: 'P-project-name'
scope: 'E-epic-name'  
scope: 'F-feature-name'
```

#### Scope Object Not Found

```javascript
try {
  await mcp.call('claimNextTask', {
    projectRoot: './planning',
    scope: 'P-nonexistent-project'
  });
} catch (error) {
  // Error: "Scope object not found: P-nonexistent-project"
  console.log('Project does not exist in planning structure');
}
```

#### No Eligible Tasks in Scope

```javascript
try {
  await mcp.call('claimNextTask', {
    projectRoot: './planning', 
    scope: 'F-completed-feature'
  });
} catch (error) {
  // Error: "No open tasks available within scope: F-completed-feature"
  console.log('All tasks in feature are completed or blocked');
}
```

### Troubleshooting Guide

| Error Type | Likely Cause | Solution |
|------------|--------------|----------|
| Invalid scope format | Incorrect prefix or characters | Use P-, E-, F- prefix with alphanumeric/dash/underscore only |
| Scope object not found | Typo in ID or object doesn't exist | Verify scope ID exists using `getObject` tool |
| No eligible tasks | All tasks completed/blocked | Check task statuses and prerequisites in scope |
| Empty project root | Missing projectRoot parameter | Provide valid path to planning directory |

### Debugging Scope Issues

1. **Verify scope object exists**:
   ```javascript
   const scopeInfo = await mcp.call('getObject', {
     id: 'P-my-project',
     projectRoot: './planning'
   });
   ```

2. **Check available tasks in scope**:
   ```javascript
   const tasks = await mcp.call('listBacklog', {
     projectRoot: './planning',
     scope: 'P-my-project',
     status: 'open'
   });
   ```

3. **Verify prerequisites**:
   ```javascript
   const task = await mcp.call('getObject', {
     id: 'T-blocked-task',
     projectRoot: './planning'
   });
   // Check task.yaml.prerequisites array
   ```

## Performance Considerations

### Scope Selection for Performance

- **Large Projects**: Use feature scope (F-*) for fastest claiming
- **Mixed Environments**: Use project scope (P-*) for balanced performance  
- **Epic-Focused Work**: Use epic scope (E-*) for medium performance
- **Global Claiming**: Omit scope for maximum flexibility

### Caching and Optimization

- **Warm Cache**: 1-5ms response times for repeated scope operations
- **Cold Cache**: 50-200ms for initial scope validation and task discovery
- **Multi-layer Caching**: Scope validation, prerequisite checking, and task discovery all cached
- **Cross-System Efficiency**: Mixed hierarchical/standalone validation optimized

### Best Practices

1. **Use appropriate scope granularity**:
   - Feature scope for focused sprints
   - Epic scope for larger work streams  
   - Project scope for mixed development

2. **Combine with task filtering**:
   ```javascript
   // Efficient: Scope + status filtering
   const urgentTasks = await mcp.call('listBacklog', {
     projectRoot: './planning',
     scope: 'E-critical-fixes',
     priority: 'high',
     status: 'open'
   });
   ```

3. **Monitor scope boundaries**:
   - Ensure scope contains eligible tasks before claiming
   - Use broader scope if narrow scope consistently empty
   - Balance focus vs. task availability

## Integration Patterns

### With Existing Workflows

Scope-based claiming preserves backward compatibility:

```javascript
// Existing workflow (no scope) - still works
const task1 = await mcp.call('claimNextTask', {
  projectRoot: './planning'
});

// Enhanced workflow (with scope) - new capability
const task2 = await mcp.call('claimNextTask', {
  projectRoot: './planning',
  scope: 'F-user-authentication'
});
```

### With Prerequisites

Scope filtering respects cross-system prerequisites:

```javascript
// Will only claim tasks where ALL prerequisites complete,
// regardless of whether prerequisites are in scope
const result = await mcp.call('claimNextTask', {
  projectRoot: './planning',
  scope: 'E-frontend-features'
});

// Claimed task might have prerequisites:
// - T-backend-api (outside scope but completed)  
// - T-ui-components (within scope and completed)
// - task-database-migration (standalone and completed)
```

### With AI Assistant Workflows

Natural language integration:

```javascript
// AI assistant can interpret:
// "Claim next task from user authentication epic"
const task = await mcp.call('claimNextTask', {
  projectRoot: './planning',
  scope: 'E-user-authentication'
});

// "Work on login feature specifically"  
const loginTask = await mcp.call('claimNextTask', {
  projectRoot: './planning',
  scope: 'F-login-feature'
});
```

## Advanced Use Cases

### Team Coordination

```javascript
// Backend team claims from backend epic
const backendTask = await mcp.call('claimNextTask', {
  projectRoot: './planning',
  scope: 'E-backend-services',
  worktree: 'backend/feature'
});

// Frontend team claims from frontend epic  
const frontendTask = await mcp.call('claimNextTask', {
  projectRoot: './planning',
  scope: 'E-frontend-development', 
  worktree: 'frontend/feature'
});
```

### Sprint Planning

```javascript
// Sprint focused on specific features
const sprintTasks = [];
const features = ['F-user-login', 'F-password-reset', 'F-user-profile'];

for (const feature of features) {
  try {
    const task = await mcp.call('claimNextTask', {
      projectRoot: './planning',
      scope: feature
    });
    sprintTasks.push(task);
  } catch (error) {
    console.log(`No available tasks in ${feature}`);
  }
}
```

### Hotfix Workflows

```javascript
// Emergency scope for critical fixes
const hotfixTask = await mcp.call('claimNextTask', {
  projectRoot: './planning', 
  scope: 'E-security-patches',
  worktree: 'hotfix/security'
});
```

## See Also

- [Task Management Workflow](./task-management-workflow.md)
- [Cross-System Prerequisites](./cross-system-prerequisites/)
- [MCP Tool Reference](./mcp-tools-reference.md)
- [Performance Optimization](./performance-optimization.md)