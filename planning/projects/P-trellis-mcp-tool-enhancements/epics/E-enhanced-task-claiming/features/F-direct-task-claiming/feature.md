---
kind: feature
id: F-direct-task-claiming
title: Direct Task Claiming
status: in-progress
priority: high
prerequisites: []
created: '2025-07-20T13:11:12.443914'
updated: '2025-07-20T13:11:12.443914'
schema_version: '1.1'
parent: E-enhanced-task-claiming
---
# Direct Task Claiming Feature

## Purpose and Functionality

Enable users to claim specific tasks by ID through the `claimNextTask` tool, bypassing the priority-based selection algorithm. This provides precise control over task assignment and supports workflows where specific tasks need immediate attention regardless of their position in the priority queue.

## Key Components to Implement

### 1. Task ID Parameter Processing
- Accept `task_id` parameter with T- prefixed hierarchical task IDs
- Support standalone task IDs for cross-system compatibility
- Validate task ID format and existence across both task systems
- Return specific errors for invalid or non-existent task IDs

### 2. Direct Task Lookup and Validation
- Locate specific task by ID in hierarchical or standalone systems
- Validate task exists and is accessible within current project root
- Check task current status and prerequisite completion
- Handle edge cases for deleted or moved tasks

### 3. Atomic Task Claiming Logic
- Claim specific task regardless of priority order
- Update task status to 'in-progress' atomically
- Set worktree field if provided in request
- Handle concurrent claiming attempts with conflict detection

## Detailed Acceptance Criteria

### Task ID Processing
- [ ] **Parameter Format**: Accept task_id parameter with T- prefix or standalone format
- [ ] **ID Validation**: Validate task ID format matches expected patterns
- [ ] **Cross-System Lookup**: Find tasks in both hierarchical and standalone systems
- [ ] **Existence Verification**: Confirm task exists before attempting claim
- [ ] **Error Messages**: Clear errors for invalid/non-existent task IDs

### Task Status Validation
- [ ] **Open Status Check**: Verify task has status='open' before claiming
- [ ] **Prerequisite Validation**: Check all prerequisites have status='done'
- [ ] **Already Claimed Detection**: Handle tasks with status='in-progress' or other states
- [ ] **Completed Task Handling**: Appropriate error for tasks marked 'done'
- [ ] **Review Status Handling**: Handle tasks in 'review' status appropriately

### Claiming Operation
- [ ] **Atomic Status Update**: Change status to 'in-progress' in single operation
- [ ] **Timestamp Recording**: Update task modification timestamp
- [ ] **Worktree Assignment**: Set optional worktree field if provided
- [ ] **Conflict Prevention**: Handle simultaneous claiming attempts gracefully
- [ ] **Rollback Capability**: Undo partial changes if claiming fails

### Cross-System Compatibility
- [ ] **Hierarchical Tasks**: Support T- prefixed task IDs in project structure
- [ ] **Standalone Tasks**: Support standalone task IDs in planning/tasks-* directories
- [ ] **Mixed Environments**: Function correctly in projects with both task types
- [ ] **Path Resolution**: Correctly resolve task file paths for both systems
- [ ] **Validation Consistency**: Use same validation logic across task types

## Implementation Guidance

### Technical Approach
1. **Parameter Processing**: Add task_id parameter to claimNextTask tool interface
2. **Task Resolution**: Create task ID resolver that works across both systems
3. **Claiming Logic**: Extend existing claim logic to handle direct task selection
4. **Error Handling**: Comprehensive error handling for all failure scenarios

### Code Organization
- `src/trellis_mcp/tools/claim_next_task.py`: Add task_id parameter to tool
- `src/trellis_mcp/claim_next_task.py`: Implement direct claiming logic
- `src/trellis_mcp/task_resolver.py`: Create task ID resolution utilities
- `src/trellis_mcp/models/filter_params.py`: Add task_id parameter validation

### Algorithm Flow
```python
def claim_specific_task(project_root: str, task_id: str, worktree: str = ""):
    # 1. Validate and resolve task ID
    task_path = resolve_task_by_id(project_root, task_id)
    
    # 2. Load and validate task
    task_data = load_task(task_path)
    validate_task_claimable(task_data)
    
    # 3. Check prerequisites
    if not all_prerequisites_done(task_data.prerequisites):
        raise ValidationError("Prerequisites not complete")
    
    # 4. Atomically claim task
    claim_task(task_path, worktree)
    
    return build_response(task_data, task_path)
```

## Testing Requirements

### Unit Testing Focus
- Task ID validation and resolution across both systems
- Direct claiming logic with various task states
- Error handling for non-existent and invalid task IDs
- Atomic claiming operations and conflict detection

### Integration Testing Scenarios
- Direct claiming in mixed hierarchical/standalone environments
- Concurrent claiming attempts by multiple clients
- Claiming workflow integration with existing priority-based claiming
- Cross-system task resolution and validation

### Edge Case Testing
- Claiming tasks with complex prerequisite chains
- Handling deleted or moved tasks during claiming
- Recovery from partial claiming failures
- Performance with large numbers of tasks

## Security Considerations

### Access Control
- Task ID validation prevents unauthorized task access
- Claiming limited to tasks within specified project root
- No privilege escalation through direct task claiming

### Input Validation
- Strict task ID format validation prevents injection attacks
- Sanitize task ID parameters before file operations
- Validate task accessibility within project boundaries

### Atomic Operations
- Prevent race conditions in concurrent claiming scenarios
- Ensure task state consistency during claiming operations
- Rollback capabilities for failed claiming attempts

## Dependencies
- Uses existing task scanner and validation infrastructure
- Integrates with current claiming and status update mechanisms
- Requires task ID resolution utilities for cross-system support

### Log

