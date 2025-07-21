---
kind: task
id: T-create-claimingparams-model-with
parent: F-enhanced-parameter-validation
status: done
title: Create ClaimingParams model with parameter validation
priority: high
prerequisites: []
created: '2025-07-20T19:12:40.313280'
updated: '2025-07-20T19:20:00.697286'
schema_version: '1.1'
worktree: null
---
## Create ClaimingParams Model with Parameter Validation

Create a new Pydantic model specifically for claimNextTask parameter validation, implementing mutual exclusivity rules and parameter combination logic.

### Detailed Context
- **Location**: Create `src/trellis_mcp/models/claiming_params.py`
- **Pattern**: Follow existing `FilterParams` model structure in `src/trellis_mcp/models/filter_params.py:17-95`
- **Dependencies**: Use existing validation infrastructure from `TrellisBaseModel` and validation patterns

### Specific Implementation Requirements

**ClaimingParams Model Structure:**
```python
class ClaimingParams(TrellisBaseModel):
    project_root: str
    worktree: str = ""
    scope: str | None = None
    task_id: str | None = None
    force_claim: bool = False
```

**Parameter Validation Rules:**
1. **Mutual Exclusivity**: `scope` and `task_id` cannot both be specified
2. **Force Claim Scope**: `force_claim=True` only valid when `task_id` is specified
3. **Required Fields**: `project_root` must be non-empty string
4. **Format Validation**: `scope` must follow P-, E-, F- prefix pattern (reuse FilterParams validation)
5. **Task ID Validation**: `task_id` must follow T- prefix or standalone format

### Technical Approach

**Use Pydantic Validators:**
- `@model_validator(mode='after')` for cross-parameter validation
- `@field_validator` for individual field format validation
- Reuse existing scope validation logic from FilterParams

**Error Handling:**
- Use consistent ValidationError patterns from existing codebase
- Provide specific error messages for each parameter combination rule
- Include context information for debugging

### Detailed Acceptance Criteria

**Parameter Combination Validation:**
- [ ] **Mutual Exclusivity Check**: Raises ValueError when both `scope` and `task_id` provided
- [ ] **Force Claim Validation**: Raises ValueError when `force_claim=True` but `task_id` is None/empty
- [ ] **Valid Combinations**: Accepts `(scope + worktree)`, `(task_id + force_claim + worktree)`, `(project_root only)`
- [ ] **Project Root Required**: Raises ValueError for empty/None project_root

**Format Validation:**
- [ ] **Scope Format**: Validates P-, E-, F- prefix pattern using existing FilterParams logic
- [ ] **Task ID Format**: Validates T- prefix or standalone task ID patterns
- [ ] **Boolean Validation**: Ensures force_claim is proper boolean type
- [ ] **String Validation**: Validates string parameters are proper types

**Error Message Quality:**
- [ ] **Specific Messages**: Different error messages for each validation rule violation
- [ ] **Actionable Guidance**: Error messages include suggestions for fixing parameter issues
- [ ] **Context Information**: Include field names and values in error context

### Unit Testing Requirements

**Include comprehensive unit tests in the same implementation:**
- Test all valid parameter combinations
- Test all invalid parameter combinations with expected errors
- Test edge cases (empty strings, None values, whitespace)
- Test format validation for scope and task_id parameters
- Test error message content and structure

### Dependencies on Other Tasks
- None - this is a foundational model

### Security Considerations
- Validate all input parameters to prevent injection attacks
- Sanitize string inputs before processing
- No privilege escalation through parameter manipulation

### Log


**2025-07-21T00:27:26.712558Z** - Implemented ClaimingParams model with comprehensive parameter validation for claimNextTask operations. The model enforces mutual exclusivity rules between scope and task_id parameters, validates force_claim usage, and implements format validation using existing system patterns. Includes comprehensive test coverage with 37 test cases covering all parameter combinations, edge cases, and error scenarios. All quality checks pass (lint, format, typecheck, tests).
- filesChanged: ["src/trellis_mcp/models/claiming_params.py", "tests/unit/test_claiming_params.py"]