# F-04-Review · Code Quality Improvements — Task Checklist

## Checklist

**IMPORTANT**: When starting a new task, read @../../docs/task_mcp_spec_and_plan.md for context.

This task addresses code quality improvements identified in Gemini's review of the F-04 CRUD Objects RPC feature implementation.

### Server-Level Testing Gap

- [ ] **R-01** (M) Add comprehensive tests for `createObject` RPC handler in `test_server.py`
  - Test valid object creation for all kinds (project, epic, feature, task)
  - Test ID generation when missing
  - Test validation error handling (invalid YAML, missing required fields)
  - Test prerequisite cycle detection and rollback
  - Test file system error handling
  - Test parent-child relationship validation
- [ ] **R-02** (M) Add comprehensive tests for `updateObject` RPC handler in `test_server.py`
  - Test yamlPatch updates for all object kinds
  - Test bodyPatch updates for markdown content
  - Test deep merge functionality with nested structures
  - Test status transition validation
  - Test prerequisite cycle detection after updates
  - Test rollback on validation failures
  - Test error handling for malformed patches
- [ ] **R-03** (M) Add comprehensive tests for `listBacklog` RPC handler in `test_server.py`
  - Test scope filtering (project/epic/feature ID)
  - Test status filtering (open, in-progress, review, done)
  - Test priority filtering (high, normal, low)
  - Test priority-based sorting with secondary date sorting
  - Test empty results handling
  - Test error handling for invalid parameters
  - Test cross-directory searching (tasks-open and tasks-done)

### Path Logic Consolidation

- [ ] **R-04** (S) Centralize path construction logic in `path_resolver` module
  - Add `resolve_path_for_new_object(kind, id, parent_id, project_root)` function
  - Move complex path construction logic from `createObject` handler
  - Ensure consistent path handling across all object kinds
  - Update existing `id_to_path` function if needed for consistency
  - Add unit tests for new path resolution function
- [ ] **R-05** (XS) Refactor `createObject` handler to use centralized path logic
  - Replace inline path construction with `resolve_path_for_new_object` calls
  - Simplify the handler logic by removing path-specific code
  - Ensure proper error handling is maintained

### Leverage Pydantic More

- [ ] **R-06** (M) Move front-matter validation into Pydantic schema models
  - Add `@field_validator` decorators to schema models for required field validation
  - Add enum validation directly in schema models
  - Move kind-specific required field logic into respective schema classes
  - Update `validate_front_matter` to delegate to Pydantic model validation
  - Ensure error message consistency with current implementation
- [ ] **R-07** (M) Move status transition validation into Pydantic schema models
  - Add `@model_validator` decorators to handle status transition logic
  - Move lifecycle transition rules into schema models
  - Update `enforce_status_transition` to work with Pydantic validation
  - Maintain current transition matrix behavior (task shortcuts, etc.)
- [ ] **R-08** (S) Update validation.py to use Pydantic-based validation
  - Refactor validation functions to use schema model validation
  - Remove duplicated validation logic
  - Maintain backward compatibility with existing error handling
  - Update tests to work with new validation approach

### Pre-emptive Cycle Checking

- [ ] **R-09** (M) Implement in-memory cycle checking before file writes
  - Create `build_dependency_graph_in_memory` function in validation.py
  - Modify `createObject` to check cycles before writing files
  - Modify `updateObject` to check cycles before writing files
  - Build dependency graph from existing files + proposed changes
  - Run cycle detection on in-memory graph
  - Maintain rollback logic as fallback safety measure
- [ ] **R-10** (S) Optimize cycle detection performance
  - Cache dependency graph where appropriate
  - Add performance benchmarks for cycle detection
  - Consider lazy loading of dependency data
  - Document performance characteristics

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