---
kind: feature
id: F-scope-based-task-filtering
title: Scope-Based Task Filtering
status: done
priority: high
prerequisites: []
created: '2025-07-20T13:10:36.133254'
updated: '2025-07-20T20:02:45.862136+00:00'
schema_version: '1.1'
parent: E-enhanced-task-claiming
---
# Scope-Based Task Filtering Feature

## Purpose and Functionality

Enhance the `claimNextTask` tool with a `scope` parameter that limits task claiming to specific hierarchical boundaries (Project, Epic, or Feature). This enables developers to focus their work within designated project areas while maintaining the existing priority-based claiming logic.

## Key Components to Implement

### 1. Scope Parameter Validation
- Accept P-, E-, F- prefixed scope IDs in claimNextTask requests
- Validate scope ID format and existence using kind inference engine
- Return specific error messages for invalid scope parameters
- Integration with existing parameter validation framework

### 2. Hierarchical Task Filtering Logic
- Filter task discovery to only include tasks within scope boundaries
- Support cross-system compatibility (hierarchical tasks only, standalone tasks unaffected)
- Maintain existing priority sorting within filtered scope
- Preserve current claiming behavior when no scope specified

### 3. Scope Boundary Resolution
- Project scope (P-*): Include all tasks within project hierarchy
- Epic scope (E-*): Include all tasks within epic and its features
- Feature scope (F-*): Include only tasks directly within the feature
- Validate scope object exists before filtering tasks

## Detailed Acceptance Criteria

### Scope Parameter Processing
- [ ] **Parameter Format**: Accept scope parameter with P-, E-, F- prefixed IDs
- [ ] **ID Validation**: Validate scope ID format matches hierarchical patterns
- [ ] **Existence Check**: Verify scope object exists in planning structure
- [ ] **Error Messages**: Return clear errors for invalid/non-existent scope IDs
- [ ] **Optional Parameter**: Scope parameter is optional; existing behavior when omitted

### Task Discovery and Filtering
- [ ] **Hierarchical Filtering**: Only discover tasks that are children of scope object
- [ ] **Cross-System Handling**: Standalone tasks not affected by scope filtering
- [ ] **Empty Results**: Handle cases where scope contains no eligible tasks
- [ ] **Priority Preservation**: Maintain priority-based sorting within scope boundaries

### Scope Boundary Logic
- [ ] **Project Scope**: Include all epics, features, and tasks within project
- [ ] **Epic Scope**: Include all features and tasks within epic
- [ ] **Feature Scope**: Include only direct tasks within feature
- [ ] **Validation Consistency**: Use existing kind inference for scope validation
- [ ] **Error Handling**: Specific messages for scope boundary violations

### Integration Requirements
- [ ] **Backward Compatibility**: Existing claimNextTask behavior preserved when scope omitted
- [ ] **Parameter Interaction**: Scope filtering works independently of worktree parameter
- [ ] **Tool Interface**: Consistent parameter pattern with other enhanced tools
- [ ] **Cross-System Support**: Functions correctly in mixed hierarchical/standalone environments

## Implementation Guidance

### Technical Approach
1. **Extend FilterParams Model**: Add scope parameter to existing filter validation
2. **Enhance Task Scanner**: Modify scan_tasks() to accept scope boundaries
3. **Scope Resolver**: Create utility to resolve scope boundaries to task paths
4. **Integration Pattern**: Follow listBacklog tool pattern for scope filtering

### Code Organization
- `src/trellis_mcp/tools/claim_next_task.py`: Add scope parameter to tool interface
- `src/trellis_mcp/claim_next_task.py`: Enhance core logic with scope filtering
- `src/trellis_mcp/models/filter_params.py`: Extend for scope validation
- `src/trellis_mcp/scanner.py`: Add scope-aware task discovery methods

### Error Handling Patterns
```python
# Scope validation errors
raise ValidationError(f"Invalid scope ID format: {scope}")
raise ValidationError(f"Scope object not found: {scope}")
raise ValidationError(f"No eligible tasks within scope: {scope}")
```

## Testing Requirements

### Unit Testing Focus
- Scope parameter validation with various ID formats
- Task filtering logic for different scope types
- Error handling for invalid scopes and empty results
- Integration with existing claiming workflow

### Integration Testing Scenarios
- Scope filtering in projects with mixed hierarchical/standalone tasks
- Claiming workflow with scope boundaries
- Error propagation through tool interface

## Security Considerations

### Access Control
- Scope validation prevents access to unauthorized project areas
- No additional permissions required beyond existing task claiming
- Scope boundaries enforce hierarchical access patterns

### Input Validation
- Strict scope ID format validation prevents injection attacks
- Sanitize scope parameters before file system operations
- Validate scope existence before processing claims

## Dependencies
- Requires kind inference engine from Tool Interface Simplification epic
- Uses existing scanner and filter infrastructure
- Integrates with current claiming and validation frameworks

### Log

