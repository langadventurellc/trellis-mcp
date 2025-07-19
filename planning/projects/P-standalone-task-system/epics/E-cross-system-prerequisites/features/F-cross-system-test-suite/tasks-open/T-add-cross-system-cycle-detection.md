---
kind: task
id: T-add-cross-system-cycle-detection
title: Add cross-system cycle detection tests
status: open
priority: normal
prerequisites:
- T-refactor-test-mixed-task-types
created: '2025-07-18T20:53:39.909482'
updated: '2025-07-18T20:58:26.534277'
schema_version: '1.1'
parent: F-cross-system-test-suite
---
### Purpose
Implement comprehensive tests for circular dependency detection spanning both hierarchical and standalone task systems.

### Implementation Requirements
- Test circular dependencies that cross system boundaries
- Validate proper error detection and reporting for cross-system cycles
- Test complex cycle scenarios with multiple tasks involved
- Ensure cycle detection performance with large dependency networks

### Test Scenarios to Cover
- **Simple cross-system cycles**: Hierarchical task ↔ Standalone task circular dependencies
- **Complex multi-task cycles**: Cycles involving multiple tasks across both systems
- **Nested cycle detection**: Cycles within larger dependency networks
- **Performance edge cases**: Cycle detection in large mixed dependency graphs
- **Error message validation**: Proper error reporting for cross-system cycles

### Acceptance Criteria
- All cross-system circular dependency scenarios are detected
- Cycle detection tests cover both simple and complex scenarios
- Proper error messages and codes are validated
- Performance tests ensure cycle detection completes in reasonable time
- Tests follow existing cycle detection test patterns

### Technical Approach
- Build on existing dependency validation test patterns from refactored modules
- Use existing error validation and assertion patterns
- Create test fixtures for circular dependency scenarios
- Implement performance benchmarks for cycle detection
- Follow existing test module organization and naming conventions

### Log