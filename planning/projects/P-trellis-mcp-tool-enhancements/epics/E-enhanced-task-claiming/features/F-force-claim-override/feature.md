---
kind: feature
id: F-force-claim-override
title: Force Claim Override
status: done
priority: high
prerequisites:
- F-direct-task-claiming
created: '2025-07-20T13:12:30.624894'
updated: '2025-07-20T23:47:36.709823+00:00'
schema_version: '1.1'
parent: E-enhanced-task-claiming
---
# Force Claim Override Feature

## Purpose and Functionality

Implement force claim capabilities for the `claimNextTask` tool, allowing users to bypass normal claiming restrictions when claiming specific tasks by ID. This supports emergency scenarios, task reassignment, and administrative workflows where standard claiming rules need to be overridden. Unit tests should be completed in the same task as the changes to production code. Do not create a separate task just for unit tests. Do not add any performance tests to this feature.

## Key Components to Implement

### 1. Force Claim Parameter Processing
- Add `force_claim` boolean parameter to claimNextTask tool
- Validate that force_claim only applies when task_id is specified
- Implement force claim logic that bypasses standard claiming restrictions
- Provide clear documentation of force claim behavior and use cases

### 2. Prerequisite Bypass Logic
- Skip prerequisite validation when force_claim=True
- Allow claiming tasks even when dependencies are incomplete
- Maintain data integrity while bypassing business rule validation
- Log force claim operations for audit trail

### 3. Status Override Capabilities
- Allow claiming tasks with status 'in-progress' (reassignment scenarios)
- Enable claiming tasks with status 'review' (priority changes)
- Support claiming tasks with status 'done' (reopening workflows)
- Implement atomic status transitions for all override scenarios

## Detailed Acceptance Criteria

### Force Claim Parameter Logic
- [ ] **Parameter Scope**: force_claim parameter only valid when task_id specified
- [ ] **Boolean Validation**: force_claim accepts only boolean values (default: False)
- [ ] **Mutual Exclusivity**: force_claim incompatible with scope-based claiming
- [ ] **Clear Documentation**: Usage patterns and warnings for force claim operations
- [ ] **Audit Logging**: Record all force claim operations with context

### Prerequisite Bypass Implementation
- [ ] **Complete Bypass**: Skip all prerequisite validation when force_claim=True
- [ ] **Dependency Integrity**: Maintain task dependency graph integrity
- [ ] **Warning System**: Log warnings when bypassing incomplete prerequisites
- [ ] **Data Consistency**: Ensure task state remains consistent after force claim
- [ ] **Rollback Safety**: Provide rollback capability if force claim fails

### Status Override Functionality
- [ ] **In-Progress Override**: Claim tasks currently assigned to other users/worktrees
- [ ] **Review Override**: Claim tasks in review status for priority changes
- [ ] **Done Override**: Reopen completed tasks for additional work
- [ ] **Open Override**: Standard claiming behavior for open tasks
- [ ] **Atomic Operations**: All status transitions complete atomically

### Safety and Validation
- [ ] **Task Existence**: Verify task exists before attempting force claim
- [ ] **Permission Checks**: Maintain access control even with force claim
- [ ] **State Validation**: Ensure target task state is valid for force operations
- [ ] **Conflict Prevention**: Handle concurrent force claim attempts gracefully
- [ ] **Error Recovery**: Comprehensive error handling and rollback procedures

## Implementation Guidance

### Technical Approach
1. **Parameter Processing**: Extend claiming parameter validation for force_claim
2. **Override Logic**: Create bypass mechanisms for standard claiming restrictions
3. **Status Management**: Implement atomic status transition handling
4. **Audit System**: Add logging for force claim operations

### Code Organization
- `src/trellis_mcp/tools/claim_next_task.py`: Add force_claim parameter
- `src/trellis_mcp/claim_next_task.py`: Implement force claiming logic
- `src/trellis_mcp/force_claim_handler.py`: Dedicated force claim processing
- `src/trellis_mcp/audit/claiming_logger.py`: Force claim operation logging

### Force Claim Logic Flow
```python
def force_claim_task(project_root: str, task_id: str, worktree: str = ""):
    # 1. Validate task exists and is accessible
    task_path = resolve_task_by_id(project_root, task_id)
    task_data = load_task(task_path)
    
    # 2. Log force claim operation
    log_force_claim_attempt(task_id, worktree)
    
    # 3. Override status validation
    if task_data.status in ['in-progress', 'review', 'done']:
        log_status_override(task_id, task_data.status)
    
    # 4. Skip prerequisite validation
    # (Normal claiming would check prerequisites here)
    
    # 5. Atomically claim task
    force_update_task_status(task_path, 'in-progress', worktree)
    
    return build_response(task_data, task_path)
```

### Status Override Handling
```python
class ForceClaimHandler:
    def handle_status_override(self, task_data, new_status, worktree):
        old_status = task_data.status
        
        # Log the override operation
        self.audit_logger.log_status_override(
            task_id=task_data.id,
            old_status=old_status,
            new_status=new_status,
            worktree=worktree
        )
        
        # Perform atomic status update
        return self.atomic_status_update(task_data, new_status, worktree)
```

## Testing Requirements

### Force Claim Logic Testing
- Test force claiming with all possible task statuses
- Verify prerequisite bypass functionality
- Test concurrent force claim attempts
- Validate atomic operations and rollback scenarios

### Status Override Testing
- Test claiming in-progress tasks (reassignment)
- Test claiming review tasks (priority changes)
- Test claiming done tasks (reopening)
- Verify audit logging for all override operations

### Integration Testing
- Test force claim with parameter validation
- Test interaction with normal claiming workflows
- Verify cross-system force claiming capabilities
- Test error handling and recovery procedures

### Security Testing
- Verify access controls maintained during force operations
- Test for privilege escalation vulnerabilities
- Validate audit trail completeness and integrity
- Test rate limiting and abuse prevention

## Security Considerations

### Access Control Preservation
- Force claim maintains project root access boundaries
- No privilege escalation through force claim operations
- Audit trail provides accountability for administrative actions
- Rate limiting prevents abuse of force claim capabilities

### Data Integrity Protection
- Atomic operations ensure consistent task state
- Rollback capabilities protect against partial failures
- Audit logging provides complete operation history
- Validation maintains core data integrity constraints

### Audit and Compliance
- Complete logging of all force claim operations
- Context capture for security and compliance reviews
- User attribution for all administrative overrides
- Immutable audit trail for forensic analysis

## Dependencies
- Requires Direct Task Claiming feature for task_id-based operations
- Requires Enhanced Parameter Validation for force_claim parameter validation
- Uses existing task resolution and status update infrastructure
- Integrates with audit logging and security frameworks

### Log

