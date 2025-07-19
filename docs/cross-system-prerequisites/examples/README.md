# Cross-System Prerequisites Examples

This directory contains practical examples and implementation patterns for cross-system prerequisites in Trellis MCP.

## Available Examples

### Basic Examples

#### 1. Simple External Service Dependency
Example of a task that depends on an external authentication service.

#### 2. Multi-Project Dependencies
Example of tasks that depend on components from other Trellis MCP projects.

#### 3. Infrastructure Dependencies
Example of tasks that require specific database schemas or system resources.

### Advanced Examples

#### 4. Complex Dependency Chains
Example of sophisticated dependency relationships across multiple systems.

#### 5. Service Discovery Integration
Example of dynamic service discovery for external prerequisites.

#### 6. Version-Aware Dependencies
Example of managing dependencies with version compatibility requirements.

## Example Structure

Each example includes:

- **Scenario Description**: Real-world use case explanation
- **Prerequisite Configuration**: YAML configuration examples
- **Implementation Code**: Sample code and setup instructions
- **Validation Logic**: Custom validation rules and checks
- **Performance Notes**: Optimization considerations for the specific pattern

## Common Patterns

### External API Dependencies

```yaml
# Basic external service prerequisite
prerequisites:
  - type: service
    reference: auth-api/v2
    validation: health_check
    timeout: 10s
```

### Database Schema Dependencies

```yaml
# Infrastructure prerequisite
prerequisites:
  - type: infrastructure
    reference: database/user_table
    validation: schema_check
    required_version: "1.2.0"
```

### Cross-Project Dependencies

```yaml
# External project prerequisite
prerequisites:
  - type: external_project
    reference: project:P-shared-components/T-logging-service
    validation: status_check
    required_status: done
```

## Usage Guidelines

1. **Choose the Right Pattern**: Select examples that match your use case
2. **Adapt Configuration**: Modify examples for your specific environment
3. **Test Thoroughly**: Validate examples in your development environment
4. **Monitor Performance**: Use performance guidelines from parent documentation

## Contributing Examples

To contribute new examples:

1. Create a new subdirectory with a descriptive name
2. Include complete configuration and code samples
3. Document the use case and expected outcomes
4. Add performance and security considerations

---

## Related Documentation

- [Architecture](../architecture.md) - System design patterns used in examples
- [Performance](../performance.md) - Optimization strategies for example patterns
- [Troubleshooting](../troubleshooting.md) - Common issues with example implementations
- [Main Index](../index.md) - Cross-system prerequisites documentation hub