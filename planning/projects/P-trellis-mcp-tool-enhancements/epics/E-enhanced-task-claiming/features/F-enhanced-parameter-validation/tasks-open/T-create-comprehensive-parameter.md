---
kind: task
id: T-create-comprehensive-parameter
title: Create comprehensive parameter validation tests
status: open
priority: normal
prerequisites:
- T-integrate-claimingparams
created: '2025-07-20T19:13:45.240208'
updated: '2025-07-20T19:13:45.240208'
schema_version: '1.1'
parent: F-enhanced-parameter-validation
---
## Create Comprehensive Parameter Validation Tests

Develop extensive integration tests for the enhanced parameter validation system to ensure all parameter combinations, error scenarios, and backward compatibility requirements are thoroughly validated.

### Detailed Context
- **Location**: Create `tests/integration/test_parameter_validation.py`
- **Pattern**: Follow existing integration test patterns in `tests/integration/test_force_claim.py`
- **Coverage**: Test all parameter combination rules and validation scenarios
- **Integration**: Test full tool integration with ClaimingParams model

### Specific Implementation Requirements

**Test Coverage Areas:**
1. **Valid Parameter Combinations**: All legitimate parameter combinations work correctly
2. **Invalid Parameter Combinations**: All invalid combinations produce appropriate errors
3. **Backward Compatibility**: Existing calling patterns continue working
4. **Error Message Quality**: Error messages are clear and actionable
5. **Edge Cases**: Boundary conditions and unusual input scenarios

**Test Structure:**
```python
class TestParameterValidation:
    def test_valid_parameter_combinations(self):
        # Test all valid combinations
        
    def test_mutual_exclusivity_errors(self):
        # Test scope + task_id conflicts
        
    def test_force_claim_validation(self):
        # Test force_claim parameter restrictions
        
    def test_format_validation(self):
        # Test scope and task_id format validation
        
    def test_backward_compatibility(self):
        # Test existing calling patterns
```

### Technical Approach

**Integration Test Strategy:**
- Use real planning structure with test data
- Test actual tool invocation through MCP interface
- Validate error responses and success scenarios
- Test parameter validation before task claiming logic

**Test Data Setup:**
- Create minimal planning structure for testing
- Set up test tasks, features, epics for validation scenarios
- Use temporary directories for test isolation
- Clean up test data after each test

**Error Validation:**
- Assert specific error types and messages
- Validate error context and parameter information
- Test error message clarity and actionability
- Ensure consistent error handling patterns

### Detailed Acceptance Criteria

**Valid Parameter Combination Tests:**
- [ ] **Project Root Only**: `claimNextTask(projectRoot="path")` works correctly
- [ ] **With Worktree**: `claimNextTask(projectRoot="path", worktree="branch")` works
- [ ] **With Scope**: `claimNextTask(projectRoot="path", scope="P-project")` works
- [ ] **Scope + Worktree**: `claimNextTask(projectRoot="path", scope="F-feature", worktree="branch")` works
- [ ] **Task ID Only**: `claimNextTask(projectRoot="path", taskId="T-task")` works
- [ ] **Task ID + Force**: `claimNextTask(projectRoot="path", taskId="T-task", force_claim=True)` works
- [ ] **Task ID + Worktree**: `claimNextTask(projectRoot="path", taskId="T-task", worktree="branch")` works

**Invalid Parameter Combination Tests:**
- [ ] **Mutual Exclusivity**: `scope="P-proj" + taskId="T-task"` raises appropriate error
- [ ] **Force Claim Without Task**: `force_claim=True` without `taskId` raises error
- [ ] **Force Claim With Scope**: `force_claim=True + scope="P-proj"` raises error
- [ ] **Empty Project Root**: `projectRoot=""` raises appropriate error
- [ ] **Invalid Scope Format**: `scope="invalid-format"` raises format error
- [ ] **Invalid Task ID Format**: `taskId="invalid-format"` raises format error

**Error Message Quality Tests:**
- [ ] **Specific Messages**: Each error type has distinct, clear message
- [ ] **Parameter Context**: Error messages include relevant parameter names and values
- [ ] **Actionable Guidance**: Error messages suggest how to fix the parameter issue
- [ ] **Consistent Format**: All parameter validation errors follow consistent format

**Backward Compatibility Tests:**
- [ ] **Legacy Calls**: All existing claimNextTask usage patterns work unchanged
- [ ] **Return Format**: Tool returns same data structure as before
- [ ] **No Regressions**: No existing functionality broken by parameter validation
- [ ] **Performance**: Parameter validation doesn't significantly impact performance

**Edge Case Tests:**
- [ ] **Whitespace Handling**: Parameters with whitespace handled correctly
- [ ] **None Values**: None values for optional parameters work correctly
- [ ] **Empty Strings**: Empty strings vs None handled consistently
- [ ] **Case Sensitivity**: Parameter validation handles case appropriately

### Integration Testing Requirements

**Test all scenarios with real tool invocation:**
- Test through actual MCP tool interface
- Use real planning directory structure
- Validate complete request/response cycle
- Test error propagation through tool interface

**Test Environment Setup:**
- Create isolated test planning structure
- Set up test data with various object types
- Use temporary directories for test isolation
- Ensure tests don't interfere with each other

### Dependencies on Other Tasks
- **T-integrate-claimingparams**: Requires ClaimingParams integration in tool

### Security Considerations
- Test parameter validation prevents injection attacks
- Validate input sanitization in error scenarios
- Test that validation doesn't expose sensitive information
- Ensure no privilege escalation through parameter manipulation

### Log

