---
kind: task
id: T-update-mcp-tool-handlers-with-1
parent: F-enhanced-error-handling
status: done
title: Update MCP tool handlers with enhanced error responses
priority: normal
prerequisites:
- T-update-standalone-task
- T-update-hierarchy-task-validation
created: '2025-07-18T10:26:09.814356'
updated: '2025-07-18T11:47:46.547798'
schema_version: '1.1'
worktree: null
---
Update MCP tool handlers to properly catch and format enhanced validation errors for client applications.

**Implementation Details:**
- Modify MCP tool handlers in src/trellis_mcp/tools/
- Implement proper error serialization for API responses
- Ensure error codes are included in responses for programmatic handling
- Update error response format to be consistent across all tools
- Add structured error objects that can be parsed by clients

**Acceptance Criteria:**
- MCP tool handlers properly catch and format enhanced validation errors
- Error responses include error codes for programmatic handling
- Error response format is consistent across all tools
- Structured error objects are serialized properly for API responses
- Client applications can parse and handle error responses effectively

**Dependencies:** Validation functions must be updated with enhanced error handling first

### Log


**2025-07-18T16:56:14.429429Z** - Updated all MCP tool handlers to use enhanced ValidationError system with structured error responses, error codes, and context information for better client application integration. Replaced legacy TrellisValidationError usage across 7 tool handler files with consistent error formatting and programmatic error handling capabilities.
- filesChanged: ["src/trellis_mcp/tools/create_object.py", "src/trellis_mcp/tools/update_object.py", "src/trellis_mcp/tools/complete_task.py", "src/trellis_mcp/tools/claim_next_task.py", "src/trellis_mcp/tools/get_object.py", "src/trellis_mcp/tools/list_backlog.py", "src/trellis_mcp/tools/get_next_reviewable_task.py"]