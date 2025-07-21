---
kind: task
id: T-add-ensure-planning-subdir
status: done
title: Add ensure_planning_subdir parameter to resolve_project_roots function
priority: high
prerequisites: []
created: '2025-07-21T01:00:56.604831'
updated: '2025-07-21T08:38:58.932824'
schema_version: '1.1'
worktree: null
---
## Context

The path resolver currently has two modes of operation:
1. **Project contains planning**: `project_root/planning/projects/...`
2. **Project IS planning**: `project_root/projects/...`

CLI commands pass the planning directory directly and expect existing behavior, while MCP tools should always create a planning subdirectory in the project root if it doesn't exist.

## Implementation Requirements

Modify the `resolve_project_roots()` function in `src/trellis_mcp/path_resolver.py` to:

1. Add a new parameter `ensure_planning_subdir: bool = False`
2. When `ensure_planning_subdir=True`:
   - If `project_root` ends with "planning", use that directory directly
   - If `project_root` doesn't end with "planning", create/use `project_root/planning/`
   - Create the planning directory if it doesn't exist
3. When `ensure_planning_subdir=False`:
   - Preserve existing dual-pattern detection logic
   - Maintain backward compatibility with CLI usage

## Technical Approach

```python
def resolve_project_roots(
    project_root: str | Path, 
    ensure_planning_subdir: bool = False
) -> tuple[Path, Path]:
    """Resolve scanning root and path resolution root from project root.

    Args:
        project_root: Either project root or planning directory path
        ensure_planning_subdir: If True, always create/use planning/ subdirectory
                               unless project_root already ends with "planning"
                               If False, use existing logic (for CLI compatibility)
    
    Returns:
        tuple[Path, Path]: (scanning_root, path_resolution_root)
    """
    project_root_path = Path(project_root)
    
    if ensure_planning_subdir:
        # Check if the supplied path already ends with "planning"
        if project_root_path.name == "planning":
            # Use the supplied planning directory directly
            planning_dir = project_root_path
            planning_dir.mkdir(parents=True, exist_ok=True)
            return project_root_path.parent, planning_dir
        else:
            # Create/use project_root/planning/ subdirectory
            planning_dir = project_root_path / "planning"
            planning_dir.mkdir(parents=True, exist_ok=True)
            return project_root_path, planning_dir
    else:
        # Existing logic for CLI compatibility
        if (project_root_path / "planning").exists():
            return project_root_path, project_root_path / "planning"
        else:
            return project_root_path.parent, project_root_path
```

## Acceptance Criteria

- Function signature includes new `ensure_planning_subdir` parameter with default `False`
- When `ensure_planning_subdir=True`:
  - If project_root ends with "planning", use that directory directly
  - If project_root doesn't end with "planning", create/use planning/ subdirectory
  - Planning directory is created if it doesn't exist
- When `ensure_planning_subdir=False`, existing behavior is preserved exactly
- All existing unit tests continue to pass
- New unit tests verify the new parameter behavior for both path scenarios
- Function docstring is updated to document the new parameter
- Type hints are maintained and correct

## Testing Requirements

Write unit tests in `tests/unit/test_project_roots.py` to verify:
- Default behavior (`ensure_planning_subdir=False`) matches existing logic
- New behavior with project root: (`/project/root`, `ensure_planning_subdir=True`) → `(/project/root, /project/root/planning)`
- New behavior with planning root: (`/project/root/planning`, `ensure_planning_subdir=True`) → `(/project/root, /project/root/planning)`
- Directory creation works correctly when planning dir doesn't exist
- Function returns correct tuple values for both modes and both path scenarios  
- Edge cases like permissions issues are handled gracefully

## Files to Modify

- `src/trellis_mcp/path_resolver.py` - Add parameter and logic
- `tests/unit/test_project_roots.py` - Add test cases

### Log


**2025-07-21T13:42:49.267304Z** - Implemented ensure_planning_subdir parameter to resolve_project_roots function with full backward compatibility. When True, automatically creates/uses planning subdirectory unless path already ends with "planning". When False, preserves existing dual-pattern detection logic for CLI compatibility. Added comprehensive test coverage for both path scenarios and directory creation edge cases. All quality checks pass and 15 tests are green.
- filesChanged: ["src/trellis_mcp/path_resolver.py", "tests/unit/test_project_roots.py"]