---
kind: task
id: T-add-cross-system-prerequisite
title: Add cross-system prerequisite existence validation
status: open
priority: high
prerequisites: []
created: '2025-07-18T17:33:12.298933'
updated: '2025-07-18T17:33:12.298933'
schema_version: '1.1'
parent: F-enhanced-error-handling-1
---
### Implementation Requirements
Create a new validation function `validate_prerequisite_existence()` that verifies all prerequisite IDs exist across both hierarchical and standalone task systems before object creation or updates.

### Technical Approach
- Add function to `src/trellis_mcp/validation/field_validation.py` 
- Use existing `get_all_objects()` to build ID mapping for efficient lookups
- Integrate with existing `ValidationErrorCollector` for consistent error handling
- Call from `validate_object_data_enhanced()` when prerequisites are present

### Acceptance Criteria
- Function validates prerequisites exist in both task systems
- Returns appropriate `ValidationError` with cross-system context
- Performance impact <10ms for typical prerequisite lists (1-10 items)
- Integrates cleanly with existing validation pipeline

### Implementation Details
```python
def validate_prerequisite_existence(
    prerequisites: list[str], 
    project_root: str,
    collector: ValidationErrorCollector
) -> None:
    """Validate that all prerequisite IDs exist in the project."""
    # Implementation using existing patterns
```

### Testing Requirements
- Unit tests with valid/invalid prerequisite combinations
- Cross-system reference validation tests
- Performance tests with large object sets
- Integration tests with existing validation flow

### Security Considerations
- Validate prerequisite ID format to prevent injection
- Ensure error messages don't expose internal paths
- Use existing path validation utilities

### Log

