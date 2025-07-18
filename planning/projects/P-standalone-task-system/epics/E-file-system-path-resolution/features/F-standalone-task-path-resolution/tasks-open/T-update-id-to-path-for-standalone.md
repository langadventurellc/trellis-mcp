---
kind: task
id: T-update-id-to-path-for-standalone
title: Update id_to_path for standalone task discovery
status: open
priority: high
prerequisites:
- T-add-standalone-task-detection
created: '2025-07-18T13:52:26.348254'
updated: '2025-07-18T13:52:26.348254'
schema_version: '1.1'
parent: F-standalone-task-path-resolution
---
### Implementation Requirements
Modify the `id_to_path` function to search for standalone tasks in the `planning/tasks/` directory when hierarchy-based lookup fails.

### Technical Approach
- Extend the existing `id_to_path` function (lines 56-132)
- Add standalone task lookup logic for task kind when hierarchy search fails
- Use the shared `find_object_path` utility pattern
- Maintain compatibility with existing hierarchy-based task resolution

### Acceptance Criteria
- When task kind is requested and hierarchy lookup fails, search `planning/tasks/` directory
- Support both `tasks-open` and `tasks-done` subdirectories
- Return correct path for standalone tasks
- Maintain existing behavior for hierarchy-based tasks
- Provide appropriate error messages when task is not found in either location

### Dependencies
- T-add-standalone-task-detection: Need detection logic for routing

### Security Considerations
- Validate task IDs to prevent directory traversal
- Ensure proper path sanitization for standalone task lookups
- Handle symbolic links and special files appropriately

### Testing Requirements
- Test standalone task lookup in tasks-open directory
- Test standalone task lookup in tasks-done directory
- Test hierarchy-based task lookup (unchanged behavior)
- Test error handling when task not found in either location
- Test with various task ID formats and edge cases

### Implementation Details
- Modify the task lookup section in `id_to_path`
- Add fallback logic to search standalone task directories
- Use consistent error handling patterns
- Preserve existing path resolution performance

### Log

