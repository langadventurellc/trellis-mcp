---
kind: task
id: T-implement-lru-cache-for
title: Implement LRU cache for inference results with invalidation
status: open
priority: normal
prerequisites:
- T-create-file-system-validation
created: '2025-07-19T14:09:12.366466'
updated: '2025-07-19T14:09:12.366466'
schema_version: '1.1'
parent: F-kind-inference-engine
---
# Implement LRU Cache for Inference Results with Invalidation

## Context

Implement a high-performance LRU cache for inference results to optimize repeated kind inference operations. This task follows existing caching patterns in `src/trellis_mcp/validation/cache.py` and integrates with the file system validation system.

## Related Files and Patterns

**Reference existing patterns:**
- `src/trellis_mcp/validation/cache.py` - Existing cache implementation patterns
- `src/trellis_mcp/inference/validator.py` - File system validation from previous task
- Python `functools.lru_cache` - Standard library LRU cache patterns

**New files to create:**
- `src/trellis_mcp/inference/cache.py` - Inference result caching system
- `tests/test_inference_cache.py` - Unit tests for caching functionality

## Specific Implementation Requirements

### 1. Inference Result Cache Class
Create an `InferenceCache` class following existing cache patterns:
```python
class InferenceCache:
    def __init__(self, max_size: int = 1000):
        self._cache: dict[str, tuple[InferenceResult, float]] = {}
        self._access_order: list[str] = []
        self.max_size = max_size
    
    def get(self, object_id: str) -> InferenceResult | None:
        # Retrieve cached result if valid
    
    def put(self, object_id: str, result: InferenceResult) -> None:
        # Cache result with LRU eviction
    
    def invalidate(self, object_id: str) -> None:
        # Remove specific entry from cache
    
    def clear(self) -> None:
        # Clear entire cache
```

### 2. Cache Invalidation Strategy
Implement intelligent cache invalidation following existing patterns:
- **File modification time tracking** using existing patterns from `DependencyGraphCache`
- **Selective invalidation** for specific object IDs
- **Bulk invalidation** for project-wide changes
- **Automatic cleanup** of stale entries

### 3. Inference Result Structure
Define cacheable inference results:
```python
@dataclass
class InferenceResult:
    object_id: str
    inferred_kind: str
    is_valid: bool
    cached_at: float
    validation_result: ValidationResult | None = None
```

### 4. Integration with Validation System
- Cache validation results alongside inference results
- Implement cache invalidation based on file system changes
- Support partial result caching for performance optimization

## Technical Approach

### LRU Implementation Strategy
```python
def get(self, object_id: str) -> InferenceResult | None:
    if object_id not in self._cache:
        return None
    
    result, cached_time = self._cache[object_id]
    
    # Check if cache entry is still valid
    if self._is_cache_valid(object_id, cached_time):
        # Update access order for LRU
        self._access_order.remove(object_id)
        self._access_order.append(object_id)
        return result
    else:
        # Remove stale entry
        self.invalidate(object_id)
        return None
```

### Cache Validation Logic
Follow existing patterns for file modification time checking:
- Use tolerance-based comparison (1ms) for filesystem timestamp resolution
- Check both object file and related dependency files
- Implement efficient validation without excessive file system calls

### Memory Management
- Implement LRU eviction when cache exceeds max_size
- Efficient memory usage with appropriate data structures
- Cleanup of stale references and circular dependencies

## Detailed Acceptance Criteria

### LRU Cache Functionality
- [ ] **Cache Hit Performance**: < 1ms for cache hit operations
- [ ] **Cache Miss Handling**: Proper handling when items not in cache
- [ ] **LRU Eviction**: Correct eviction of least recently used items when cache is full
- [ ] **Cache Size Management**: Maintain cache size within configured limits
- [ ] **Access Order Tracking**: Accurate tracking of item access patterns for LRU

### Cache Invalidation
- [ ] **File Change Detection**: Invalidate cache when object files are modified
- [ ] **Selective Invalidation**: Remove specific entries without affecting others
- [ ] **Bulk Invalidation**: Support clearing entire cache or project-specific entries
- [ ] **Automatic Cleanup**: Remove stale entries based on file modification times
- [ ] **Dependency Tracking**: Invalidate related entries when dependencies change

### Performance Requirements
- [ ] **Cache Hit Speed**: < 1ms for cached inference results
- [ ] **Cache Miss Overhead**: < 5ms additional overhead for cache operations
- [ ] **Memory Efficiency**: Reasonable memory usage proportional to cache size
- [ ] **Invalidation Speed**: < 10ms for cache invalidation operations
- [ ] **Concurrent Access**: Thread-safe operations for concurrent cache access

### Integration Requirements
- [ ] **Validation Integration**: Cache validation results alongside inference results
- [ ] **File System Integration**: Use existing file modification time patterns
- [ ] **Error Handling**: Proper cache behavior during validation errors
- [ ] **Configuration**: Configurable cache size and invalidation policies
- [ ] **Monitoring**: Cache hit/miss statistics for performance monitoring

### Reliability and Safety
- [ ] **Thread Safety**: Safe concurrent access from multiple threads
- [ ] **Memory Leaks**: Proper cleanup to prevent memory leaks
- [ ] **Cache Corruption**: Recovery from cache corruption scenarios
- [ ] **Error Isolation**: Cache errors don't affect inference functionality
- [ ] **Graceful Degradation**: System works correctly when cache is disabled

## Implementation Guidance

### Cache Key Strategy
- Use normalized object IDs as cache keys
- Include project root context for multi-project scenarios
- Implement consistent key generation across all cache operations

### Eviction Algorithm
```python
def _evict_lru(self):
    if len(self._cache) >= self.max_size and self._access_order:
        oldest_key = self._access_order.pop(0)
        del self._cache[oldest_key]
```

### File Modification Time Integration
Follow existing patterns from `DependencyGraphCache`:
```python
def _is_cache_valid(self, object_id: str, cached_time: float) -> bool:
    # Use existing file modification time checking patterns
    # Include tolerance for filesystem timestamp resolution
    path = self.path_builder.build_object_path(kind, object_id)
    if not path.exists():
        return False
    
    current_mtime = os.path.getmtime(path)
    return abs(current_mtime - cached_time) <= 0.001  # 1ms tolerance
```

## Testing Requirements

### Unit Tests (in `tests/test_inference_cache.py`)
```python
def test_cache_hit_performance():
    # Verify < 1ms cache hit operations
    
def test_lru_eviction_behavior():
    # Test correct LRU eviction when cache is full
    
def test_cache_invalidation():
    # Test selective and bulk invalidation
    
def test_file_modification_invalidation():
    # Test cache invalidation based on file changes
    
def test_concurrent_cache_access():
    # Test thread safety with concurrent operations
    
def test_cache_memory_management():
    # Test memory usage and leak prevention
    
def test_cache_miss_handling():
    # Test behavior when items not in cache
    
def test_cache_statistics():
    # Test cache hit/miss statistics tracking
```

### Performance Tests
```python
def test_cache_performance_under_load():
    # Test cache performance with high load
    
def test_cache_invalidation_performance():
    # Test invalidation performance with large cache
```

### Integration Tests
```python
def test_integration_with_validation():
    # Test caching of validation results
    
def test_real_project_caching():
    # Test cache behavior with actual project structures
```

## Security Considerations

### Cache Security
- **Memory Safety**: Prevent cache-based memory exhaustion attacks
- **Cache Timing**: Avoid cache timing attacks through consistent operation times
- **Data Isolation**: Ensure cached data doesn't leak between different contexts
- **Access Control**: Respect existing file system permissions in cache operations

### Error Handling Security
- **Information Disclosure**: Avoid exposing internal cache state in errors
- **Error Consistency**: Provide consistent error behavior regardless of cache state

## Performance Optimization

### Cache Size Tuning
- Default cache size of 1000 entries for typical usage
- Configurable cache size based on project requirements
- Memory usage monitoring and optimization

### Access Pattern Optimization
- Optimize for common inference patterns (repeated access to same objects)
- Batch invalidation for efficiency
- Lazy cleanup of stale entries

## Dependencies

**Prerequisites:**
- File system validation from previous task must be complete
- Existing cache patterns must be available for reference
- Path resolution system must be stable

**Outputs for next tasks:**
- InferenceCache class ready for integration with core inference engine
- Performance-optimized caching for < 1ms cache hits
- Comprehensive invalidation system for reliability

## Integration Points

### With Inference Engine
- **Cache Integration**: Seamless integration with core inference logic
- **Performance Boost**: Significant performance improvement for repeated operations
- **Reliability**: Cache doesn't affect inference correctness

### With Existing Systems
- **Cache Patterns**: Follow established caching patterns from existing code
- **File System**: Integrate with existing file modification time tracking
- **Configuration**: Support existing configuration and settings patterns

This task provides the performance optimization needed to make the Kind Inference Engine suitable for high-frequency operations while maintaining reliability and accuracy.

### Log

