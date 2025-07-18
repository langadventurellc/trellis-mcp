---
kind: task
id: T-update-data-classes-and-pydantic
parent: F-type-system-enhancement
status: done
title: Update data classes and Pydantic models with correct type annotations
priority: high
prerequisites:
- T-update-core-type-annotations-for
created: '2025-07-18T08:10:47.069643'
updated: '2025-07-18T08:45:50.317978'
schema_version: '1.1'
worktree: null
---
Update all data classes and Pydantic models to use correct type annotations for optional parent fields.

**Implementation Requirements:**
- Update task data classes to use `str | None` for parent fields
- Update Pydantic models with proper optional field types
- Ensure field validation works correctly with optional types
- Update model serialization/deserialization to handle None values
- Maintain backward compatibility with existing data structures

**Acceptance Criteria:**
- All data classes have correct type annotations for optional fields
- Pydantic models validate optional parent fields properly
- Serialization/deserialization handles None values correctly
- No breaking changes to existing model usage
- Type checking tools pass without errors

**Files to Update:**
- Data class definitions for tasks, features, epics, projects
- Pydantic model definitions
- Model validation logic
- Serialization/deserialization utilities

**Testing Requirements:**
- Test model creation with None parent values
- Test model validation with various parent field types
- Test serialization/deserialization with optional fields
- Verify backward compatibility with existing data

### Log


**2025-07-18T13:49:37.458348Z** - Updated the createObject function in src/trellis_mcp/tools/create_object.py to use proper optional type annotations for the parent parameter. Changed from parent: str = "" to parent: str | None = None and simplified the internal logic to handle None values directly instead of converting empty strings. This ensures consistency with the modern Python union syntax used throughout the codebase and aligns with the schema model's handling of optional parent fields.
- filesChanged: ["src/trellis_mcp/tools/create_object.py"]