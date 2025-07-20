---
kind: task
id: T-remove-dependency-functions-from
title: Remove Dependency Functions from query.py
status: open
priority: high
prerequisites:
- T-clean-up-module-exports-for
created: '2025-07-20T11:32:46.123908'
updated: '2025-07-20T11:32:46.123908'
schema_version: '1.1'
parent: F-core-tool-removal-and
---
# Remove Dependency Functions from query.py

## Purpose
Remove the `get_oldest_review()` and `is_reviewable()` functions from query.py as they are only used by the getNextReviewableTask tool. This cleanup eliminates orphaned code and optimizes the query module.

## Technical Context
Based on code analysis, the functions to remove are:
- `get_oldest_review()` function (lines 30-69): Only used by getNextReviewableTask tool
- `is_reviewable()` function (lines 14-27): Only used by `get_oldest_review()` function
- Both functions have no other dependencies in the codebase
- Query.py imports: Remove any imports only used by these functions

## Implementation Requirements

### 1. Remove get_oldest_review() Function
Remove the complete function definition (lines 30-69):
```python
def get_oldest_review(project_root: Path) -> TaskModel | None:
    # ... complete function body
```

### 2. Remove is_reviewable() Function  
Remove the complete function definition (lines 14-27):
```python
def is_reviewable(obj: BaseSchemaModel) -> bool:
    # ... complete function body
```

### 3. Clean Up Orphaned Imports
Check and remove any imports only used by the removed functions:
- Review imports for `scanner`, `BaseSchemaModel`, `StatusEnum`, `TaskModel`
- Remove imports that are no longer referenced
- Preserve imports used by other potential functions

### 4. Micro-Cycle Implementation Approach
- Remove `get_oldest_review()` function first (higher level dependency)
- Test module imports after removal
- Remove `is_reviewable()` function second
- Clean up orphaned imports
- Verify module functionality

## Detailed Acceptance Criteria

### Function Removal
- [ ] `get_oldest_review()` function completely removed from query.py
- [ ] `is_reviewable()` function completely removed from query.py
- [ ] No remnants of function code or comments remain
- [ ] Proper code formatting maintained after removal

### Import Cleanup
- [ ] Remove any imports only used by removed functions
- [ ] Preserve imports needed by other code or future functions
- [ ] Verify import statements are properly formatted
- [ ] Check for any unused import warnings

### Module Integrity
- [ ] query.py module imports successfully after cleanup
- [ ] No syntax errors or import errors
- [ ] Module docstring and structure remain intact
- [ ] File remains valid Python module

### Code Quality
- [ ] No orphaned variables or constants related to removed functions
- [ ] No broken docstring references to removed functions
- [ ] Proper module-level documentation maintained
- [ ] Code style consistent with project standards

## Implementation Steps

1. **Verify prerequisites**: Ensure tool file deleted and exports cleaned
2. **Identify function boundaries**: Locate exact start/end lines for each function
3. **Remove get_oldest_review()**: Delete function and its docstring
4. **Test module import**: Verify query.py still imports correctly
5. **Remove is_reviewable()**: Delete function and its docstring
6. **Review imports**: Check each import for continued usage
7. **Clean orphaned imports**: Remove unused imports
8. **Verify module**: Test complete module functionality

## Dependencies and Prerequisites
- **Prerequisite**: T-clean-up-module-exports-for must be completed first
- Tool implementation and exports must be removed to prevent import attempts
- Should complete before integration testing to provide clean module state

## Security Considerations
- Ensure no security validation logic removed inappropriately
- Verify no authorization or access control code affected
- Maintain audit trail of function removal
- Check that remaining code doesn't depend on removed security checks

## Performance Impact
- Reduced memory usage (functions no longer loaded)
- Faster module imports (less code to parse)
- Improved code maintainability (less dead code)
- No impact on remaining system functionality

## Error Handling
- If function removal breaks syntax: Check for proper bracket/indentation matching
- If import cleanup causes errors: Verify remaining code dependencies
- If module fails to import: Check for missing dependencies or syntax errors
- If tests fail: Verify no hidden dependencies on removed functions

## Rollback Procedure
If function removal causes unexpected issues:
1. **Restore functions**: Add back function definitions from git history
2. **Restore imports**: Add back any removed import statements
3. **Test module**: Verify query.py imports and functions correctly
4. **Investigate**: Determine if hidden dependencies exist before re-attempting

## Files Modified
- `/src/trellis_mcp/query.py`: Remove functions and clean up imports

## Verification Commands
```bash
# Test module import
python3 -c "from trellis_mcp.query import *; print('Query module imports successfully')"

# Test module compilation
python3 -m py_compile src/trellis_mcp/query.py

# Check for function removal
grep -n "def get_oldest_review\|def is_reviewable" src/trellis_mcp/query.py || echo "Functions successfully removed"

# Verify no broken imports
python3 -c "import trellis_mcp.query; print('Module loads without errors')"

# Check for unused imports (if tools available)
python3 -m flake8 --select=F401 src/trellis_mcp/query.py
```

## Testing Requirements
- Module import testing to verify query.py loads correctly
- Function removal verification to confirm complete deletion
- Import cleanup testing to ensure no unused imports
- Module compilation testing to verify syntax correctness
- Integration testing with other modules that may import query.py

## Related Files Analysis
Based on research, only the getNextReviewableTask tool uses these functions:
- No other tools or modules reference `get_oldest_review()`  
- No other code uses `is_reviewable()` function
- Safe to remove both functions without affecting other functionality

### Log

