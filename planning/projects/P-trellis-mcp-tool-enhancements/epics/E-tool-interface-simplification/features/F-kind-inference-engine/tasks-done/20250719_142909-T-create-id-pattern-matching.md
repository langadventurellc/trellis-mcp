---
kind: task
id: T-create-id-pattern-matching
parent: F-kind-inference-engine
status: done
title: Create ID pattern matching system with regex compilation
priority: high
prerequisites: []
created: '2025-07-19T14:07:04.739108'
updated: '2025-07-19T14:12:48.907019'
schema_version: '1.1'
worktree: null
---
# Create ID Pattern Matching System with Regex Compilation

## Context

Implement the core pattern matching system for the Kind Inference Engine that recognizes object ID prefixes and maps them to appropriate object types. This task follows existing Trellis patterns found in `src/trellis_mcp/id_utils.py` and `src/trellis_mcp/schema/kind_enum.py`.

## Related Files and Patterns

**Reference existing patterns:**
- `src/trellis_mcp/schema/kind_enum.py` - KindEnum definitions
- `src/trellis_mcp/id_utils.py` - ID validation and cleaning utilities
- `src/trellis_mcp/exceptions/validation_error.py` - Error handling patterns

**New files to create:**
- `src/trellis_mcp/inference/pattern_matcher.py` - Core pattern matching logic
- `tests/test_pattern_matcher.py` - Comprehensive unit tests

## Specific Implementation Requirements

### 1. ID Prefix Pattern System
Create compiled regex patterns for efficient ID prefix recognition:
- **P-** prefix → project type
- **E-** prefix → epic type  
- **F-** prefix → feature type
- **T-** prefix → hierarchical and standalone task type

### 2. Pattern Matcher Class
Implement a `PatternMatcher` class following the existing validation patterns:
```python
class PatternMatcher:
    def __init__(self):
        # Pre-compile regex patterns for performance
        self._patterns: dict[str, re.Pattern[str]] = self._compile_patterns()
    
    def infer_kind(self, object_id: str) -> str:
        # Return KindEnum value for valid patterns
        # Raise ValidationError for invalid patterns
    
    def validate_id_format(self, object_id: str) -> bool:
        # Check if ID follows expected format patterns
```

### 3. Integration with Existing Systems
- Use existing `KindEnum` values from `src/trellis_mcp/schema/kind_enum.py`
- Follow existing error handling patterns from `src/trellis_mcp/exceptions/validation_error.py`
- Integrate with existing ID utilities from `src/trellis_mcp/id_utils.py`

## Technical Approach

### Pattern Definition Strategy
```python
# Pre-compiled regex patterns for optimal performance
HIERARCHICAL_PATTERNS = {
    KindEnum.PROJECT: re.compile(r"^P-[a-z0-9-]+$"),
    KindEnum.EPIC: re.compile(r"^E-[a-z0-9-]+$"), 
    KindEnum.FEATURE: re.compile(r"^F-[a-z0-9-]+$"),
    KindEnum.TASK: re.compile(r"^T-[a-z0-9-]+$"),
}

STANDALONE_PATTERNS = {
    KindEnum.TASK: re.compile(r"^T-[a-z0-9-]+$"),
}
```

### Error Handling Integration
- Use existing `ValidationError` with appropriate error codes
- Follow existing error message formats for consistency
- Include context information for debugging

### Performance Requirements
- Pattern compilation at initialization for < 1ms matching operations
- Support for concurrent access (thread-safe operations)
- Memory-efficient pattern storage

## Detailed Acceptance Criteria

### Pattern Recognition Accuracy
- [ ] **Hierarchical Prefixes**: Correctly identify P- → project, E- → epic, F- → feature, T- → task
- [ ] **Standalone Prefixes**: Correctly identify T- → standalone task  
- [ ] **Pattern Validation**: Reject malformed IDs (empty strings, invalid characters, wrong format)
- [ ] **Case Handling**: Support lowercase prefixes only (following existing ID patterns)
- [ ] **Edge Cases**: Handle edge cases like extra hyphens, numeric-only IDs, special characters

### Error Handling
- [ ] **Invalid Format**: Clear ValidationError with INVALID_FIELD error code
- [ ] **Empty Input**: ValidationError with MISSING_REQUIRED_FIELD error code
- [ ] **Unrecognized Pattern**: ValidationError with specific error message and correction suggestions
- [ ] **Error Context**: Include object ID and attempted operation in error context
- [ ] **Error Consistency**: Follow existing error message formats from other tools

### Performance and Reliability
- [ ] **Pattern Compilation**: Pre-compile all regex patterns during initialization
- [ ] **Matching Speed**: Complete pattern matching in < 1ms for typical IDs
- [ ] **Thread Safety**: Safe for concurrent access from multiple threads
- [ ] **Memory Efficiency**: Minimal memory footprint for pattern storage
- [ ] **Validation Integration**: Seamless integration with existing ID validation utilities

### Unit Testing Requirements
- [ ] **Pattern Coverage**: Test all supported ID prefix patterns
- [ ] **Invalid Input Testing**: Comprehensive tests for all invalid ID formats
- [ ] **Edge Case Testing**: Test boundary conditions and malformed inputs
- [ ] **Performance Testing**: Verify pattern matching meets speed requirements
- [ ] **Error Testing**: Validate all error conditions and message formats
- [ ] **Integration Testing**: Test integration with existing KindEnum and ValidationError systems

## Security Considerations

### Input Validation
- **Pattern Safety**: Ensure regex patterns are not vulnerable to ReDoS attacks
- **Input Sanitization**: Validate input parameters before pattern matching
- **Memory Safety**: Prevent excessive memory usage with malicious inputs

### Error Information Security
- **Information Disclosure**: Avoid exposing internal system details in error messages
- **Consistent Errors**: Provide consistent error responses regardless of internal state

## Dependencies

**Prerequisites:**
- Existing KindEnum definitions must remain stable
- ValidationError class interface must be available
- ID utilities must be accessible for integration

**Outputs for next tasks:**
- PatternMatcher class ready for integration with path resolution
- Comprehensive error handling for invalid ID patterns
- Performance-optimized pattern matching for validation integration

## Testing Requirements

### Unit Tests (in `tests/test_pattern_matcher.py`)
```python
def test_hierarchical_pattern_recognition():
    # Test P-, E-, F-, T- prefix recognition
    
def test_standalone_pattern_recognition():
    # Test T- prefix recognition

def test_invalid_pattern_handling():
    # Test error cases and edge conditions
    
def test_pattern_matching_performance():
    # Verify < 1ms pattern matching speed
```

This task establishes the foundational pattern matching system that will be used by subsequent path resolution and validation tasks.

### Log


**2025-07-19T19:29:09.300118Z** - Successfully implemented ID pattern matching system with regex compilation for the Kind Inference Engine. Created PatternMatcher class with pre-compiled regex patterns that achieve < 1ms performance for pattern recognition. The system correctly identifies P- (project), E- (epic), F- (feature), and T- (task) prefixes and maps them to KindEnum values. Implemented comprehensive error handling with ValidationError integration, providing clear error messages for invalid patterns, missing fields, and format issues. Added robust input validation that handles None, non-string inputs, and malformed IDs with appropriate error codes. Created extensive unit test suite covering pattern recognition accuracy, error handling, performance validation (< 1ms requirement met), edge cases, and integration with existing systems. All quality checks pass including linting, type checking, formatting, and 100% test coverage.
- filesChanged: ["src/trellis_mcp/inference/__init__.py", "src/trellis_mcp/inference/pattern_matcher.py", "tests/test_pattern_matcher.py"]