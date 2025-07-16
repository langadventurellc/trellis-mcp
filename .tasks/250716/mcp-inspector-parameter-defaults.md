# MCP Inspector Parameter Defaults Fix — Task Checklist

## Overview

This task addresses an issue with the MCP Inspector for Local Development where optional parameters with `None` as default values don't populate correctly in the UI. The solution is to replace `None` defaults with concrete default values (empty strings, empty lists, etc.) and update the function logic to handle these new defaults.

## Analysis of Tools Requiring Changes

After analyzing all tools in `src/trellis_mcp/tools/`, the following 5 tools have optional parameters with `None` defaults that need to be updated:

1. **claim_next_task.py**: 1 parameter
2. **complete_task.py**: 2 parameters  
3. **create_object.py**: 6 parameters
4. **list_backlog.py**: 3 parameters
5. **update_object.py**: 2 parameters

## Implementation

```python
# Before (MCP Inspector issue)
@mcp.tool
def createObject(
    kind: str,
    title: str,
    projectRoot: str,
    id: str | None = None,
    parent: str | None = None,
    status: str | None = None,
    priority: str | None = None,
    prerequisites: list[str] | None = None,
    description: str | None = None,
) -> dict[str, str]:
    # Logic handles None values
    if not id:
        id = generate_id(kind, title, planning_root)
    if prerequisites is None:
        prerequisites = []
```

```python
# After (MCP Inspector compatible)
@mcp.tool
def createObject(
    kind: str,
    title: str,
    projectRoot: str,
    id: str = "",
    parent: str = "",
    status: str = "",
    priority: str = "",
    prerequisites: list[str] = [],
    description: str = "",
) -> dict[str, str]:
    # Logic handles empty values
    if not id or not id.strip():
        id = generate_id(kind, title, planning_root)
    if not prerequisites:
        prerequisites = []
```

## Checklist

**IMPORTANT**: When starting a new task, read @../../docs/task_mcp_spec_and_plan.md for context.

- [x] **T-01** (S) Update `claim_next_task.py` parameter defaults
  - ✅ Changed `worktree: str | None = None` → `worktree: str = ""`
  - ✅ Updated line 84: `worktree if worktree is not None else ""` → `worktree`
  - ✅ Updated core function: `if worktree_path is not None:` → `if worktree_path and worktree_path.strip():`
  - ✅ All quality checks passed (745 tests, linting, type checking)
  - **Summary**: Successfully updated tool parameter to use empty string default instead of None. The MCP Inspector will now populate the worktree field with an empty string by default. Core logic updated to handle empty strings the same way as None values (ignore them when setting worktree on tasks).
  - **Files modified**: 
    - `src/trellis_mcp/tools/claim_next_task.py` - Tool parameter and return logic
    - `src/trellis_mcp/claim_next_task.py` - Core function logic for empty string handling

- [x] **T-02** (M) Update `complete_task.py` parameter defaults
  - ✅ Changed `summary: str | None = None` → `summary: str = ""`
  - ✅ Changed `filesChanged: list[str] | None = None` → `filesChanged: list[str] = []`
  - ✅ Updated tool docstring to reflect non-optional parameters
  - ✅ Updated core function parameters and docstring for consistency  
  - ✅ Updated core function logic: `if summary is not None:` → `if summary:`
  - ✅ Fixed CLI module to pass empty values instead of None
  - ✅ All quality checks passed (745 tests, linting, type checking)
  - **Summary**: Successfully updated both tool and core function parameters to use empty defaults instead of None. The MCP Inspector will now populate the summary field with an empty string and filesChanged with an empty list by default. Updated CLI handling to maintain compatibility. All existing functionality preserved with no regressions.
  - **Files modified**: 
    - `src/trellis_mcp/tools/complete_task.py` - Tool parameter defaults and docstring
    - `src/trellis_mcp/complete_task.py` - Core function parameters, docstring, and empty string logic
    - `src/trellis_mcp/cli.py` - CLI parameter handling for empty values

- [x] **T-03** (L) Update `create_object.py` parameter defaults
  - ✅ Changed `id: str | None = None` → `id: str = ""`
  - ✅ Changed `parent: str | None = None` → `parent: str = ""`
  - ✅ Changed `status: str | None = None` → `status: str = ""`
  - ✅ Changed `priority: str | None = None` → `priority: str = ""`
  - ✅ Changed `prerequisites: list[str] | None = None` → `prerequisites: list[str] = []`
  - ✅ Changed `description: str | None = None` → `description: str = ""`
  - ✅ Updated line 86: Replace `if not id:` with `if not id or not id.strip():`
  - ✅ Updated lines 90-91: Replace `if not status:` with `if not status or not status.strip():`
  - ✅ Updated lines 94-95: Replace `if not priority:` with `if not priority or not priority.strip():`
  - ✅ Updated lines 97-99: Replace `if prerequisites is None:` with `if not prerequisites:`
  - ✅ Updated lines 118-119: Replace `if parent:` with `if parent and parent.strip():`
  - ✅ Updated lines 156-157: Replace `if description:` with `if description and description.strip():`
  - ✅ All quality checks passed (745 tests, linting, type checking)
  - **Summary**: Successfully updated tool parameters to use concrete defaults instead of None. The MCP Inspector will now populate all optional fields with appropriate default values (empty strings and empty list). Updated all conditional logic to handle empty strings the same way as None values, preserving existing behavior while ensuring MCP Inspector compatibility. All 6 optional parameters now work seamlessly with the inspector.
  - **Files modified**: 
    - `src/trellis_mcp/tools/create_object.py` - Tool parameter defaults and conditional logic handling

- [x] **T-04** (M) Update `list_backlog.py` parameter defaults
  - ✅ Changed `scope: str | None = None` → `scope: str = ""`
  - ✅ Changed `status: str | None = None` → `status: str = ""`
  - ✅ Changed `priority: str | None = None` → `priority: str = ""`
  - ✅ Updated lines 80-81: Replace `filter_status = [status] if status else []` with `filter_status = [status] if status and status.strip() else []`
  - ✅ Updated lines 81-82: Replace `filter_priority = [priority] if priority else []` with `filter_priority = [priority] if priority and priority.strip() else []`
  - ✅ Updated lines 88-89: Replace `if scope:` with `if scope and scope.strip():`
  - ✅ Tested filtering works correctly with empty strings - confirmed empty strings behave identically to None values
  - ✅ All quality checks passed (745 tests, linting, type checking)
  - **Summary**: Successfully updated tool parameters to use concrete defaults instead of None. The MCP Inspector will now populate all optional fields with empty strings by default. Updated all conditional logic to handle empty strings (including whitespace-only strings) the same way as None values, preserving existing behavior while ensuring MCP Inspector compatibility. Comprehensive testing confirmed that empty strings, whitespace strings, and no parameters all produce identical results.
  - **Files modified**: 
    - `src/trellis_mcp/tools/list_backlog.py` - Tool parameter defaults and conditional logic for empty string handling

- [x] **T-05** (M) Update `update_object.py` parameter defaults
  - ✅ Changed `yamlPatch: dict[str, str | list[str] | None] | None = None` → `yamlPatch: dict[str, str | list[str] | None] = {}`
  - ✅ Changed `bodyPatch: str | None = None` → `bodyPatch: str = ""`
  - ✅ Updated line 123: Replaced `if yamlPatch is None and bodyPatch is None:` with `if not yamlPatch and not bodyPatch:`
  - ✅ Updated line 158: Replaced `updated_body = bodyPatch if bodyPatch is not None else existing_body` with `updated_body = bodyPatch if bodyPatch else existing_body`
  - ✅ Updated line 300: Replaced `if bodyPatch is not None:` with `if bodyPatch:`
  - ✅ All quality checks passed (745 tests, linting, type checking)
  - **Summary**: Successfully updated tool parameters to use concrete defaults instead of None. The MCP Inspector will now populate yamlPatch with an empty dictionary and bodyPatch with an empty string by default. Updated all conditional logic to handle empty values (empty dict/string) the same way as None values, preserving existing behavior while ensuring MCP Inspector compatibility. All patch operations work correctly with empty defaults.
  - **Files modified**: 
    - `src/trellis_mcp/tools/update_object.py` - Tool parameter defaults and conditional logic for empty value handling

- [x] **T-06** (S) System verification and testing
  - ✅ Full test suite: `uv run pytest -q` - 745 tests passed in 8.13s
  - ✅ Linting and formatting: `uv run pre-commit run --all-files` - All checks passed (isort, black, flake8, pyright, pytest)
  - ✅ Type checking: `uv run pyright src/` - 0 errors, 0 warnings, 0 informations
  - ✅ Parameter verification: Confirmed all 5 modified tools have correct concrete defaults
  - ✅ Verified optional parameters now use empty strings/lists/dicts instead of None
  - ✅ All functionality intact - no test failures or regressions detected
  - **Summary**: Successfully completed comprehensive system verification. All quality checks pass with 745 tests green, zero linting/type errors, and confirmed that all 5 tools (claim_next_task, complete_task, create_object, list_backlog, update_object) now use concrete parameter defaults compatible with MCP Inspector. The migration from None defaults to empty values is complete and functional.
  - **Files verified**: 
    - `src/trellis_mcp/tools/claim_next_task.py` - worktree: str = ""
    - `src/trellis_mcp/tools/complete_task.py` - summary: str = "", filesChanged: list[str] = []
    - `src/trellis_mcp/tools/create_object.py` - 6 parameters with concrete defaults
    - `src/trellis_mcp/tools/list_backlog.py` - scope: str = "", status: str = "", priority: str = ""
    - `src/trellis_mcp/tools/update_object.py` - yamlPatch: dict = {}, bodyPatch: str = ""

## Quality Gates

* All optional `None` parameters replaced with concrete defaults
* All function logic updated to handle empty values appropriately
* All existing tests pass without modification
* Pre-commit hooks and linting remain green
* MCP Inspector correctly populates default values for all tools
* No behavioral changes to existing functionality

## Benefits

* **MCP Inspector compatibility**: Optional parameters now populate correctly in the UI
* **Better developer experience**: No more empty parameter fields in the inspector
* **Cleaner defaults**: Explicit empty values instead of `None` reduce conditional logic
* **Consistent behavior**: All tools follow the same parameter pattern