---
kind: task
id: T-add-standalone-task-path
title: Add standalone task path construction methods
status: open
priority: normal
prerequisites:
- T-add-standalone-task-detection
created: '2025-07-18T13:52:54.094639'
updated: '2025-07-18T13:52:54.094639'
schema_version: '1.1'
parent: F-standalone-task-path-resolution
---
### Implementation Requirements
Create helper functions for constructing standalone task paths, including directory creation and filename generation utilities.

### Technical Approach
- Add `construct_standalone_task_path` helper function
- Add `get_standalone_task_filename` helper function
- Add `ensure_standalone_task_directory` helper function
- Follow existing code patterns and naming conventions

### Acceptance Criteria
- Helper functions for standalone task path construction
- Support for both tasks-open and tasks-done directory structures
- Proper filename generation based on task status
- Directory creation utilities for new task directories
- Consistent error handling and validation

### Dependencies
- T-add-standalone-task-detection: Need detection logic for routing

### Security Considerations
- Validate all input parameters
- Ensure proper directory permissions when creating directories
- Sanitize task IDs and status values

### Testing Requirements
- Test path construction for various task statuses
- Test directory creation functionality
- Test filename generation for different scenarios
- Test error handling for invalid inputs
- Test edge cases with unusual task IDs

### Implementation Details
- Add helper functions after the existing utility functions
- Use consistent naming conventions with existing code
- Add proper type hints and docstrings
- Include comprehensive error handling
- Follow the existing pattern of other helper functions in the file

### Log

