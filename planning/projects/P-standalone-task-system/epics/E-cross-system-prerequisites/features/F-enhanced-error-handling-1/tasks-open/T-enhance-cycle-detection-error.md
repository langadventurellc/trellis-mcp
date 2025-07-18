---
kind: task
id: T-enhance-cycle-detection-error
title: Enhance cycle detection error messages
status: open
priority: high
prerequisites: []
created: '2025-07-18T17:33:23.587431'
updated: '2025-07-18T17:33:23.587431'
schema_version: '1.1'
parent: F-enhanced-error-handling-1
---
### Implementation Requirements
Enhance `CircularDependencyError` in cycle detection to provide clear context about which task systems are involved in dependency cycles, making errors more actionable for users.

### Technical Approach
- Modify `src/trellis_mcp/validation/cycle_detection.py`
- Update `detect_cycle_dfs()` to track task types in cycle paths
- Enhance `CircularDependencyError` to include system boundary information
- Use existing task type detection patterns from codebase

### Acceptance Criteria
- Error messages clearly indicate "standalone" vs "hierarchical" tasks in cycles
- Cycle path shows task types: "T-task1 (standalone) → F-feature1 (hierarchical) → T-task2 (standalone)"
- Maintains existing performance characteristics
- Backward compatible with existing error handling

### Implementation Details
```python
# Enhanced error message format:
"Circular dependency detected: T-auth-setup (standalone) → F-user-login (hierarchical) → T-auth-setup (standalone)"
```

### Testing Requirements
- Unit tests for cycle detection with mixed task types
- Error message format validation tests
- Performance regression tests
- Integration tests with existing cycle detection flow

### Security Considerations
- Ensure cycle path doesn't expose sensitive file paths
- Validate that enhanced context doesn't leak internal structure
- Maintain existing path sanitization patterns

### Log

