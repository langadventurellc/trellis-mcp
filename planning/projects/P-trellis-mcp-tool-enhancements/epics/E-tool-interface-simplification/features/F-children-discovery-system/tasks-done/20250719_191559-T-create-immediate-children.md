---
kind: task
id: T-create-immediate-children
parent: F-children-discovery-system
status: done
title: Create immediate children discovery function with unit tests and documentation
priority: high
prerequisites: []
created: '2025-07-19T19:01:21.073884'
updated: '2025-07-19T19:08:20.591230'
schema_version: '1.1'
worktree: null
---
# Create Immediate Children Discovery Function

## Context
Implement a new children discovery function that finds only immediate child objects (Project → Epics, Epic → Features, Feature → Tasks) unlike the existing `children_of` function in `src/trellis_mcp/path_resolver.py:463` which returns ALL descendants recursively.

## Technical Approach
Create `discover_immediate_children()` function in `src/trellis_mcp/path_resolver.py` that:
- Takes same parameters as `children_of()`: `kind: str, obj_id: str, project_root: Path`
- Returns `list[dict]` with child metadata (not just file paths)
- Uses existing security validation patterns from `children_of()` function
- Leverages existing `find_object_path()` utility from `src/trellis_mcp/fs_utils.py`
- Reuses metadata parsing patterns from `src/trellis_mcp/markdown_loader.py`

## Specific Implementation Requirements

### Function Signature
```python
def discover_immediate_children(kind: str, obj_id: str, project_root: Path) -> list[dict[str, str]]:
    """Find immediate child objects with metadata.
    
    Returns:
        List of dictionaries with structure:
        {
            "id": str,        # Clean child ID (without prefix)
            "title": str,     # Child object title  
            "status": str,    # Child object status
            "kind": str,      # Child object type
            "created": str,   # ISO timestamp
            "file_path": str  # Path to child file
        }
    """
```

### Parent-Child Relationships
- **Project → Epics**: Scan `{project_dir}/epics/E-*/epic.md` files only
- **Epic → Features**: Scan `{epic_dir}/features/F-*/feature.md` files only  
- **Feature → Tasks**: Scan `{feature_dir}/tasks-open/T-*.md` and `{feature_dir}/tasks-done/*-T-*.md` files only
- **Task → []**: Tasks have no children, return empty list

### Metadata Extraction
- Parse YAML front-matter using `load_markdown()` from `src/trellis_mcp/markdown_loader.py`
- Extract: `id`, `title`, `status`, `created` fields
- Add computed: `kind`, `file_path` fields
- Handle missing fields gracefully with defaults

### Security & Validation
- Reuse validation patterns from `children_of()` lines 502-525
- Apply same path boundary checks and security validation
- Validate parent object exists before scanning for children
- Use `_validate_task_id_security()` for input sanitization

### Performance Requirements
- Target < 50ms for small collections (1-10 children)
- Target < 100ms for medium collections (11-50 children)  
- Target < 200ms for large collections (51+ children)
- Sort results by creation date (oldest first) for consistent ordering

## Detailed Acceptance Criteria

### Functional Requirements
- [ ] **Project Children**: Correctly discovers only immediate epics under a project
- [ ] **Epic Children**: Correctly discovers only immediate features under an epic
- [ ] **Feature Children**: Correctly discovers only immediate tasks under a feature
- [ ] **Task Children**: Returns empty list for tasks (no children)
- [ ] **Metadata Completeness**: All returned objects include id, title, status, kind, created, file_path
- [ ] **Error Handling**: Graceful handling when parent doesn't exist or has no children
- [ ] **Security Validation**: Prevents path traversal and validates all inputs

### Integration Requirements
- [ ] **Existing Patterns**: Uses same validation and security patterns as `children_of()`
- [ ] **Shared Utilities**: Leverages `find_object_path()`, `load_markdown()`, validation functions
- [ ] **Type Safety**: Proper type hints and Pydantic integration where applicable
- [ ] **Error Consistency**: Same error handling patterns as other path resolver functions

### Performance Requirements
- [ ] **Response Times**: Meets target response times for different collection sizes
- [ ] **Memory Efficiency**: Doesn't load entire child objects into memory unnecessarily
- [ ] **File I/O Optimization**: Minimizes file system operations through efficient scanning
- [ ] **Sorted Results**: Returns children ordered by creation date for consistent output

## Testing Requirements

### Unit Tests (in `tests/test_path_resolver.py`)
- [ ] **Valid Parent Types**: Test discovery for projects, epics, features, tasks
- [ ] **Empty Collections**: Test parents with no children return empty list
- [ ] **Mixed Collections**: Test parents with valid and invalid children
- [ ] **Metadata Parsing**: Verify all required fields are extracted correctly
- [ ] **Error Conditions**: Test invalid parents, missing directories, corrupted files
- [ ] **Security Validation**: Test path traversal prevention and input sanitization
- [ ] **Performance**: Validate response times meet requirements

### Test Data Structure
```python
# Expected test scenarios
test_cases = [
    ("project", "valid-project", ["epic1", "epic2"]),
    ("epic", "valid-epic", ["feature1", "feature2"]),  
    ("feature", "valid-feature", ["task1", "task2"]),
    ("task", "valid-task", []),  # No children
    ("project", "nonexistent", FileNotFoundError),
    ("feature", "feature-no-children", []),
]
```

## Documentation Requirements
- [ ] **Function Docstring**: Comprehensive docstring with examples and parameter descriptions
- [ ] **Code Comments**: Inline comments explaining security validations and performance optimizations
- [ ] **Error Messages**: Clear, actionable error messages for all failure scenarios
- [ ] **Usage Examples**: Include examples in docstring showing typical usage patterns

## Dependencies
- Security validation functions from `src/trellis_mcp/validation/`
- Metadata parsing from `src/trellis_mcp/markdown_loader.py`
- Object discovery from `src/trellis_mcp/fs_utils.py`
- Existing constants and patterns from `src/trellis_mcp/path_resolver.py`

### Log


**2025-07-20T00:15:59.638261Z** - Implemented discover_immediate_children() function in src/trellis_mcp/path_resolver.py that finds only immediate child objects (not recursive descendants) and returns rich metadata instead of just file paths. The function uses the same security validation patterns as children_of(), supports all parent-child relationships (Project→Epics, Epic→Features, Feature→Tasks), and includes comprehensive error handling with graceful defaults for missing metadata fields. Performance targets are met (< 50ms for small collections) with results sorted by creation date. Added comprehensive unit tests with 25 test cases covering all scenarios including edge cases, security validation, corrupted file handling, and performance testing. All quality checks pass (black, isort, flake8, pyright, pytest) with 1738 total tests passing.
- filesChanged: ["src/trellis_mcp/path_resolver.py", "tests/unit/test_discover_immediate_children.py"]