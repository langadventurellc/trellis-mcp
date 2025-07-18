---
kind: task
id: T-enhance-validationerror-with
title: Enhance ValidationError with cross-system context
status: open
priority: normal
prerequisites: []
created: '2025-07-18T17:33:34.262019'
updated: '2025-07-18T17:33:34.262019'
schema_version: '1.1'
parent: F-enhanced-error-handling-1
---
### Implementation Requirements
Extend the existing `ValidationError` class to include cross-system context information, enabling better error messages that specify task types and system boundaries involved in validation failures.

### Technical Approach
- Enhance `src/trellis_mcp/exceptions/validation_error.py`
- Add task type detection to error context creation
- Update message templates in `message_templates/` for cross-system scenarios
- Use existing task type detection utilities

### Acceptance Criteria
- ValidationError includes task system context (standalone/hierarchical)
- Error messages specify which systems are involved in conflicts
- Maintains backward compatibility with existing error handling
- Performance impact is minimal (<1ms per error)

### Implementation Details
```python
# Enhanced error context examples:
"Cannot reference standalone task 'T-auth' from hierarchical task 'T-user-model'"
"Prerequisite validation failed: hierarchical task 'F-user-login' requires standalone task 'T-auth-setup' which does not exist"
```

### Testing Requirements
- Unit tests for enhanced error context creation
- Message template validation tests
- Cross-system error scenario tests
- Backward compatibility tests for existing error handling

### Security Considerations
- Ensure enhanced context doesn't expose internal file paths
- Validate that task type information doesn't leak sensitive details
- Follow existing security patterns for error message sanitization

### Log

