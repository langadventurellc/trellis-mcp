---
kind: task
id: T-implement-type-guard-functions
parent: F-type-system-enhancement
status: done
title: Implement type guard functions for runtime type checking
priority: high
prerequisites:
- T-update-core-type-annotations-for
created: '2025-07-18T08:10:39.294477'
updated: '2025-07-18T08:31:37.281413'
schema_version: '1.1'
worktree: null
---
Create type guard functions using `typing.TypeGuard` for proper type narrowing and runtime type checking.

**Implementation Requirements:**
- Implement `is_standalone_task()` type guard function
- Implement `is_hierarchy_task()` type guard function
- Use `typing.TypeGuard` for proper type narrowing support
- Create utility functions for checking task types at runtime
- Add type guards for different object types (project, epic, feature, task)

**Acceptance Criteria:**
- Type guard functions properly narrow types in conditional blocks
- IDE provides accurate type information after type guard checks
- Runtime type checking works correctly for both task types
- Type guards handle edge cases (None values, malformed data)

**Files to Create/Update:**
- `src/trellis_mcp/types.py` or similar module for type utilities
- Update modules that perform runtime type checks
- Add type guard imports where needed

**Testing Requirements:**
- Unit tests for each type guard function
- Test type narrowing behavior with various inputs
- Test edge cases (None, empty strings, malformed data)
- Verify IDE type checking with manual testing

### Log

**2025-07-18T08:32:00.000000Z** - Implemented comprehensive type guard functions using `typing.TypeGuard` for proper type narrowing and runtime type checking. Created new `src/trellis_mcp/types.py` module with type guards for all object types (project, epic, feature, task) and specialized task type guards for standalone vs hierarchy tasks. Updated `src/trellis_mcp/validation/task_utils.py` to add TypeGuard versions of existing functions while maintaining backward compatibility. All type guards provide proper type narrowing for static type checkers and handle edge cases including None values, empty strings, and malformed data. Added comprehensive test suite with 30 test cases covering all functions, edge cases, and type narrowing behavior. All tests pass and code quality checks pass including isort, black, flake8, and pyright.


**2025-07-18T13:36:42.613721Z** - Implemented comprehensive type guard functions using typing.TypeGuard for proper type narrowing and runtime type checking. Created new src/trellis_mcp/types.py module with type guards for all object types (project, epic, feature, task) and specialized task type guards for standalone vs hierarchy tasks. Updated src/trellis_mcp/validation/task_utils.py to add TypeGuard versions of existing functions while maintaining backward compatibility. All type guards provide proper type narrowing for static type checkers and handle edge cases including None values, empty strings, and malformed data. Added comprehensive test suite with 30 test cases covering all functions, edge cases, and type narrowing behavior. All tests pass and code quality checks pass including isort, black, flake8, and pyright.
- filesChanged: ["src/trellis_mcp/types.py", "src/trellis_mcp/validation/task_utils.py", "src/trellis_mcp/validation/__init__.py", "src/trellis_mcp/__init__.py", "tests/unit/test_type_guards.py"]