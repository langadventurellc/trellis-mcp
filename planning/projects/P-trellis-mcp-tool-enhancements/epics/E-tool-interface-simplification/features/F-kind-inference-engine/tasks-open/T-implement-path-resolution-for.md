---
kind: task
id: T-implement-path-resolution-for
title: Implement path resolution for hierarchical and standalone objects
status: open
priority: high
prerequisites:
- T-create-id-pattern-matching
created: '2025-07-19T14:07:42.931082'
updated: '2025-07-19T14:07:42.931082'
schema_version: '1.1'
parent: F-kind-inference-engine
---
# Implement Path Resolution for Hierarchical and Standalone Objects

## Context

Implement path resolution logic that maps inferred object types to correct file system paths, supporting both hierarchical and standalone object structures. This task builds on the pattern matching system and follows existing path resolution patterns in `src/trellis_mcp/path_resolver.py`.

## Related Files and Patterns

**Reference existing patterns:**
- `src/trellis_mcp/path_resolver.py` - Path resolution utilities
- `src/trellis_mcp/fs_utils.py` - File system utilities  
- `src/trellis_mcp/scanner.py` - Cross-system scanning patterns
- `src/trellis_mcp/inference/pattern_matcher.py` - Pattern matching from previous task

**New files to create:**
- `src/trellis_mcp/inference/path_builder.py` - Path construction logic
- `tests/test_path_builder.py` - Unit tests for path resolution

## Specific Implementation Requirements

### 1. Path Builder Class
Create a `PathBuilder` class that constructs appropriate file paths based on inferred object types:
```python
class PathBuilder:
    def __init__(self, project_root: Path):
        self.scanning_root, self.resolution_root = resolve_project_roots(project_root)
    
    def build_object_path(self, kind: str, object_id: str) -> Path:
        # Construct path based on object type and project structure
        # Handle both hierarchical and standalone paths
    
    def validate_path_bounds(self, constructed_path: Path) -> bool:
        # Ensure path stays within project boundaries
```

### 2. Hierarchical Path Construction
Implement hierarchical path building following existing patterns:
- **Projects**: `planning/projects/P-{id}/project.md`
- **Epics**: `planning/projects/P-{parent}/epics/E-{id}/epic.md`
- **Features**: `planning/projects/P-{project}/epics/E-{epic}/features/F-{id}/feature.md`
- **Tasks**: `planning/projects/P-{project}/epics/E-{epic}/features/F-{feature}/tasks-open/T-{id}.md`

### 3. Standalone Path Construction
Implement standalone path building for standalone tasks:
- **Standalone Tasks**: `planning/tasks-open/T-{id}.md` or `planning/tasks-open/task-{id}.md`

### 4. Cross-System Path Detection
Create logic to handle mixed environments with both hierarchical and standalone objects:
- Detect project structure type dynamically
- Support projects with mixed object types
- Handle edge cases where paths might conflict

## Technical Approach

### Path Construction Strategy
```python
def build_object_path(self, kind: str, object_id: str) -> Path:
    cleaned_id = clean_prerequisite_id(object_id)
    
    if kind == KindEnum.PROJECT:
        return self.resolution_root / "projects" / f"P-{cleaned_id}" / "project.md"
    elif kind == KindEnum.EPIC:
        # Requires parent project discovery for full path
        return self._build_epic_path(cleaned_id)
    # ... additional kind handling
```

### Security and Validation
- Use existing path validation patterns from `fs_utils.py`
- Implement path traversal protection
- Validate paths stay within project boundaries

### Integration with Existing Systems
- Use existing `resolve_project_roots()` function
- Follow existing path construction patterns
- Integrate with existing ID cleaning utilities

## Detailed Acceptance Criteria

### Hierarchical Path Resolution
- [ ] **Project Paths**: Correctly construct paths for project objects (P- prefix)
- [ ] **Epic Paths**: Build epic paths within correct project structure  
- [ ] **Feature Paths**: Construct feature paths within correct epic/project hierarchy
- [ ] **Task Paths**: Build hierarchical task paths within correct feature/epic/project structure
- [ ] **Parent Discovery**: Automatically discover parent relationships for path construction

### Standalone Path Resolution
- [ ] **Standalone Task Paths**: Correctly construct paths for standalone tasks (task- prefix)
- [ ] **Root Level Placement**: Place standalone tasks at appropriate root level locations
- [ ] **ID Format Handling**: Support both T- and task- prefixed standalone tasks
- [ ] **Conflict Avoidance**: Avoid path conflicts between hierarchical and standalone objects

### Cross-System Compatibility
- [ ] **Mixed Environment Support**: Handle projects with both hierarchical and standalone objects
- [ ] **Dynamic Detection**: Automatically detect project structure type
- [ ] **Path Uniqueness**: Ensure path uniqueness across hierarchical and standalone systems
- [ ] **Edge Case Handling**: Handle edge cases like missing parent objects
- [ ] **Graceful Degradation**: Provide reasonable fallbacks when path construction fails

### Security and Validation
- [ ] **Path Boundary Validation**: Ensure all constructed paths stay within project boundaries
- [ ] **Path Traversal Protection**: Prevent directory traversal attacks through malicious IDs
- [ ] **Input Sanitization**: Validate and sanitize all input parameters
- [ ] **Error Handling**: Provide clear errors for invalid path construction attempts
- [ ] **Permission Respect**: Honor existing file system permissions and constraints

### Performance Requirements
- [ ] **Path Construction Speed**: Complete path construction in < 5ms for typical objects
- [ ] **Memory Efficiency**: Minimal memory usage for path building operations
- [ ] **Caching Integration**: Prepare for integration with caching system
- [ ] **Concurrent Safety**: Safe for concurrent access from multiple threads

## Implementation Guidance

### Path Building Algorithm
1. **Clean ID**: Use existing ID cleaning utilities to normalize object ID
2. **Determine Structure**: Detect if project uses hierarchical or standalone structure
3. **Build Base Path**: Construct appropriate base path based on object type
4. **Validate Bounds**: Ensure constructed path stays within project boundaries
5. **Return Path**: Provide complete, validated file path

### Error Handling Strategy
- **Invalid Kind**: ValidationError with INVALID_FIELD error code for unsupported object types
- **Path Traversal**: ValidationError with security-specific error message
- **Missing Context**: ValidationError when required parent information is unavailable
- **Boundary Violation**: ValidationError when path exceeds project boundaries

### Integration Points
- **Pattern Matcher**: Use inferred kind from pattern matching system
- **Existing Utilities**: Leverage existing path resolution and ID cleaning functions
- **Validation System**: Integrate with existing ValidationError patterns
- **Security Framework**: Follow existing security validation patterns

## Testing Requirements

### Unit Tests (in `tests/test_path_builder.py`)
```python
def test_hierarchical_path_construction():
    # Test path building for all hierarchical object types
    
def test_standalone_path_construction():
    # Test standalone task path building
    
def test_cross_system_path_handling():
    # Test mixed environment path construction
    
def test_path_security_validation():
    # Test path traversal protection and boundary validation
    
def test_path_construction_performance():
    # Verify < 5ms path construction speed
    
def test_integration_with_pattern_matcher():
    # Test integration with pattern matching system
```

### Integration Tests
```python
def test_real_project_path_construction():
    # Test with actual project directory structures
    
def test_mixed_environment_scenarios():
    # Test projects with both hierarchical and standalone objects
```

## Security Considerations

### Path Security
- **Traversal Protection**: Prevent `../` and similar path traversal attempts
- **Boundary Validation**: Ensure paths remain within designated project directories
- **Input Validation**: Sanitize all input parameters before path construction

### Error Information Security
- **Information Disclosure**: Avoid exposing sensitive file system details in errors
- **Consistent Response**: Provide consistent error formats regardless of internal structure

## Dependencies

**Prerequisites:**
- Pattern matching system from previous task must be complete
- Existing path resolution utilities must be available
- KindEnum and ValidationError systems must be stable

**Outputs for next tasks:**
- PathBuilder class ready for integration with file system validation
- Comprehensive path construction for all object types
- Security-validated path building for validation integration

This task provides the essential path resolution infrastructure needed for the file system validation and caching components of the Kind Inference Engine.

### Log

