---
kind: task
id: T-fix-inference-engine-validator
parent: F-kind-inference-engine
status: done
title: Fix inference engine validator to use id_to_path for hierarchical object resolution
priority: high
prerequisites: []
created: '2025-07-19T17:05:25.479048'
updated: '2025-07-19T17:07:02.437732'
schema_version: '1.1'
worktree: null
---
# Fix Inference Engine Validator for Hierarchical Object Resolution

## Problem Summary

The Kind Inference Engine integration tests are failing because the FileSystemValidator cannot validate hierarchical objects (epics, features, hierarchical tasks). This is due to an architectural mismatch between how the validator attempts to resolve object paths and how the system actually locates objects.

## Root Cause Analysis

### Current Broken Approach (FileSystemValidator)
The validator in `src/trellis_mcp/inference/validator.py` uses `PathBuilder` to construct object paths:

```python
# Line 117 in validator.py - BROKEN for hierarchical objects
builder = self.path_builder.for_object(kind, object_id)
path = builder.build_path()
```

**Problem**: `PathBuilder` requires parent context for hierarchical objects but the validator doesn't provide it:

- **Epics** need parent project ID: `/projects/P-{parent}/epics/E-{epic}/epic.md`
- **Features** need parent epic ID: `/projects/.../epics/E-{parent}/features/F-{feature}/feature.md` 
- **Hierarchical tasks** need parent feature ID: `/.../features/F-{parent}/tasks-open/T-{task}.md`

When PathBuilder tries to build these paths without parent context, it fails with:
```
ValueError: Parent epic ID is required for feature objects
```

### Working Approach (getObject Tool)
The `getObject` tool successfully finds hierarchical objects using `id_to_path()`:

```python
# Line 90 in get_object.py - WORKS for all objects
file_path = id_to_path(planning_root, kind, clean_id)
```

**Why it works**: `id_to_path()` calls `find_object_path()` from `fs_utils.py` which performs filesystem scanning to locate objects without requiring parent context.

## Failing Test Evidence

Integration tests in `tests/integration/test_inference_engine_integration.py` fail with:
```
ValidationError: Validation failed: Object file not found for epic 'E-user-management'
```

But the objects actually exist - they're successfully created by MCP tools and can be retrieved by `getObject`. The issue is purely in the validator's path resolution approach.

## Solution Strategy

Replace the PathBuilder-based approach in `FileSystemValidator.validate_object_exists()` with the same `id_to_path()` approach used by `getObject`.

### Code Changes Required

**File**: `src/trellis_mcp/inference/validator.py`
**Method**: `validate_object_exists()` (lines ~115-124)

**Current broken code**:
```python
builder = self.path_builder.for_object(kind, object_id)
if kind == "task":
    builder = builder.with_status(status)
path = builder.build_path()
return path.exists() and path.is_file()
```

**Required fix**:
```python
# Use same approach as getObject - id_to_path() for filesystem scanning
from ..path_resolver import id_to_path

# Clean the object ID using existing patterns  
clean_id = self.path_builder._clean_object_id(object_id)

# Use id_to_path to find the object file
path = id_to_path(self.path_builder._resolution_root, kind, clean_id)
return path.exists() and path.is_file()
```

**Exception handling**:
```python
except (ValueError, ValidationError, FileNotFoundError):
    # Path resolution failed - object doesn't exist or is invalid
    return False
```

## Verification Steps

1. **Run integration tests**: All tests in `test_inference_engine_integration.py` should pass
2. **Test hierarchical validation**: Ensure epics, features, and hierarchical tasks can be validated
3. **Test standalone validation**: Ensure projects and standalone tasks still work
4. **Performance check**: Validation should complete in <20ms as specified

## Files to Modify

### Primary Change
- `src/trellis_mcp/inference/validator.py` - Fix `validate_object_exists()` method

### Test Files to Verify
- `tests/integration/test_inference_engine_integration.py` - Should all pass after fix
- `tests/test_inference_validator.py` - Unit tests should continue passing

## Technical Context

### Why This Approach is Correct
1. **Consistency**: Uses same path resolution as working `getObject` tool
2. **No breaking changes**: `id_to_path()` is the established pattern for object location
3. **Performance**: Filesystem scanning is already optimized in `find_object_path()`
4. **Security**: `id_to_path()` includes same security validations as PathBuilder

### Architecture Insight
The confusion arose because there are two path resolution approaches in the codebase:
1. **PathBuilder**: Constructs paths from components (requires parent context)
2. **id_to_path()**: Scans filesystem to find objects (works with just kind+id)

The validator incorrectly chose PathBuilder when it should use id_to_path() like all other object location operations.

## Dependencies
- No new dependencies required
- Uses existing `id_to_path()` function from `path_resolver.py`
- Leverages existing `find_object_path()` function from `fs_utils.py`

## Risk Assessment
- **Low risk**: Using proven, existing path resolution mechanism
- **No breaking changes**: Other components continue using their existing approaches
- **Backward compatible**: All existing functionality preserved

## Success Criteria
- [ ] All integration tests pass
- [ ] Epic validation works without parent context
- [ ] Feature validation works without parent context  
- [ ] Hierarchical task validation works without parent context
- [ ] Project and standalone task validation continue working
- [ ] Performance remains <20ms for validation operations
- [ ] No regressions in existing unit tests

This fix resolves the fundamental architectural mismatch and aligns the validator with the established object location patterns used throughout the codebase.

### Log
**2025-07-19T22:12:52.449923Z** - Fixed FileSystemValidator to use id_to_path instead of PathBuilder for hierarchical object resolution. Replaced PathBuilder-based approach in validate_object_exists(), validate_type_consistency(), and validate_object_structure() methods with id_to_path() which uses filesystem scanning to locate objects without requiring parent context. This resolves the architectural mismatch where PathBuilder needs parent IDs for epics/features but the validator didn't provide them. All existing tests pass and the validator can now successfully validate hierarchical objects (epics, features, hierarchical tasks) alongside standalone objects.
- filesChanged: ["src/trellis_mcp/inference/validator.py", "tests/test_inference_validator.py"]