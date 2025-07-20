---
kind: task
id: T-delete-getnextreviewabletask
title: Delete getNextReviewableTask Tool Implementation File
status: open
priority: high
prerequisites:
- T-remove-server-registration-and
created: '2025-07-20T11:31:29.215320'
updated: '2025-07-20T11:31:29.215320'
schema_version: '1.1'
parent: F-core-tool-removal-and
---
# Delete getNextReviewableTask Tool Implementation File

## Purpose
Completely remove the getNextReviewableTask tool implementation file from the filesystem as the second step in the tool removal process. This eliminates the core functionality while ensuring clean file deletion and git tracking.

## Technical Context
The tool implementation is located at `/src/trellis_mcp/tools/get_next_reviewable_task.py` (127 lines total) containing:
- `create_get_next_reviewable_task_tool()` factory function
- `getNextReviewableTask()` MCP tool implementation with FastMCP decorators
- Comprehensive error handling and validation logic
- Integration with query.py functions (`get_oldest_review`)

## Implementation Requirements

### 1. Safe File Deletion
Use git operations for safe file removal to maintain history and enable rollback:
```bash
git rm src/trellis_mcp/tools/get_next_reviewable_task.py
```

### 2. Verification of Complete Removal
- Confirm file no longer exists in filesystem
- Verify no backup files (.pyc, .pyo, __pycache__) remain
- Check git tracking shows file as deleted
- Ensure directory structure remains intact

### 3. Micro-Cycle Implementation Approach
- Delete file using git command for safety
- Verify file deletion immediately
- Test import integrity after deletion
- Confirm no broken references exist

## Detailed Acceptance Criteria

### File Deletion
- [ ] `/src/trellis_mcp/tools/get_next_reviewable_task.py` completely removed from filesystem
- [ ] File properly deleted from git tracking (shows as deleted in git status)
- [ ] No backup files or Python cache files remain (.pyc, .pyo, __pycache__ entries)
- [ ] Directory `/src/trellis_mcp/tools/` still exists with other tool files intact

### Git Tracking Cleanup
- [ ] File shows as deleted in `git status`
- [ ] Git history preserved for rollback capability
- [ ] No untracked remnant files in git status
- [ ] Repository remains in clean state after deletion

### Filesystem Verification
- [ ] Attempting to read file returns "file not found" error
- [ ] No symbolic links or shortcuts pointing to deleted file
- [ ] Parent directory permissions remain correct
- [ ] No orphaned directory entries

### Import Integrity Testing
- [ ] Python import of deleted module fails with ImportError
- [ ] No import statements in other files break due to deletion
- [ ] Tools module structure remains valid
- [ ] Server module imports continue working

## Implementation Steps

1. **Verify prerequisite completion**: Ensure server registration removed first
2. **Create backup** (optional): `cp src/trellis_mcp/tools/get_next_reviewable_task.py /tmp/backup_get_next_reviewable_task.py`
3. **Delete using git**: `git rm src/trellis_mcp/tools/get_next_reviewable_task.py`
4. **Verify deletion**: Check file no longer exists with `ls` and `git status`
5. **Clean cache files**: Remove any Python cache entries
6. **Test import failure**: Verify import attempts fail appropriately
7. **Check directory integrity**: Ensure tools directory structure intact

## Dependencies and Prerequisites
- **Prerequisite**: T-remove-server-registration-and must be completed first
- Server registration must be removed to prevent import attempts during server startup
- Requires access to git commands for safe file deletion
- Should complete before module export cleanup to prevent import errors

## Security Considerations
- Use git operations for secure file deletion with audit trail
- Preserve file content in git history for security review if needed
- Ensure no sensitive information exposed in file deletion process
- Verify no security holes created by removing authentication/validation code

## Performance Impact
- Reduced disk space usage (127 lines removed)
- Faster file system operations in tools directory
- Slightly faster Python import scanning
- No impact on remaining tool performance

## Error Handling
- If `git rm` fails: Check file permissions and git repository status
- If file deletion incomplete: Manually remove with `rm` and stage deletion
- If cache files persist: Clear Python cache manually with `find` command
- If directory corruption: Verify other tool files and restore directory if needed

## Rollback Procedure
If file deletion causes unexpected issues:
1. **Restore from git**: `git checkout HEAD~1 -- src/trellis_mcp/tools/get_next_reviewable_task.py`
2. **Verify restoration**: Check file content and permissions
3. **Test functionality**: Ensure tool works if server registration restored
4. **Investigate issue**: Determine root cause before re-attempting deletion

## Files Modified
- **Deleted**: `/src/trellis_mcp/tools/get_next_reviewable_task.py`
- **Git tracking**: File marked as deleted in git index

## Verification Commands
```bash
# Verify file deletion
ls src/trellis_mcp/tools/get_next_reviewable_task.py 2>/dev/null || echo "File successfully deleted"

# Check git status
git status | grep get_next_reviewable_task

# Verify import failure
python3 -c "
try:
    from src.trellis_mcp.tools.get_next_reviewable_task import create_get_next_reviewable_task_tool
    print('ERROR: Import should have failed')
except ImportError:
    print('SUCCESS: Import correctly fails')
"

# Check for cache files
find . -name "*get_next_reviewable_task*" -type f
```

## Testing Requirements
- File deletion verification using filesystem commands
- Git status checking for proper tracking of deletion
- Import failure testing to confirm module unavailable
- Cache cleanup verification to ensure no remnants
- Directory integrity testing to ensure tools structure intact

### Log

