---
kind: task
id: T-update-all-mcp-tools-to-use
title: Update all MCP tools to use ensure_planning_subdir=True
status: open
priority: high
prerequisites:
- T-add-ensure-planning-subdir
created: '2025-07-21T01:01:13.909367'
updated: '2025-07-21T01:01:13.909367'
schema_version: '1.1'
---
## Context

After adding the `ensure_planning_subdir` parameter to `resolve_project_roots()`, all MCP tools need to be updated to use this new parameter to ensure they always create and use a planning subdirectory.

## Implementation Requirements

Update all MCP tool implementations to pass `ensure_planning_subdir=True` when calling `resolve_project_roots()`. The following tools need to be updated:

### MCP Tools to Update

1. **claim_next_task.py** - Updates `claim_next_task()` function
2. **complete_task.py** - Updates `complete_task()` function  
3. **create_object.py** - Updates `create_object()` function
4. **get_object.py** - Updates `get_object()` function
5. **list_backlog.py** - Updates `list_backlog()` function
6. **update_object.py** - Updates `update_object()` function

### Supporting Modules to Update

1. **backlog_loader.py** - If it calls `resolve_project_roots()`
2. **query.py** - If it calls `resolve_project_roots()`
3. **Any other modules** in the tools/ directory that use path resolution

## Technical Approach

For each tool file, find calls to `resolve_project_roots()` and update them:

```python
# Before:
scanning_root, path_resolution_root = resolve_project_roots(project_root)

# After:
scanning_root, path_resolution_root = resolve_project_roots(project_root, ensure_planning_subdir=True)
```

## Search Strategy

1. Use grep/search to find all calls to `resolve_project_roots()` in the codebase
2. Identify which calls are from MCP tools vs CLI commands
3. Update only the MCP tool calls to use `ensure_planning_subdir=True`
4. Leave CLI calls unchanged to maintain backward compatibility

## Acceptance Criteria

- All MCP tool functions pass `ensure_planning_subdir=True` to `resolve_project_roots()`
- CLI commands continue to use the default `ensure_planning_subdir=False`
- All existing integration tests continue to pass
- MCP operations now always create/use planning subdirectories
- No breaking changes to existing CLI functionality

## Testing Requirements

- Run existing integration tests to ensure no regressions
- Verify that MCP operations create planning subdirectories when they don't exist
- Verify that CLI operations continue to work with existing behavior
- Add integration tests to verify the new MCP behavior

## Files to Modify

- `src/trellis_mcp/tools/claim_next_task.py`
- `src/trellis_mcp/tools/complete_task.py`
- `src/trellis_mcp/tools/create_object.py`
- `src/trellis_mcp/tools/get_object.py`
- `src/trellis_mcp/tools/list_backlog.py`
- `src/trellis_mcp/tools/update_object.py`
- Any supporting modules that call `resolve_project_roots()`
- Integration test files to verify new behavior

### Log

