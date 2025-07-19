---
kind: task
id: T-create-practical-examples-for
title: Create practical examples for cross-system dependency patterns
status: open
priority: normal
prerequisites:
- T-create-cross-system
created: '2025-07-18T19:40:47.390165'
updated: '2025-07-18T19:40:47.390165'
schema_version: '1.1'
parent: F-documentation-and-examples
---
Create a comprehensive collection of practical examples demonstrating real-world cross-system dependency patterns that developers encounter.

**Implementation Requirements:**
- Create at least 5 distinct cross-system dependency examples
- Include complete command sequences with expected outputs
- Cover simple to complex dependency scenarios
- Provide working sample project structures
- Include both successful and error scenarios

**Technical Approach:**
- Create example project structures in docs/cross-system-prerequisites/examples/
- Use realistic development scenarios (CI/CD, feature development, etc.)
- Include complete MCP command sequences
- Show before/after states for each example
- Reference actual Trellis MCP commands and responses

**Acceptance Criteria:**
- 5+ complete examples with different complexity levels
- Each example includes context, commands, and expected results
- Examples cover various real-world development scenarios
- All command sequences are tested and accurate
- Examples include both success and error handling cases
- Clear explanations of when to use each pattern

**Example Categories:**
1. Simple standalone task depending on hierarchy task
2. Complex multi-level mixed dependencies for feature development
3. CI/CD pipeline integration with cross-system tasks
4. Error handling and recovery scenarios
5. Performance optimization for large dependency networks

**File Location:** `docs/cross-system-prerequisites/examples/` directory with individual example files

### Log

