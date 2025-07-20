# Task Claiming Workflows

Comprehensive guide to task claiming patterns and workflows using the Trellis MCP system. Covers priority-based, scope-based, and direct task claiming strategies for different development scenarios.

## Overview

Trellis MCP provides three distinct task claiming approaches, each optimized for different development workflows:

1. **Priority-Based Claiming** - Automatic selection of highest-priority available tasks
2. **Scope-Based Claiming** - Focused claiming within specific project boundaries
3. **Direct Task Claiming** - Precise claiming of specific tasks by ID

## Workflow Patterns

### Standard Development Workflow

**Use Case**: Normal development work where team members pick up next available priority work.

```javascript
// Step 1: Check available work
const availableTasks = await mcp.call('listBacklog', {
  projectRoot: './planning',
  status: 'open',
  sortByPriority: true
});

// Step 2: Claim highest priority task
const claimedTask = await mcp.call('claimNextTask', {
  projectRoot: './planning',
  worktree: 'feature/next-task'
});

// Step 3: Work on task, then complete
await mcp.call('completeTask', {
  projectRoot: './planning',
  taskId: claimedTask.task.id,
  summary: 'Completed implementation with tests',
  filesChanged: ['src/feature.js', 'tests/feature.test.js']
});
```

### Team-Based Development Workflow

**Use Case**: Multiple teams working on different areas of a large project.

```javascript
// Backend team workflow
const backendTask = await mcp.call('claimNextTask', {
  projectRoot: './planning',
  scope: 'E-backend-services',
  worktree: 'backend/feature'
});

// Frontend team workflow  
const frontendTask = await mcp.call('claimNextTask', {
  projectRoot: './planning',
  scope: 'E-frontend-development',
  worktree: 'frontend/feature'
});

// DevOps team workflow
const infraTask = await mcp.call('claimNextTask', {
  projectRoot: './planning', 
  scope: 'E-infrastructure',
  worktree: 'infra/enhancement'
});
```

### Issue-Driven Development Workflow

**Use Case**: Working on specific reported issues or feature requests.

```javascript
// Claim specific task linked to GitHub issue #456
const issueTask = await mcp.call('claimNextTask', {
  projectRoot: './planning',
  taskId: 'T-fix-authentication-bug',  // Maps to issue #456
  worktree: 'bugfix/auth-validation'
});

// Work on the specific issue
// Complete with reference to issue
await mcp.call('completeTask', {
  projectRoot: './planning',
  taskId: 'T-fix-authentication-bug',
  summary: 'Fixed authentication validation bug. Resolves GitHub issue #456.',
  filesChanged: ['src/auth/validator.js', 'tests/auth/validator.test.js']
});
```

### Sprint Planning Workflow

**Use Case**: Planning and executing focused sprints on specific features.

```javascript
// Sprint focused on user management features
const sprintFeatures = ['F-user-registration', 'F-user-profile', 'F-password-reset'];
const sprintTasks = [];

for (const feature of sprintFeatures) {
  try {
    const task = await mcp.call('claimNextTask', {
      projectRoot: './planning',
      scope: feature,
      worktree: `sprint-3/${feature}`
    });
    sprintTasks.push(task);
    console.log(`Claimed: ${task.task.title} from ${feature}`);
  } catch (error) {
    console.log(`No available tasks in ${feature}`);
  }
}
```

### Hotfix Workflow

**Use Case**: Emergency fixes that need immediate attention.

```javascript
// 1. Claim specific critical task
const hotfixTask = await mcp.call('claimNextTask', {
  projectRoot: './planning',
  taskId: 'T-security-vulnerability-patch',
  worktree: 'hotfix/security-patch'
});

// 2. Fast implementation and testing
// 3. Complete with detailed summary
await mcp.call('completeTask', {
  projectRoot: './planning', 
  taskId: 'T-security-vulnerability-patch',
  summary: 'Applied security patch for CVE-2025-0001. Updated input validation and added security tests.',
  filesChanged: [
    'src/security/validator.js',
    'src/middleware/auth.js', 
    'tests/security/validator.test.js'
  ]
});
```

### Code Review Follow-up Workflow

**Use Case**: Addressing specific feedback from code reviews.

```javascript
// Claim task for addressing code review feedback
const reviewTask = await mcp.call('claimNextTask', {
  projectRoot: './planning',
  taskId: 'T-address-review-feedback-pr-789',
  worktree: 'review/address-feedback'
});

// Make changes based on review
// Complete with reference to review
await mcp.call('completeTask', {
  projectRoot: './planning',
  taskId: 'T-address-review-feedback-pr-789', 
  summary: 'Addressed code review feedback: improved error handling, added input validation, updated tests per reviewer suggestions.',
  filesChanged: ['src/api/handlers.js', 'tests/api/handlers.test.js']
});
```

## Advanced Workflow Patterns

### Dependency-Aware Development

**Use Case**: Working on tasks with complex prerequisite relationships.

```javascript
// Check task dependencies before claiming
const taskInfo = await mcp.call('getObject', {
  id: 'T-implement-payment-flow',
  projectRoot: './planning'
});

// Verify prerequisites are complete
console.log('Prerequisites:', taskInfo.yaml.prerequisites);

// Claim only if ready
const paymentTask = await mcp.call('claimNextTask', {
  projectRoot: './planning',
  taskId: 'T-implement-payment-flow'
});
```

### Cross-System Task Management

**Use Case**: Projects mixing hierarchical and standalone tasks.

```javascript
// Claim hierarchical task with cross-system dependencies
const hierarchicalTask = await mcp.call('claimNextTask', {
  projectRoot: './planning',
  taskId: 'T-frontend-integration'  // Depends on standalone infra tasks
});

// Claim standalone urgent task
const standaloneTask = await mcp.call('claimNextTask', {
  projectRoot: './planning', 
  taskId: 'task-database-migration'  // Standalone critical task
});
```

### Parallel Development Workflow

**Use Case**: Multiple developers working on related features simultaneously.

```javascript
// Developer A: Claims from authentication epic
const authTask = await mcp.call('claimNextTask', {
  projectRoot: './planning',
  scope: 'E-authentication-system', 
  worktree: 'dev-a/auth-feature'
});

// Developer B: Claims from user management epic  
const userTask = await mcp.call('claimNextTask', {
  projectRoot: './planning',
  scope: 'E-user-management',
  worktree: 'dev-b/user-feature'
});

// Developer C: Claims specific high-priority task
const urgentTask = await mcp.call('claimNextTask', {
  projectRoot: './planning',
  taskId: 'T-critical-security-fix',
  worktree: 'dev-c/security-hotfix'
});
```

## Workflow Best Practices

### Task Selection Guidelines

1. **Use Priority-Based When**:
   - Starting fresh development session
   - No specific requirements or constraints
   - Following normal team workflow
   - Need to work on highest business value

2. **Use Scope-Based When**:
   - Working within team boundaries (frontend/backend)
   - Focusing on specific project areas
   - Coordinating parallel development efforts
   - Sprint planning with feature focus

3. **Use Direct Claiming When**:
   - Addressing specific reported issues
   - Following up on code review feedback
   - Implementing specific feature requirements
   - Resuming interrupted work
   - Emergency hotfixes

### Error Recovery Patterns

#### Handling Unavailable Tasks

```javascript
async function claimTaskWithFallback(primaryTaskId, fallbackScope) {
  try {
    // Try to claim specific task first
    return await mcp.call('claimNextTask', {
      projectRoot: './planning',
      taskId: primaryTaskId
    });
  } catch (error) {
    console.log(`Primary task unavailable: ${error.message}`);
    
    // Fall back to scope-based claiming
    return await mcp.call('claimNextTask', {
      projectRoot: './planning',
      scope: fallbackScope
    });
  }
}
```

#### Prerequisite Resolution

```javascript
async function ensurePrerequisitesComplete(taskId) {
  const task = await mcp.call('getObject', {
    id: taskId,
    projectRoot: './planning'
  });
  
  for (const prereq of task.yaml.prerequisites || []) {
    const prereqTask = await mcp.call('getObject', {
      id: prereq,
      projectRoot: './planning'
    });
    
    if (prereqTask.yaml.status !== 'done') {
      throw new Error(`Prerequisite ${prereq} not complete (status: ${prereqTask.yaml.status})`);
    }
  }
}
```

### Integration with Git Workflows

#### Feature Branch Workflow

```javascript
// Claim task and create feature branch
const task = await mcp.call('claimNextTask', {
  projectRoot: './planning',
  scope: 'F-user-authentication',
  worktree: 'feature/auth-enhancement'
});

// Git commands would be:
// git worktree add feature/auth-enhancement
// git checkout -b feature/auth-enhancement
```

#### Hotfix Branch Workflow

```javascript
// Emergency fix workflow
const hotfix = await mcp.call('claimNextTask', {
  projectRoot: './planning',
  taskId: 'T-critical-security-patch',
  worktree: 'hotfix/security-2025-001'
});

// Git commands would be:
// git worktree add hotfix/security-2025-001 main
// git checkout -b hotfix/security-2025-001
```

## Monitoring and Metrics

### Workflow Analytics

```javascript
// Track team productivity by scope
const backlogMetrics = await mcp.call('listBacklog', {
  projectRoot: './planning',
  scope: 'E-backend-services',
  status: 'done'
});

console.log(`Backend team completed: ${backlogMetrics.tasks.length} tasks`);
```

### Task Assignment Patterns

```javascript
// Monitor direct claiming vs priority-based patterns
const directClaims = taskHistory.filter(t => t.claimedWith === 'taskId');
const scopeClaims = taskHistory.filter(t => t.claimedWith === 'scope');
const priorityClaims = taskHistory.filter(t => t.claimedWith === 'priority');

console.log('Claiming patterns:', {
  direct: directClaims.length,
  scope: scopeClaims.length, 
  priority: priorityClaims.length
});
```

## Common Pitfalls and Solutions

### Anti-Patterns to Avoid

1. **Over-specific claiming**: Don't use direct claiming for routine work
2. **Ignoring prerequisites**: Always check dependencies before claiming
3. **Conflicting parameters**: Don't use scope + taskId together
4. **Stale task IDs**: Verify task still exists before direct claiming

### Error Prevention

```javascript
// Robust claiming with validation
async function robustClaimTask(options) {
  // Validate parameters
  if (options.scope && options.taskId) {
    throw new Error('Cannot specify both scope and taskId');
  }
  
  // If direct claiming, verify task exists
  if (options.taskId) {
    try {
      await mcp.call('getObject', {
        id: options.taskId,
        projectRoot: options.projectRoot
      });
    } catch (error) {
      throw new Error(`Task ${options.taskId} not found: ${error.message}`);
    }
  }
  
  return await mcp.call('claimNextTask', options);
}
```

## See Also

- [claimNextTask Tool Reference](../tools/claim-next-task.md)
- [Scope-Based Task Claiming](../scope-based-task-claiming.md)
- [Cross-System Prerequisites](../cross-system-prerequisites/)
- [MCP Tools API Reference](../api/mcp-tools.md)