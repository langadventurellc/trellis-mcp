---
kind: task
id: T-add-force-claim-parameter-to
parent: F-force-claim-override
status: done
title: Add force_claim parameter to claimNextTask tool interface
priority: high
prerequisites: []
created: '2025-07-20T17:59:42.898885'
updated: '2025-07-20T18:02:35.709763'
schema_version: '1.1'
worktree: null
---
# Add force_claim parameter to claimNextTask tool interface

## Context
The claimNextTask tool needs to support a force_claim parameter that bypasses normal claiming restrictions when claiming specific tasks by ID. This parameter should only work with task_id-based claiming and requires proper validation.

## Implementation Requirements

### Parameter Addition
- Add `force_claim: bool = False` parameter to ClaimTaskParams model in `src/trellis_mcp/tools/claim_next_task.py`
- Ensure parameter is properly documented with clear usage guidelines
- Add parameter validation that force_claim only works when task_id is specified

### Validation Logic
- Implement mutual exclusivity: force_claim incompatible with scope-based claiming
- Add validation that force_claim requires task_id parameter to be provided
- Ensure force_claim defaults to False for backward compatibility

### Tool Interface Updates
- Update tool function signature to accept force_claim parameter
- Pass force_claim parameter to core claiming function
- Update tool documentation with force_claim usage examples and warnings

## Detailed Acceptance Criteria
- [ ] force_claim parameter added to ClaimTaskParams model with proper type annotation
- [ ] Parameter validation prevents force_claim=True when task_id is empty/None
- [ ] Parameter validation prevents force_claim=True when scope parameter is used
- [ ] force_claim parameter properly passed from tool interface to core claiming logic
- [ ] Tool documentation updated with force_claim usage patterns and warnings
- [ ] Unit tests verify parameter validation rules and error cases
- [ ] Unit tests verify force_claim parameter is properly passed through to core logic

## Technical Approach
1. Update ClaimTaskParams Pydantic model in tool interface
2. Add @model_validator to enforce force_claim + task_id requirement
3. Add mutual exclusivity validation for force_claim + scope parameters
4. Update claimNextTask function to pass force_claim to core logic
5. Write comprehensive unit tests for parameter validation

## Files to Modify
- `src/trellis_mcp/tools/claim_next_task.py`: Add parameter and validation
- `tests/tools/test_claim_next_task.py`: Add unit tests for parameter validation

## Dependencies
- None (foundational change for other force claim tasks)

## Security Considerations
- Parameter validation prevents misuse of force claim functionality
- Access control boundaries maintained through existing projectRoot validation
- Force claim operations will be audited by subsequent tasks

### Log


**2025-07-20T23:07:22.740958Z** - Successfully implemented force_claim parameter for claimNextTask tool interface with comprehensive validation and testing. Added force_claim: bool = False parameter with robust validation logic requiring taskId when True and preventing use with scope parameter. Implemented 7 comprehensive unit tests covering all validation scenarios including edge cases, error contexts, and parameter passing. Updated tool documentation with clear usage examples and warnings. All quality checks pass (isort, black, flake8, pyright) with no regressions in existing functionality. This foundational interface change enables subsequent tasks to implement core force claiming logic while maintaining security boundaries and backward compatibility.
- filesChanged: ["src/trellis_mcp/tools/claim_next_task.py", "tests/unit/tools/test_claim_next_task.py"]