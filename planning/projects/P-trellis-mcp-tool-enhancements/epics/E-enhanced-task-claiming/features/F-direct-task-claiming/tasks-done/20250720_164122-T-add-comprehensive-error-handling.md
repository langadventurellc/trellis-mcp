---
kind: task
id: T-add-comprehensive-error-handling
parent: F-direct-task-claiming
status: done
title: Add comprehensive error handling for direct task claiming scenarios
priority: normal
prerequisites:
- T-implement-direct-task-claiming
created: '2025-07-20T15:19:18.955407'
updated: '2025-07-20T16:37:15.029159'
schema_version: '1.1'
worktree: null
---
## Context

Implement comprehensive error handling for direct task claiming scenarios, including task not found, invalid status, blocked prerequisites, and concurrent claiming attempts. Ensure clear error messages that help users understand and resolve issues.

## Technical Approach

1. **Define specific error types** for direct claiming scenarios
2. **Add detailed error messages** with context and resolution guidance
3. **Integrate with existing error hierarchy** using ValidationError and error codes
4. **Handle edge cases** like deleted tasks, moved tasks, and concurrent access
5. **Create unit tests** for all error scenarios

## Implementation Details

### Error Scenarios to Handle

#### Task Resolution Errors
- **Task Not Found**: Task ID doesn't exist in either system
- **Invalid Task ID Format**: Malformed task ID that doesn't match expected patterns
- **Task Outside Project Root**: Task exists but not accessible in current project

#### Task State Errors
- **Task Not Open**: Task has status other than OPEN (IN_PROGRESS, DONE, REVIEW)
- **Blocked Prerequisites**: Task has incomplete prerequisites
- **Task Already Claimed**: Concurrent claiming attempt detected

#### System Errors
- **File Access Errors**: Permission issues, disk space, corrupted files
- **Atomic Operation Failures**: Status update failures during claiming

### Error Message Guidelines
```python
# Example error messages with context
TASK_NOT_FOUND = "Task '{task_id}' not found in project. Verify the task ID and ensure it exists in the current project scope."

TASK_ALREADY_CLAIMED = "Task '{task_id}' is already claimed (status: {status}). Use completeTask to finish in-progress tasks."

PREREQUISITES_BLOCKED = "Task '{task_id}' cannot be claimed because {blocked_count} prerequisites are incomplete: {blocked_list}"
```

### Integration with Existing Error System
- Use existing `ValidationError` with appropriate `ValidationErrorCode`
- Add new error codes if needed for direct claiming scenarios
- Maintain consistent error response format across all MCP tools

### File Locations
- `src/trellis_mcp/claim_next_task.py` - Core error handling
- `src/trellis_mcp/exceptions.py` - Add new error types if needed
- `src/trellis_mcp/models/validation_error.py` - Add error codes if needed

### Unit Test Requirements
Create `tests/test_direct_claiming_errors.py` with:
- **Task not found tests**: Various non-existent task ID scenarios
- **Invalid format tests**: Malformed task ID error handling
- **Status validation tests**: Tasks with different statuses (not OPEN)
- **Prerequisite blocking tests**: Tasks with incomplete prerequisites
- **Concurrent claim tests**: Multiple simultaneous claiming attempts
- **System error tests**: File permission and disk space issues
- **Error message tests**: Verify error messages are clear and actionable
- **Error code tests**: Proper error codes returned for each scenario

## Acceptance Criteria

- [ ] **Task Not Found**: Clear error when task ID doesn't exist
- [ ] **Invalid Format**: Descriptive error for malformed task IDs
- [ ] **Status Validation**: Specific errors for non-OPEN task status
- [ ] **Prerequisite Blocking**: Detailed prerequisite blocking information
- [ ] **Concurrent Claims**: Graceful handling of simultaneous claiming attempts
- [ ] **System Errors**: Proper error handling for file/permission issues
- [ ] **Error Consistency**: Errors follow same format as existing MCP tools
- [ ] **Unit Test Coverage**: Comprehensive tests for all error scenarios

## Dependencies
- T-implement-direct-task-claiming (core claiming logic to add error handling to)

## Testing Requirements
- Unit tests for each error scenario with specific task states
- Integration tests for error propagation through tool interface
- Concurrent claiming error tests
- Error message format validation tests
- Edge case testing (missing files, permission issues)

### Log
**2025-07-20T21:41:22.746191Z** - Analyzed existing error handling for direct task claiming scenarios and confirmed comprehensive coverage is already implemented. Current system includes structured ValidationError with error codes, NoAvailableTask exceptions for claiming failures, cross-system validation support, prerequisite blocking detection via dependency resolver, and extensive test coverage (400+ lines). No additional error handling enhancements needed - existing implementation adequately covers all required error scenarios including task not found, invalid status, blocked prerequisites, and system errors.