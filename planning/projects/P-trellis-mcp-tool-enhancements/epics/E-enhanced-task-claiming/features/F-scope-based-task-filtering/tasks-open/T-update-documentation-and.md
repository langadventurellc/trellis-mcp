---
kind: task
id: T-update-documentation-and
title: Update documentation and examples for scope-based task claiming
status: open
priority: low
prerequisites:
- T-add-comprehensive-integration
created: '2025-07-20T13:20:56.438377'
updated: '2025-07-20T13:20:56.438377'
schema_version: '1.1'
parent: F-scope-based-task-filtering
---
## Context

With scope-based task filtering fully implemented and tested, we need to update documentation to help users understand and effectively use the new scope parameter functionality in claimNextTask tool.

## Implementation Requirements

### Update tool documentation
- Add scope parameter documentation to claimNextTask tool docstring
- Include parameter format requirements (P-, E-, F- prefixes)
- Document scope boundary behavior for each hierarchy level
- Add usage examples for different scope scenarios

### Create usage examples
```python
# Example documentation to add:
"""
claimNextTask Tool - Enhanced with Scope Filtering

Parameters:
- projectRoot: Root directory for planning structure
- worktree: Optional worktree identifier (informational only)
- scope: Optional hierarchical scope for task filtering
  - P-<project-id>: Claim tasks within entire project
  - E-<epic-id>: Claim tasks within epic and its features  
  - F-<feature-id>: Claim tasks only within specific feature

Examples:
- claimNextTask(projectRoot="/path/to/planning")  # Claim any available task
- claimNextTask(projectRoot="/path/to/planning", scope="P-core-platform")  # Project scope
- claimNextTask(projectRoot="/path/to/planning", scope="F-user-auth")  # Feature scope
"""
```

### Error handling documentation
- Document common error scenarios and solutions
- Include troubleshooting guide for scope validation failures
- Add guidance for when scope contains no eligible tasks

### Integration examples
- Show how scope filtering works with existing prerequisite validation
- Demonstrate priority preservation within scope boundaries
- Include examples of cross-system compatibility scenarios

### Performance considerations
- Document performance characteristics of scope filtering
- Provide guidance on when to use scope filtering vs. full task scanning
- Include best practices for large project hierarchies

## Acceptance Criteria

- [ ] claimNextTask tool docstring updated with scope parameter documentation
- [ ] Usage examples provided for all scope types (P-, E-, F-)
- [ ] Error scenarios documented with troubleshooting guidance
- [ ] Integration examples show scope filtering with prerequisites
- [ ] Performance considerations and best practices documented
- [ ] Documentation follows existing project documentation standards

## Testing Requirements

- Verify documentation examples are accurate and functional
- Test all documented usage patterns work as described
- Validate error scenarios match documented behavior

## Dependencies

- Requires T-add-comprehensive-integration for complete implementation validation
- All previous tasks must be complete for accurate documentation

## Files to Modify

- `src/trellis_mcp/tools/claim_next_task.py`: Update tool docstring and examples
- `docs/` (if exists): Add scope filtering documentation to relevant guides
- `README.md` (if exists): Update with new scope filtering capabilities

### Log

