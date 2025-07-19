---
kind: task
id: T-create-kind-inference-engine-api
parent: F-kind-inference-engine
status: done
title: Create kind inference engine API with error handling
priority: high
prerequisites:
- T-implement-lru-cache-for
created: '2025-07-19T14:10:04.869598'
updated: '2025-07-19T15:36:09.615294'
schema_version: '1.1'
worktree: null
---
# Create Kind Inference Engine API with Error Handling

## Context

Create the main Kind Inference Engine API that integrates all previous components (pattern matching, path resolution, validation, and caching) into a cohesive, easy-to-use interface. This task follows existing tool patterns in `src/trellis_mcp/tools/` and creates the public API for simplified tool integration.

## Related Files and Patterns

**Reference existing patterns:**
- `src/trellis_mcp/tools/` - Existing tool implementation patterns
- `src/trellis_mcp/inference/pattern_matcher.py` - Pattern matching from previous tasks
- `src/trellis_mcp/inference/path_builder.py` - Path resolution from previous tasks  
- `src/trellis_mcp/inference/validator.py` - Validation from previous tasks
- `src/trellis_mcp/inference/cache.py` - Caching from previous tasks

**New files to create:**
- `src/trellis_mcp/inference/engine.py` - Main inference engine API
- `src/trellis_mcp/inference/__init__.py` - Package initialization with public API
- `tests/test_inference_engine.py` - Integration tests for complete engine

## Specific Implementation Requirements

### 1. Kind Inference Engine Class
Create a `KindInferenceEngine` class that orchestrates all inference components:
```python
class KindInferenceEngine:
    def __init__(self, project_root: str | Path, cache_size: int = 1000):
        self.project_root = Path(project_root)
        self.pattern_matcher = PatternMatcher()
        self.path_builder = PathBuilder(self.project_root)
        self.validator = FileSystemValidator(self.path_builder)
        self.cache = InferenceCache(cache_size)
    
    def infer_kind(self, object_id: str, validate: bool = True) -> str:
        # Main inference API - returns KindEnum value
    
    def infer_with_validation(self, object_id: str) -> InferenceResult:
        # Extended API with full validation results
    
    def validate_object(self, object_id: str, expected_kind: str | None = None) -> ValidationResult:
        # Validation-only API for existing objects
```

### 2. Public API Design
Create a clean public API following existing tool patterns:
- Simple `infer_kind()` function for basic usage
- Extended `infer_with_validation()` for comprehensive results
- Error handling with existing ValidationError patterns
- Optional validation control for performance optimization

### 3. Error Handling Integration
Implement comprehensive error handling following existing patterns:
- Use existing ValidationError class with appropriate error codes
- Provide clear, actionable error messages with context
- Handle all error conditions from underlying components
- Support error recovery and graceful degradation

### 4. Performance Integration
Integrate caching and performance optimizations:
- Cache inference results for repeated operations
- Optimize for common usage patterns
- Support batch operations for efficiency
- Provide performance monitoring and statistics

## Technical Approach

### Main Inference Algorithm
```python
def infer_kind(self, object_id: str, validate: bool = True) -> str:
    # 1. Check cache first
    cached_result = self.cache.get(object_id)
    if cached_result and cached_result.is_valid:
        return cached_result.inferred_kind
    
    # 2. Pattern matching
    try:
        inferred_kind = self.pattern_matcher.infer_kind(object_id)
    except ValidationError:
        # Re-raise pattern matching errors
        raise
    
    # 3. Optional validation
    if validate:
        validation_result = self.validator.validate_object_structure(
            inferred_kind, object_id
        )
        if not validation_result.is_valid:
            raise ValidationError(
                errors=validation_result.errors,
                error_codes=[ValidationErrorCode.INVALID_FIELD],
                context={"object_id": object_id, "inferred_kind": inferred_kind}
            )
    
    # 4. Cache result
    inference_result = InferenceResult(
        object_id=object_id,
        inferred_kind=inferred_kind,
        is_valid=True,
        cached_at=time.time()
    )
    self.cache.put(object_id, inference_result)
    
    return inferred_kind
```

### Error Handling Strategy
- **Pattern Errors**: Re-raise with additional context
- **Validation Errors**: Aggregate validation failures with clear messages
- **System Errors**: Convert to appropriate ValidationError instances
- **Cache Errors**: Graceful degradation without affecting inference

### Integration Orchestration
- Coordinate all inference components through single interface
- Handle component initialization and dependency management
- Provide lifecycle management for long-lived instances
- Support configuration and customization options

## Detailed Acceptance Criteria

### Core Inference API
- [ ] **Basic Inference**: `infer_kind()` returns correct KindEnum values for valid IDs
- [ ] **Performance Target**: Complete inference in < 10ms for typical objects
- [ ] **Cache Integration**: Use cached results when available and valid
- [ ] **Error Propagation**: Clear error messages for all failure scenarios
- [ ] **Optional Validation**: Support disabling validation for performance optimization

### Extended Inference API
- [ ] **Comprehensive Results**: `infer_with_validation()` returns complete InferenceResult
- [ ] **Validation Details**: Include detailed validation results in extended API
- [ ] **Performance Metrics**: Provide timing and cache statistics
- [ ] **Error Context**: Rich error context for debugging and troubleshooting
- [ ] **Batch Support**: Efficient processing of multiple inference requests

### Error Handling
- [ ] **Pattern Matching Errors**: Clear errors for invalid ID patterns with examples
- [ ] **Validation Errors**: Detailed errors when objects don't match inferred types
- [ ] **File System Errors**: Graceful handling of missing files or permission issues
- [ ] **System Errors**: Appropriate error mapping for all underlying component failures
- [ ] **Error Recovery**: Graceful degradation when components fail

### Performance and Reliability
- [ ] **Response Time**: < 10ms for inference operations (including validation)
- [ ] **Cache Hit Performance**: < 1ms for cached results
- [ ] **Memory Efficiency**: Reasonable memory usage for engine instances
- [ ] **Concurrent Safety**: Thread-safe operations for concurrent access
- [ ] **Resource Management**: Proper cleanup and resource management

### Integration Requirements
- [ ] **Component Integration**: Seamless integration of all inference components
- [ ] **Configuration Support**: Configurable cache size and validation behavior
- [ ] **Monitoring Integration**: Support for performance monitoring and statistics
- [ ] **Tool Integration**: Ready for integration with simplified getObject/updateObject tools
- [ ] **API Stability**: Stable public API suitable for long-term usage

## Implementation Guidance

### Component Initialization
```python
def __init__(self, project_root: str | Path, cache_size: int = 1000):
    self.project_root = Path(project_root)
    
    # Initialize components in dependency order
    self.pattern_matcher = PatternMatcher()
    self.path_builder = PathBuilder(self.project_root)
    self.validator = FileSystemValidator(self.path_builder)
    self.cache = InferenceCache(cache_size)
    
    # Validate project root accessibility
    if not self.project_root.exists():
        raise ValidationError(
            errors=[f"Project root does not exist: {self.project_root}"],
            error_codes=[ValidationErrorCode.INVALID_FIELD],
            context={"project_root": str(self.project_root)}
        )
```

### Public Package API (in `__init__.py`)
```python
from .engine import KindInferenceEngine
from .pattern_matcher import PatternMatcher
from .cache import InferenceResult

# Public API
__all__ = [
    "KindInferenceEngine",
    "InferenceResult",
    # Expose main functions for convenience
    "infer_kind",
    "infer_with_validation",
]

# Convenience functions
def infer_kind(object_id: str, project_root: str | Path, validate: bool = True) -> str:
    """Convenience function for one-off kind inference."""
    engine = KindInferenceEngine(project_root)
    return engine.infer_kind(object_id, validate)
```

### Error Context Enhancement
- Include object ID, project root, and operation context in all errors
- Provide suggestions for common error scenarios
- Include validation details when available
- Support error aggregation for batch operations

## Testing Requirements

### Unit Tests (in `tests/test_inference_engine.py`)
```python
def test_basic_kind_inference():
    # Test basic infer_kind() functionality
    
def test_inference_with_validation():
    # Test extended API with validation results
    
def test_cache_integration():
    # Test cache hit/miss behavior
    
def test_error_handling():
    # Test all error scenarios and edge cases
    
def test_performance_requirements():
    # Verify < 10ms inference speed
    
def test_concurrent_access():
    # Test thread safety with concurrent operations
    
def test_component_integration():
    # Test integration of all inference components
```

### Integration Tests
```python
def test_real_project_inference():
    # Test with actual project structures
    
def test_mixed_environment_inference():
    # Test projects with both hierarchical and standalone objects
    
def test_tool_integration_readiness():
    # Test readiness for integration with simplified tools
```

### Performance Tests
```python
def test_inference_performance_under_load():
    # Test performance with high-frequency operations
    
def test_cache_effectiveness():
    # Test cache hit rates and performance impact
```

## Security Considerations

### API Security
- **Input Validation**: Validate all API parameters before processing
- **Path Safety**: Ensure all operations stay within project boundaries
- **Error Information**: Avoid exposing sensitive system details in errors
- **Resource Limits**: Prevent resource exhaustion through malicious usage

### Component Security
- **Access Control**: Respect existing file system permissions
- **Memory Safety**: Prevent memory exhaustion through cache or component misuse
- **Error Isolation**: Prevent component errors from affecting system stability

## Dependencies

**Prerequisites:**
- All previous inference component tasks must be complete
- Existing ValidationError and type systems must be stable
- Tool integration patterns must be established

**Outputs for simplified tools:**
- Complete KindInferenceEngine ready for tool integration
- Stable public API for getObject/updateObject simplification
- Performance-optimized inference suitable for production usage

## Integration Points

### With Simplified Tools
- **Direct Integration**: Ready for use in simplified getObject/updateObject tools
- **Error Compatibility**: Compatible with existing tool error handling patterns
- **Performance Suitable**: Optimized for high-frequency tool operations

### With Existing Systems
- **Validation Integration**: Uses existing ValidationError and type systems
- **Configuration Integration**: Supports existing configuration patterns
- **Monitoring Integration**: Ready for integration with existing monitoring systems

This task completes the Kind Inference Engine by providing a production-ready API that integrates all inference components and is ready for use by the simplified tool interfaces.

### Log


**2025-07-19T20:45:46.962787Z** - Implemented the main Kind Inference Engine API that integrates all inference components (pattern matching, path resolution, validation, and caching) into a production-ready interface for simplified tool integration. Created KindInferenceEngine class with infer_kind(), infer_with_validation(), and validate_object() methods. Added comprehensive error handling, cache integration, and performance optimization. Includes full test coverage with component integration tests and error scenario validation. All quality checks pass including format, lint, type check, and 1665 tests.
- filesChanged: ["src/trellis_mcp/inference/engine.py", "src/trellis_mcp/inference/__init__.py", "tests/test_inference_engine.py"]