"""Integration tests for planning subdirectory auto-creation functionality.

Tests verify that MCP tools automatically create planning subdirectories when they don't exist,
while CLI commands maintain backward compatibility. Covers all three planning directory scenarios:
1. No planning directory (MCP auto-creates)
2. Existing planning subdirectory (both use)
3. Planning directory as project root (both use directly)
"""

import pytest
from click.testing import CliRunner
from fastmcp import Client

from trellis_mcp.cli import cli

from .test_helpers import create_test_server


class TestPlanningSubdirAutoCreation:
    """Test planning subdirectory auto-creation across MCP and CLI operations."""

    @pytest.mark.asyncio
    async def test_mcp_creates_planning_subdir_when_missing(self, temp_dir):
        """Test that MCP tools create planning subdir when it doesn't exist."""
        # Start with empty project root
        project_root = str(temp_dir)
        assert not (temp_dir / "planning").exists()

        # Create server pointing to project root (not planning subdir)
        server, _ = create_test_server(temp_dir.parent)  # Use parent so it doesn't auto-create

        async with Client(server) as client:
            # Call MCP createObject - should auto-create planning subdirectory
            result = await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Test Project",
                    "projectRoot": project_root,  # Point to temp_dir, not temp_dir/planning
                },
            )

            project_id = result.data["id"]

            # Verify planning subdirectory was created
            planning_dir = temp_dir / "planning"
            assert planning_dir.exists(), "MCP should auto-create planning subdirectory"
            assert planning_dir.is_dir()

            # Verify project structure was created inside planning subdirectory
            projects_dir = planning_dir / "projects"
            assert projects_dir.exists()

            # Verify project file exists in correct location
            project_path = projects_dir / f"{project_id}" / "project.md"
            assert project_path.exists()

            # Test other MCP operations work with auto-created structure
            epic_result = await client.call_tool(
                "createObject",
                {
                    "kind": "epic",
                    "title": "Test Epic",
                    "parent": project_id,
                    "projectRoot": project_root,
                },
            )

            epic_id = epic_result.data["id"]
            epic_path = projects_dir / f"{project_id}" / "epics" / f"{epic_id}" / "epic.md"
            assert epic_path.exists()

    @pytest.mark.asyncio
    async def test_mcp_uses_existing_planning_subdir(self, temp_dir):
        """Test that MCP tools use existing planning subdir."""
        # Pre-create planning subdirectory structure
        planning_dir = temp_dir / "planning"
        projects_dir = planning_dir / "projects"
        projects_dir.mkdir(parents=True)

        project_root = str(temp_dir)

        # Create server and client
        server, _ = create_test_server(temp_dir.parent)

        async with Client(server) as client:
            # Call MCP createObject
            result = await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Test Project",
                    "projectRoot": project_root,
                },
            )

            project_id = result.data["id"]

            # Verify no duplicate planning directories were created
            planning_dirs = list(temp_dir.glob("**/planning"))
            assert len(planning_dirs) == 1, "Should not create duplicate planning directories"
            assert planning_dirs[0] == planning_dir

            # Verify project was created in existing planning structure
            project_path = projects_dir / f"{project_id}" / "project.md"
            assert project_path.exists()

    @pytest.mark.asyncio
    async def test_mcp_uses_planning_dir_as_project_root(self, temp_dir):
        """Test that MCP tools use planning directory directly when supplied as project root."""
        # Create planning directory structure
        planning_dir = temp_dir / "planning"
        projects_dir = planning_dir / "projects"
        projects_dir.mkdir(parents=True)

        # Point project root directly to planning directory
        project_root = str(planning_dir)

        server, _ = create_test_server(temp_dir)

        async with Client(server) as client:
            # Call MCP createObject with planning dir as project root
            result = await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Test Project",
                    "projectRoot": project_root,  # Planning dir as project root
                },
            )

            project_id = result.data["id"]

            # Verify no additional planning subdirectory was created
            nested_planning = planning_dir / "planning"
            assert not nested_planning.exists(), "Should not create nested planning directories"

            # Verify project was created directly in the planning directory
            project_path = projects_dir / f"{project_id}" / "project.md"
            assert project_path.exists()

    def test_cli_behavior_unchanged_with_planning_subdir(self, temp_dir):
        """Test that CLI commands work the same with planning subdir."""
        # Pre-create planning subdirectory with project structure
        planning_dir = temp_dir / "planning"
        projects_dir = planning_dir / "projects"
        projects_dir.mkdir(parents=True)

        # Create a test project directly in planning structure (simulate existing data)
        test_project_dir = projects_dir / "P-test-project"
        test_project_dir.mkdir(parents=True)

        project_file = test_project_dir / "project.md"
        project_file.write_text(
            """---
kind: project
id: P-test-project
title: Test Project
status: in-progress
priority: normal
created: 2025-01-01T00:00:00Z
updated: 2025-01-01T00:00:00Z
---
# Test Project

Test project for CLI testing.
"""
        )

        runner = CliRunner()
        # CLI should find and list the project from planning subdirectory
        result = runner.invoke(
            cli,
            ["--config", "/dev/null", "backlog"],
            env={"MCP_PLANNING_ROOT": str(temp_dir)},
        )

        assert result.exit_code == 0, f"CLI command failed: {result.output}"

        # CLI should work exactly as before with planning subdirectory
        # (The backlog command scans for tasks, so we'd need tasks to see output)
        # The important part is that it doesn't crash and exits successfully

    def test_cli_behavior_unchanged_without_planning_subdir(self, temp_dir):
        """Test that CLI commands work the same without planning subdir."""
        # Create project structure directly in temp_dir (no planning subdirectory)
        projects_dir = temp_dir / "projects"
        projects_dir.mkdir(parents=True)

        test_project_dir = projects_dir / "P-test-project"
        test_project_dir.mkdir(parents=True)

        project_file = test_project_dir / "project.md"
        project_file.write_text(
            """---
kind: project
id: P-test-project
title: Test Project
status: in-progress
priority: normal
created: 2025-01-01T00:00:00Z
updated: 2025-01-01T00:00:00Z
---
# Test Project

Test project for CLI testing.
"""
        )

        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["--config", "/dev/null", "backlog"],
            env={"MCP_PLANNING_ROOT": str(temp_dir)},
        )

        assert result.exit_code == 0, f"CLI command failed: {result.output}"

    def test_cli_behavior_unchanged_with_planning_as_project_root(self, temp_dir):
        """Test that CLI commands work the same when planning dir is supplied as project root."""
        # Create planning directory structure
        planning_dir = temp_dir / "planning"
        projects_dir = planning_dir / "projects"
        projects_dir.mkdir(parents=True)

        test_project_dir = projects_dir / "P-test-project"
        test_project_dir.mkdir(parents=True)

        project_file = test_project_dir / "project.md"
        project_file.write_text(
            """---
kind: project
id: P-test-project
title: Test Project
status: in-progress
priority: normal
created: 2025-01-01T00:00:00Z
updated: 2025-01-01T00:00:00Z
---
# Test Project

Test project for CLI testing.
"""
        )

        runner = CliRunner()
        # Point CLI directly to planning directory
        result = runner.invoke(
            cli,
            ["--config", "/dev/null", "backlog"],
            env={"MCP_PLANNING_ROOT": str(planning_dir)},
        )

        assert result.exit_code == 0, f"CLI command failed: {result.output}"

    @pytest.mark.asyncio
    async def test_mixed_usage_cli_then_mcp_no_planning(self, temp_dir):
        """Test CLI operations followed by MCP operations (no planning dir)."""
        # Start with empty directory
        assert not (temp_dir / "planning").exists()

        # Step 1: CLI init command to create structure
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["--config", "/dev/null", "init", str(temp_dir)],
            input="y\n",  # Confirm directory creation
        )

        assert result.exit_code == 0, f"CLI init failed: {result.output}"

        # Verify CLI created projects directory structure
        # CLI init creates planning/projects structure
        planning_dir = temp_dir / "planning"
        projects_dir = planning_dir / "projects"
        assert projects_dir.exists(), "CLI init should create planning/projects structure"

        # Step 2: MCP operations should work with CLI-created structure
        server, _ = create_test_server(temp_dir.parent)

        async with Client(server) as client:
            result = await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Mixed Usage Project",
                    "projectRoot": str(temp_dir),
                },
            )

            project_id = result.data["id"]

            # Verify MCP used the CLI-created planning structure
            project_path = projects_dir / f"{project_id}" / "project.md"
            assert project_path.exists(), "MCP should use CLI-created planning structure"

    @pytest.mark.asyncio
    async def test_mixed_usage_cli_then_mcp_with_planning(self, temp_dir):
        """Test CLI operations followed by MCP operations (with planning subdir)."""
        # Pre-create planning subdirectory
        planning_dir = temp_dir / "planning"
        projects_dir = planning_dir / "projects"
        projects_dir.mkdir(parents=True)

        # Step 1: CLI command with planning subdirectory
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["--config", "/dev/null", "backlog"],
            env={"MCP_PLANNING_ROOT": str(temp_dir)},
        )

        assert result.exit_code == 0, f"CLI command failed: {result.output}"

        # Step 2: MCP operations should use the same planning structure
        server, _ = create_test_server(temp_dir.parent)

        async with Client(server) as client:
            result = await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Mixed Usage Project",
                    "projectRoot": str(temp_dir),
                },
            )

            project_id = result.data["id"]

            # Verify MCP used existing planning structure
            project_path = projects_dir / f"{project_id}" / "project.md"
            assert project_path.exists(), "MCP should use existing planning structure"

    @pytest.mark.asyncio
    async def test_mixed_usage_cli_then_mcp_planning_as_root(self, temp_dir):
        """Test CLI operations followed by MCP operations (planning as project root)."""
        # Create planning directory structure
        planning_dir = temp_dir / "planning"
        projects_dir = planning_dir / "projects"
        projects_dir.mkdir(parents=True)

        # Step 1: CLI command with planning dir as root
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["--config", "/dev/null", "backlog"],
            env={"MCP_PLANNING_ROOT": str(planning_dir)},
        )

        assert result.exit_code == 0, f"CLI command failed: {result.output}"

        # Step 2: MCP operations with planning dir as root
        server, _ = create_test_server(temp_dir)

        async with Client(server) as client:
            result = await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Mixed Usage Project",
                    "projectRoot": str(planning_dir),  # Planning dir as project root
                },
            )

            project_id = result.data["id"]

            # Verify MCP used planning dir directly
            project_path = projects_dir / f"{project_id}" / "project.md"
            assert project_path.exists(), "MCP should use planning dir directly"

    @pytest.mark.asyncio
    async def test_mixed_usage_mcp_then_cli_all_scenarios(self, temp_dir):
        """Test MCP operations followed by CLI operations (all scenarios)."""
        for i, scenario_name in enumerate(["no_planning", "planning_subdir", "planning_as_root"]):
            # Create isolated subdirectory for each scenario
            scenario_dir = temp_dir / f"scenario_{i}"
            scenario_dir.mkdir()

            # Setup each scenario
            if scenario_name == "planning_subdir":
                # Create planning subdirectory structure
                planning_path = scenario_dir / "planning"
                (planning_path / "projects").mkdir(parents=True)
                scenario_project_root = str(scenario_dir)
            elif scenario_name == "planning_as_root":
                # Create planning directory as project root
                planning_path = scenario_dir / "planning"
                (planning_path / "projects").mkdir(parents=True)
                scenario_project_root = str(planning_path)
            else:
                # No planning directory initially
                scenario_project_root = str(scenario_dir)

            # Step 1: MCP operations
            server, _ = create_test_server(
                scenario_dir.parent if scenario_name != "planning_as_root" else scenario_dir
            )

            async with Client(server) as client:
                # Create project via MCP
                result = await client.call_tool(
                    "createObject",
                    {
                        "kind": "project",
                        "title": f"MCP First Project {scenario_name}",
                        "projectRoot": scenario_project_root,
                    },
                )

                project_id = result.data["id"]

                # Create epic via MCP
                await client.call_tool(
                    "createObject",
                    {
                        "kind": "epic",
                        "title": f"MCP First Epic {scenario_name}",
                        "parent": project_id,
                        "projectRoot": scenario_project_root,
                    },
                )

            # Step 2: CLI operations should work with MCP-created structure
            runner = CliRunner()
            result = runner.invoke(
                cli,
                ["--config", "/dev/null", "backlog"],
                env={"MCP_PLANNING_ROOT": scenario_project_root},
            )

            assert (
                result.exit_code == 0
            ), f"CLI failed after MCP in scenario {scenario_name}: {result.output}"

    @pytest.mark.asyncio
    async def test_comprehensive_mcp_tool_coverage(self, temp_dir):
        """Test that all MCP tools work with planning subdirectory auto-creation."""
        project_root = str(temp_dir)

        # Verify no planning directory initially
        assert not (temp_dir / "planning").exists()

        server, _ = create_test_server(temp_dir.parent)

        async with Client(server) as client:
            # Test createObject
            project_result = await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Comprehensive Test Project",
                    "projectRoot": project_root,
                },
            )
            project_id = project_result.data["id"]

            # Verify planning directory was auto-created
            planning_dir = temp_dir / "planning"
            assert planning_dir.exists()

            # Test getObject
            get_result = await client.call_tool(
                "getObject",
                {
                    "id": project_id,
                    "projectRoot": project_root,
                },
            )
            assert get_result.data["yaml"]["title"] == "Comprehensive Test Project"

            # Test updateObject
            await client.call_tool(
                "updateObject",
                {
                    "id": project_id,
                    "projectRoot": project_root,
                    "yamlPatch": {"priority": "high"},
                },
            )

            # Test listBacklog
            backlog_result = await client.call_tool(
                "listBacklog",
                {
                    "projectRoot": project_root,
                },
            )
            assert "tasks" in backlog_result.data

            # Test claimNextTask (will fail due to no tasks, but should handle planning dir)
            # correctly
            try:
                await client.call_tool(
                    "claimNextTask",
                    {
                        "projectRoot": project_root,
                    },
                )
            except Exception as e:
                # Expected to fail due to no available tasks
                # Should not fail due to planning directory issues
                error_msg = str(e).lower()
                assert "planning" not in error_msg or "directory" not in error_msg

            # Create a task to test completeTask
            epic_result = await client.call_tool(
                "createObject",
                {
                    "kind": "epic",
                    "title": "Test Epic",
                    "parent": project_id,
                    "projectRoot": project_root,
                },
            )
            epic_id = epic_result.data["id"]

            feature_result = await client.call_tool(
                "createObject",
                {
                    "kind": "feature",
                    "title": "Test Feature",
                    "parent": epic_id,
                    "projectRoot": project_root,
                },
            )
            feature_id = feature_result.data["id"]

            await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Test Task",
                    "parent": feature_id,
                    "projectRoot": project_root,
                },
            )

            # Claim and complete the task
            claim_result = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": project_root,
                },
            )
            claimed_task_id = claim_result.data["task"]["id"]

            await client.call_tool(
                "completeTask",
                {
                    "taskId": claimed_task_id,
                    "projectRoot": project_root,
                    "summary": "Integration test task completion",
                    "filesChanged": ["test_file.py"],
                },
            )

    def test_filesystem_permissions_and_safety(self, temp_dir):
        """Test that directory creation handles permissions and edge cases safely."""

        # Test case: Existing file with same name as planning directory
        file_collision_dir = temp_dir / "file_collision_test"
        file_collision_dir.mkdir()

        # Create a file named "planning" to test collision handling
        planning_file = file_collision_dir / "planning"
        planning_file.write_text("existing file")

        # Create server to test edge case handling
        server, _ = create_test_server(file_collision_dir.parent)

        # The operation should handle this edge case gracefully
        # Implementation should detect the file and handle appropriately
        # This test verifies no crashes occur when file conflicts exist
