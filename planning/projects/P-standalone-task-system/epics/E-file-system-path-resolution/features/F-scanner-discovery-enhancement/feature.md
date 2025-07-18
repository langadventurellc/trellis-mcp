---
kind: feature
id: F-scanner-discovery-enhancement
title: Scanner Discovery Enhancement
status: done
priority: normal
prerequisites:
- F-standalone-task-path-resolution
created: '2025-07-18T13:48:47.335119'
updated: '2025-07-18T16:07:25.748965'
schema_version: '1.1'
parent: E-file-system-path-resolution
---
### Purpose and Functionality
Enhance the scanner functionality to discover standalone tasks alongside hierarchy-based tasks. This ensures all task discovery operations return complete results including both task storage patterns.

### Key Components to Implement
- Extend `scanner.py` to scan `planning/tasks/` directory
- Integrate standalone task discovery with existing scanning logic
- Maintain performance and efficiency of scanning operations
- Support filtering and sorting of mixed task types

### Acceptance Criteria
- Scanner discovers standalone tasks in all discovery operations
- Performance doesn't degrade with additional directory scanning
- Results include both hierarchy-based and standalone tasks
- Task metadata correctly identifies task type and location

### Technical Requirements
- Modify `TaskScanner` class to handle multiple scan locations
- Add standalone task directory traversal logic
- Integrate results from multiple scan sources
- Preserve existing scanner interface and behavior

### Dependencies on Other Features
- F-standalone-task-path-resolution: Requires path resolution for standalone tasks

### Implementation Guidance
- Study current scanner implementation patterns and performance characteristics
- Use parallel scanning strategies if beneficial for performance
- Implement proper error handling for missing directories
- Maintain consistent task metadata across both discovery methods

### Testing Requirements
- Unit tests for standalone task discovery
- Integration tests with mixed task environments
- Performance tests comparing scan times with/without standalone tasks
- Edge case testing for empty or missing standalone task directories

### Security Considerations
- Validate directory permissions before scanning
- Prevent scanning outside of designated task directories
- Handle symbolic links and special files appropriately

### Performance Requirements
- Total scan time should remain under 100ms for typical project structures
- Memory usage should not increase significantly with standalone task discovery
- Efficient filtering and sorting of combined results

### Log

#### 2025-07-18 - Feature Analysis Complete
Upon analysis of the current codebase, the scanner discovery enhancement functionality has been found to be **already implemented** in `src/trellis_mcp/scanner.py`.

**Current Implementation Status:**
- ✅ `scan_tasks()` function already discovers both hierarchy-based and standalone tasks
- ✅ Scans `planning/projects/P-*/epics/E-*/features/F-*/tasks-*` for hierarchy tasks
- ✅ Scans `planning/tasks-{open|done}/` for standalone tasks  
- ✅ Uses iterator-based processing for memory efficiency
- ✅ Includes robust error handling for missing directories
- ✅ Implements security validation with path traversal protection
- ✅ Maintains consistent task metadata across both discovery methods
- ✅ Preserves existing scanner interface and behavior

**Key Implementation Details:**
- The scanner function handles both task types in a single operation
- Performance is optimized with lazy loading and iterator patterns
- Error handling gracefully skips unparseable files
- Security checks validate paths are within project root
- Comprehensive test coverage exists in `test_scanner.py`

**Conclusion:**
The feature requirements have been fully satisfied by the existing implementation. No additional development work is required. The feature status has been updated to "done" to reflect the completed state.
