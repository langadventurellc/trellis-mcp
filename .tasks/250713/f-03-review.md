# F-03 Review Tasks - YAML Schema Improvements

## Task Checklist

See below for requirements on each task.

- [ ] T-01: Consolidate Redundant Validation Logic
- [ ] T-02: Standardize Error Handling Strategy
- [ ] T-03: Improve Path Discovery with Glob Patterns
- [ ] T-04: Fix ID Prefix Assumption Bug
- [ ] T-05: Add Comprehensive Tests

## Context

After implementing the initial YAML schema validation system, Gemini provided a comprehensive review identifying several areas for improvement. The current implementation has solid architecture but suffers from code duplication, inconsistent error handling, and some brittle path logic.

## Priority Tasks

### T-01: Consolidate Redundant Validation Logic

**Problem**: Status and parent validators are duplicated across `project.py`, `epic.py`, `feature.py`, and `task.py`. The factory functions in `validation.py` (`create_status_validator`, `create_parent_validator`) exist but aren't being used consistently.

**Solution**:
1. Move validator factories from `validation.py` to `src/trellis_mcp/schema/base_schema.py` for better co-location with models
2. Remove individual `validate_*_status` and `validate_*_parent` methods from concrete schema classes
3. Apply the factory validators to `BaseSchemaModel` so all models inherit them automatically
4. Update the factory functions to use the `info.data.get("kind")` pattern to determine object type dynamically

**Files to modify**:
- `src/trellis_mcp/schema/base_schema.py` - add factory functions and apply to base model
- `src/trellis_mcp/schema/project.py` - remove `validate_project_status`, `validate_project_parent`
- `src/trellis_mcp/schema/epic.py` - remove `validate_epic_status`, `validate_epic_parent`
- `src/trellis_mcp/schema/feature.py` - remove `validate_feature_status`, `validate_feature_parent`
- `src/trellis_mcp/schema/task.py` - remove `validate_task_status`, `validate_task_parent`
- `src/trellis_mcp/validation.py` - remove factory functions (moved to base_schema)

### T-02: Standardize Error Handling Strategy

**Problem**: Mixed error types across the codebase - some functions raise exceptions, others return `List[str]` of error messages. This makes the API inconsistent and harder for callers to handle.

**Solution**:
1. Standardize on raising exceptions for all validation failures
2. Create a custom `ValidationError` exception class that can hold multiple error messages
3. Update `validate_object_data` to raise exceptions instead of returning string lists
4. Update `get_all_objects` to log warnings for invalid files instead of silently skipping them
5. Ensure all validation functions follow the same error handling pattern

**Files to modify**:
- `src/trellis_mcp/validation.py` - create custom ValidationError, update all validation functions
- `src/trellis_mcp/object_parser.py` - update error handling in `parse_object`
- Add logging configuration for warning about skipped files

**Example**:
```python
class TrellisValidationError(Exception):
    """Custom validation error that can hold multiple error messages."""
    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__(f"Validation failed: {'; '.join(errors)}")
```

### T-03: Improve Path Discovery with Glob Patterns

**Problem**: The nested loops and hardcoded directory names in `get_all_objects` are brittle. Code assumes specific directory structure and naming conventions.

**Solution**:
1. Replace hardcoded path traversal with glob patterns for more resilient file discovery
2. Use patterns like `project_root_path.glob('**/T-*.md')` to find all task files
3. Extract object type and hierarchy from file paths dynamically
4. Make the system more tolerant of directory structure changes

**Files to modify**:
- `src/trellis_mcp/validation.py` - update `get_all_objects` function
- Consider updating `object_parser.py` if path parsing logic needs to be more flexible

**Example approach**:
```python
def get_all_objects(project_root_path: Path) -> Dict[str, Any]:
    """Get all objects using glob patterns for resilient discovery."""
    objects = {}
    
    # Find all markdown files with ID prefixes
    for pattern in ['P-*.md', 'E-*.md', 'F-*.md', 'T-*.md']:
        for file_path in project_root_path.glob(f'**/{pattern}'):
            try:
                obj = parse_object(file_path)
                objects[obj.id] = obj
            except Exception as e:
                logger.warning(f"Skipping invalid file {file_path}: {e}")
                continue
    
    return objects
```

### T-04: Fix ID Prefix Assumption Bug

**Problem**: In `build_prerequisites_graph`, the code `clean_prereqs.append(prereq[2:])` assumes all IDs have a 2-character prefix. If an ID is entered without a prefix, this will slice incorrectly.

**Solution**:
1. Add robust ID prefix detection
2. Handle cases where IDs might not have prefixes
3. Add validation to ensure prerequisite IDs are properly formatted

**Files to modify**:
- `src/trellis_mcp/validation.py` - update `build_prerequisites_graph`

**Example**:
```python
def clean_prerequisite_id(prereq_id: str) -> str:
    """Clean prerequisite ID by removing prefix if present."""
    if len(prereq_id) > 2 and prereq_id[2] == '-':
        return prereq_id[3:]  # Remove "X-" prefix
    return prereq_id  # Return as-is if no prefix detected
```

## Implementation Notes

1. **Order matters**: Complete T-01 first as it affects the base model structure
2. **Backward compatibility**: Ensure existing functionality still works after refactoring
3. **Testing**: Add tests as you implement each change to prevent regressions
4. **Documentation**: Update any inline documentation that references the old validation approach

## Success Criteria

- All validation logic is centralized in base schema model
- Consistent exception-based error handling throughout
- Robust file discovery using glob patterns
- No ID prefix assumptions in prerequisite handling
- Comprehensive test coverage for edge cases
- All existing tests still pass
- Code quality gate passes (`uv run pre-commit run --all-files`)