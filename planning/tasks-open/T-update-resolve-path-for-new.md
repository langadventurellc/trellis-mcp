---
kind: task
id: T-update-resolve-path-for-new
title: Update resolve_path_for_new_object to use ensure_planning_subdir parameter
status: open
priority: high
prerequisites:
- T-add-ensure-planning-subdir
created: '2025-07-21T01:01:31.765982'
updated: '2025-07-21T01:01:31.765982'
schema_version: '1.1'
---
## Context

The `resolve_path_for_new_object()` function in `path_resolver.py` calls `resolve_project_roots()` and needs to be updated to support the new `ensure_planning_subdir` parameter. This function is used by MCP tools when creating new objects.

## Implementation Requirements

Update the `resolve_path_for_new_object()` function to:

1. Add `ensure_planning_subdir: bool = False` parameter to the function signature
2. Pass this parameter through to the `resolve_project_roots()` call
3. Maintain backward compatibility by defaulting to `False`
4. Update the function docstring to document the new parameter

## Technical Approach

```python
def resolve_path_for_new_object(
    kind: str,
    obj_id: str,
    parent_id: str | None,
    project_root: str | Path,
    status: str | None = None,
    ensure_planning_subdir: bool = False,
) -> Path:
    """Resolve filesystem path for creating a new object.
    
    Args:
        kind: Object type ('project', 'epic', 'feature', 'task')
        obj_id: Object identifier
        parent_id: Parent object ID (if applicable)
        project_root: Project root directory path
        status: Object status (for tasks, determines subdirectory)
        ensure_planning_subdir: If True, always create/use planning/ subdirectory
    
    Returns:
        Path: Complete filesystem path for the new object
    """
    # Pass ensure_planning_subdir to resolve_project_roots
    _, path_resolution_root = resolve_project_roots(project_root, ensure_planning_subdir)
    
    # Rest of function logic remains the same...
```

## Callers to Update

After updating `resolve_path_for_new_object()`, update its callers in MCP tools:

1. **create_object.py** - Pass `ensure_planning_subdir=True`
2. Any other functions that call `resolve_path_for_new_object()`

## Acceptance Criteria

- Function signature includes new `ensure_planning_subdir` parameter with default `False`
- Parameter is passed through to `resolve_project_roots()` call
- All existing unit tests continue to pass
- New unit tests verify the parameter behavior
- Function docstring is updated
- MCP tools can now control planning subdirectory creation behavior

## Testing Requirements

Write unit tests in `tests/unit/test_resolve_path_for_new_object.py` to verify:
- Default behavior (`ensure_planning_subdir=False`) matches existing logic
- New behavior (`ensure_planning_subdir=True`) uses planning subdirectory
- All object types (project, epic, feature, task) work correctly with new parameter
- Path resolution is correct for both modes

## Files to Modify

- `src/trellis_mcp/path_resolver.py` - Update `resolve_path_for_new_object()` function
- `src/trellis_mcp/tools/create_object.py` - Update calls to use new parameter
- `tests/unit/test_resolve_path_for_new_object.py` - Add test cases

### Log

