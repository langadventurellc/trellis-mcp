---
kind: task
id: T-system-integration-testing-after
title: System Integration Testing After Tool Removal
status: open
priority: high
prerequisites:
- T-remove-dependency-functions-from
created: '2025-07-20T11:33:28.291072'
updated: '2025-07-20T11:33:28.291072'
schema_version: '1.1'
parent: F-core-tool-removal-and
---
# System Integration Testing After Tool Removal

## Purpose
Perform comprehensive testing of the MCP server after getNextReviewableTask tool removal to verify system integrity, identify any broken dependencies, and ensure all remaining functionality works correctly.

## Technical Context
After removing the getNextReviewableTask tool, we need to verify:
- Server starts up correctly without the removed tool
- All remaining tools function properly 
- No hidden dependencies were broken
- Test suite passes (or only expected failures related to removed tool)
- Performance and stability remain intact

## Implementation Requirements

### 1. Server Startup Testing
Test that the MCP server initializes correctly:
- STDIO transport mode startup
- HTTP transport mode startup
- Tool registration verification
- Error-free initialization logs

### 2. Remaining Tool Functionality Testing
Verify all remaining tools work correctly:
- health_check tool
- create_object tool
- get_object tool
- update_object tool
- list_backlog tool
- claim_next_task tool
- complete_task tool

### 3. Test Suite Execution
Run the complete test suite and analyze results:
- Identify tests that should fail (those testing removed tool)
- Verify other tests continue passing
- Document expected test failures
- Ensure no unexpected test failures

### 4. Integration Workflow Testing
Test complete workflows that might use multiple tools:
- Object creation → listing → claiming workflows
- Task completion workflows
- Project/epic/feature management workflows

## Detailed Acceptance Criteria

### Server Startup Verification
- [ ] Server starts successfully in STDIO mode: `uv run trellis-mcp serve`
- [ ] Server starts successfully in HTTP mode: `uv run trellis-mcp serve --http localhost:8000`
- [ ] No errors or warnings in startup logs
- [ ] Tool listing shows all remaining tools (7 tools total, excluding getNextReviewableTask)
- [ ] Server info resource returns correct information

### Tool Functionality Testing
- [ ] health_check tool responds correctly
- [ ] create_object tool can create projects, epics, features, tasks
- [ ] get_object tool can retrieve created objects
- [ ] update_object tool can modify objects
- [ ] list_backlog tool returns task lists correctly
- [ ] claim_next_task tool can claim available tasks
- [ ] complete_task tool can mark tasks as done

### Error Handling Verification
- [ ] Attempts to call removed getNextReviewableTask fail gracefully
- [ ] Error messages are clear and appropriate
- [ ] No server crashes or hangs when accessing removed tool
- [ ] Remaining tools handle errors correctly

### Test Suite Analysis
- [ ] Run full test suite: `uv run pytest -v`
- [ ] Document expected failures (tests for removed tool)
- [ ] Verify no unexpected test failures
- [ ] Confirm remaining tests pass at expected rates
- [ ] Test coverage remains adequate for remaining functionality

### Performance Testing
- [ ] Server response times remain consistent
- [ ] Memory usage appropriate (should be slightly lower)
- [ ] Tool discovery/listing performance acceptable
- [ ] No performance regressions in remaining tools

## Implementation Steps

1. **Server startup testing**: Test both STDIO and HTTP modes
2. **Tool listing verification**: Confirm getNextReviewableTask absent
3. **Individual tool testing**: Test each remaining tool
4. **Workflow testing**: Test multi-tool operations
5. **Error handling testing**: Test removed tool access
6. **Test suite execution**: Run pytest and analyze results
7. **Performance verification**: Check response times and resource usage
8. **Documentation update**: Record test results and any issues

## Dependencies and Prerequisites
- **Prerequisite**: T-remove-dependency-functions-from must be completed first
- All removal tasks must be complete before integration testing
- Access to test environment and test data
- Should complete before final verification task

## Security Considerations
- Verify no security vulnerabilities introduced by removal
- Test that authentication/authorization still work correctly
- Ensure audit logging functionality intact
- Verify error handling doesn't expose sensitive information

## Performance Benchmarks
- Server startup time should be equal or better
- Tool response times should remain consistent
- Memory usage should be slightly reduced
- Tool discovery should be marginally faster

## Error Handling and Recovery
- If server fails to start: Check for broken imports or syntax errors
- If tools fail: Verify tool implementations and registrations intact
- If tests fail unexpectedly: Investigate hidden dependencies
- If performance degrades: Check for unintended resource usage

## Expected Test Failures
Tests that should fail after tool removal:
- Tests specifically for getNextReviewableTask functionality
- Integration tests that call the removed tool
- Workflow tests that depend on review queue functionality
- Tests for get_oldest_review() and is_reviewable() functions

## Files Tested
Testing focus areas:
- `/src/trellis_mcp/server.py`: Server startup and tool registration
- `/src/trellis_mcp/tools/*.py`: All remaining tool implementations
- `/src/trellis_mcp/query.py`: Remaining query functionality
- Test files: All test modules for integration verification

## Verification Commands
```bash
# Test server startup (STDIO)
timeout 10s uv run trellis-mcp serve --help

# Test server startup (HTTP)
timeout 10s uv run trellis-mcp serve --http localhost:8000 &
sleep 3 && kill $!

# Run quality gate
uv run poe quality

# Run full test suite with verbose output
uv run pytest -v --tb=short

# Test individual tools (if MCP client available)
# uv run test-mcp-client

# Check for memory leaks or performance issues
# time uv run trellis-mcp serve --help
```

## Success Criteria
- Server starts successfully in both transport modes
- All 7 remaining tools function correctly
- Test suite results show only expected failures
- No performance regressions detected
- Error handling works appropriately for removed tool
- Documentation accurately reflects removed functionality

## Documentation of Results
Record in task completion log:
- Server startup test results
- Tool functionality test results
- Test suite execution summary
- Any unexpected issues discovered
- Performance impact assessment
- Recommended follow-up actions

### Log

