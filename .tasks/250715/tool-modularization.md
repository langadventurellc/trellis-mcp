# Tool Modularization — Task Checklist

## Overview

This task implements modular organization of FastMCP tools by extracting individual tools from the monolithic `server.py` file into separate, focused modules. Each tool will be moved to its own dedicated file to improve maintainability, testability, and code organization.

## Implementation

```python
# tools/example_tool.py
from fastmcp import FastMCP
from fastmcp.tools import Tool

mcp = FastMCP()

# The original, generic tool
@mcp.tool
def example_tool(query: str, category: str = "all") -> list[dict]:
    """Searches for items in the database."""
    return database.search(query, category)

# Create a more domain-specific version by changing its metadata
product_search_tool = Tool.from_tool(
    search,
    name="find_products",
    description="""
        Search for ...
        """,
)
```

```python
# server.py
from fastmcp import FastMCP
from tools.example_tool import example_tool

def create_server(settings: Settings) -> FastMCP:
    """Create and configure the FastMCP server."""
    server = FastMCP(settings=settings)
    
    # Register the example tool
    server.add_tool(example_tool)
    
    # Additional server configuration...
    
    return server
```

## Checklist

**IMPORTANT**: When starting a new task, read @../../docs/task_mcp_spec_and_plan.md for context.

- [x] **T-01** (S) Create `tools/` directory structure and `__init__.py`
  - Create `src/trellis_mcp/tools/` directory
  - Add `tools/__init__.py` with module exports
  - Establish consistent import patterns for tool modules
  - Files to create: `src/trellis_mcp/tools/__init__.py`
  - **COMPLETED**: Created `/Users/zach/code/trellis-mcp/src/trellis_mcp/tools/` directory and `__init__.py` file following established project patterns. Package includes proper docstring, placeholder imports for future tool modules, and empty `__all__` list ready for population. All quality checks pass (format, lint, type-check, tests, build).

- [x] **T-02** (M) Extract `health_check` tool to `tools/health_check.py`
  - Move `health_check` function from `server.py` to dedicated module
  - Add proper imports and dependencies (Settings type)
  - Ensure function signature matches FastMCP tool requirements
  - Update `server.py` to import and register this tool from the new module
  - Update imports and exports in `tools/__init__.py` for this tool
  - Run tests to verify no regressions for this tool
  - Update any documentation referencing this tool's location
  - Files to create: `src/trellis_mcp/tools/health_check.py`
  - Files to modify: `src/trellis_mcp/server.py`, `src/trellis_mcp/tools/__init__.py`
  - **COMPLETED**: Successfully extracted `health_check` tool from `server.py` to dedicated module `src/trellis_mcp/tools/health_check.py`. Created factory function `create_health_check_tool(settings: Settings)` that returns configured tool function. Updated `server.py` to import and register tool from new module. Updated `tools/__init__.py` with proper imports and exports. All quality checks pass (format, lint, type-check). All 745 tests pass with no regressions. Tool maintains exact same functionality and interface.

- [x] **T-03** (L) Extract `createObject` tool to `tools/create_object.py`
  - Move `createObject` function and `_deep_merge_dict` helper to dedicated module
  - Add all necessary imports (datetime, validation, path utilities, etc.)
  - Preserve all existing functionality and error handling
  - Update `server.py` to import and register this tool from the new module
  - Update imports and exports in `tools/__init__.py` for this tool
  - Run tests to verify no regressions for this tool
  - Update any documentation referencing this tool's location
  - Files to create: `src/trellis_mcp/tools/create_object.py`
  - Files to modify: `src/trellis_mcp/server.py`, `src/trellis_mcp/tools/__init__.py`
  - **COMPLETED**: Successfully extracted `createObject` tool from `server.py` to dedicated module `src/trellis_mcp/tools/create_object.py`. Created factory function `create_create_object_tool(settings: Settings)` that returns configured tool function. Updated `server.py` to import and register tool from new module, removed unused imports. Updated `tools/__init__.py` with proper imports and exports. All quality checks pass (format, lint, type-check). All 745 tests pass with no regressions. Tool maintains exact same functionality and interface. Note: `_deep_merge_dict` was not moved as it's not used by `createObject` - it will be handled in task T-05 with `updateObject`.

- [x] **T-04** (M) Extract `getObject` tool to `tools/get_object.py` 
  - Move `getObject` function to dedicated module
  - Add required imports (path_resolver, io_utils, etc.)
  - Maintain existing parameter validation and error handling
  - Update `server.py` to import and register this tool from the new module
  - Update imports and exports in `tools/__init__.py` for this tool
  - Run tests to verify no regressions for this tool
  - Update any documentation referencing this tool's location
  - Files to create: `src/trellis_mcp/tools/get_object.py`
  - Files to modify: `src/trellis_mcp/server.py`, `src/trellis_mcp/tools/__init__.py`
  - **COMPLETED**: Successfully extracted `getObject` tool from `server.py` to dedicated module `src/trellis_mcp/tools/get_object.py`. Created factory function `create_get_object_tool(settings: Settings)` that returns configured tool function. Updated `server.py` to import and register tool from new module. Updated `tools/__init__.py` with proper imports and exports. All quality checks pass (format, lint, type-check). All 745 tests pass with no regressions. Tool maintains exact same functionality and interface.

- [x] **T-05** (L) Extract `updateObject` tool to `tools/update_object.py`
  - Move `updateObject` function and `_deep_merge_dict` helper (if not already moved)
  - Handle cascade deletion logic and protected object validation
  - Preserve all validation, status transitions, and prerequisite checking
  - Update `server.py` to import and register this tool from the new module
  - Update imports and exports in `tools/__init__.py` for this tool
  - Run tests to verify no regressions for this tool
  - Update any documentation referencing this tool's location
  - Files to create: `src/trellis_mcp/tools/update_object.py`
  - Files to modify: `src/trellis_mcp/server.py`, `src/trellis_mcp/tools/__init__.py`
  - **COMPLETED**: Successfully extracted `updateObject` tool from `server.py` to dedicated module `src/trellis_mcp/tools/update_object.py`. Created factory function `create_update_object_tool(settings: Settings)` that returns configured tool function. Moved `_deep_merge_dict` helper function to the new module. Updated `server.py` to import and register tool from new module, removed unused imports. Updated `tools/__init__.py` with proper imports and exports. All quality checks pass (format, lint, type-check). All 745 tests pass with no regressions. Tool maintains exact same functionality and interface including complex cascade deletion logic, status transition validation, and protected object checking.

- [x] **T-06** (M) Extract `listBacklog` tool to `tools/list_backlog.py`
  - Move `listBacklog` function to dedicated module
  - Add imports for filters, scanner, and task sorting utilities
  - Maintain existing filtering and sorting logic
  - Update `server.py` to import and register this tool from the new module
  - Update imports and exports in `tools/__init__.py` for this tool
  - Run tests to verify no regressions for this tool
  - Update any documentation referencing this tool's location
  - Files to create: `src/trellis_mcp/tools/list_backlog.py`
  - Files to modify: `src/trellis_mcp/server.py`, `src/trellis_mcp/tools/__init__.py`
  - **COMPLETED**: Successfully extracted `listBacklog` tool from `server.py` to dedicated module `src/trellis_mcp/tools/list_backlog.py`. Created factory function `create_list_backlog_tool(settings: Settings)` that returns configured tool function. Updated `server.py` to import and register tool from new module, removed unused imports (filters, scanner, etc.). Updated `tools/__init__.py` with proper imports and exports. All quality checks pass (format, lint, type-check). All 745 tests pass with no regressions. Tool maintains exact same functionality and interface including filtering, sorting, and result formatting.

- [x] **T-07** (M) Extract `claimNextTask` tool to `tools/claim_next_task.py`
  - Move `claimNextTask` function to dedicated module
  - Add imports for claim_next_task core function and exception handling
  - Preserve task claiming logic and validation
  - Update `server.py` to import and register this tool from the new module
  - Update imports and exports in `tools/__init__.py` for this tool
  - Run tests to verify no regressions for this tool
  - Update any documentation referencing this tool's location
  - Files to create: `src/trellis_mcp/tools/claim_next_task.py`
  - Files to modify: `src/trellis_mcp/server.py`, `src/trellis_mcp/tools/__init__.py`
  - **COMPLETED**: Successfully extracted `claimNextTask` tool from `server.py` to dedicated module `src/trellis_mcp/tools/claim_next_task.py`. Created factory function `create_claim_next_task_tool(settings: Settings)` that returns configured tool function. Updated `server.py` to import and register tool from new module, removed unused imports. Updated `tools/__init__.py` with proper imports and exports. All quality checks pass (format, lint, type-check). All 745 tests pass with no regressions. Tool maintains exact same functionality and interface including task claiming logic, validation, and error handling.

- [x] **T-08** (M) Extract `completeTask` tool to `tools/complete_task.py`
  - Move `completeTask` function to dedicated module
  - Add imports for complete_task core function and validation
  - Maintain task completion workflow and status validation
  - Update `server.py` to import and register this tool from the new module
  - Update imports and exports in `tools/__init__.py` for this tool
  - Run tests to verify no regressions for this tool
  - Update any documentation referencing this tool's location
  - Files to create: `src/trellis_mcp/tools/complete_task.py`
  - Files to modify: `src/trellis_mcp/server.py`, `src/trellis_mcp/tools/__init__.py`
  - **COMPLETED**: Successfully extracted `completeTask` tool from `server.py` to dedicated module `src/trellis_mcp/tools/complete_task.py`. Created factory function `create_complete_task_tool(settings: Settings)` that returns configured tool function. Updated `server.py` to import and register tool from new module, removed unused imports (`complete_task`, `InvalidStatusForCompletion`). Updated `tools/__init__.py` with proper imports and exports. All quality checks pass (format, lint, type-check). All 745 tests pass with no regressions. Tool maintains exact same functionality and interface including task completion workflow, validation, and log entry functionality.

- [x] **T-09** (M) Extract `getNextReviewableTask` tool to `tools/get_next_reviewable_task.py`
  - Move `getNextReviewableTask` function to dedicated module
  - Add imports for query utilities and task model conversion
  - Preserve review task querying logic
  - Update `server.py` to import and register this tool from the new module
  - Update imports and exports in `tools/__init__.py` for this tool
  - Run tests to verify no regressions for this tool
  - Update any documentation referencing this tool's location
  - Files to create: `src/trellis_mcp/tools/get_next_reviewable_task.py`
  - Files to modify: `src/trellis_mcp/server.py`, `src/trellis_mcp/tools/__init__.py`
  - **COMPLETED**: Successfully extracted `getNextReviewableTask` tool from `server.py` to dedicated module `src/trellis_mcp/tools/get_next_reviewable_task.py`. Created factory function `create_get_next_reviewable_task_tool(settings: Settings)` that returns configured tool function. Updated `server.py` to import and register tool from new module, removed unused imports (`id_to_path`, `resolve_project_roots`, `get_oldest_review`, `TrellisValidationError`). Updated `tools/__init__.py` with proper imports and exports. All quality checks pass (format, lint, type-check). All 745 tests pass with no regressions. Tool maintains exact same functionality and interface including review task querying logic, oldest timestamp ordering, priority tiebreaking, and proper error handling.

- [x] **T-10** (S) Final system verification
  - Run full test suite to ensure no regressions across the entire system
  - Verify MCP server functionality remains intact and all tools are discoverable
  - Confirm all 8 tools have been successfully extracted and are working
  - Update any remaining documentation referencing the old monolithic structure
  - **COMPLETED**: ✅ All 745 tests pass with no regressions. ✅ All quality checks pass (format, lint, type-check). ✅ Server creates successfully with name "Trellis MCP Server". ✅ All 8 tool modules import correctly: health_check, create_object, get_object, update_object, list_backlog, claim_next_task, complete_task, get_next_reviewable_task. ✅ All tool factory functions work correctly. ✅ Documentation does not reference old monolithic structure. System verification complete - modularization successful with no regressions.

## Quality Gates

* All 8 tools successfully extracted to individual modules
* `server.py` contains only server creation and tool registration logic
* All existing tests pass without modification (verified per tool during extraction)
* No changes to tool names, signatures, or external behavior
* Each tool module has proper imports and dependencies
* Pre-commit & CI hooks remain green
* MCP server starts successfully and all tools are discoverable
* Documentation updated throughout the process

## Benefits

* **Improved maintainability**: Each tool in its own focused file
* **Better testability**: Individual tools can be unit tested in isolation
* **Enhanced readability**: Smaller, more focused files are easier to understand
* **Easier collaboration**: Reduced merge conflicts when working on different tools
* **Future extensibility**: New tools can be added as separate modules