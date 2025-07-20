---
kind: task
id: T-create-task-id-resolution
parent: F-direct-task-claiming
status: done
title: Create task ID resolution utility for cross-system lookup
priority: high
prerequisites: []
created: '2025-07-20T15:18:26.972930'
updated: '2025-07-20T15:35:55.105099'
schema_version: '1.1'
worktree: null
---
## Context

Create a utility module to resolve task IDs across both hierarchical (T- prefixed) and standalone task systems. This utility will locate specific tasks by ID and return their file paths and metadata for direct claiming operations.

## Technical Approach

1. **Create task_resolver.py module** with ID resolution functions
2. **Implement cross-system lookup logic** that searches both hierarchical and standalone directories
3. **Add ID validation and normalization** for T- prefixed and standalone formats
4. **Integrate with existing scanner infrastructure** for efficient task discovery
5. **Create comprehensive unit tests** for all resolution scenarios

## Implementation Details

### New File to Create
- `src/trellis_mcp/task_resolver.py`

### Core Functions Needed
```python
def resolve_task_by_id(project_root: str, task_id: str) -> Optional[Path]:
    """Resolve task ID to file path across both task systems."""
    
def validate_task_id_format(task_id: str) -> bool:
    """Validate task ID format for both hierarchical and standalone tasks."""
    
def normalize_task_id(task_id: str) -> str:
    """Normalize task ID for consistent lookup operations."""
```

### Lookup Strategy
- **Hierarchical tasks**: Search in `planning/projects/P-*/epics/E-*/features/F-*/tasks-*` directories
- **Standalone tasks**: Search in `planning/tasks-*` directories at project root
- **ID normalization**: Handle T- prefix variations and clean task IDs
- **Efficient search**: Use existing scanner patterns for file discovery

### Integration Points
- Leverage existing `scanner.py` task discovery patterns
- Use `utils.id_utils` for ID cleaning and validation
- Follow same error handling patterns as current task operations

### Unit Test Requirements
Create `tests/test_task_resolver.py` with:
- **Cross-system lookup tests**: Find tasks in both hierarchical and standalone systems
- **ID format validation tests**: Various task ID formats (T-*, standalone, invalid)
- **Path resolution tests**: Verify correct file paths returned
- **Normalization tests**: ID cleaning and normalization accuracy
- **Performance tests**: Efficient lookup with large task hierarchies
- **Error handling tests**: Invalid IDs and non-existent tasks
- **Edge case tests**: Malformed files, permission issues

## Acceptance Criteria

- [ ] **Cross-System Lookup**: Finds tasks in both hierarchical and standalone systems
- [ ] **ID Format Support**: Handles T- prefixed and standalone task ID formats
- [ ] **Path Resolution**: Returns correct file paths for found tasks
- [ ] **Validation**: Validates task ID format before lookup operations
- [ ] **Error Handling**: Returns None for non-existent tasks, raises for invalid formats
- [ ] **Performance**: Efficient lookup using existing scanning infrastructure
- [ ] **Unit Test Coverage**: Comprehensive tests for all resolution scenarios

## Dependencies
- None (foundational utility)

## Testing Requirements
- Unit tests for task ID validation with various formats
- Cross-system lookup tests with hierarchical and standalone tasks
- Path resolution accuracy tests
- Performance tests for large task hierarchies
- Error handling tests for invalid IDs and non-existent tasks

### Log
**2025-07-20T20:43:12.797256Z** - Implemented comprehensive task ID resolution utility for cross-system lookup functionality. Created task_resolver.py module with three core functions: resolve_task_by_id for locating tasks across both hierarchical and standalone systems, validate_task_id_format for validating T- prefixed and standalone task ID formats, and normalize_task_id for consistent ID cleaning and normalization. Integrated with existing scanner infrastructure and security validation patterns. Added comprehensive unit tests covering cross-system lookup, ID validation, normalization, error handling, and edge cases. All quality checks pass (format, lint, typecheck, tests). This foundational utility enables the direct task claiming feature by providing reliable task ID resolution across both task systems.
- filesChanged: ["src/trellis_mcp/task_resolver.py", "tests/test_task_resolver.py"]