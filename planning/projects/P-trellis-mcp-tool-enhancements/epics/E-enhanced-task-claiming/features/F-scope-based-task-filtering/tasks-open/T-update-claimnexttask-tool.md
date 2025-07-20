---
kind: task
id: T-update-claimnexttask-tool
title: Update claimNextTask tool interface to accept scope parameter
status: open
priority: high
prerequisites:
- T-extend-filterparams-model-to
created: '2025-07-20T13:20:03.015535'
updated: '2025-07-20T13:20:03.015535'
schema_version: '1.1'
parent: F-scope-based-task-filtering
---
## Context

The claimNextTask tool in `src/trellis_mcp/tools/claim_next_task.py` currently accepts projectRoot and optional worktree parameters. Following the listBacklog pattern, we need to add scope parameter to the tool interface while maintaining backward compatibility.

## Implementation Requirements

### Add scope parameter to tool function
- Add optional `scope: str = ""` parameter to claimNextTask tool function
- Follow existing pattern from listBacklog tool for parameter handling
- Maintain backward compatibility (empty string means no scope filtering)

### Parameter validation and conversion
```python
@trellis_tool
def claimNextTask(
    projectRoot: str,
    worktree: str = "",
    scope: str = ""
) -> dict[str, Any]:
    """Claim next highest-priority task, optionally within scope boundaries."""
    # Validate and convert parameters
    if not projectRoot:
        raise ValidationError("projectRoot is required")
    
    # Convert scope to None if empty (consistent with other tools)
    scope_param = scope.strip() if scope.strip() else None
    
    # Call enhanced core logic with scope parameter
    result = claim_next_task(projectRoot, worktree, scope_param)
    return result
```

### Error handling integration
- Convert core exceptions to tool-level ValidationError
- Preserve existing error handling for NoAvailableTask
- Add scope-specific error handling for invalid scope parameters

### Response format consistency
- Maintain existing response format with task data and file_path
- No changes needed to response structure (scope is input-only parameter)

## Acceptance Criteria

- [ ] claimNextTask tool accepts optional scope parameter
- [ ] Empty scope parameter maintains existing behavior (no filtering)
- [ ] Valid scope parameter passed to core claiming logic
- [ ] Parameter validation follows existing patterns
- [ ] Error handling consistent with other enhanced tools
- [ ] Backward compatibility maintained for existing clients

## Testing Requirements

Create integration tests in `tests/tools/test_claim_next_task.py`:
- Tool parameter validation for scope formats
- Empty scope parameter handling (existing behavior)
- Valid scope parameter passing to core logic
- Error propagation from core to tool layer
- Response format consistency

## Dependencies

- Requires T-extend-filterparams-model-to for scope validation patterns
- Will integrate with enhanced core logic from subsequent tasks

## Files to Modify

- `src/trellis_mcp/tools/claim_next_task.py`: Add scope parameter and validation
- `tests/tools/test_claim_next_task.py`: Add scope parameter test coverage

### Log

