---
kind: task
id: T-update-pathbuilder-class-to
title: Update PathBuilder class to support ensure_planning_subdir parameter
status: open
priority: normal
prerequisites:
- T-add-ensure-planning-subdir
created: '2025-07-21T01:02:06.856332'
updated: '2025-07-21T01:02:06.856332'
schema_version: '1.1'
---
## Context

The `PathBuilder` class in `src/trellis_mcp/inference/path_builder.py` uses `resolve_project_roots()` in its constructor. After adding the `ensure_planning_subdir` parameter, the PathBuilder needs to be updated to support this new functionality.

## Implementation Requirements

Update the `PathBuilder` class to:

1. Add `ensure_planning_subdir: bool = False` parameter to the constructor
2. Pass this parameter to the `resolve_project_roots()` call
3. Update the class docstring to document the new parameter
4. Maintain backward compatibility by defaulting to `False`

## Technical Approach

```python
class PathBuilder:
    """Fluent interface for building paths within the Trellis hierarchy."""
    
    def __init__(self, project_root: str | Path, ensure_planning_subdir: bool = False):
        """Initialize PathBuilder with project root.
        
        Args:
            project_root: Project root directory path  
            ensure_planning_subdir: If True, always create/use planning/ subdirectory
                unless project_root already ends with "planning"
        """
        self._project_root = Path(project_root)
        self._scanning_root, self._resolution_root = resolve_project_roots(
            self._project_root, 
            ensure_planning_subdir
        )
        # Rest of initialization...
```

## Callers to Consider

Identify all callers of `PathBuilder` and determine if any need to be updated:

1. Check `inference/` module files
2. Check if any MCP tools use `PathBuilder`
3. Check if any CLI commands use `PathBuilder`
4. Update only MCP-related usage to pass `ensure_planning_subdir=True`

## Acceptance Criteria

- Constructor includes new `ensure_planning_subdir` parameter with default `False`
- Parameter is passed through to `resolve_project_roots()` call
- All existing unit tests continue to pass
- New unit tests verify the parameter behavior
- Class docstring is updated
- Backward compatibility is maintained

## Testing Requirements

Write unit tests in `tests/test_path_builder.py` to verify:
- Default behavior (`ensure_planning_subdir=False`) matches existing logic
- New behavior with project root (`ensure_planning_subdir=True`) uses planning subdirectory
- New behavior with planning root (`ensure_planning_subdir=True`) uses existing planning directory
- PathBuilder methods work correctly with both modes and both path scenarios
- All path building operations produce correct results for both input path patterns

## Files to Modify

- `src/trellis_mcp/inference/path_builder.py` - Update PathBuilder class
- `tests/test_path_builder.py` - Add test cases
- Any files that instantiate PathBuilder and need the new behavior

### Log

