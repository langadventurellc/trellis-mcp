---
kind: task
id: T-create-task-type-detection
title: Create task type detection utility functions
status: open
priority: high
prerequisites: []
created: '2025-07-17T23:08:42.863464'
updated: '2025-07-17T23:08:42.863464'
schema_version: '1.0'
parent: F-task-validation-logic-updates
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

