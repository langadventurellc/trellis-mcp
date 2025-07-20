---
kind: task
id: T-remove-server-registration-and
parent: F-core-tool-removal-and
status: in-progress
title: Remove Server Registration and Imports for getNextReviewableTask Tool
priority: high
prerequisites: []
created: '2025-07-20T11:30:49.786010'
updated: '2025-07-20T11:35:51.928801'
schema_version: '1.1'
---
# Remove Server Registration and Imports for getNextReviewableTask Tool

## Purpose
Remove the getNextReviewableTask tool from server registration and clean up associated imports in server.py as the first step in tool removal process. This prevents the tool from being accessible while maintaining server functionality.

## Technical Context
The getNextReviewableTask tool is currently registered in `/src/trellis_mcp/server.py` at lines:
- Line 16: Import statement `from .tools.get_next_reviewable_task import create_get_next_reviewable_task_tool`
- Lines 77-78: Tool creation and registration with FastMCP server

## Implementation Requirements

### 1. Remove Import Statement
Remove the import line from server.py:
```python
from .tools.get_next_reviewable_task import create_get_next_reviewable_task_tool
```

### 2. Remove Tool Registration
Remove the tool creation and registration code:
```python
# Create and register getNextReviewableTask tool
get_next_reviewable_task_tool = create_get_next_reviewable_task_tool(settings)
server.add_tool(get_next_reviewable_task_tool)
```

### 3. Micro-Cycle Implementation Approach
- Make one change at a time (import removal, then registration removal)
- Test server startup after each change
- Verify tool no longer appears in tool listings
- Confirm remaining tools still function correctly

## Detailed Acceptance Criteria

### Import Cleanup
- [ ] Remove import statement from server.py line 16
- [ ] Verify no unused import warnings after removal
- [ ] Confirm server.py still imports all necessary modules for remaining tools
- [ ] Check that no other imports depend on the removed import

### Registration Removal
- [ ] Remove tool creation code (get_next_reviewable_task_tool = create_get_next_reviewable_task_tool(settings))
- [ ] Remove server.add_tool() call for getNextReviewableTask
- [ ] Ensure proper code formatting after removal (no extra blank lines)
- [ ] Verify server initialization order remains correct

### Server Functionality Verification
- [ ] Server starts successfully without attempting to register removed tool
- [ ] No startup errors or warnings related to getNextReviewableTask
- [ ] Tool no longer appears in tool discovery/listings
- [ ] All other tools continue to load and function correctly
- [ ] Server info resource still returns correct information

### Testing Requirements
- [ ] Run server startup test: `uv run trellis-mcp serve --help` (should work)
- [ ] Verify tool listing doesn't include getNextReviewableTask
- [ ] Test remaining tools are accessible and functional
- [ ] Check server logs for any errors or warnings

## Implementation Steps

1. **Backup current server.py** (optional but recommended)
2. **Remove import statement** (line 16)
3. **Test import cleanup**: Run basic Python import test
4. **Remove tool registration code** (lines 77-78) 
5. **Test server startup**: Verify server initializes correctly
6. **Verify tool removal**: Check that tool is no longer available
7. **Test remaining functionality**: Verify other tools still work

## Dependencies and Prerequisites
- No dependencies on other tasks (this is the starting point)
- Requires access to /src/trellis_mcp/server.py
- Should complete before any other removal tasks to prevent tool access

## Security Considerations
- Ensure tool is immediately inaccessible after registration removal
- Verify no security holes created by removing authentication/authorization paths
- Maintain audit trail by preserving git history of changes
- No sensitive information exposed during removal process

## Performance Impact
- Server startup should be marginally faster (one less tool to register)
- Memory usage should decrease slightly (tool not loaded into memory)
- No negative performance impact on remaining tools
- Tool discovery should be faster with fewer tools to enumerate

## Rollback Procedure
If removal causes issues:
1. Restore import statement: `from .tools.get_next_reviewable_task import create_get_next_reviewable_task_tool`
2. Restore registration code:
   ```python
   get_next_reviewable_task_tool = create_get_next_reviewable_task_tool(settings)
   server.add_tool(get_next_reviewable_task_tool)
   ```
3. Test server startup to confirm restoration
4. Investigate root cause before attempting removal again

## Files Modified
- `/src/trellis_mcp/server.py`: Remove import and registration code

## Verification Commands
```bash
# Test basic server functionality
uv run trellis-mcp serve --help

# Test server startup (should not hang or error)
timeout 5s uv run trellis-mcp serve || echo "Server started successfully"

# Run basic linting to catch syntax errors
uv run flake8 src/trellis_mcp/server.py
```

### Log

