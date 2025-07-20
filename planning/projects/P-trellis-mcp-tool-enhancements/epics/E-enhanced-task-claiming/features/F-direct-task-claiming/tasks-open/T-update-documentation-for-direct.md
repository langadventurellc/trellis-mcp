---
kind: task
id: T-update-documentation-for-direct
title: Update documentation for direct task claiming feature
status: open
priority: low
prerequisites:
- T-update-claimnexttask-tool-to
created: '2025-07-20T15:20:13.959954'
updated: '2025-07-20T15:20:13.959954'
schema_version: '1.1'
parent: F-direct-task-claiming
---
## Context

Update project documentation to reflect the new direct task claiming functionality, including MCP tool specification updates, usage examples, and integration guidance for API consumers.

## Technical Approach

1. **Update MCP tool documentation** with new task_id parameter
2. **Add usage examples** for direct claiming scenarios
3. **Update workflow documentation** to include direct claiming patterns
4. **Create API reference** for new functionality

## Implementation Details

### Documentation Files to Update

#### Tool Specification Updates
- Update tool schema documentation with task_id parameter
- Add parameter validation rules and format requirements
- Document response format consistency between claiming modes

#### Usage Examples
```markdown
## Direct Task Claiming

Claim a specific task by ID instead of using priority-based selection:

```python
# Claim specific hierarchical task
result = claim_next_task(
    project_root="/path/to/planning",
    task_id="T-implement-user-auth"
)

# Claim specific standalone task  
result = claim_next_task(
    project_root="/path/to/planning", 
    task_id="task-security-audit"
)
```

#### Workflow Documentation
- Add direct claiming to development workflow guides
- Document integration with scope-based filtering
- Explain use cases for direct vs priority-based claiming

#### API Reference
- Complete parameter documentation for task_id
- Error code reference for direct claiming failures
- Response format specification

### Files to Update
- `docs/tools/claim-next-task.md` - Tool documentation
- `docs/workflows/task-claiming.md` - Workflow guidance
- `docs/api/mcp-tools.md` - API reference
- `README.md` - Feature highlights

### Documentation Standards
- Follow existing documentation format and style
- Include practical examples with real task IDs
- Provide troubleshooting guidance for common issues
- Maintain consistency with existing tool documentation

## Acceptance Criteria

- [ ] **Tool Documentation**: claimNextTask tool documentation includes task_id parameter
- [ ] **Usage Examples**: Clear examples for both hierarchical and standalone claiming
- [ ] **Workflow Integration**: Direct claiming integrated into workflow documentation
- [ ] **API Reference**: Complete API documentation for new functionality
- [ ] **Error Reference**: Error codes and troubleshooting guide
- [ ] **README Updates**: Feature highlights and quick examples

## Dependencies
- T-update-claimnexttask-tool-to (complete implementation to document)

## Testing Requirements
- Documentation accuracy validation against implementation
- Example code verification in realistic environments
- Link validation for cross-references
- Style and format consistency checks

### Log

