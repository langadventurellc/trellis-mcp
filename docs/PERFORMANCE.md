# Cycle Detection Performance Optimization

This document describes the performance optimizations implemented for cycle detection in Trellis MCP.

## Overview

The cycle detection system has been optimized to reduce redundant file I/O operations through intelligent caching and lazy loading strategies.

## Performance Characteristics

### Before Optimization

- **File Loading**: Every cycle check scanned all project files using glob patterns
- **Graph Building**: Dependency graph rebuilt from scratch on every operation
- **RPC Operations**: Each create/update operation performed cycle detection twice (pre-check + post-validation)
- **Cold Performance**: ~50-200ms for medium projects (100-500 objects)

### After Optimization

- **File Loading**: Cached with modification time (mtime) validation
- **Graph Building**: Reused when no files have changed
- **Cache Hit Performance**: ~1-5ms for repeated operations on unchanged projects
- **Cache Miss Performance**: Same as before optimization, but cached for subsequent operations

## Caching Strategy

### Cache Structure

The `DependencyGraphCache` maintains:

- **Graph Cache**: Pre-built adjacency list representation of dependencies
- **File Modification Times**: Timestamps for cache invalidation
- **Project Isolation**: Separate cache entries per project root

### Cache Invalidation

Cache is invalidated when:

1. **File Modification**: Any tracked file's mtime changes
2. **File Addition**: New object files are detected
3. **File Deletion**: Previously tracked files no longer exist
4. **Manual Clear**: Explicit cache clearing via API

### Cache Validation Algorithm

```python
def is_cache_valid(project_root, cached_mtimes):
    # Check if any cached files have been modified
    for file_path, cached_mtime in cached_mtimes.items():
        if not os.path.exists(file_path):
            return False  # File was deleted
        if os.path.getmtime(file_path) != cached_mtime:
            return False  # File was modified
    
    # Check for new files using glob patterns
    current_files = discover_all_object_files(project_root)
    cached_files = set(cached_mtimes.keys())
    
    return current_files == cached_files
```

## Performance Benchmarking

### Built-in Benchmarking

Use the `benchmark_cycle_detection()` function to measure performance:

```python
from trellis_mcp import benchmark_cycle_detection

# Run benchmark with 10 operations
results = benchmark_cycle_detection("/path/to/project", operations=10)

# Results include:
# - cold_cycle_check: First operation (cache miss)
# - avg_warm_time: Average of subsequent operations (cache hits)
# - cache_speedup_factor: Cold time / avg warm time
# - cache_improvement_percent: % improvement from caching
```

### Manual Benchmarking

For custom benchmarking:

```python
from trellis_mcp import PerformanceBenchmark, check_prereq_cycles

benchmark = PerformanceBenchmark()
result = check_prereq_cycles(project_root, benchmark)
timings = benchmark.get_timings()
benchmark.log_summary()
```

## Lazy Loading Considerations

### Current Implementation

- **Eager Loading**: All objects loaded when cache miss occurs
- **Full Validation**: Complete dependency graph built for thorough cycle detection
- **Memory Efficient**: Objects not kept in memory after graph construction

### Future Optimizations

For very large projects (1000+ objects), consider:

1. **Incremental Loading**: Load only objects with prerequisites
2. **Partial Graph Building**: Build subgraphs for specific hierarchies
3. **Streaming Validation**: Process objects in batches
4. **Persistent Caching**: Store cache to disk across server restarts

## Performance Guidelines

### When Cache is Effective

- **Repeated Operations**: Multiple cycle checks on unchanged projects
- **Batch Operations**: Multiple object operations in short time periods
- **Development Workflows**: Frequent validation during active development

### When Cache is Less Effective

- **Continuous File Changes**: Projects with frequent external modifications
- **Large Projects**: Memory usage grows with project size
- **Single Operations**: One-off operations don't benefit from caching

### Memory Usage

- **Small Projects** (< 50 objects): ~10-50KB per cached project
- **Medium Projects** (50-500 objects): ~50-500KB per cached project  
- **Large Projects** (500+ objects): ~500KB-5MB per cached project

## Cache Management

### Monitoring Cache Performance

```python
from trellis_mcp import get_cache_stats

stats = get_cache_stats()
print(f"Cached projects: {stats['cached_projects']}")
print(f"Cache keys: {stats['cache_keys']}")
```

### Manual Cache Control

```python
from trellis_mcp import clear_dependency_cache

# Clear specific project cache
clear_dependency_cache("/path/to/project")

# Clear all cached projects
clear_dependency_cache()
```

### Production Recommendations

1. **Monitor Memory Usage**: Watch cache size in production environments
2. **Periodic Cleanup**: Clear cache periodically for long-running servers
3. **Cache Warming**: Pre-load frequently accessed projects
4. **Performance Logging**: Enable debug logging to monitor cache hit rates

## Algorithm Complexity

### Time Complexity

- **Cache Hit**: O(F) where F = number of files (mtime checks only)
- **Cache Miss**: O(F + V + E) where V = vertices (objects), E = edges (dependencies)
- **Cycle Detection**: O(V + E) using depth-first search

### Space Complexity

- **Graph Storage**: O(V + E) for adjacency list representation
- **Cache Overhead**: O(F) for file modification times
- **Total**: O(V + E + F) per cached project

## Integration Notes

### Server Integration

The optimizations are automatically used by:

- `createObject` RPC handler (pre-validation cycle check)
- `updateObject` RPC handler (pre-validation cycle check)
- Post-validation cycle checks (fallback safety measure)

### Backward Compatibility

All existing APIs maintain the same interface:

- `check_prereq_cycles()` - Enhanced with optional benchmarking
- `validate_acyclic_prerequisites()` - Enhanced with caching
- Error handling and return values unchanged

### Thread Safety

**Note**: The current cache implementation is not thread-safe. For multi-threaded environments, consider:

1. **Process Isolation**: Run separate MCP server processes
2. **Locking**: Add thread synchronization to cache operations
3. **Read-Only Caching**: Use cache only for read operations

## Testing Performance

Run the included performance test:

```bash
cd /path/to/trellis-mcp
python test_cycle_performance.py
```

This test verifies:

- Cache functionality works correctly
- Performance improvements are measurable
- No regressions in cycle detection accuracy

## Troubleshooting

### Cache Not Working

1. **Check File Permissions**: Ensure files are readable
2. **Verify Paths**: Confirm project root paths are correct
3. **Enable Debug Logging**: Set logging level to DEBUG
4. **Clear Cache**: Reset cache and retry

### Performance Degradation

1. **Monitor Cache Hit Rate**: Check if cache is being invalidated frequently
2. **Profile File System**: Look for slow disk I/O
3. **Check Memory Usage**: Ensure cache isn't consuming excessive memory
4. **Review Project Size**: Consider optimizations for very large projects

### Debug Logging

Enable detailed performance logging:

```python
import logging
logging.getLogger('trellis_mcp.validation').setLevel(logging.DEBUG)
```

This logs:
- Cache hit/miss information
- Performance timing details
- File system operation details
- Graph construction metrics