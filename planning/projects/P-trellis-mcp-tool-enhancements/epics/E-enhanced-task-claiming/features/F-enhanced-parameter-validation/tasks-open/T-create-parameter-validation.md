---
kind: task
id: T-create-parameter-validation
title: Create parameter validation error classes
status: open
priority: high
prerequisites: []
created: '2025-07-20T19:12:58.947562'
updated: '2025-07-20T19:12:58.947562'
schema_version: '1.1'
parent: F-enhanced-parameter-validation
---
## Create Parameter Validation Error Classes

Implement specific error classes for claiming parameter validation to provide clear, actionable error messages for different validation failure scenarios.

### Detailed Context
- **Location**: Create `src/trellis_mcp/exceptions/claiming_errors.py`
- **Pattern**: Follow existing error class patterns in `src/trellis_mcp/exceptions/validation_error.py`
- **Integration**: Work with ClaimingParams model for consistent error reporting

### Specific Implementation Requirements

**Error Class Structure:**
```python
class ParameterValidationError(ValidationError):
    """Specific error for parameter validation failures in claiming operations."""
    
class MutualExclusivityError(ParameterValidationError):
    """Error when mutually exclusive parameters are both specified."""
    
class InvalidParameterCombinationError(ParameterValidationError):
    """Error for invalid parameter combinations."""
    
class ParameterFormatError(ParameterValidationError):
    """Error for invalid parameter format or value."""
```

**Error Message Constants:**
- Define standardized error messages for each validation scenario
- Include parameter names and suggested fixes in messages
- Support dynamic message formatting with parameter values

### Technical Approach

**Error Classification System:**
1. **MUTUAL_EXCLUSIVITY**: scope and task_id both provided
2. **INVALID_FORCE_CLAIM_SCOPE**: force_claim=True without task_id
3. **INVALID_SCOPE_FORMAT**: scope doesn't match P-, E-, F- pattern
4. **INVALID_TASK_ID_FORMAT**: task_id doesn't match expected patterns
5. **MISSING_REQUIRED_PARAMETER**: project_root is empty/None

**Integration with ValidationError:**
- Extend existing ValidationError infrastructure
- Use consistent error_codes enumeration
- Maintain backward compatibility with existing error handling

### Detailed Acceptance Criteria

**Error Class Functionality:**
- [ ] **Inheritance**: All classes properly inherit from appropriate base classes
- [ ] **Message Formatting**: Support dynamic message formatting with parameter values
- [ ] **Error Codes**: Include appropriate ValidationErrorCode values
- [ ] **Context Information**: Capture relevant parameter values and names

**Error Message Quality:**
- [ ] **Clear Language**: Use non-technical language accessible to users
- [ ] **Specific Guidance**: Include specific suggestions for fixing each error type
- [ ] **Parameter Context**: Show which parameters caused the conflict
- [ ] **Format Examples**: Include examples of correct parameter formats where applicable

**Integration Requirements:**
- [ ] **ValidationError Compatibility**: Work seamlessly with existing error handling
- [ ] **Error Code Consistency**: Use existing ValidationErrorCode enumeration
- [ ] **Exception Hierarchy**: Maintain proper exception inheritance chain

### Unit Testing Requirements

**Include comprehensive unit tests in the same implementation:**
- Test error class instantiation with various parameter combinations
- Test error message formatting with different parameter values
- Test integration with ValidationError infrastructure
- Test error code assignment and context capture
- Test inheritance chain and exception handling

### Dependencies on Other Tasks
- None - this provides foundation for parameter validation

### Security Considerations
- Sanitize parameter values in error messages to prevent information leakage
- Avoid exposing sensitive information in error messages
- Validate parameter values before including in error context

### Log

