---
kind: task
id: T-integrate-claimingparams
title: Integrate ClaimingParams validation into claimNextTask tool
status: open
priority: high
prerequisites:
- T-create-claimingparams-model-with
- T-create-parameter-validation
created: '2025-07-20T19:13:21.180705'
updated: '2025-07-20T19:13:21.180705'
schema_version: '1.1'
parent: F-enhanced-parameter-validation
---
## Integrate ClaimingParams Validation into claimNextTask Tool

Replace the current inline parameter validation in claimNextTask tool with ClaimingParams model validation, providing comprehensive parameter validation and improved error messages.

### Detailed Context
- **Location**: Modify `src/trellis_mcp/tools/claim_next_task.py:161-203`
- **Current Pattern**: Inline validation with individual parameter checks
- **New Pattern**: Use ClaimingParams model for comprehensive validation before processing
- **Integration**: Replace existing validation logic while maintaining backward compatibility

### Specific Implementation Requirements

**Replace Existing Validation Logic:**
```python
# Replace lines 161-203 with ClaimingParams usage
try:
    claiming_params = ClaimingParams(
        project_root=projectRoot,
        worktree=worktree,
        scope=scope,
        task_id=taskId,
        force_claim=force_claim
    )
except Exception as e:
    # Convert to appropriate ValidationError
    raise ValidationError(...)
```

**Parameter Processing:**
- Use validated parameters from ClaimingParams instance
- Maintain existing behavior for backward compatibility
- Pass validated parameters to core claim_next_task function

### Technical Approach

**Validation Pipeline:**
1. Create ClaimingParams instance with all tool parameters
2. Let Pydantic handle parameter validation and cross-validation
3. Extract validated parameters for use in core claiming logic
4. Convert any validation errors to appropriate ValidationError format

**Error Handling Integration:**
- Catch Pydantic validation errors and convert to ValidationError
- Use new claiming error classes for specific error types
- Maintain existing error context and error code patterns
- Preserve backward compatibility with error handling

**Backward Compatibility:**
- Ensure existing tool signature remains unchanged
- Maintain same return value format and structure
- Preserve existing parameter behavior when no validation errors occur

### Detailed Acceptance Criteria

**Parameter Validation Integration:**
- [ ] **ClaimingParams Usage**: Tool uses ClaimingParams for all parameter validation
- [ ] **Error Conversion**: Pydantic validation errors properly converted to ValidationError
- [ ] **Parameter Extraction**: Validated parameters correctly extracted and used
- [ ] **Core Function Integration**: Validated parameters passed to claim_next_task function

**Backward Compatibility:**
- [ ] **Tool Signature**: claimNextTask tool signature remains unchanged
- [ ] **Return Format**: Tool return value format and structure preserved
- [ ] **Existing Behavior**: All existing valid parameter combinations continue working
- [ ] **Error Handling**: Error handling patterns remain consistent with existing code

**Error Message Improvement:**
- [ ] **Better Messages**: Parameter validation errors provide clearer, more actionable messages
- [ ] **Specific Errors**: Different error types for different validation failures
- [ ] **Context Preservation**: Error context includes relevant parameter information
- [ ] **User Guidance**: Error messages include suggestions for fixing parameter issues

**Performance Requirements:**
- [ ] **No Regression**: Parameter validation doesn't significantly impact performance
- [ ] **Efficient Validation**: ClaimingParams validation executes quickly
- [ ] **Memory Usage**: No significant increase in memory usage during validation

### Unit Testing Requirements

**Include comprehensive unit tests in the same implementation:**
- Test tool with all valid parameter combinations
- Test tool with all invalid parameter combinations
- Test error message quality and content
- Test backward compatibility with existing calling patterns
- Test performance impact of new validation
- Test integration with core claim_next_task function

### Dependencies on Other Tasks
- **T-create-claimingparams-model-with**: Requires ClaimingParams model implementation
- **T-create-parameter-validation**: Requires parameter validation error classes

### Security Considerations
- Parameter validation prevents malicious parameter combinations
- Input sanitization handled by ClaimingParams model
- No security regressions from validation changes
- Maintain existing security constraints and access controls

### Log

