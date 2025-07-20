---
kind: task
id: T-clean-up-module-exports-for
title: Clean Up Module Exports for getNextReviewableTask Tool
status: open
priority: high
prerequisites:
- T-delete-getnextreviewabletask
created: '2025-07-20T11:32:06.508821'
updated: '2025-07-20T11:32:06.508821'
schema_version: '1.1'
parent: F-core-tool-removal-and
---
# Clean Up Module Exports for getNextReviewableTask Tool

## Purpose
Remove getNextReviewableTask tool exports from the tools module to prevent import errors and maintain module integrity after tool file deletion. This ensures clean module structure and eliminates broken references.

## Technical Context
The tools module exports are managed in `/src/trellis_mcp/tools/__init__.py` with:
- Line 15: Import statement `from .get_next_reviewable_task import create_get_next_reviewable_task_tool`
- Line 34: Export in `__all__` list `"create_get_next_reviewable_task_tool"`
- Module provides centralized tool exports for the entire tools package

## Implementation Requirements

### 1. Remove Import Statement
Remove the import line from tools/__init__.py:
```python
from .get_next_reviewable_task import create_get_next_reviewable_task_tool
```

### 2. Remove Export from __all__ List
Remove the export from the __all__ list:
```python
"create_get_next_reviewable_task_tool",
```

### 3. Maintain Module Integrity
- Preserve correct formatting and alphabetical ordering of remaining exports
- Ensure no trailing commas or syntax errors
- Verify module imports correctly after cleanup
- Test that other tool imports continue working

### 4. Micro-Cycle Implementation Approach
- Remove import statement first
- Test module import integrity
- Remove __all__ export entry
- Verify complete module functionality

## Detailed Acceptance Criteria

### Import Statement Cleanup
- [ ] Remove `from .get_next_reviewable_task import create_get_next_reviewable_task_tool` from line 15
- [ ] Verify no unused import warnings after removal
- [ ] Confirm remaining imports are properly formatted
- [ ] Check that import order/grouping remains consistent with project standards

### __all__ List Cleanup
- [ ] Remove `"create_get_next_reviewable_task_tool"` from __all__ list (line 34)
- [ ] Maintain proper formatting of __all__ list (no trailing commas)
- [ ] Preserve alphabetical ordering of remaining exports
- [ ] Ensure proper Python list syntax after removal

### Module Integrity Verification
- [ ] Tools module imports successfully: `from trellis_mcp.tools import *`
- [ ] All remaining tool imports work correctly
- [ ] No ImportError exceptions when importing tools module
- [ ] Module structure follows project conventions

### Import Testing
- [ ] Test individual tool imports still work (health_check, create_object, etc.)
- [ ] Verify tools module can be imported from server.py
- [ ] Confirm no broken references in other modules
- [ ] Test that getNextReviewableTask import fails appropriately

## Implementation Steps

1. **Verify prerequisite**: Ensure tool file deleted and server registration removed
2. **Remove import statement** from line 15
3. **Test import**: Verify tools module still imports correctly
4. **Remove __all__ export** from line 34
5. **Format cleanup**: Ensure proper list formatting
6. **Test module integrity**: Import all remaining tools
7. **Verify functionality**: Test that remaining exports work

## Dependencies and Prerequisites
- **Prerequisite**: T-delete-getnextreviewabletask must be completed first
- Tool file must be deleted to prevent import attempts
- Server registration should be removed to prevent tool loading attempts
- Should complete before dependency function cleanup

## Security Considerations
- Ensure no security holes created by removing tool exports
- Verify module access controls remain intact
- Maintain audit trail of export changes
- No sensitive information exposed during cleanup

## Performance Impact
- Slightly faster module imports (one less import to process)
- Reduced memory usage during module initialization
- No negative impact on remaining tool functionality
- Module discovery operations marginally faster

## Error Handling
- If import removal causes syntax errors: Check for missing commas or brackets
- If __all__ cleanup breaks: Verify list syntax and proper string quoting
- If module import fails: Check remaining import statements for errors
- If tool imports break: Verify remaining tool files and exports are correct

## Rollback Procedure
If module cleanup causes import issues:
1. **Restore import**: Add back `from .get_next_reviewable_task import create_get_next_reviewable_task_tool`
2. **Restore export**: Add back `"create_get_next_reviewable_task_tool"` to __all__ list
3. **Test module**: Verify tools module imports correctly
4. **Note**: This requires tool file to exist, so coordinate with file deletion rollback

## Files Modified
- `/src/trellis_mcp/tools/__init__.py`: Remove import and __all__ export

## Verification Commands
```bash
# Test tools module import
python3 -c "from trellis_mcp.tools import *; print('Tools module imports successfully')"

# Test specific tool imports (should work)
python3 -c "from trellis_mcp.tools import create_health_check_tool; print('Individual imports work')"

# Test removed tool import (should fail)
python3 -c "
try:
    from trellis_mcp.tools import create_get_next_reviewable_task_tool
    print('ERROR: Removed tool import should fail')
except ImportError:
    print('SUCCESS: Removed tool import correctly fails')
"

# Check syntax
python3 -m py_compile src/trellis_mcp/tools/__init__.py
```

## Testing Requirements
- Module import testing to verify tools package loads correctly
- Individual tool import testing to ensure remaining functionality
- Removed tool import failure testing to confirm cleanup success
- Syntax validation to ensure proper Python module structure
- Integration testing with server module imports

### Log

