---
kind: task
id: T-update-validation-error-messages
parent: F-task-validation-logic-updates
status: done
title: Update validation error messages for contextual clarity
priority: normal
prerequisites:
- T-implement-conditional-validation
created: '2025-07-17T23:08:56.682283'
updated: '2025-07-17T23:40:08.747583'
schema_version: '1.0'
worktree: null
---
Update validation error messages to be contextually appropriate for both standalone and hierarchy-based tasks. Error messages should clearly indicate the task type and provide relevant guidance for fixing validation issues.

**Implementation Requirements:**
- Update error messages to specify task type in validation failures
- Provide clear guidance for fixing validation issues
- Maintain consistent error message formatting
- Include task type context in error details
- Follow existing error message patterns and conventions

**Acceptance Criteria:**
- Error messages distinguish between standalone and hierarchy task validation failures
- Messages provide clear guidance for resolving validation issues
- Error message formatting remains consistent across task types
- No ambiguous or misleading error messages
- Error messages are helpful for debugging validation issues

**Testing Requirements:**
- Unit tests for error message generation
- Tests for both standalone and hierarchy task error scenarios
- Tests for different types of validation failures
- Verification that error messages are contextually appropriate

### Log

**2025-07-18** - Implemented contextual validation error messages for standalone and hierarchy tasks.

Added enhanced error message system that provides clear contextual information distinguishing between standalone tasks (no parent) and hierarchy tasks (with parent). The implementation includes:

1. **Core Functions Added**:
   - `get_task_type_context()` - Detects task type (standalone/hierarchy)
   - `format_validation_error_with_context()` - Formats existing errors with context
   - `generate_contextual_error_message()` - Generates new contextual error messages

2. **Enhanced Error Messages**:
   - Status errors: "Invalid status 'draft' for standalone task" vs "Invalid status 'draft' for hierarchy task"
   - Priority errors: "Invalid priority 'invalid' for standalone task" vs "Invalid priority 'invalid' for hierarchy task"
   - Parent errors: "Parent feature with ID 'nonexistent' does not exist (hierarchy task validation)"
   - Missing fields: "Missing required fields for standalone task: status, created"

3. **Backward Compatibility**:
   - Non-task objects (projects, epics, features) maintain original error messages
   - All existing tests continue to pass (889 tests total)
   - Error message structure and aggregation preserved

4. **Comprehensive Testing**:
   - 33 new tests covering all contextual error scenarios
   - Tests for both standalone and hierarchy task validation
   - Backward compatibility verification
   - Integration with existing validation pipeline

The implementation successfully provides contextual clarity for validation errors while maintaining full backward compatibility with existing error handling patterns.


**2025-07-18T04:46:53.289865Z** - Implemented contextual validation error messages for standalone and hierarchy tasks. Added enhanced error message system that provides clear contextual information distinguishing between standalone tasks (no parent) and hierarchy tasks (with parent). The implementation includes new contextual error generation functions, enhanced error messages for status/priority/parent validation, full backward compatibility, and comprehensive testing with 33 new tests covering all scenarios.
- filesChanged: ["src/trellis_mcp/validation.py", "tests/unit/test_validation_error_messages.py"]