---
kind: task
id: T-enhance-validationerror-with
parent: F-enhanced-error-handling-1
status: done
title: Enhance ValidationError with cross-system context
priority: normal
prerequisites: []
created: '2025-07-18T17:33:34.262019'
updated: '2025-07-18T18:15:27.356839'
schema_version: '1.1'
worktree: null
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


**2025-07-18T23:26:50.127547Z** - Enhanced ValidationError class with cross-system context information for better error messages between standalone and hierarchical task systems. Added two new error codes (CROSS_SYSTEM_REFERENCE_CONFLICT, CROSS_SYSTEM_PREREQUISITE_INVALID) and a create_cross_system_error() class method that generates contextual error messages like "Cannot reference hierarchical task 'user-model' from standalone task 'auth-setup'". Added five new message templates for cross-system scenarios. Enhanced context includes source/target task types, IDs, and conflict types while maintaining security by cleaning task IDs for display and preventing file path exposure. Performance requirement met (<1ms per error) with comprehensive test coverage including 16 new unit tests, scenario tests, and backward compatibility validation. All existing functionality preserved.
- filesChanged: ["src/trellis_mcp/exceptions/validation_error.py", "src/trellis_mcp/validation/message_templates/templates.py", "tests/unit/exceptions/test_cross_system_validation_error.py", "tests/unit/test_error_messages.py"]