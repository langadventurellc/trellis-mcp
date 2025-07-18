---
kind: task
id: T-fix-getnextreviewabletask-to
title: Fix getNextReviewableTask to include standalone tasks
status: open
priority: high
prerequisites: []
created: '2025-07-18T16:13:42.972770'
updated: '2025-07-18T16:13:42.972770'
schema_version: '1.1'
parent: F-discovery-integration
---
### Purpose
Fix the `getNextReviewableTask` MCP operation to include standalone tasks in review status, ensuring complete task discovery across both storage patterns.

### Current Issue
The `get_oldest_review()` function in `src/trellis_mcp/query.py` only searches hierarchical tasks in the `planning/projects/` directory structure, completely ignoring standalone tasks in `planning/tasks-open/` that have status='review'.

### Technical Requirements
- Extend `get_oldest_review()` to scan `planning/tasks-open/` directory for standalone tasks
- Combine results from both hierarchical and standalone task scans
- Maintain existing priority and timestamp ordering logic
- Preserve backward compatibility with existing behavior

### Implementation Approach
1. Add standalone task scanning after hierarchical task scanning
2. Use existing `scan_tasks()` utility for consistency
3. Filter standalone tasks by status='review' 
4. Merge results and apply existing oldest-updated timestamp logic
5. Ensure security validation applies to both task types

### Acceptance Criteria
- `getNextReviewableTask` returns standalone tasks when they are the oldest in review
- Existing hierarchical task review functionality remains unchanged
- Priority ordering works correctly across both task types
- Performance remains acceptable with mixed task scanning

### Testing Requirements
- Add unit tests for standalone task review discovery
- Add integration tests with mixed task environments
- Test edge cases with no reviewable tasks of each type
- Verify timestamp ordering across both task types

### Security Considerations
- Apply same path validation to standalone task scanning
- Ensure proper access controls for standalone tasks in review
- Validate task metadata consistency

### Performance Requirements
- Review discovery should complete in < 50ms for typical project sizes
- No significant performance degradation with standalone task inclusion
- Memory usage should remain efficient with iterator-based scanning

### Files to Modify
- `src/trellis_mcp/query.py` - Add standalone task scanning to `get_oldest_review()`
- `tests/test_query.py` - Add comprehensive test coverage

### Log

