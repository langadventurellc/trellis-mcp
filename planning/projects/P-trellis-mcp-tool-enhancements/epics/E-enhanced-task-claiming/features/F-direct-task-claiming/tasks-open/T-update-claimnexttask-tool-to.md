---
kind: task
id: T-update-claimnexttask-tool-to
title: Update claimNextTask tool to route between priority and direct claiming
status: open
priority: normal
prerequisites:
- T-add-task-id-parameter-to
- T-implement-direct-task-claiming
created: '2025-07-20T15:18:59.252142'
updated: '2025-07-20T15:22:36.747556'
schema_version: '1.1'
parent: F-direct-task-claiming
---
## Context

Update the MCP tool handler to intelligently route between priority-based claiming (existing behavior) and direct task claiming (new functionality) based on whether a task_id parameter is provided.

## Technical Approach

1. **Update tool handler logic** to check for task_id parameter presence
2. **Route to appropriate claiming function** based on parameter presence
3. **Maintain consistent response format** for both claiming modes
4. **Preserve backward compatibility** for existing API consumers
5. **Create unit tests** for routing logic and integration

## Implementation Details

### File to Modify
- `src/trellis_mcp/tools/claim_next_task.py`

### Handler Logic Updates
```python
async def claim_next_task_handler(args: ClaimNextTaskArgs) -> Dict[str, Any]:
    if args.task_id and args.task_id.strip():
        # Direct claiming by task ID
        return claim_specific_task(
            project_root=args.project_root,
            task_id=args.task_id.strip(),
            worktree=args.worktree,
            scope=args.scope  # May need scope validation for direct claims
        )
    else:
        # Priority-based claiming (existing behavior)
        return claim_next_task(
            project_root=args.project_root,
            worktree=args.worktree,
            scope=args.scope
        )
```

### Parameter Validation
- Validate task_id format when provided (delegate to core logic)
- Handle scope parameter interaction with direct claiming
- Maintain existing parameter validation for other fields

### Response Consistency
- Ensure both claiming modes return identical response structure
- Preserve all existing response fields and formatting
- Maintain error response format consistency

### Unit Test Requirements
Update `tests/tools/test_claim_next_task_tool.py` with:
- **Routing logic tests**: Verify correct function called based on task_id presence
- **Response consistency tests**: Both modes return identical response structure
- **Backward compatibility tests**: Existing API calls work unchanged
- **Error propagation tests**: Errors from both modes handled consistently
- **Scope integration tests**: Scope parameter works with direct claiming
- **Integration tests**: End-to-end testing through tool interface
- **Mock core functions**: Isolate tool routing logic for testing

## Acceptance Criteria

- [ ] **Parameter Detection**: Correctly detects presence of task_id parameter
- [ ] **Routing Logic**: Routes to direct claiming when task_id provided, priority-based otherwise
- [ ] **Response Consistency**: Both modes return identical response structure
- [ ] **Backward Compatibility**: Existing API calls work unchanged
- [ ] **Error Handling**: Proper error propagation from both claiming modes
- [ ] **Scope Integration**: Scope parameter works correctly with direct claiming
- [ ] **Unit Test Coverage**: Comprehensive tests for routing and integration logic

## Dependencies
- T-add-task-id-parameter-to (tool interface updates)
- T-implement-direct-task-claiming (core direct claiming logic)

## Testing Requirements
- Integration tests for both claiming modes through tool interface
- Backward compatibility tests with existing API calls
- Parameter validation tests for task_id routing
- Response format consistency tests
- Error handling integration tests