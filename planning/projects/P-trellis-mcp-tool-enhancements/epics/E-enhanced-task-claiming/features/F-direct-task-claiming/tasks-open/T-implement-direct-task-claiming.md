---
kind: task
id: T-implement-direct-task-claiming
title: Implement direct task claiming logic in core claim module
status: open
priority: high
prerequisites:
- T-create-task-id-resolution
created: '2025-07-20T15:18:44.367417'
updated: '2025-07-20T15:22:19.647321'
schema_version: '1.1'
parent: F-direct-task-claiming
---
## Context

Extend the core claiming logic in `claim_next_task.py` to support direct task claiming by ID. This involves adding a new code path that locates a specific task by ID, validates its claimability, and claims it atomically.

## Technical Approach

1. **Add direct claiming function** to handle task_id-based claiming
2. **Extend main claim_next_task function** to route between priority-based and direct claiming
3. **Integrate task ID resolution** using the new task_resolver utility
4. **Maintain atomic claiming operations** with proper status updates and error handling
5. **Create comprehensive unit tests** for all claiming scenarios

## Implementation Details

### File to Modify
- `src/trellis_mcp/claim_next_task.py`

### New Function to Add
```python
def claim_specific_task(
    project_root: str, 
    task_id: str, 
    worktree: str = ""
) -> Dict[str, Any]:
    """Claim a specific task by ID with validation and atomic updates."""
```

### Core Logic Flow
1. **Resolve task ID** using task_resolver.resolve_task_by_id()
2. **Load task data** from resolved file path
3. **Validate task status** (must be OPEN)
4. **Check prerequisites** using existing dependency_resolver.is_unblocked()
5. **Atomic claim operation** using existing write_object() for status update
6. **Return standardized response** matching current claim_next_task format

### Integration Points
- Use task_resolver for ID-to-path resolution
- Leverage existing TaskModel loading and validation
- Use dependency_resolver.is_unblocked() for prerequisite checking
- Apply same atomic update patterns as priority-based claiming

### Error Handling
- TaskNotFoundError for non-existent task IDs
- ValidationError for invalid task states (not OPEN, blocked prerequisites)
- Proper error context and codes for API consumers

### Unit Test Requirements
Create `tests/test_direct_claim_next_task.py` with:
- **Direct claiming success tests**: Valid task IDs across both systems
- **Status validation tests**: Tasks with various statuses (IN_PROGRESS, DONE, REVIEW should fail)
- **Prerequisite validation tests**: Blocked and unblocked task scenarios
- **Atomic operation tests**: Verify status updates work correctly
- **Error handling tests**: All failure scenarios (not found, invalid state, blocked)
- **Response format tests**: Verify response matches existing API format
- **Integration tests**: Work with both hierarchical and standalone tasks
- **Concurrent access tests**: Mock atomic operations under concurrent load

## Acceptance Criteria

- [ ] **Task Resolution**: Successfully locates tasks by ID across both systems
- [ ] **Status Validation**: Verifies task status is OPEN before claiming
- [ ] **Prerequisite Checking**: Validates all prerequisites are completed
- [ ] **Atomic Claiming**: Updates task status to IN_PROGRESS atomically
- [ ] **Worktree Support**: Optional worktree assignment during claiming
- [ ] **Error Handling**: Comprehensive error handling for all failure scenarios
- [ ] **Response Format**: Returns standardized response matching existing API
- [ ] **Unit Test Coverage**: Comprehensive tests for all claiming scenarios

## Dependencies
- T-create-task-id-resolution (task resolver utility)

## Testing Requirements
- Unit tests for direct claiming with valid task IDs
- Status validation tests (non-OPEN tasks should fail)
- Prerequisite validation tests (blocked tasks should fail)
- Atomic operation tests (verify status updates)
- Error handling tests for all failure scenarios
- Integration tests with both hierarchical and standalone tasks