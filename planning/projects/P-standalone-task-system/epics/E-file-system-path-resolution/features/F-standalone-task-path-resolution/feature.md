---
kind: feature
id: F-standalone-task-path-resolution
title: Standalone Task Path Resolution
status: in-progress
priority: normal
prerequisites: []
created: '2025-07-18T13:48:35.834458'
updated: '2025-07-18T13:48:35.834458'
schema_version: '1.1'
parent: E-file-system-path-resolution
---
### Purpose and Functionality
Update the path resolution system to handle standalone tasks stored in `planning/tasks/` directory structure. This includes creating, retrieving, and organizing standalone task files while maintaining compatibility with existing hierarchy-based task paths.

### Key Components to Implement
- Extend `path_resolver.py` with standalone task path logic
- Add support for `planning/tasks/` directory structure
- Implement `tasks-open` and `tasks-done` subdirectory patterns
- Maintain backward compatibility with existing path resolution

### Acceptance Criteria
- Standalone tasks are correctly resolved to `planning/tasks/` directory
- Path resolution works for both task creation and retrieval operations
- File naming patterns remain consistent (T-{task-id}.md)
- Existing hierarchy-based path resolution continues to work unchanged

### Technical Requirements
- Modify `PathResolver` class to detect standalone vs hierarchy-based tasks
- Add path construction methods for standalone task directories
- Support both immediate and subdirectory organization patterns
- Preserve existing path resolution interface and behavior

### Dependencies on Other Features
- None (foundational feature)

### Implementation Guidance
- Examine current `path_resolver.py` implementation patterns
- Use task metadata (presence/absence of parent feature) to determine path type
- Follow existing code style and error handling patterns
- Consider future status transition requirements in path structure

### Testing Requirements
- Unit tests for standalone task path construction
- Unit tests for standalone task path parsing
- Integration tests with existing path resolution functionality
- Edge case testing for malformed or missing task IDs

### Security Considerations
- Validate task IDs to prevent directory traversal attacks
- Ensure proper file permissions on created directories
- Sanitize input parameters in path construction

### Performance Requirements
- Path resolution should complete in < 1ms for typical operations
- No degradation of existing path resolution performance
- Efficient handling of both path types without unnecessary overhead

### Log

