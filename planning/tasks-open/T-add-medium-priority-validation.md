---
kind: task
id: T-add-medium-priority-validation
title: Add medium priority support to createObject validation
status: open
priority: normal
prerequisites: []
created: '2025-07-20T17:49:45.639234'
updated: '2025-07-20T17:49:45.639234'
schema_version: '1.1'
---
Update the createObject tool validation to accept "medium" as a valid priority value that gets internally converted to "normal" for consistency with the rest of the system.

## Context

The current Priority enum in `src/trellis_mcp/models/common.py` supports three values: HIGH (1), NORMAL (2), and LOW (3). The system uses "normal" as the standard medium priority level, but users may naturally expect "medium" to be accepted as well.

The createObject tool in `src/trellis_mcp/tools/create_object.py` accepts priority as a string parameter and validates it through the Priority enum. We need to add support for "medium" values that get automatically converted to "normal" internally.

## Technical Approach

1. **Modify Priority enum validation**: Update the `_missing_` method in the Priority class to handle "medium" as an alias for "normal"
2. **Update createObject tool**: Add priority value normalization before validation
3. **Comprehensive testing**: Add test cases for the new "medium" priority handling

## Acceptance Criteria

1. **Priority Enum Enhancement**:
   - The Priority enum accepts "medium" as input and returns Priority.NORMAL
   - Existing priority values ("high", "normal", "low") continue to work unchanged
   - String representation still returns "normal" for Priority.NORMAL (not "medium")

2. **createObject Tool Support**:
   - Users can specify priority="medium" when calling createObject
   - "medium" priority values are internally converted to "normal" before storage
   - YAML front-matter in created files shows priority: normal (not medium)
   - All existing createObject functionality remains unchanged

3. **Validation Consistency**:
   - Priority validation in `validate_priority_field()` accepts "medium" values
   - Error messages for invalid priorities include "medium" as a valid option
   - Internal system operations continue using "normal" as the canonical value

4. **Testing Coverage**:
   - Unit tests for Priority enum with "medium" input
   - Integration tests for createObject with priority="medium"
   - Validation tests ensuring proper conversion and storage

## Implementation Files

- `src/trellis_mcp/models/common.py` - Priority enum enhancement
- `src/trellis_mcp/tools/create_object.py` - Priority normalization logic
- `src/trellis_mcp/validation/field_validation.py` - Validation updates (if needed)
- Tests for comprehensive coverage

## Security Considerations

- Input validation ensures only valid priority values are accepted
- No impact on existing priority-based task sorting or claiming logic
- Maintains backward compatibility with all existing objects

### Log

