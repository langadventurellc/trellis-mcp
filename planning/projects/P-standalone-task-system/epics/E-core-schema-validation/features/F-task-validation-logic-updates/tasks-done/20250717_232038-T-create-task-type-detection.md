---
kind: task
id: T-create-task-type-detection
parent: F-task-validation-logic-updates
status: done
title: Create task type detection utility functions
priority: high
prerequisites: []
created: '2025-07-17T23:08:42.863464'
updated: '2025-07-17T23:10:31.333098'
schema_version: '1.0'
worktree: null
---
Create utility functions to detect task types: `is_standalone_task()` and `is_hierarchy_task()`. These functions should examine the task data structure to determine if a task is standalone (no parent field) or hierarchy-based (has parent field).

**Implementation Requirements:**
- Create helper functions in validation module
- Functions should accept task data as parameter
- Return boolean values for type detection
- Handle edge cases like malformed data gracefully
- Follow existing code patterns and conventions

**Acceptance Criteria:**
- `is_standalone_task()` returns True for tasks without parent field
- `is_hierarchy_task()` returns True for tasks with parent field
- Functions handle None/empty task data without crashing
- Functions are properly typed with type hints

**Testing Requirements:**
- Unit tests for both detection functions
- Tests for edge cases (None, empty dict, malformed data)
- Tests for typical standalone and hierarchy task structures

### Log


**2025-07-18T04:20:38.994041Z** - Implemented task type detection utility functions with comprehensive edge case handling. Created overloaded is_standalone_task() function to support both original signature and new task data parameter, plus new is_hierarchy_task() function. Added 14 comprehensive test cases covering all scenarios including None/empty data, malformed data, and complementary function behavior. All quality checks pass and maintains backward compatibility.
- filesChanged: ["src/trellis_mcp/validation.py", "src/trellis_mcp/__init__.py", "tests/unit/test_validation.py"]