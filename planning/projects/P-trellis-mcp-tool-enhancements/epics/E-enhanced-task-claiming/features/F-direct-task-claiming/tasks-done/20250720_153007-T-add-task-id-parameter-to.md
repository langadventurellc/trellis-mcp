---
kind: task
id: T-add-task-id-parameter-to
parent: F-direct-task-claiming
status: done
title: Add task_id parameter to claimNextTask tool interface
priority: high
prerequisites: []
created: '2025-07-20T15:18:12.649969'
updated: '2025-07-20T15:23:31.607332'
schema_version: '1.1'
worktree: null
---
## Context

Extend the existing `claimNextTask` MCP tool to accept an optional `task_id` parameter that enables direct task claiming by ID, bypassing the priority-based selection algorithm.

## Technical Approach

1. **Add task_id parameter** to the tool schema in `src/trellis_mcp/tools/claim_next_task.py`
2. **Update parameter validation** to handle optional task_id with proper format validation
3. **Extend tool handler** to pass task_id to core claiming logic
4. **Maintain backward compatibility** with existing priority-based claiming when task_id is not provided
5. **Create unit tests** for parameter validation and routing logic

## Implementation Details

### File to Modify
- `src/trellis_mcp/tools/claim_next_task.py`

### Parameter Schema Updates
```python
# Add to tool schema
task_id: Optional[str] = Field(
    default="",
    description="Optional task ID to claim directly (T- prefixed or standalone format). "
                "If provided, claims specific task instead of priority-based selection."
)
```

### Validation Requirements
- Accept empty string or None for priority-based claiming (backward compatibility)
- Validate task_id format when provided (T- prefix or standalone format)
- Pass validated task_id to core claiming logic

### Unit Test Requirements
Create `tests/tools/test_claim_next_task_tool.py` with:
- **Parameter validation tests**: Various task_id formats (valid T-*, standalone, invalid)
- **Backward compatibility tests**: Empty/None task_id values work unchanged
- **Format validation tests**: Invalid task_id formats raise appropriate errors
- **Tool schema tests**: Parameter is properly defined in tool schema
- **Routing tests**: Mock core functions to verify correct routing logic

## Acceptance Criteria

- [ ] **Parameter Addition**: task_id parameter added to tool schema with proper typing
- [ ] **Format Validation**: Validate task_id format matches expected patterns (T-* or standalone)
- [ ] **Backward Compatibility**: Existing priority-based claiming works unchanged when task_id empty
- [ ] **Error Handling**: Clear error messages for invalid task_id formats
- [ ] **Documentation**: Parameter description explains direct claiming functionality
- [ ] **Unit Test Coverage**: Comprehensive tests for all parameter validation scenarios

## Dependencies
- None (foundational task)

## Testing Requirements
- Unit tests for parameter validation with various task_id formats
- Backward compatibility tests with empty/None task_id values
- Error handling tests for invalid task_id formats
- Tool schema validation tests

### Log
**2025-07-20T20:30:07.859788Z** - Successfully implemented task_id parameter for claimNextTask tool interface, enabling direct task claiming by ID. Added comprehensive task resolution functionality that searches both hierarchical and standalone tasks. The implementation maintains full backward compatibility with existing priority-based claiming when task_id is empty. Added extensive unit test coverage for all parameter validation scenarios, direct claiming workflows, and error handling. All quality checks (formatting, linting, type checking) pass successfully.
- filesChanged: ["src/trellis_mcp/claim_next_task.py", "src/trellis_mcp/tools/claim_next_task.py", "tests/unit/tools/test_claim_next_task.py"]