---
kind: task
id: T-enhance-getobject-tool-to
parent: F-children-discovery-system
status: done
title: Enhance getObject tool to include children array with tests and integration
  docs
priority: high
prerequisites:
- T-create-immediate-children
created: '2025-07-19T19:01:56.428186'
updated: '2025-07-19T19:19:10.351622'
schema_version: '1.1'
worktree: null
---
# Enhance getObject Tool with Children Array

## Context
Modify the existing `getObject` tool in `src/trellis_mcp/tools/get_object.py` to always include a `children` array in the response using the `discover_immediate_children()` function from the previous task.

## Technical Approach
Integrate the children discovery functionality into the existing `getObject` tool by:
- Importing the new `discover_immediate_children()` function 
- Calling it after successful object retrieval
- Adding the children array to the response dictionary
- Maintaining backward compatibility with existing response structure
- Following the existing error handling patterns in `get_object.py`

## Specific Implementation Requirements

### Response Structure Enhancement
```python
# Current response structure (lines 111-117)
return {
    "yaml": yaml_dict,
    "body": body_str,
    "file_path": str(file_path),
    "kind": kind,
    "id": clean_id,
    # NEW: Add children array
    "children": children_list,  # list[dict[str, str]]
}
```

### Children Array Structure
Each child object in the array should contain:
```python
{
    "id": str,        # Clean child ID (without prefix)
    "title": str,     # Child object title from YAML
    "status": str,    # Child object status from YAML
    "kind": str,      # Child object type (epic/feature/task)
    "created": str,   # ISO timestamp from YAML
    "file_path": str  # Relative path to child file
}
```

### Integration Points
- Import: `from ..path_resolver import discover_immediate_children`
- Call after line 104: `children_list = discover_immediate_children(kind, clean_id, planning_root)`
- Add to response dict before return (line 111)
- Handle errors from children discovery gracefully

### Error Handling Strategy
- **Children Discovery Failure**: Log warning but continue with empty children array
- **No Children**: Return empty list (not null) for consistency
- **Partial Children**: Include successfully parsed children, log warnings for failures
- **Original Errors**: Preserve all existing getObject error handling behavior

## Detailed Acceptance Criteria

### Functional Requirements
- [ ] **Response Structure**: All getObject responses include `children` array field
- [ ] **Immediate Children**: Children array contains only direct child objects, not descendants
- [ ] **Complete Metadata**: Each child includes id, title, status, kind, created, file_path
- [ ] **Empty Arrays**: Parents with no children return `children: []` (not null)
- [ ] **Backward Compatibility**: All existing getObject response fields remain unchanged

### Integration Requirements
- [ ] **Error Independence**: Children discovery errors don't break getObject functionality
- [ ] **Performance Impact**: Children discovery adds < 50ms to getObject response time
- [ ] **Security Preservation**: All existing security validations remain intact
- [ ] **Type Consistency**: Response typing remains compatible with existing clients

### Parent-Child Validation
- [ ] **Projects**: Include immediate epics in children array
- [ ] **Epics**: Include immediate features in children array
- [ ] **Features**: Include immediate tasks in children array
- [ ] **Tasks**: Include empty children array (tasks have no children)

## Testing Requirements

### Unit Tests (in `tests/test_get_object_tool.py`)
- [ ] **Response Structure**: Verify children array is always present in response
- [ ] **Children Content**: Validate children array contains correct child metadata
- [ ] **Empty Children**: Test objects with no children return empty array
- [ ] **Error Isolation**: Verify children discovery errors don't break getObject
- [ ] **Performance**: Ensure enhanced getObject meets response time requirements
- [ ] **Backward Compatibility**: Verify all existing getObject tests still pass

### Integration Tests (in `tests/integration/`)
- [ ] **Full Hierarchy**: Test getObject for all parent types with various child configurations
- [ ] **Real Projects**: Test with actual project structures from test fixtures
- [ ] **Cross-System**: Test with mixed hierarchical and standalone task environments
- [ ] **Large Collections**: Test performance with parents having many children

### Test Scenarios
```python
# Key test scenarios to implement
test_scenarios = [
    # Basic functionality
    ("project_with_epics", "children array contains epic metadata"),
    ("epic_with_features", "children array contains feature metadata"),
    ("feature_with_tasks", "children array contains task metadata"),
    ("task_object", "children array is empty"),
    
    # Edge cases
    ("project_no_epics", "children array is empty list"),
    ("corrupted_child", "children array excludes corrupted child"),
    ("permission_denied_child", "children array excludes inaccessible child"),
    
    # Performance
    ("project_many_epics", "response time < 100ms"),
    ("feature_many_tasks", "response time < 200ms"),
]
```

## Documentation Requirements
- [ ] **Function Docstring**: Update getObject docstring to document children array
- [ ] **Response Examples**: Include children array in docstring examples
- [ ] **API Changes**: Document the enhancement in any API documentation
- [ ] **Migration Notes**: Ensure clients understand the new response structure

### Updated Docstring Example
```python
def getObject(...) -> dict[str, str | dict[str, str | list[str] | None] | list[dict[str, str]]]:
    """Retrieve a Trellis MCP object by kind and ID.
    
    Returns:
        Dictionary containing the object data with structure:
        {
            "yaml": dict,     # YAML front-matter as dictionary
            "body": str,      # Markdown body content  
            "file_path": str, # Path to the object file
            "kind": str,      # Object kind
            "id": str,        # Clean object ID
            "children": list[dict[str, str]]  # Immediate child objects
        }
        
    The children array contains immediate child objects only:
    - Projects: immediate epics
    - Epics: immediate features  
    - Features: immediate tasks
    - Tasks: empty array (no children)
    """
```

## Performance Requirements
- [ ] **Response Time Impact**: Children discovery adds < 50ms to getObject calls
- [ ] **Memory Efficiency**: Enhanced getObject doesn't significantly increase memory usage
- [ ] **Concurrent Safety**: Multiple simultaneous getObject calls work correctly
- [ ] **Error Performance**: Error cases (missing parent, no children) complete quickly

## Security Considerations
- [ ] **Input Validation**: All existing getObject security validations remain intact
- [ ] **Path Security**: Children discovery uses same security patterns as parent object
- [ ] **Information Disclosure**: Children array doesn't expose sensitive file system details
- [ ] **Error Security**: Children discovery errors don't reveal internal structure

## Dependencies
- Successful completion of T-create-immediate-children task
- Import of `discover_immediate_children` function from path_resolver
- Existing getObject tool error handling and validation patterns
- FastMCP tool configuration and response structure requirements

### Log


**2025-07-20T00:29:59.696281Z** - Successfully enhanced getObject tool to include children array with complete metadata. Integrated discover_immediate_children() function to add immediate child objects to all getObject responses. Implemented graceful error handling ensuring children discovery failures don't break getObject functionality. Created comprehensive unit and integration test suites covering all parent-child relationships, error scenarios, and backward compatibility. All tests pass with 100% quality checks.
- filesChanged: ["src/trellis_mcp/tools/get_object.py", "tests/unit/test_get_object_tool.py", "tests/integration/test_get_object_children_integration.py", "tests/unit/test_mcp_tool_optional_parent_simple.py"]