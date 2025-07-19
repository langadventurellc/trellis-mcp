---
kind: task
id: T-create-file-system-validation
title: Create file system validation with metadata consistency checking
status: open
priority: high
prerequisites:
- T-implement-path-resolution-for
created: '2025-07-19T14:08:25.465913'
updated: '2025-07-19T14:08:25.465913'
schema_version: '1.1'
parent: F-kind-inference-engine
---
# Create File System Validation with Metadata Consistency Checking

## Context

Implement file system validation that verifies inferred object types match actual objects on disk, including YAML metadata consistency checking. This task builds on the path resolution system and follows existing validation patterns in `src/trellis_mcp/validation/`.

## Related Files and Patterns

**Reference existing patterns:**
- `src/trellis_mcp/validation/` - Existing validation framework
- `src/trellis_mcp/parser.py` - Object parsing and metadata extraction
- `src/trellis_mcp/schema/` - Object schema definitions
- `src/trellis_mcp/inference/path_builder.py` - Path resolution from previous task

**New files to create:**
- `src/trellis_mcp/inference/validator.py` - File system validation logic
- `tests/test_inference_validator.py` - Unit tests for validation

## Specific Implementation Requirements

### 1. File System Validator Class
Create a `FileSystemValidator` class that verifies inferred types against actual files:
```python
class FileSystemValidator:
    def __init__(self, path_builder: PathBuilder):
        self.path_builder = path_builder
    
    def validate_object_exists(self, kind: str, object_id: str) -> bool:
        # Check if object file exists at inferred path
    
    def validate_type_consistency(self, kind: str, object_id: str) -> bool:
        # Verify YAML metadata matches inferred type
    
    def validate_object_structure(self, kind: str, object_id: str) -> ValidationResult:
        # Complete validation with detailed results
```

### 2. Metadata Consistency Checking
Implement YAML metadata validation following existing patterns:
- Parse object YAML front-matter using existing parser utilities
- Verify `kind` field matches inferred type
- Validate object structure against schema definitions
- Check for required fields and data consistency

### 3. Cross-System Validation
Support validation across both hierarchical and standalone systems:
- Handle both hierarchical and standalone task validation
- Verify parent-child relationships where applicable
- Validate cross-references and dependencies
- Support mixed project environments

### 4. Validation Result Structure
Create comprehensive validation results following existing error patterns:
```python
@dataclass
class ValidationResult:
    is_valid: bool
    object_exists: bool
    type_matches: bool
    metadata_valid: bool
    errors: list[str]
    warnings: list[str]
```

## Technical Approach

### Validation Pipeline
```python
def validate_object_structure(self, kind: str, object_id: str) -> ValidationResult:
    # 1. Check file existence
    path = self.path_builder.build_object_path(kind, object_id)
    if not path.exists():
        return ValidationResult(is_valid=False, object_exists=False, ...)
    
    # 2. Parse object metadata
    try:
        obj = parse_object(path)
    except Exception as e:
        return ValidationResult(is_valid=False, metadata_valid=False, ...)
    
    # 3. Verify type consistency
    if obj.kind != kind:
        return ValidationResult(is_valid=False, type_matches=False, ...)
    
    # 4. Validate schema compliance
    # ... additional validation steps
    
    return ValidationResult(is_valid=True, ...)
```

### Integration with Existing Systems
- Use existing `parse_object()` function from parser module
- Leverage existing schema validation from `src/trellis_mcp/schema/`
- Follow existing ValidationError patterns for error reporting
- Integrate with existing file system utilities

### Performance Optimization
- Cache validation results for frequently accessed objects
- Minimize file system operations through efficient checks
- Support concurrent validation requests

## Detailed Acceptance Criteria

### File System Validation
- [ ] **Object Existence**: Accurately verify if object files exist at inferred paths
- [ ] **Path Accuracy**: Validate that inferred paths correspond to actual object files
- [ ] **File Access**: Handle file permission and access errors gracefully
- [ ] **Path Security**: Ensure validation stays within project boundaries
- [ ] **Cross-System Support**: Validate both hierarchical and standalone objects

### Metadata Consistency Checking
- [ ] **YAML Parsing**: Successfully parse object YAML front-matter
- [ ] **Kind Verification**: Verify object `kind` field matches inferred type
- [ ] **Schema Compliance**: Validate objects against existing schema definitions
- [ ] **Required Fields**: Check for presence of all required metadata fields
- [ ] **Data Type Validation**: Verify field data types match schema requirements

### Error Handling and Reporting
- [ ] **File Not Found**: Clear error messages when object files don't exist
- [ ] **Parse Errors**: Detailed errors for malformed YAML or object structure
- [ ] **Type Mismatch**: Specific errors when inferred type doesn't match actual type
- [ ] **Schema Violations**: Clear messages for schema validation failures
- [ ] **Permission Errors**: Graceful handling of file system permission issues

### Performance and Reliability
- [ ] **Validation Speed**: Complete validation in < 20ms for typical objects
- [ ] **Memory Efficiency**: Minimal memory usage during validation operations
- [ ] **Error Recovery**: Graceful handling of corrupted or malformed objects
- [ ] **Concurrent Safety**: Safe for concurrent validation requests
- [ ] **Resource Management**: Proper cleanup of file handles and resources

### Integration Requirements
- [ ] **Parser Integration**: Seamless integration with existing object parser
- [ ] **Schema Integration**: Use existing schema definitions for validation
- [ ] **Error System Integration**: Follow existing ValidationError patterns
- [ ] **Path Builder Integration**: Correctly use path resolution from previous task
- [ ] **Type System Integration**: Work with existing KindEnum and type definitions

## Implementation Guidance

### Validation Algorithm
1. **Build Path**: Use PathBuilder to construct object file path
2. **Check Existence**: Verify file exists and is accessible
3. **Parse Object**: Use existing parser to extract metadata
4. **Verify Type**: Compare inferred kind with actual object kind
5. **Validate Schema**: Check object structure against schema definitions
6. **Return Results**: Provide comprehensive validation results

### Error Handling Strategy
- **File Access Errors**: Map to appropriate ValidationError codes
- **Parse Failures**: Provide detailed context about parsing issues
- **Type Mismatches**: Clear explanation of expected vs actual types
- **Schema Violations**: Specific field-level validation errors

### Caching Strategy (for future integration)
- Design validation results structure to support caching
- Include cache invalidation hooks for file modification times
- Prepare for integration with existing cache infrastructure

## Testing Requirements

### Unit Tests (in `tests/test_inference_validator.py`)
```python
def test_valid_object_validation():
    # Test validation of correctly structured objects
    
def test_object_not_found_handling():
    # Test error handling when object files don't exist
    
def test_type_mismatch_detection():
    # Test detection of inferred vs actual type mismatches
    
def test_metadata_consistency_checking():
    # Test YAML metadata validation and schema compliance
    
def test_cross_system_validation():
    # Test validation across hierarchical and standalone systems
    
def test_validation_performance():
    # Verify < 20ms validation speed requirements
    
def test_malformed_object_handling():
    # Test graceful handling of corrupted or malformed objects
```

### Integration Tests
```python
def test_real_project_validation():
    # Test validation with actual project structures
    
def test_parser_integration():
    # Test integration with existing object parser
    
def test_schema_validation_integration():
    # Test integration with existing schema validation
```

## Security Considerations

### File System Security
- **Path Validation**: Ensure validation operations stay within project boundaries
- **Permission Respect**: Honor existing file system permissions
- **Access Control**: Prevent unauthorized access to system files
- **Resource Limits**: Prevent excessive resource consumption during validation

### Error Information Security
- **Information Disclosure**: Avoid exposing sensitive file system details
- **Consistent Errors**: Provide consistent error formats regardless of internal state
- **Path Safety**: Don't expose internal path structures in error messages

## Dependencies

**Prerequisites:**
- Path resolution system from previous task must be complete
- Existing parser and schema validation systems must be available
- ValidationError and type system must be stable

**Outputs for next tasks:**
- FileSystemValidator class ready for integration with inference engine
- Comprehensive validation results for type verification
- Performance-optimized validation for caching integration

## Integration Points

### With Existing Systems
- **Parser Module**: Use existing `parse_object()` for metadata extraction
- **Schema System**: Leverage existing schema validation framework
- **Error System**: Follow existing ValidationError patterns and codes
- **Type System**: Integrate with KindEnum and existing type definitions

### With Kind Inference Engine
- **Validation Pipeline**: Integrate as validation step in inference process
- **Error Propagation**: Provide detailed validation errors for inference failures
- **Performance Integration**: Optimize for integration with caching system

This task provides the essential validation infrastructure that ensures the Kind Inference Engine's type inferences are accurate and reliable.

### Log

