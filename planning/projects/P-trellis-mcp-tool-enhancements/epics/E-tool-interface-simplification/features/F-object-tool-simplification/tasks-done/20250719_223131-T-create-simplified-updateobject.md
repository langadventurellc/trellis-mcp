---
kind: task
id: T-create-simplified-updateobject
parent: F-object-tool-simplification
status: done
title: Create simplified updateObject tool implementation
priority: high
prerequisites:
- T-create-simplified-getobject-tool
created: '2025-07-19T20:23:13.966668'
updated: '2025-07-19T21:36:37.759816'
schema_version: '1.1'
worktree: null
---
## Purpose

Implement a simplified updateObject tool that removes the `kind` parameter and uses the kind inference engine to automatically determine object types from ID prefixes, following the pattern established in the simplified getObject tool.

## Context

This task builds on the simplified getObject implementation and applies the same interface simplification principles to the updateObject tool. The existing updateObject tool requires a `kind` parameter, but with the kind inference engine, this can be eliminated.

**Reference files:**
- Current implementation: `src/trellis_mcp/tools/update_object.py:72-421`
- Simplified getObject pattern: Task T-create-simplified-getobject-tool  
- Kind inference engine: `src/trellis_mcp/inference/__init__.py:29-51`
- Response building: `src/trellis_mcp/tools/update_object.py:412-419`

**Technologies to use:**
- FastMCP for tool registration
- Kind inference engine (`KindInferenceEngine`)
- Pydantic Field annotations for parameter validation
- Existing validation and I/O utilities

## Implementation Requirements

### 1. Tool Signature Simplification
Update the tool signature from:
```python
def updateObject(kind: str, id: str, projectRoot: str, yamlPatch: dict, bodyPatch: str, force: bool)
```
To:
```python
def updateObject(id: str, projectRoot: str, yamlPatch: dict, bodyPatch: str, force: bool)
```

### 2. Kind Inference Integration
- Import and use `KindInferenceEngine` from `src/trellis_mcp/inference`
- Replace manual kind validation with automatic inference at the start of the function
- Handle inference errors and propagate them with appropriate context
- Use inferred kind throughout the rest of the function logic

### 3. Parameter Validation Enhancement  
Use Pydantic Field annotations for robust input validation:
```python
from typing import Annotated
from pydantic import Field

def updateObject(
    id: Annotated[str, Field(
        description="Object ID (P-, E-, F-, T- prefixed)",
        pattern=r"^(P-|E-|F-|T-).+", 
        min_length=3
    )],
    projectRoot: Annotated[str, Field(
        description="Root directory for planning structure",
        min_length=1
    )],
    yamlPatch: Annotated[dict[str, str | list[str] | None], Field(
        description="YAML fields to update/merge",
        default={}
    )],
    bodyPatch: Annotated[str, Field(
        description="New body content to replace existing body", 
        default=""
    )],
    force: Annotated[bool, Field(
        description="Bypass safeguards when deleting objects with protected children",
        default=False
    )]
)
```

### 4. Response Format Cleanup
Remove `file_path` from response and ensure inferred `kind` is included:
```python
# Current response format (REMOVE file_path):
{
    "id": str,
    "kind": str,
    "file_path": str,    # REMOVE THIS
    "updated": str,
    "changes": dict
}

# New response format:
{
    "id": str,
    "kind": str,         # Now inferred, not explicit parameter  
    "updated": str,
    "changes": dict
}
```

### 5. Preserve All Existing Logic
- **Atomic Operations**: Maintain all existing atomic update logic
- **Validation Pipeline**: Keep all existing validation (front-matter, object data, status transitions)
- **Cascade Deletion**: Preserve cascade deletion logic when status="deleted"
- **Protected Objects**: Maintain protected object handling with force parameter
- **Dependency Validation**: Keep acyclic prerequisite validation
- **Error Handling**: Preserve all existing error handling patterns

## Detailed Implementation Steps

### Step 1: Update Tool Function Signature
1. Remove `kind` parameter from function signature
2. Add Pydantic Field annotations for all parameters
3. Update docstring to reflect simplified interface
4. Update type hints for return value

### Step 2: Integrate Kind Inference
1. Import `KindInferenceEngine` from inference module
2. Add kind inference at the beginning of the function (after basic parameter validation)
3. Replace all uses of `kind` parameter with inferred kind value
4. Handle `ValidationError` from inference and wrap with appropriate context

### Step 3: Update Validation Integration
1. Ensure inferred kind is used in all validation calls:
   - `validate_front_matter(updated_yaml, kind)` → use inferred kind
   - `validate_object_data(updated_yaml, planning_root)` → uses inferred paths
   - `enforce_status_transition(original_status, new_status, kind)` → use inferred kind
2. Update error context to include inferred kind information

### Step 4: Update Response Building
1. Remove `file_path` from return dictionary in all return statements
2. Use inferred kind in response building
3. Ensure cascade deletion response also excludes file_path

### Step 5: Error Handling Enhancement  
1. Add kind inference error handling at function start
2. Update all error context dictionaries to use inferred kind
3. Maintain existing error message formats and codes

## Acceptance Criteria

### Functional Requirements
- [ ] **Simplified Interface**: Tool accepts `id`, `projectRoot`, and optional patch parameters
- [ ] **Kind Inference**: Automatically detects object type from ID prefix
- [ ] **Clean Response**: Response format excludes `file_path` and includes inferred `kind` 
- [ ] **Atomic Updates**: All update operations remain atomic (complete or rollback)
- [ ] **Validation Preservation**: All existing validation logic continues working
- [ ] **Cascade Deletion**: Protected object validation and cascade deletion work correctly
- [ ] **Dependency Validation**: Acyclic prerequisite validation continues working

### Performance Requirements
- [ ] **Response Time**: Complete operations in < 100ms for typical updates (same as current)
- [ ] **Inference Overhead**: Minimal additional latency from kind inference (< 10ms)
- [ ] **Memory Efficiency**: No performance degradation from interface changes

### Quality Requirements
- [ ] **Parameter Validation**: Robust input validation using Pydantic Field annotations
- [ ] **Error Consistency**: Error messages maintain consistency with existing patterns
- [ ] **Backward Compatibility**: Existing update logic remains fully functional
- [ ] **Documentation**: Updated docstring with clear migration guidance

### Testing Requirements
- [ ] **Valid ID Patterns**: Test all valid ID prefixes with updates
- [ ] **Invalid ID Patterns**: Test malformed IDs and appropriate error responses  
- [ ] **Missing Objects**: Test behavior when inferred object doesn't exist
- [ ] **Response Format**: Verify clean response format without file_path
- [ ] **Update Operations**: Test YAML patch and body patch operations
- [ ] **Status Transitions**: Test valid and invalid status transitions
- [ ] **Cascade Deletion**: Test protected object validation and cascade deletion
- [ ] **Dependency Validation**: Test prerequisite updates and cycle detection

## Security Considerations

### Input Validation
- **ID Sanitization**: Pydantic pattern validation prevents malicious ID inputs
- **Patch Validation**: Maintain existing validation for YAML and body patches
- **Parameter Validation**: Field annotations provide comprehensive input validation

### Information Disclosure
- **File Path Removal**: Eliminate internal file system details from responses
- **Error Context**: Provide helpful errors without exposing sensitive system information
- **Access Control**: Maintain all existing security boundaries and permission checks

### Operation Safety
- **Atomic Updates**: Preserve atomic operation guarantees
- **Rollback Safety**: Maintain safe rollback capabilities for failed operations
- **Validation Integrity**: Keep all validation checks to prevent invalid state

## Integration Notes

### Dependencies
- Requires completed simplified getObject implementation for pattern consistency
- Uses kind inference engine from F-kind-inference-engine feature  
- Integrates with existing validation and I/O utilities

### Consistency Requirements
- Must follow same interface patterns as simplified getObject
- Error handling should be consistent across both simplified tools
- Response formats should be aligned between getObject and updateObject

## Files to Modify

### Primary Implementation File
- `src/trellis_mcp/tools/update_object.py` - Main implementation updates

### Testing Files
- Add tests for simplified interface in existing test files
- Verify integration with inference engine
- Test complex update scenarios and edge cases

## Complex Logic Areas Requiring Attention

### 1. Cascade Deletion Logic (lines 280-357)
- Ensure inferred kind is used correctly in protected children validation
- Maintain file_path removal from cascade deletion responses
- Test cascade deletion with inferred object types

### 2. Dependency Graph Validation (lines 365-403)  
- Verify dependency graph building works with inferred kinds
- Ensure rollback logic uses correct inferred paths
- Test circular dependency detection with simplified interface

### 3. Deep Merge Dictionary Logic (lines 28-58)
- No changes needed, but test integration with simplified interface
- Ensure YAML patch operations work correctly with inferred kinds

This implementation extends the tool interface simplification pattern to updateObject, delivering the complete simplified tool suite while maintaining all existing functionality and reliability guarantees.

### Log


**2025-07-20T03:31:31.056356Z** - Completed simplified updateObject tool implementation by enhancing Pydantic parameter validation. The tool was already mostly implemented with kind inference integration, simplified interface, and clean response format. Added missing regex pattern validation (^(P-|E-|F-|T-).+), updated minimum length to 3, and corrected ID field description to require prefixed format. All quality checks pass with 1780 tests passing, ensuring robust input validation while maintaining all existing functionality.
- filesChanged: ["src/trellis_mcp/tools/update_object.py"]