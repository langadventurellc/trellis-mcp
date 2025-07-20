---
kind: task
id: T-create-simplified-getobject-tool
parent: F-object-tool-simplification
status: done
title: Create simplified getObject tool implementation
priority: high
prerequisites: []
created: '2025-07-19T20:22:32.419774'
updated: '2025-07-19T20:26:32.445567'
schema_version: '1.1'
worktree: null
---
## Purpose

Implement a simplified getObject tool that removes the `kind` parameter and uses the kind inference engine to automatically determine object types from ID prefixes.

## Context

This task implements the core functionality for tool interface simplification as specified in F-object-tool-simplification. The existing getObject tool requires both `kind` and `id` parameters, but with the completed kind inference engine (F-kind-inference-engine), we can eliminate the explicit `kind` parameter.

**Reference files:**
- Current implementation: `src/trellis_mcp/tools/get_object.py:26-138`
- Kind inference engine: `src/trellis_mcp/inference/__init__.py:29-51` 
- Response building pattern: `src/trellis_mcp/tools/get_object.py:129-136`

**Technologies to use:**
- FastMCP for tool registration
- Existing kind inference engine (`KindInferenceEngine`)
- Pydantic Field annotations for parameter validation
- Existing path resolution and I/O utilities

## Implementation Requirements

### 1. Tool Signature Simplification
Update the tool signature from:
```python
def getObject(kind: str, id: str, projectRoot: str)
```
To:
```python  
def getObject(id: str, projectRoot: str)
```

### 2. Kind Inference Integration
- Import and use `KindInferenceEngine` from `src/trellis_mcp/inference`
- Replace manual kind validation with automatic inference
- Handle inference errors appropriately and propagate them with context

### 3. Parameter Validation Enhancement
Use Pydantic Field annotations for robust input validation:
```python
from typing import Annotated
from pydantic import Field

def getObject(
    id: Annotated[str, Field(
        description="Object ID (P-, E-, F-, T- prefixed)", 
        pattern=r"^(P-|E-|F-|T-).+",
        min_length=3
    )],
    projectRoot: Annotated[str, Field(
        description="Root directory for planning structure",
        min_length=1
    )]
)
```

### 4. Response Format Cleanup
Remove `file_path` from response and ensure inferred `kind` is included:
```python
# Current response format (REMOVE file_path):
{
    "yaml": dict,
    "body": str, 
    "file_path": str,  # REMOVE THIS
    "kind": str,       # Now inferred, not explicit parameter
    "id": str,
    "children": list
}

# New response format:
{
    "yaml": dict,
    "body": str,
    "kind": str,       # Inferred from kind inference engine
    "id": str,         # Cleaned ID
    "children": list
}
```

### 5. Error Handling Integration
- Catch and re-raise kind inference errors with additional context
- Maintain existing error handling for file operations and validation
- Ensure error messages are clear and actionable

## Detailed Implementation Steps

### Step 1: Update Tool Function Signature
1. Modify the function signature to remove `kind` parameter
2. Add Pydantic Field annotations for validation
3. Update docstring to reflect simplified interface

### Step 2: Integrate Kind Inference  
1. Import `KindInferenceEngine` from inference module
2. Create engine instance using `projectRoot`
3. Replace kind parameter validation with `engine.infer_kind(id)`
4. Handle `ValidationError` from inference and propagate with context

### Step 3: Update Response Building
1. Remove `file_path` from return dictionary
2. Use inferred kind instead of passed kind parameter  
3. Ensure all other response fields remain consistent

### Step 4: Error Handling Enhancement
1. Wrap inference errors in ValidationError with appropriate context
2. Maintain existing error handling patterns for consistency
3. Test error scenarios comprehensively

## Acceptance Criteria

### Functional Requirements
- [ ] **Simplified Interface**: Tool accepts only `id` and `projectRoot` parameters
- [ ] **Kind Inference**: Automatically detects object type from ID prefix using inference engine
- [ ] **Clean Response**: Response format excludes `file_path` and includes inferred `kind`
- [ ] **Children Discovery**: Continues to return immediate children as in current implementation  
- [ ] **Error Handling**: Clear error messages for invalid IDs and missing objects

### Performance Requirements
- [ ] **Response Time**: Complete operations in < 50ms for typical objects (same as current)
- [ ] **Inference Overhead**: Minimal additional latency from kind inference (< 10ms)
- [ ] **Memory Efficiency**: No memory leaks or excessive allocations

### Quality Requirements
- [ ] **Parameter Validation**: Robust input validation using Pydantic Field annotations
- [ ] **Error Consistency**: Error messages maintain consistency with existing tools
- [ ] **Documentation**: Updated docstring with clear usage examples and migration guidance

### Testing Requirements  
- [ ] **Valid ID Patterns**: Test all valid ID prefixes (P-, E-, F-, T-)
- [ ] **Invalid ID Patterns**: Test malformed IDs and appropriate error responses
- [ ] **Missing Objects**: Test behavior when inferred object doesn't exist
- [ ] **Response Format**: Verify clean response format without file_path
- [ ] **Children Discovery**: Ensure children discovery continues working correctly

## Security Considerations

### Input Validation
- **ID Sanitization**: Pydantic pattern validation prevents malicious ID inputs
- **Path Safety**: Kind inference engine handles path traversal protection
- **Parameter Validation**: Field annotations provide robust input validation

### Information Disclosure
- **File Path Removal**: Eliminate internal file system details from responses
- **Error Messages**: Provide helpful errors without exposing sensitive system information
- **Access Control**: Maintain existing security boundaries and permissions

## Integration Notes

### Dependencies
- Requires completed F-kind-inference-engine feature
- Uses existing path resolution utilities from `path_resolver` module
- Integrates with existing I/O utilities from `io_utils` module

### Tool Registration
- Function should be compatible with existing FastMCP registration pattern
- Tool will be registered separately in main server initialization
- Parameter schema changes require corresponding registration updates

## Files to Modify

### Primary Implementation File
- `src/trellis_mcp/tools/get_object.py` - Main implementation updates

### Testing Files
- Add tests for simplified interface in existing test files
- Verify integration with inference engine
- Test error handling scenarios

This implementation establishes the pattern for tool interface simplification that will be extended to updateObject and other tools, delivering intuitive interfaces while maintaining full system functionality.

### Log


**2025-07-20T01:36:11.149586Z** - Implemented simplified getObject tool that removes the kind parameter and uses automatic kind inference from the KindInferenceEngine. The tool now accepts only id and projectRoot parameters, automatically detects object type from ID prefixes, and returns clean response format without file_path. Added comprehensive error handling for inference failures and updated all tests to use the new simplified interface. All quality checks pass including formatting, linting, type checking, and unit tests.
- filesChanged: ["src/trellis_mcp/tools/get_object.py", "tests/unit/test_get_object_tool.py", "tests/integration/test_children_discovery_integration.py"]