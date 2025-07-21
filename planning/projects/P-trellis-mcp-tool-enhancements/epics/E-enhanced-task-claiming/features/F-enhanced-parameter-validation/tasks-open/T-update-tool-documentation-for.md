---
kind: task
id: T-update-tool-documentation-for
title: Update tool documentation for enhanced parameter validation
status: open
priority: low
prerequisites:
- T-create-comprehensive-parameter
created: '2025-07-20T19:14:07.183213'
updated: '2025-07-20T19:14:07.183213'
schema_version: '1.1'
parent: F-enhanced-parameter-validation
---
## Update Tool Documentation for Enhanced Parameter Validation

Update claimNextTask tool documentation to reflect the enhanced parameter validation system, including clear guidance on parameter combination rules and improved error handling.

### Detailed Context
- **Location**: Update `docs/tools/claim-next-task.md`
- **Pattern**: Follow existing tool documentation structure and format
- **Focus**: Clarify parameter combination rules and validation behavior
- **Audience**: Users and developers using the claimNextTask tool

### Specific Implementation Requirements

**Documentation Updates:**
1. **Parameter Combination Rules**: Clear explanation of mutual exclusivity and valid combinations
2. **Error Scenarios**: Document common parameter validation errors and solutions
3. **Examples**: Update examples to show both valid and invalid parameter usage
4. **Migration Guide**: Help users understand any changes from previous behavior

**Enhanced Parameter Documentation:**
```markdown
## Parameter Combination Rules

### Valid Combinations
- `projectRoot` only (legacy behavior)
- `projectRoot + worktree` (legacy behavior) 
- `projectRoot + scope` (scope-based claiming)
- `projectRoot + scope + worktree` (scope-based with worktree)
- `projectRoot + taskId` (direct task claiming)
- `projectRoot + taskId + worktree` (direct claiming with worktree)
- `projectRoot + taskId + force_claim` (force claiming)

### Invalid Combinations
- `scope + taskId` (mutually exclusive)
- `force_claim` without `taskId` (force claim requires specific task)
- `force_claim + scope` (force claim incompatible with scope filtering)
```

### Technical Approach

**Documentation Structure:**
- Add "Parameter Validation" section to existing documentation
- Include "Common Errors" section with solutions
- Update existing examples to show parameter validation
- Add troubleshooting guide for parameter issues

**Error Documentation:**
- Document each parameter validation error type
- Include example error messages and solutions
- Provide clear guidance on fixing parameter issues
- Link to related concepts and workflows

### Detailed Acceptance Criteria

**Parameter Rules Documentation:**
- [ ] **Clear Rules**: Parameter combination rules clearly explained
- [ ] **Valid Combinations**: All valid parameter combinations documented with examples
- [ ] **Invalid Combinations**: All invalid combinations documented with explanations
- [ ] **Mutual Exclusivity**: Clear explanation of scope vs taskId mutual exclusivity

**Error Guidance Documentation:**
- [ ] **Error Types**: All parameter validation error types documented
- [ ] **Example Messages**: Example error messages for each validation failure
- [ ] **Solutions**: Clear guidance on how to fix each parameter validation error
- [ ] **Troubleshooting**: Step-by-step troubleshooting guide for parameter issues

**Examples and Usage:**
- [ ] **Updated Examples**: All examples use valid parameter combinations
- [ ] **Error Examples**: Examples showing invalid usage and resulting errors
- [ ] **Migration Examples**: Examples showing how to update existing usage patterns
- [ ] **Best Practices**: Guidance on optimal parameter usage patterns

**Backward Compatibility Documentation:**
- [ ] **Legacy Support**: Clear explanation of continued support for existing patterns
- [ ] **Migration Guide**: Guide for users wanting to adopt new parameter features
- [ ] **Breaking Changes**: Documentation of any breaking changes (if any)
- [ ] **Upgrade Path**: Clear path for upgrading to enhanced parameter validation

### Documentation Quality Requirements

**Include comprehensive documentation updates:**
- Use clear, non-technical language accessible to all users
- Provide practical examples that users can copy and modify
- Include both success and error scenarios
- Link to related documentation and concepts
- Use consistent formatting and structure with existing docs

### Dependencies on Other Tasks
- **T-create-comprehensive-parameter**: Requires completed implementation and testing

### Security Considerations
- Document security implications of parameter validation
- Explain how validation prevents malicious parameter usage
- Include guidance on secure parameter handling
- Document any security-related parameter restrictions

### Log

