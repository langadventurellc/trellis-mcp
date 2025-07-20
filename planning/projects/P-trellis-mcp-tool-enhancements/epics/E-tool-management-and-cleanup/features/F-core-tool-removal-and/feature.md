---
kind: feature
id: F-core-tool-removal-and
title: Core Tool Removal and Registration Cleanup
status: in-progress
priority: high
prerequisites: []
created: '2025-07-20T11:21:08.746788'
updated: '2025-07-20T11:21:08.746788'
schema_version: '1.1'
parent: E-tool-management-and-cleanup
---
# Core Tool Removal and Registration Cleanup Feature

## Purpose and Functionality
Execute the systematic removal of the getNextReviewableTask tool from the MCP server, including deleting the tool implementation, cleaning up server registration, removing imports, and eliminating associated utility functions. This feature performs the core removal operations that physically eliminate the tool from the system.

## Key Components to Implement

### 1. Tool File Deletion
- **Primary tool file removal**: Delete `/src/trellis_mcp/tools/get_next_reviewable_task.py` completely
- **Factory function elimination**: Remove `create_get_next_reviewable_task_tool()` function
- **Tool implementation cleanup**: Remove all getNextReviewableTask-specific code
- **Verification scanning**: Confirm complete file removal with no remnants

### 2. Server Registration Cleanup
- **FastMCP registration removal**: Remove tool from server.py registration code
- **Import statement cleanup**: Remove getNextReviewableTask imports from server.py
- **Tool instance cleanup**: Remove tool creation and server.add_tool() calls
- **Registration verification**: Ensure clean server startup after removal

### 3. Module Export Cleanup
- **Tools module cleanup**: Remove exports from `/src/trellis_mcp/tools/__init__.py`
- **Import cleanup**: Remove internal imports of getNextReviewableTask functions
- **__all__ list updates**: Remove tool from module export lists
- **Module integrity**: Ensure tools module remains valid after cleanup

### 4. Dependency Function Removal
- **get_oldest_review() removal**: Delete unused function from query.py
- **Utility function cleanup**: Remove any functions only used by getNextReviewableTask
- **Import optimization**: Clean up any orphaned imports after function removal
- **Module verification**: Ensure query.py remains functional after cleanup

## Detailed Acceptance Criteria

### File Deletion and Cleanup
- [ ] **Tool file deletion**: `/src/trellis_mcp/tools/get_next_reviewable_task.py` completely removed
- [ ] **No file remnants**: Verify no backup files, .pyc files, or other remnants exist
- [ ] **Git tracking**: Ensure file is properly deleted from git tracking
- [ ] **Directory cleanup**: Remove any empty directories created by deletion

### Server Registration Updates
- [ ] **Import removal**: Remove `from .tools.get_next_reviewable_task import create_get_next_reviewable_task_tool` from server.py
- [ ] **Registration removal**: Remove tool creation and server.add_tool() calls for getNextReviewableTask
- [ ] **Clean startup**: Server starts successfully without attempting to register removed tool
- [ ] **Error handling**: Server handles removal gracefully with no startup errors

### Module Export Cleanup
- [ ] **Export removal**: Remove `create_get_next_reviewable_task_tool` from tools/__init__.py __all__ list
- [ ] **Import cleanup**: Remove import statements for getNextReviewableTask functions
- [ ] **Module validity**: tools module imports successfully after cleanup
- [ ] **No broken references**: No remaining references to removed tool in module

### Dependency Function Cleanup
- [ ] **get_oldest_review() removal**: Function completely removed from query.py
- [ ] **Import optimization**: Remove any imports only used by removed functions
- [ ] **Module functionality**: query.py functions correctly after cleanup
- [ ] **No orphaned code**: All functions and imports have valid usage

## Implementation Guidance

### Technical Approach
- **Sequential removal order**: Delete in dependency order to prevent temporary broken states
- **Atomic operations**: Group related changes together for clean rollback if needed
- **Verification at each step**: Validate system integrity after each major removal
- **Conservative file handling**: Use git operations for safe file deletion

### Removal Sequence
1. **Remove server registration** first to prevent tool from being accessible
2. **Delete tool implementation file** to remove core functionality
3. **Clean up module exports** to prevent import errors
4. **Remove dependency functions** last to ensure no broken references

### Safety Measures
```python
# Example verification after server registration removal
def verify_server_startup():
    """Verify server starts cleanly after tool removal"""
    # Test server initialization
    # Confirm no registration errors
    # Validate remaining tools load correctly

# Example verification after file deletion
def verify_import_integrity():
    """Verify no broken imports after file deletion"""
    # Test all module imports
    # Confirm no missing references
    # Validate module structure
```

## Testing Requirements

### Removal Verification
- **File deletion confirmation**: Verify files are completely removed from filesystem
- **Import testing**: Confirm no broken imports after removal operations
- **Server startup testing**: Validate server starts cleanly after each removal step
- **Registration testing**: Verify tool no longer appears in tool listings

### System Integrity Testing
- **Remaining tool functionality**: Ensure other tools continue working correctly
- **Module import testing**: Verify all remaining modules import successfully
- **Error handling validation**: Confirm appropriate errors for removed tool access
- **Performance testing**: Ensure removal doesn't negatively impact server performance

### Rollback Testing
- **Rollback capability**: Verify ability to restore tool if removal causes issues
- **State consistency**: Ensure system remains in consistent state during rollback
- **Recovery validation**: Confirm complete recovery from failed removal attempts
- **Data integrity**: Verify no data corruption during removal or rollback

## Security Considerations

### Safe Removal Practices
- **Backup before removal**: Create backup of all files before deletion
- **Atomic operations**: Ensure removal operations are atomic where possible
- **Access control**: Maintain proper access controls during removal process
- **Audit trail**: Log all removal operations for security and debugging

### Error Prevention
- **Validation before removal**: Verify all preconditions before executing removal
- **Dependency checking**: Ensure no critical dependencies before removing functions
- **State verification**: Validate system state before and after each removal step
- **Recovery procedures**: Maintain clear procedures for recovery from failed removal

## Performance Requirements

### Removal Efficiency
- **Fast execution**: Complete removal operations within 30 seconds
- **Minimal downtime**: If server restart required, minimize downtime duration
- **Resource efficiency**: Removal operations should not consume excessive resources
- **Clean completion**: All operations complete cleanly with no hanging processes

### System Impact
- **No performance degradation**: Remaining tools should perform at same level or better
- **Memory optimization**: Removal should reduce memory footprint appropriately
- **Startup optimization**: Server startup should be faster after tool removal
- **Registration efficiency**: Tool discovery should be faster with fewer tools

## Integration Points

### With Code Analysis Feature
- **Dependency on analysis results**: Use findings from analysis feature to guide removal
- **Reference validation**: Confirm all identified references are addressed
- **Impact verification**: Validate removal matches analysis predictions
- **Plan execution**: Follow removal plan created in analysis phase

### With Test Cleanup Feature
- **Coordination timing**: Removal should complete before test cleanup begins
- **Test impact**: Removal may cause test failures that cleanup feature will address
- **Validation support**: Provide clean tool state for test validation
- **Error documentation**: Document any removal-related test impacts

### With Documentation Feature
- **Status updates**: Provide removal status for documentation updates
- **Error scenarios**: Document any error conditions for user guidance
- **Migration support**: Provide information needed for migration documentation
- **Tool listings**: Ensure documentation feature has updated tool availability

This feature executes the core removal operations that physically eliminate the getNextReviewableTask tool from the system while maintaining system integrity and enabling safe rollback if needed.

### Log

