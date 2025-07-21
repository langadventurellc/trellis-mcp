---
kind: feature
id: F-enhanced-parameter-validation
title: Enhanced Parameter Validation
status: done
priority: high
prerequisites:
- F-scope-based-task-filtering
- F-direct-task-claiming
created: '2025-07-20T13:11:48.994371'
updated: '2025-07-21T01:16:49.175923+00:00'
schema_version: '1.1'
parent: E-enhanced-task-claiming
---
# Enhanced Parameter Validation Feature

## Purpose and Functionality

Implement comprehensive parameter validation for the enhanced `claimNextTask` tool, establishing mutual exclusivity rules, parameter interaction logic, and consistent error handling. This ensures users receive clear guidance on proper parameter usage while maintaining backward compatibility with existing workflows.

## Key Components to Implement

### 1. Parameter Mutual Exclusivity Rules
- Enforce that `scope` and `task_id` parameters cannot be used together
- Validate that `force_claim` only applies when `task_id` is specified
- Implement parameter combination validation before processing requests
- Return clear error messages for invalid parameter combinations

### 2. Enhanced Parameter Validation Framework
- Extend existing FilterParams model for new claiming parameters
- Validate scope ID format (P-, E-, F- prefixes) and existence
- Validate task ID format (T- prefix or standalone) and existence
- Implement consistent validation patterns across all parameters

### 3. Backward Compatibility Preservation
- Maintain existing behavior when no enhanced parameters provided
- Preserve current priority-based claiming when only worktree specified
- Ensure existing claimNextTask usage continues working unchanged
- Validate that enhancements don't break current workflows

## Detailed Acceptance Criteria

### Parameter Combination Rules
- [ ] **Mutual Exclusivity**: Return error when both scope and task_id provided
- [ ] **Force Claim Scope**: force_claim parameter only valid with task_id parameter
- [ ] **Valid Combinations**: Allow scope + worktree, task_id + force_claim + worktree
- [ ] **Legacy Support**: Accept projectRoot + worktree (existing behavior)
- [ ] **Clear Error Messages**: Specific messages for each invalid parameter combination

### Enhanced Parameter Validation
- [ ] **Scope Format**: Validate P-, E-, F- prefixed IDs for scope parameter
- [ ] **Task ID Format**: Validate T- prefixed or standalone task IDs
- [ ] **Existence Checks**: Verify scope and task objects exist before processing
- [ ] **Type Validation**: Ensure force_claim is boolean, other parameters are strings
- [ ] **Length Limits**: Validate parameter lengths and content restrictions

### Error Message Quality
- [ ] **Specific Errors**: Different messages for format vs existence vs permission errors
- [ ] **Actionable Guidance**: Include suggestions for fixing parameter issues
- [ ] **Context Awareness**: Error messages reference the specific operation being attempted
- [ ] **Consistent Format**: Use consistent error message patterns across tool
- [ ] **User-Friendly Language**: Clear, non-technical language for common parameter mistakes

### Backward Compatibility
- [ ] **Legacy Behavior**: claimNextTask(projectRoot, worktree) works unchanged
- [ ] **No Regressions**: Existing calling patterns continue working
- [ ] **Default Values**: Appropriate defaults for new optional parameters
- [ ] **API Stability**: Tool interface remains stable for existing users
- [ ] **Migration Path**: Clear upgrade path for users wanting new functionality

## Implementation Guidance

### Technical Approach
1. **Parameter Validation Pipeline**: Create validation pipeline that checks parameters before processing
2. **Error Aggregation**: Collect and return all validation errors in single response
3. **Validation Utilities**: Reusable validation functions for scope and task ID checking
4. **Testing Framework**: Comprehensive parameter validation test suite

### Code Organization
- `src/trellis_mcp/models/claiming_params.py`: New model for claiming parameter validation
- `src/trellis_mcp/validators/parameter_validator.py`: Parameter combination validation logic
- `src/trellis_mcp/tools/claim_next_task.py`: Integrate validation into tool interface
- `src/trellis_mcp/exceptions/claiming_errors.py`: Specific error classes for claiming operations

### Validation Logic Structure
```python
class ClaimingParams(BaseModel):
    project_root: str
    scope: Optional[str] = None
    task_id: Optional[str] = None
    force_claim: Optional[bool] = False
    worktree: Optional[str] = ""
    
    def validate_parameter_combinations(self):
        # Mutual exclusivity checks
        # Force claim scope validation
        # Parameter format validation
        # Existence checks
```

### Error Classification System
```python
class ParameterValidationError(ValidationError):
    MUTUAL_EXCLUSIVITY = "Cannot specify both scope and task_id"
    INVALID_FORCE_CLAIM_SCOPE = "force_claim only valid with task_id"
    INVALID_SCOPE_FORMAT = "Scope must use P-, E-, or F- prefix"
    SCOPE_NOT_FOUND = "Specified scope object not found"
    TASK_NOT_FOUND = "Specified task not found"
```

## Testing Requirements

### Parameter Validation Testing
- Test all valid parameter combinations
- Test all invalid parameter combinations with expected errors
- Test boundary conditions and edge cases
- Test parameter format validation

### Backward Compatibility Testing
- Verify existing claimNextTask calls continue working
- Test that no regressions introduced to current behavior
- Validate that default parameter values work correctly
- Test migration scenarios from old to new parameter patterns

### Integration Testing
- Test parameter validation with actual claiming operations
- Verify error handling propagates correctly through tool interface
- Test validation performance with various parameter combinations
- Validate cross-system parameter validation works correctly

## Security Considerations

### Input Validation
- Strict parameter format validation prevents injection attacks
- Validate all user inputs before processing or file operations
- Sanitize parameters to prevent path traversal attacks
- Implement rate limiting for parameter validation requests

### Access Control
- Parameter validation respects project root boundaries
- Scope and task ID validation prevents unauthorized access
- Force claim operations maintain security constraints
- No privilege escalation through parameter manipulation

## Dependencies
- Requires Scope-Based Task Filtering feature for scope parameter validation
- Requires Direct Task Claiming feature for task_id parameter validation
- Uses existing validation infrastructure and error handling patterns
- Integrates with tool interface simplification patterns

### Log

