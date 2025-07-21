---
kind: task
id: T-add-integration-tests-for
status: done
title: Add integration tests for planning subdirectory auto-creation
priority: normal
prerequisites:
- T-update-all-mcp-tools-to-use
- T-update-resolve-path-for-new
created: '2025-07-21T01:01:51.390879'
updated: '2025-07-21T09:06:52.521481'
schema_version: '1.1'
worktree: null
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
   - Start with empty project root (`/project/root`)
   - Call MCP tools (createObject, listBacklog, claimNextTask, etc.)
   - Verify planning subdirectory is created automatically (`/project/root/planning`)
   - Verify objects are created in correct locations

2. **MCP Operations with Existing Planning Directory**
   - Start with project root containing planning subdirectory (`/project/root/planning`)
   - Call MCP tools
   - Verify existing planning directory is used
   - Verify no duplicate directories are created

3. **MCP Operations with Planning Directory as Project Root**
   - Start with planning directory supplied as project root (`/project/root/planning`)
   - Call MCP tools (createObject, listBacklog, claimNextTask, etc.)
   - Verify the planning directory is used directly (no additional `planning/` subfolder)
   - Verify objects are created in correct locations within the planning directory

4. **CLI Operations Remain Unchanged**
   - Test CLI commands with all three planning directory scenarios:
     - No planning directory
     - Planning as subdirectory  
     - Planning as project root
   - Verify CLI behavior is exactly the same as before
   - Verify no unexpected directory creation

5. **Mixed Usage Scenarios**
   - Test CLI followed by MCP operations (all three scenarios)
   - Test MCP followed by CLI operations (all three scenarios)
   - Verify both systems work harmoniously in all combinations

## Technical Approach

Create a new test file `tests/integration/test_planning_subdir_auto_creation.py` with:

```python
class TestPlanningSubdirAutoCreation:
    def test_mcp_creates_planning_subdir_when_missing(self, temp_dir):
        """Test that MCP tools create planning subdir when it doesn't exist."""
        
    def test_mcp_uses_existing_planning_subdir(self, temp_dir):
        """Test that MCP tools use existing planning subdir."""
        
    def test_mcp_uses_planning_dir_as_project_root(self, temp_dir):
        """Test that MCP tools use planning directory directly when supplied as project root."""
        
    def test_cli_behavior_unchanged_with_planning_subdir(self, temp_dir):
        """Test that CLI commands work the same with planning subdir."""
        
    def test_cli_behavior_unchanged_without_planning_subdir(self, temp_dir):
        """Test that CLI commands work the same without planning subdir."""
        
    def test_cli_behavior_unchanged_with_planning_as_project_root(self, temp_dir):
        """Test that CLI commands work the same when planning dir is supplied as project root."""
        
    def test_mixed_usage_cli_then_mcp_no_planning(self, temp_dir):
        """Test CLI operations followed by MCP operations (no planning dir)."""
        
    def test_mixed_usage_cli_then_mcp_with_planning(self, temp_dir):
        """Test CLI operations followed by MCP operations (with planning subdir)."""
        
    def test_mixed_usage_cli_then_mcp_planning_as_root(self, temp_dir):
        """Test CLI operations followed by MCP operations (planning as project root)."""
        
    def test_mixed_usage_mcp_then_cli_all_scenarios(self, temp_dir):
        """Test MCP operations followed by CLI operations (all scenarios)."""
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


**2025-07-21T14:15:28.726775Z** - Implemented comprehensive integration tests for planning subdirectory auto-creation functionality. Created a complete test suite with 12 test scenarios that verify MCP tools automatically create planning subdirectories when they don't exist, while CLI commands maintain backward compatibility. Tests cover all three planning directory scenarios: no planning directory (MCP auto-creates), existing planning subdirectory (both systems use), and planning directory as project root (both use directly). Also includes mixed usage scenarios, comprehensive MCP tool coverage, and edge case handling. All tests pass and meet quality standards (format, lint, type check).
- filesChanged: ["tests/integration/test_planning_subdir_auto_creation.py"]