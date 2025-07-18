---
kind: task
id: T-implement-type-guard-functions
title: Implement type guard functions for runtime type checking
status: open
priority: high
prerequisites:
- T-update-core-type-annotations-for
created: '2025-07-18T08:10:39.294477'
updated: '2025-07-18T08:10:39.294477'
schema_version: '1.1'
parent: F-type-system-enhancement
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

