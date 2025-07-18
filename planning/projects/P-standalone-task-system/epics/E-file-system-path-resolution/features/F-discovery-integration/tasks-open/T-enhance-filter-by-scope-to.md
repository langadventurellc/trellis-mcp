---
kind: task
id: T-enhance-filter-by-scope-to
title: Enhance filter_by_scope to support standalone tasks
status: open
priority: high
prerequisites: []
created: '2025-07-18T16:13:54.757929'
updated: '2025-07-18T16:13:54.757929'
schema_version: '1.1'
parent: F-discovery-integration
---
### Purpose
Enhance the `filter_by_scope()` function to properly handle standalone tasks when scope filtering is applied, ensuring comprehensive task filtering across both storage patterns.

### Current Issue
The `filter_by_scope()` function in `src/trellis_mcp/filters.py` only searches hierarchical tasks within the specified project/epic/feature scope, completely ignoring standalone tasks that could be relevant to the scope.

### Technical Requirements
- Update `filter_by_scope()` to include standalone tasks when appropriate
- Define clear scope matching logic for standalone tasks
- Maintain existing hierarchical task filtering behavior
- Preserve performance with efficient standalone task scanning

### Implementation Approach
1. Analyze the provided scope parameter (project, epic, or feature ID)
2. For project-level scope: include all standalone tasks as "global scope" items
3. For epic/feature-level scope: include standalone tasks that match specific criteria
4. Use existing scanner utilities for consistency
5. Apply same task model filtering logic to both task types

### Scope Matching Logic
- **Project scope (P-*)**: Include all standalone tasks (they belong to the project globally)
- **Epic scope (E-*)**: Include standalone tasks that reference the epic in metadata
- **Feature scope (F-*)**: Include standalone tasks that reference the feature in metadata

### Acceptance Criteria
- Standalone tasks appear in scope-filtered results when appropriate
- Existing hierarchical task filtering continues to work unchanged
- Project-level scope filtering includes all standalone tasks
- Epic/feature-level scope filtering includes relevant standalone tasks
- Performance remains acceptable with mixed task filtering

### Testing Requirements
- Add unit tests for standalone task scope filtering
- Add integration tests with mixed task environments and various scope types
- Test edge cases with no standalone tasks matching scope
- Verify filtering performance with large numbers of standalone tasks

### Security Considerations
- Apply same access controls to standalone task filtering
- Ensure proper validation of scope parameters
- Maintain consistent security checks across task types

### Performance Requirements
- Scope filtering should complete in < 100ms for typical project sizes
- No significant performance degradation with standalone task inclusion
- Memory usage should remain efficient with proper task yielding

### Files to Modify
- `src/trellis_mcp/filters.py` - Enhance `filter_by_scope()` with standalone task support
- `tests/test_filters.py` - Add comprehensive test coverage for scope filtering

### Log

