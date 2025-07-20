---
kind: task
id: T-implement-status-override
title: Implement status override capabilities for all task statuses
status: open
priority: high
prerequisites:
- T-add-force-claim-parameter-to
created: '2025-07-20T18:00:14.767590'
updated: '2025-07-20T18:00:14.767590'
schema_version: '1.1'
parent: F-force-claim-override
---
# Implement status override capabilities for all task statuses

## Context
Force claiming should allow claiming tasks with any status (in-progress, review, done, open) rather than just open tasks. This enables reassignment, priority changes, and task reopening workflows while maintaining atomic status transitions.

## Implementation Requirements

### Status Validation Override
- Modify status validation in `claim_specific_task()` to allow any status when force_claim=True
- Remove `StatusEnum.OPEN` restriction when force_claim=True
- Maintain existing status validation for normal claiming (force_claim=False)
- Implement proper error handling for invalid task states

### Atomic Status Transitions
- Ensure all status transitions complete atomically using existing `write_object()` infrastructure
- Handle concurrent access scenarios during status override operations
- Provide rollback capability if status transitions fail
- Maintain timestamp consistency during status updates

### Status Override Logging
- Log the original status being overridden during force claim operations
- Record the new status being applied (always 'in-progress')
- Include worktree assignment context in status override logs
- Provide clear audit trail for all status override operations

## Detailed Acceptance Criteria
- [ ] Tasks with status 'open' can be force claimed (existing behavior preserved)
- [ ] Tasks with status 'in-progress' can be force claimed (reassignment scenario)
- [ ] Tasks with status 'review' can be force claimed (priority change scenario)  
- [ ] Tasks with status 'done' can be force claimed (reopening scenario)
- [ ] Normal claiming still requires status 'open' when force_claim=False
- [ ] All status transitions complete atomically using write_object()
- [ ] Status override operations logged with original and new status
- [ ] Worktree assignment properly handled during status override
- [ ] Unit tests verify force claiming works for all task statuses
- [ ] Unit tests verify normal claiming behavior unchanged for status validation
- [ ] Unit tests verify atomic status transitions and error handling

## Technical Approach
1. Modify status validation logic in claim_specific_task() function
2. Add conditional status check that bypasses OPEN requirement when force_claim=True
3. Implement status override logging with original status context
4. Add comprehensive error handling for concurrent access scenarios
5. Write unit tests covering all status override scenarios

## Files to Modify
- `src/trellis_mcp/claim_next_task.py`: Modify status validation and add logging
- `tests/test_claim_next_task.py`: Add unit tests for status override functionality

## Dependencies
- Requires T-add-force-claim-parameter-to for force_claim parameter availability

## Security Considerations
- Atomic operations prevent partial state corruption during status override
- Audit logging provides complete status change history for compliance
- Access control maintained through existing project boundary validation

### Log

