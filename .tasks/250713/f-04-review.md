# F-04-Review · Code Quality Improvements — Task Checklist

## Checklist

**IMPORTANT**: When starting a new task, read @../../docs/task_mcp_spec_and_plan.md for context.

This task addresses code quality improvements identified in Gemini's review of the F-04 CRUD Objects RPC feature implementation.

### Server-Level Testing Gap

- [x] **R-01** (M) Add comprehensive tests for `createObject` RPC handler in `test_server.py`
  - Test valid object creation for all kinds (project, epic, feature, task)
  - Test ID generation when missing
  - Test validation error handling (invalid YAML, missing required fields)
  - Test prerequisite cycle detection and rollback
  - Test file system error handling
  - Test parent-child relationship validation
  
  **Implementation Summary:**
  - Added comprehensive `TestCreateObject` class with 20 test methods
  - Tests cover all object kinds (project, epic, feature, task) with full hierarchical validation
  - Tests verify ID generation, status/priority defaults, and parameter validation
  - Tests cover error handling for invalid parameters, missing parents, and file conflicts
  - Tests verify cycle detection with self-referencing prerequisites
  - Tests verify rollback functionality when validation fails
  - All tests pass with 100% success rate
  - Quality checks (black, flake8, pyright) all pass
  - Files changed: `tests/test_server.py` (added ~800 lines of comprehensive tests)
- [x] **R-02** (M) Add comprehensive tests for `updateObject` RPC handler in `test_server.py`
  - Test yamlPatch updates for all object kinds
  - Test bodyPatch updates for markdown content
  - Test deep merge functionality with nested structures
  - Test status transition validation
  - Test prerequisite cycle detection after updates
  - Test rollback on validation failures
  - Test error handling for malformed patches
  
  **Implementation Summary:**
  - Added comprehensive `TestUpdateObject` class with 20+ test methods
  - Tests cover yamlPatch updates for all object kinds (project, epic, feature, task)
  - Tests cover bodyPatch updates and combined yaml/body updates
  - Tests verify deep merge functionality preserves existing fields
  - Tests validate status transition rules for all object types
  - Tests validate that tasks cannot be set to 'done' status via updateObject
  - Tests verify prerequisite cycle detection and rollback functionality
  - Tests cover error handling for invalid parameters, malformed patches, and validation failures
  - Tests verify timestamp auto-updates, prefix ID handling, and required field preservation
  - All tests pass with 100% success rate
  - Quality checks (black, flake8, pyright) all pass
  - Files changed: `tests/test_server.py` (added ~1,200 lines of comprehensive tests)
- [x] **R-03** (M) Add comprehensive tests for `listBacklog` RPC handler in `test_server.py`
  - Test scope filtering (project/epic/feature ID)
  - Test status filtering (open, in-progress, review, done)
  - Test priority filtering (high, normal, low)
  - Test priority-based sorting with secondary date sorting
  - Test empty results handling
  - Test error handling for invalid parameters
  - Test cross-directory searching (tasks-open and tasks-done)
  
  **Implementation Summary:**
  - Added comprehensive `TestListBacklog` class with 13 test methods covering all specified requirements
  - Tests cover scope filtering by project, epic, and feature IDs with proper hierarchical validation
  - Tests verify status filtering for all valid statuses (open, in-progress, review, done)
  - Tests verify priority filtering for all priority levels (high, normal, low)
  - Tests verify combined filtering with multiple criteria (scope + status + priority)
  - Tests verify priority-based sorting with high->normal->low order and secondary date sorting
  - Tests verify cross-directory searching finds tasks in both tasks-open and tasks-done directories
  - Tests cover edge cases: empty results, missing projects directory, malformed task files
  - Tests verify comprehensive error handling for invalid parameters
  - All tests pass with 100% success rate and include proper task data structure validation
  - Fixed FastMCP type annotation issue that was converting task dictionaries to empty Root objects
  - Fixed `createObject` function to use correct file naming convention for done tasks (timestamp prefix)
  - Quality checks (black, flake8, pyright, pytest) all pass
  - Files changed: `tests/test_server.py` (added ~600 lines of comprehensive tests), `src/trellis_mcp/server.py` (fixed task file naming and removed problematic return type annotation)

### Path Logic Consolidation

- [x] **R-04** (S) Centralize path construction logic in `path_resolver` module
  - Add `resolve_path_for_new_object(kind, id, parent_id, project_root)` function
  - Move complex path construction logic from `createObject` handler
  - Ensure consistent path handling across all object kinds
  - Update existing `id_to_path` function if needed for consistency
  - Add unit tests for new path resolution function
  
  **Implementation Summary:**
  - Added `resolve_path_for_new_object(kind, obj_id, parent_id, project_root, status=None)` function to path_resolver.py
  - Function handles all object kinds (project, epic, feature, task) with proper hierarchy validation
  - Supports status-dependent path logic for tasks (open vs done directories, timestamp prefixes)
  - Handles ID prefix stripping consistently (P-, E-, F-, T- prefixes)
  - Includes proper parent validation (requires parent for epics, features, tasks)
  - Added comprehensive test suite with 23 test methods covering all scenarios
  - Tests cover path construction, error handling, prefix stripping, and consistency validation
  - All quality checks pass (black, flake8, pyright, pytest)
  - Files changed: `src/trellis_mcp/path_resolver.py` (added ~100 lines), `tests/test_path_resolver.py` (added ~340 lines of tests)
- [x] **R-05** (XS) Refactor `createObject` handler to use centralized path logic
  - Replace inline path construction with `resolve_path_for_new_object` calls
  - Simplify the handler logic by removing path-specific code
  - Ensure proper error handling is maintained
  
  **Implementation Summary:**
  - Updated import statement in server.py to include `resolve_path_for_new_object` from path_resolver
  - Replaced 80 lines of complex path construction logic (lines 189-268) with a 7-line call to the centralized function
  - Maintained proper error handling by catching and re-raising ValueError and FileNotFoundError exceptions
  - Removed duplicated path logic for all object kinds (project, epic, feature, task)
  - Simplified createObject handler by removing path-specific conditional logic and directory traversal code
  - All quality checks pass (black, flake8, pyright, pytest with 470 tests)
  - Files changed: `src/trellis_mcp/server.py` (removed ~73 lines of path construction code, added 1 import)

### Leverage Pydantic More

- [x] **R-06** (M) Move front-matter validation into Pydantic schema models
  - Add `@field_validator` decorators to schema models for required field validation
  - Add enum validation directly in schema models
  - Move kind-specific required field logic into respective schema classes
  - Update `validate_front_matter` to delegate to Pydantic model validation
  - Ensure error message consistency with current implementation
  
  **Implementation Summary:**
  - Created `get_model_class_for_kind()` function in schema/__init__.py to map object kinds to appropriate Pydantic model classes
  - Enhanced BaseSchemaModel parent field validation by adding `validate_default=True` to ensure parent validators run for default None values
  - Completely refactored `validate_front_matter()` function in validation.py to use Pydantic model validation instead of manual validation
  - Implemented comprehensive error parsing logic to convert Pydantic ValidationError objects into error message format that matches original implementation
  - Added special handling for parent validation errors to treat them as "missing required fields" to maintain backward compatibility
  - Added error message cleanup for status validation errors to remove "StatusEnum." prefixes and format correctly
  - Added handling for None enum values to treat them as missing fields rather than enum validation errors
  - Added field filtering to only validate fields defined in the model schema, allowing extra fields to be ignored (maintaining original permissive behavior)
  - All 20 front-matter validation tests pass with exact same error message format as original implementation
  - All quality checks pass: black formatting, flake8 linting, pyright type checking, and all 470 tests
  - Files changed: `src/trellis_mcp/schema/__init__.py` (added model factory function), `src/trellis_mcp/schema/base_schema.py` (added validate_default=True), `src/trellis_mcp/validation.py` (completely refactored validate_front_matter function)
- [x] **R-07** (M) Move status transition validation into Pydantic schema models
  - Add `@model_validator` decorators to handle status transition logic
  - Move lifecycle transition rules into schema models
  - Update `enforce_status_transition` to work with Pydantic validation
  - Maintain current transition matrix behavior (task shortcuts, etc.)
  
  **Implementation Summary:**
  - Added transition matrices as class attributes to all schema models (ProjectModel, EpicModel, FeatureModel, TaskModel)
  - Added `validate_status_transition` class method to BaseSchemaModel that validates transitions using model-specific matrices
  - Added `@model_validator` decorator to BaseSchemaModel for context-based transition validation
  - Refactored `enforce_status_transition` function to delegate to schema model validation while maintaining same interface
  - Preserved all existing behavior including task shortcuts (open→done, in-progress→done), terminal status handling, and error message format
  - All 470 tests pass including 20 comprehensive status transition tests that verify exact behavioral compatibility
  - Quality checks (black, flake8, pyright, pytest) all pass
  - Files changed: `src/trellis_mcp/schema/base_schema.py` (added transition validation methods), `src/trellis_mcp/schema/project.py` (added transition matrix), `src/trellis_mcp/schema/epic.py` (added transition matrix), `src/trellis_mcp/schema/feature.py` (added transition matrix), `src/trellis_mcp/schema/task.py` (added transition matrix), `src/trellis_mcp/validation.py` (refactored to delegate to schema models)
- [x] **R-08** (S) Update validation.py to use Pydantic-based validation
  - Refactor validation functions to use schema model validation
  - Remove duplicated validation logic
  - Maintain backward compatibility with existing error handling
  - Update tests to work with new validation approach
  
  **Implementation Summary:**
  - Refactored `validate_required_fields_per_kind` to use Pydantic model validation instead of manual field checking
  - Refactored `validate_enum_membership` to use Pydantic validation with fallback to manual validation when kind is missing
  - Refactored `validate_status_for_kind` to use Pydantic schema status validation instead of hardcoded status sets
  - Refactored `validate_object_data` to use Pydantic model validation directly instead of calling individual manual functions
  - Maintained exact backward compatibility by parsing Pydantic ValidationError objects and formatting error messages to match original format
  - Added special handling for fields with defaults (like schema_version) that were considered required in original logic
  - All 470 tests pass with exact same behavior as before, ensuring no regression
  - Quality checks (black, flake8, pyright, pytest) all pass
  - Successfully removed duplicated validation logic while preserving all existing functionality and error message formats
  - Files changed: `src/trellis_mcp/validation.py` (completely refactored 4 validation functions to use Pydantic)

### Pre-emptive Cycle Checking

- [x] **R-09** (M) Implement in-memory cycle checking before file writes
  - Create `build_dependency_graph_in_memory` function in validation.py
  - Modify `createObject` to check cycles before writing files
  - Modify `updateObject` to check cycles before writing files
  - Build dependency graph from existing files + proposed changes
  - Run cycle detection on in-memory graph
  - Maintain rollback logic as fallback safety measure

  **Implementation Summary:**
  - Added `build_dependency_graph_in_memory(project_root, proposed_object_data, operation_type)` function to validation.py that builds dependency graphs without file writes
  - Added `check_prereq_cycles_in_memory(project_root, proposed_object_data, operation_type)` convenience function that performs complete in-memory cycle validation
  - Function loads existing objects using `get_all_objects`, merges with proposed changes, and runs cycle detection using existing `detect_cycle_dfs` algorithm
  - Supports both "create" and "update" operations with proper ID cleaning using `clean_prerequisite_id`
  - Modified `createObject` handler in server.py to call in-memory cycle check BEFORE writing files to prevent unnecessary file operations
  - Modified `updateObject` handler in server.py to call in-memory cycle check BEFORE writing updated files to prevent unnecessary file operations  
  - Maintained existing post-validation rollback logic as fallback safety measure (defense in depth)
  - Preserves all existing error handling and message formats - raises same `CircularDependencyError` with same cycle path format
  - All 470 existing tests pass, ensuring backward compatibility and no regressions
  - Quality checks (black, flake8, pyright) all pass
  - Verified functionality with comprehensive test covering valid dependencies, self-reference cycles, update-induced cycles, and graph construction
  - Files changed: `src/trellis_mcp/validation.py` (added 2 new functions ~50 lines), `src/trellis_mcp/server.py` (added imports and pre-validation logic ~20 lines)
- [x] **R-10** (S) Optimize cycle detection performance
  - Cache dependency graph where appropriate
  - Add performance benchmarks for cycle detection
  - Consider lazy loading of dependency data
  - Document performance characteristics
  
  **Implementation Summary:**
  - Added `DependencyGraphCache` class with file modification time-based invalidation for efficient caching
  - Implemented `PerformanceBenchmark` utility class for measuring cycle detection performance
  - Enhanced `get_all_objects` to optionally return file modification times for cache validation
  - Updated `validate_acyclic_prerequisites` and `check_prereq_cycles` to use optimized caching with cache hit/miss logic
  - Added performance benchmarking functions: `benchmark_cycle_detection`, `get_cache_stats`, `clear_dependency_cache`
  - Created comprehensive performance documentation in PERFORMANCE.md covering caching strategy, benchmarking, and optimization guidelines
  - Implemented lazy loading considerations through efficient cache validation (only checks file mtimes on cache hits)
  - All existing 470 tests pass, ensuring no regressions in cycle detection accuracy
  - Quality checks (black, flake8, pyright, pytest) all pass
  - Cache provides significant performance improvements for repeated operations on unchanged projects
  - Files changed: `src/trellis_mcp/validation.py` (added ~400 lines of caching and benchmarking code), `src/trellis_mcp/__init__.py` (added exports), `docs/PERFORMANCE.md` (added comprehensive performance documentation)

### Quality Gates

* All existing tests continue to pass
* New server-level tests achieve >90% coverage for RPC handlers
* Path resolution logic is centralized and consistent
* Pydantic validation reduces code duplication
* Pre-emptive cycle checking reduces unnecessary file operations
* No regression in error handling or validation behavior
* Code follows existing patterns and style guidelines

### Context for Developers

**Architecture Overview:**
- Trellis MCP is a file-backed JSON-RPC server using FastMCP
- Stores state as Markdown files with YAML front-matter
- Hierarchy: Projects → Epics → Features → Tasks
- Files stored in `planning/projects/P-{id}/epics/E-{id}/features/F-{id}/tasks-{status}/T-{id}.md`

**Key Files:**
- `src/trellis_mcp/server.py` - RPC handlers (createObject, getObject, updateObject, listBacklog)
- `src/trellis_mcp/validation.py` - Business logic validation
- `src/trellis_mcp/schema/` - Pydantic data models
- `src/trellis_mcp/path_resolver.py` - Path resolution utilities
- `tests/test_server.py` - RPC handler tests (currently incomplete)

**Current Implementation Notes:**
- Atomic file operations using tempfile and os.replace
- Comprehensive validation with TrellisValidationError aggregation
- Status transition lifecycle enforcement
- Acyclic prerequisite validation using DFS
- JSON merge patch support for updates

**Testing Standards:**
- Type hints everywhere
- Functions ≤ 40 LOC, classes ≤ 200 LOC
- Unit test coverage ≥ 90% for validators and RPC handlers
- Integration tests for end-to-end workflows
- Quality gate: `uv run pre-commit run --all-files && uv run pytest -q`