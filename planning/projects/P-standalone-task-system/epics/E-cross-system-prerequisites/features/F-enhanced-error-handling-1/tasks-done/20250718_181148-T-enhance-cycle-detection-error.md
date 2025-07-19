---
kind: task
id: T-enhance-cycle-detection-error
parent: F-enhanced-error-handling-1
status: done
title: Enhance cycle detection error messages
priority: high
prerequisites: []
created: '2025-07-18T17:33:23.587431'
updated: '2025-07-18T18:04:26.233217'
schema_version: '1.1'
worktree: null
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


**2025-07-18T23:11:48.831023Z** - Enhanced CircularDependencyError to provide clear context about task systems involved in dependency cycles. Added object type detection to show "standalone" vs "hierarchical" tasks and object kinds (project, epic, feature) in cycle paths. Error messages now display: "T-task1 (standalone) → F-feature1 (hierarchical) → T-task2 (standalone)" format with enhanced arrows. Maintains full backward compatibility with existing error handling. Added comprehensive test coverage for mixed task types and objects. All existing functionality preserved while providing more actionable error context for users.
- filesChanged: ["src/trellis_mcp/validation/exceptions.py", "src/trellis_mcp/validation/cycle_detection.py", "tests/unit/test_validation.py", "tests/unit/test_validation_failures.py"]