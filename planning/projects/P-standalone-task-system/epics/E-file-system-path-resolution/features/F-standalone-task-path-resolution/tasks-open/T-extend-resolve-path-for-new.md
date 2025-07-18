---
kind: task
id: T-extend-resolve-path-for-new
title: Extend resolve_path_for_new_object for standalone tasks
status: open
priority: normal
prerequisites:
- T-add-standalone-task-detection
created: '2025-07-18T13:52:36.008199'
updated: '2025-07-18T13:52:36.008199'
schema_version: '1.1'
parent: F-standalone-task-path-resolution
---
### Implementation Requirements
Verify and enhance the existing standalone task logic in `resolve_path_for_new_object` function to ensure complete coverage of standalone task path construction.

### Technical Approach
- Review the existing standalone task implementation (lines 236-251)
- Ensure the logic properly handles all status transitions
- Verify directory structure creation logic
- Enhance error handling and edge case coverage

### Acceptance Criteria
- Standalone tasks are correctly routed to `planning/tasks/` directory
- Support for both `tasks-open` and `tasks-done` subdirectories
- Proper filename generation for different task statuses
- Directory creation logic works correctly
- Error handling for invalid status values

### Dependencies
- T-add-standalone-task-detection: Need detection logic for routing

### Security Considerations
- Validate status parameter to prevent directory traversal
- Ensure proper sanitization of task IDs
- Handle malformed or unexpected status values

### Testing Requirements
- Test standalone task creation with status="open"
- Test standalone task creation with status="done"
- Test standalone task creation with no status (defaults to open)
- Test directory creation for new task directories
- Test error handling for invalid status values

### Implementation Details
- The logic already exists but may need enhancement
- Focus on validation and error handling improvements
- Ensure consistency with hierarchy-based task creation
- Add proper documentation for the standalone task path structure

### Log

