---
kind: task
id: T-enhance-core-claimnexttask-logic
title: Enhance core claimNextTask logic with scope filtering
status: open
priority: high
prerequisites:
- T-add-scope-filtering-capability
- T-update-claimnexttask-tool
created: '2025-07-20T13:20:21.191222'
updated: '2025-07-20T13:20:21.191222'
schema_version: '1.1'
parent: F-scope-based-task-filtering
---
## Context

The core claiming logic in `src/trellis_mcp/claim_next_task.py` currently uses `scan_tasks()` to discover all available tasks. Following the listBacklog pattern, we need to enhance it to use scope-aware task discovery when scope parameter is provided.

## Implementation Requirements

### Modify claim_next_task function signature
- Add optional `scope: str | None = None` parameter to core function
- Maintain backward compatibility with existing function calls

### Conditional task discovery logic
```python
def claim_next_task(
    project_root: str, 
    worktree: str = "", 
    scope: str | None = None
) -> TaskModel:
    """Claim next highest-priority open task with all prerequisites completed."""
    scanning_root, path_resolution_root = resolve_project_roots(project_root)
    
    # Use scope-aware task discovery if scope provided
    if scope:
        task_iterator = filter_by_scope(scope, scanning_root)
    else:
        task_iterator = scan_tasks(scanning_root)
    
    # Apply existing filtering and claiming logic
    filter_params = FilterParams(status=["open"], priority=[])
    filtered_tasks = apply_filters(task_iterator, filter_params)
    # ... rest of existing logic unchanged
```

### Scope validation integration
- Use KindInferenceEngine to validate scope object exists before task discovery
- Raise ValidationError with clear message if scope object not found
- Follow existing validation patterns from other enhanced tools

### Priority preservation within scope
- Maintain existing priority-based sorting within scope boundaries
- Use existing `sort_tasks_by_priority()` function for consistent ordering
- Preserve prerequisite validation logic within scope

### Error handling enhancements
- Add scope-specific error cases to NoAvailableTask exception handling
- Provide clear error messages when scope contains no eligible tasks
- Maintain existing error handling for general claiming failures

## Acceptance Criteria

- [ ] claim_next_task() accepts optional scope parameter
- [ ] Scope filtering uses filter_by_scope() when scope provided
- [ ] No scope parameter maintains existing scan_tasks() behavior
- [ ] Scope validation uses kind inference engine
- [ ] Priority sorting preserved within scope boundaries
- [ ] Prerequisites validation works within scope filtering
- [ ] Clear error messages for scope-related failures
- [ ] Backward compatibility maintained for existing calls

## Testing Requirements

Create unit tests in `tests/test_claim_next_task.py`:
- Scope parameter integration with task discovery
- Priority preservation within scope boundaries
- Prerequisite validation with scope filtering
- Error handling for invalid/empty scopes
- Backward compatibility with no scope parameter

## Dependencies

- Requires T-add-scope-filtering-capability for scope-aware task discovery
- Requires T-update-claimnexttask-tool for tool interface changes
- Uses existing priority sorting and prerequisite validation

## Files to Modify

- `src/trellis_mcp/claim_next_task.py`: Add scope parameter and conditional task discovery
- `tests/test_claim_next_task.py`: Add scope filtering test coverage

### Log

