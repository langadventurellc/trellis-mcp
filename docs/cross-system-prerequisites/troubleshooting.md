# Cross-System Prerequisites Troubleshooting

This guide provides diagnostic procedures and solutions for common issues encountered when working with cross-system prerequisites in Trellis MCP.

## Common Issues

### 1. External Dependency Validation Failures

#### Symptoms
- Prerequisites validation fails for external systems
- Error messages indicating unreachable external dependencies
- Timeout errors during cross-system validation

#### Diagnostic Steps

```bash
# Check external system connectivity
curl -I https://external-service.example.com/health

# Verify authentication credentials
curl -H "Authorization: Bearer $TOKEN" https://external-api.example.com/status

# Test network connectivity
ping external-system.example.com
nslookup external-system.example.com
```

#### Solutions

**Network Connectivity Issues:**
```yaml
# Update configuration with alternative endpoints
cross_system_validation:
  services:
    fallback_endpoints:
      - https://backup-api.example.com
      - https://secondary-service.example.com
```

**Authentication Failures:**
1. Verify credentials are current and not expired
2. Check access permissions for the service account
3. Rotate authentication tokens if necessary

**Timeout Issues:**
```yaml
# Increase timeout values in configuration
cross_system_validation:
  services:
    timeout: 30s  # Increased from default 10s
    retry_attempts: 5  # Increased retry count
```

### 2. Cycle Detection False Positives

#### Symptoms
- Cycle detection reports false cycles involving external systems
- Valid cross-system dependencies rejected as circular
- Unexpected validation failures in complex dependency graphs

#### Diagnostic Steps

```python
# Enable debug logging for cycle detection
import logging
logging.getLogger('trellis_mcp.validation.cycle_detection').setLevel(logging.DEBUG)

# Manually trace dependency paths
from trellis_mcp import trace_dependency_path
path = trace_dependency_path(project_root, 'T-problematic-task')
```

#### Solutions

**External System Leaf Nodes:**
Ensure external dependencies are properly classified as leaf nodes that cannot create cycles:

```yaml
prerequisites:
  - type: service
    reference: external-api
    is_leaf: true  # Explicitly mark as leaf node
```

**Graph Visualization:**
Generate dependency graph visualization to identify actual cycles:

```python
from trellis_mcp import generate_dependency_graph_visual
generate_dependency_graph_visual(project_root, output_file='deps.png')
```

### 3. Performance Degradation

#### Symptoms
- Slow validation times for cross-system operations
- High network latency during prerequisite checks
- Memory usage increasing with external validations

#### Diagnostic Steps

```python
# Enable performance benchmarking
from trellis_mcp import benchmark_cross_system_validation
results = benchmark_cross_system_validation(project_root)
print(f"External validation time: {results['external_validation_time']}")
print(f"Cache hit rate: {results['cache_hit_rate']}")
```

#### Solutions

**Enable Aggressive Caching:**
```yaml
cross_system_validation:
  caching:
    enabled: true
    external_cache_duration: 15m  # Increased cache time
    batch_validation: true
```

**Parallel Validation:**
```yaml
cross_system_validation:
  parallel_validation:
    enabled: true
    max_concurrent: 10
    timeout_per_validation: 5s
```

**Optimize Network Calls:**
```python
# Batch external validations
from trellis_mcp import batch_external_validation
results = batch_external_validation(external_prerequisites)
```

### 4. Configuration Issues

#### Symptoms
- External systems not found or misconfigured
- Authentication errors despite correct credentials
- Inconsistent behavior across environments

#### Diagnostic Steps

```bash
# Validate configuration file syntax
python -c "import yaml; yaml.safe_load(open('cross_system_config.yml'))"

# Check environment variables
env | grep TRELLIS_
env | grep CROSS_SYSTEM_

# Verify file permissions
ls -la ~/.trellis/cross_system_credentials
```

#### Solutions

**Configuration Validation:**
```python
from trellis_mcp import validate_cross_system_config
errors = validate_cross_system_config('config.yml')
if errors:
    print("Configuration errors found:", errors)
```

**Environment-Specific Configuration:**
```yaml
# Use environment-specific configuration files
cross_system_validation:
  config_file: "${ENVIRONMENT}_cross_system.yml"
  
# Development environment
development_cross_system.yml:
  services:
    auth_api: "https://dev-auth.example.com"
    
# Production environment  
production_cross_system.yml:
  services:
    auth_api: "https://auth.example.com"
```

## Debugging Techniques

### 1. Enable Debug Logging

```python
import logging

# Enable comprehensive debug logging
logging.getLogger('trellis_mcp').setLevel(logging.DEBUG)
logging.getLogger('trellis_mcp.cross_system').setLevel(logging.DEBUG)

# Enable specific component logging
logging.getLogger('trellis_mcp.validation.external').setLevel(logging.DEBUG)
logging.getLogger('trellis_mcp.network.retries').setLevel(logging.DEBUG)
```

### 2. Trace Dependency Resolution

```python
from trellis_mcp import trace_cross_system_resolution

# Trace how external dependencies are resolved
trace = trace_cross_system_resolution(
    project_root='/path/to/project',
    task_id='T-problematic-task',
    verbose=True
)

print("Resolution trace:")
for step in trace.steps:
    print(f"  {step.timestamp}: {step.action} - {step.result}")
```

### 3. Manual Validation Testing

```python
from trellis_mcp import manual_validate_external_prerequisite

# Test individual external prerequisites
result = manual_validate_external_prerequisite(
    prerequisite_reference='service:auth-api/v2',
    config=cross_system_config
)

print(f"Validation result: {result.status}")
print(f"Response time: {result.response_time}ms")
print(f"Error details: {result.error_details}")
```

### 4. Network Connectivity Testing

```bash
# Test connectivity to external services
trellis-mcp test-connectivity --config cross_system_config.yml

# Test specific service endpoints
trellis-mcp test-service auth-api --endpoint /health --timeout 10s

# Validate authentication
trellis-mcp test-auth service:auth-api --credentials ~/.trellis/auth_token
```

## Error Code Reference

### Cross-System Error Codes

| Code | Description | Solution |
|------|-------------|----------|
| CSP001 | External service unreachable | Check network connectivity, verify endpoint URLs |
| CSP002 | Authentication failure | Verify credentials, check token expiration |
| CSP003 | Timeout during validation | Increase timeout values, check service performance |
| CSP004 | Invalid external reference format | Review reference syntax in prerequisites |
| CSP005 | Cross-system cycle detected | Verify dependency graph, check for circular references |
| CSP006 | External service version mismatch | Update service version or compatibility configuration |
| CSP007 | Insufficient permissions | Check service account permissions and access rights |
| CSP008 | External validation cache error | Clear cache, verify cache configuration |

### Detailed Error Information

**CSP001 - External Service Unreachable**
```yaml
error:
  code: CSP001
  message: "Cannot reach external service: auth-api"
  details:
    service_url: "https://auth.example.com"
    attempted_at: "2025-07-19T14:30:00Z"
    network_error: "Connection timeout after 10s"
  suggestions:
    - "Check network connectivity"
    - "Verify service endpoint URL"
    - "Check firewall and proxy settings"
```

**CSP005 - Cross-System Cycle Detected**
```yaml
error:
  code: CSP005
  message: "Circular dependency detected involving external system"
  details:
    cycle_path: ["T-task-a", "service:external-api", "T-task-b", "T-task-a"]
    external_nodes: ["service:external-api"]
  suggestions:
    - "Review dependency graph structure"
    - "Ensure external services are leaf nodes"
    - "Check for indirect circular references"
```

## Prevention Strategies

### 1. Proactive Monitoring

```yaml
# Set up health checks for external dependencies
monitoring:
  external_services:
    - name: auth-api
      health_endpoint: /health
      check_interval: 30s
      alert_threshold: 3_consecutive_failures
      
  dependency_graphs:
    cycle_check_interval: 1h
    performance_threshold: 5s
```

### 2. Graceful Degradation

```yaml
# Configure fallback strategies
cross_system_validation:
  fallback_strategies:
    auth-api:
      fallback_mode: cached_validation
      cache_duration: 1h
      
    external-database:
      fallback_mode: skip_validation
      warning_level: warn
```

### 3. Regular Maintenance

```bash
# Regular maintenance tasks
trellis-mcp cleanup-external-cache --older-than 24h
trellis-mcp validate-all-external-references --project-root ./planning
trellis-mcp test-connectivity --all-services --report-file connectivity_report.json
```

## Advanced Troubleshooting

### Memory and Performance Profiling

```python
import cProfile
from trellis_mcp import validate_cross_system_prerequisites

# Profile cross-system validation performance
profiler = cProfile.Profile()
profiler.enable()

result = validate_cross_system_prerequisites(project_root, task_id)

profiler.disable()
profiler.dump_stats('cross_system_validation_profile.prof')
```

### Network Traffic Analysis

```bash
# Capture network traffic for external service calls
tcpdump -i any -w cross_system_traffic.pcap host external-service.example.com

# Analyze with wireshark or tshark
tshark -r cross_system_traffic.pcap -Y "http" -T fields -e http.request.method -e http.request.uri
```

### Database Query Analysis

```python
# Enable SQL query logging for external database dependencies
import logging
logging.getLogger('sqlalchemy.engine').setLevel(logging.INFO)

# Analyze slow queries
from trellis_mcp import analyze_external_db_performance
analysis = analyze_external_db_performance(db_connection)
```

## Getting Help

### Log Collection

When reporting issues, collect the following information:

```bash
# Collect relevant logs
trellis-mcp collect-logs --include-cross-system --output support_bundle.zip

# Include configuration (sanitized)
trellis-mcp export-config --sanitize-credentials --output config_export.yml

# Generate system information
trellis-mcp system-info --include-network --output system_info.txt
```

### Support Channels

1. **GitHub Issues**: [Trellis MCP Repository](https://github.com/langadventurellc/trellis-mcp)
2. **Documentation**: [Cross-System Prerequisites Index](./index.md)
3. **Community**: [Discussion Forums](https://github.com/langadventurellc/trellis-mcp/discussions)

---

## Related Documentation

- [Architecture](./architecture.md) - System design and component relationships
- [Performance](./performance.md) - Optimization strategies and benchmarking
- [Examples](./examples/) - Practical implementation examples
- [Main Index](./index.md) - Cross-system prerequisites documentation hub