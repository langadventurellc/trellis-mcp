---
kind: task
id: T-update-path-to-id-for-standalone
parent: F-standalone-task-path-resolution
status: done
title: Update path_to_id for standalone task paths
priority: normal
prerequisites:
- T-update-id-to-path-for-standalone
created: '2025-07-18T13:52:46.739437'
updated: '2025-07-18T14:45:56.355164'
schema_version: '1.1'
worktree: null
---
### Implementation Requirements
Modify the `path_to_id` function to correctly parse standalone task paths from the `planning/tasks/` directory structure.

### Technical Approach
- Extend the existing `path_to_id` function (lines 293-381)
- Add recognition for standalone task paths in format: planning/tasks/T-{id}.md or planning/tasks/{timestamp}-T-{id}.md
- Support both `tasks-open` and `tasks-done` subdirectory patterns
- Maintain existing task path recognition for hierarchy-based tasks

### Acceptance Criteria
- Recognize standalone task paths in `planning/tasks/tasks-open/T-{id}.md` format
- Recognize standalone task paths in `planning/tasks/tasks-done/{timestamp}-T-{id}.md` format
- Return correct (kind='task', id) tuple for standalone tasks
- Maintain existing behavior for hierarchy-based task paths
- Handle edge cases and malformed paths gracefully

### Dependencies
- T-update-id-to-path-for-standalone: Need to understand the path structures being created

### Security Considerations
- Validate path components to prevent injection attacks
- Ensure proper handling of symbolic links and special files
- Validate task ID extraction from filenames

### Testing Requirements
- Test standalone task path recognition for tasks-open
- Test standalone task path recognition for tasks-done
- Test hierarchy-based task path recognition (unchanged)
- Test error handling for malformed paths
- Test edge cases with unusual filename formats

### Implementation Details
- Add path pattern matching for standalone tasks
- Modify the filename parsing logic to handle both path types
- Use consistent error handling patterns
- Add appropriate comments and documentation for the new logic

### Log


**2025-07-18T19:50:22.020528Z** - Updated path_to_id function to correctly handle standalone task paths by adding security validation for task IDs and comprehensive documentation. The function now recognizes both standalone tasks (planning/tasks-open/T-{id}.md and planning/tasks-done/{timestamp}-T-{id}.md) and hierarchy-based tasks, validating task IDs to prevent path traversal attacks. All existing tests continue to pass.
- filesChanged: ["src/trellis_mcp/path_resolver.py"]