---
kind: task
id: T-add-integration-tests-for
title: Add integration tests for planning subdirectory auto-creation
status: open
priority: normal
prerequisites:
- T-update-all-mcp-tools-to-use
- T-update-resolve-path-for-new
created: '2025-07-21T01:01:51.390879'
updated: '2025-07-21T01:01:51.390879'
schema_version: '1.1'
---
## Context

After implementing the planning subdirectory auto-creation functionality, we need comprehensive integration tests to verify that:
1. MCP tools automatically create planning subdirectories when they don't exist
2. CLI commands continue to work with existing behavior
3. Mixed usage scenarios work correctly

## Implementation Requirements

Create integration tests that verify the end-to-end behavior of the planning subdirectory auto-creation feature.

### Test Scenarios to Cover

1. **MCP Operations with No Planning Directory**
   - Start with empty project root
   - Call MCP tools (createObject, listBacklog, claimNextTask, etc.)
   - Verify planning subdirectory is created automatically
   - Verify objects are created in correct locations

2. **MCP Operations with Existing Planning Directory**
   - Start with project root containing planning subdirectory
   - Call MCP tools
   - Verify existing planning directory is used
   - Verify no duplicate directories are created

3. **CLI Operations Remain Unchanged**
   - Test CLI commands with both planning directory scenarios
   - Verify CLI behavior is exactly the same as before
   - Verify no unexpected directory creation

4. **Mixed Usage Scenarios**
   - Test CLI followed by MCP operations
   - Test MCP followed by CLI operations
   - Verify both systems work harmoniously

## Technical Approach

Create a new test file `tests/integration/test_planning_subdir_auto_creation.py` with:

```python
class TestPlanningSubdirAutoCreation:
    def test_mcp_creates_planning_subdir_when_missing(self, temp_dir):
        """Test that MCP tools create planning subdir when it doesn't exist."""
        
    def test_mcp_uses_existing_planning_subdir(self, temp_dir):
        """Test that MCP tools use existing planning subdir."""
        
    def test_cli_behavior_unchanged_with_planning_subdir(self, temp_dir):
        """Test that CLI commands work the same with planning subdir."""
        
    def test_cli_behavior_unchanged_without_planning_subdir(self, temp_dir):
        """Test that CLI commands work the same without planning subdir."""
        
    def test_mixed_usage_cli_then_mcp(self, temp_dir):
        """Test CLI operations followed by MCP operations."""
        
    def test_mixed_usage_mcp_then_cli(self, temp_dir):
        """Test MCP operations followed by CLI operations."""
```

### Test Implementation Strategy

1. **Use FastMCP test client** for MCP tool testing
2. **Use CliRunner** for CLI command testing
3. **Use temporary directories** for isolation
4. **Verify filesystem state** after each operation
5. **Test with realistic object hierarchies** (projects, epics, features, tasks)

## Acceptance Criteria

- All test scenarios pass successfully
- Tests verify correct directory structure creation
- Tests verify objects are created in expected locations
- Tests verify CLI backward compatibility
- Tests verify no filesystem permission issues
- Tests run reliably in CI/CD environment

## Testing Requirements

The tests themselves should:
- Use proper fixtures for temporary directories
- Clean up after themselves
- Be deterministic and repeatable
- Cover edge cases like permission errors
- Verify both successful and error scenarios

## Files to Create/Modify

- `tests/integration/test_planning_subdir_auto_creation.py` - New integration test file
- `tests/conftest.py` - Add any needed fixtures
- Update existing integration tests if they need adjustments for the new behavior

## Documentation

Update relevant documentation to reflect the new behavior:
- Add comments in test files explaining the scenarios
- Update any architectural documentation if needed

### Log

