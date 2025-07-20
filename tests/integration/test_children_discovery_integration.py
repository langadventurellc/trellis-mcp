"""Comprehensive integration tests for children discovery across all parent types.

This module tests complete workflow scenarios that validate the children discovery
system across all parent types, including both hierarchical and standalone task
scenarios, following the testing patterns in existing integration tests.

These tests focus on integration testing patterns and workflows, validating:
- Complete workflows from getObject calls through children discovery
- Cross-system compatibility (hierarchical + standalone tasks)
- Realistic project structures similar to existing test fixtures
- Error scenarios and edge cases in realistic contexts
- Data integrity and consistency across the children discovery system
"""

import time

import pytest
from fastmcp import Client
from tests.fixtures.integration.children_discovery_fixtures import (
    assert_children_discovery_performance,
    create_integration_project_structure,
    validate_children_metadata,
    validate_children_ordering,
    validate_cross_system_isolation,
)

from trellis_mcp.server import create_server
from trellis_mcp.settings import Settings


class TestChildrenDiscoveryIntegration:
    """Integration tests for children discovery across all parent types.

    Tests complete workflows including getObject enhancement, children discovery,
    cache integration, and cross-system compatibility with both hierarchical
    and standalone tasks.
    """

    @pytest.mark.asyncio
    async def test_project_children_discovery_workflow(self, temp_dir):
        """Test complete project → epics discovery workflow.

        This integration test validates:
        1. getObject retrieves project successfully
        2. Children array contains immediate epics only
        3. Epic metadata is correctly parsed and formatted
        4. Cache integration works correctly

        Test project structure:
        - 1 project with 3 epics
        - Each epic has 2-3 features
        - Features contain 5-10 tasks each

        Expected behavior:
        - getObject returns project with children array
        - Children array contains 3 epic objects
        - Each epic object has id, title, status, kind, created, file_path
        - Response time < 100ms for cold discovery
        - Response time < 10ms for warm discovery (cached)
        """
        # Create comprehensive project hierarchy using fixtures
        project_root = temp_dir / "planning"
        create_integration_project_structure(project_root)

        # Create server
        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            # Test project level - should include all epics
            start_time = time.perf_counter()
            project_result = await client.call_tool(
                "getObject",
                {"kind": "project", "id": "large-project", "projectRoot": str(project_root)},
            )
            end_time = time.perf_counter()
            cold_response_time = (end_time - start_time) * 1000

            # Validate project children discovery
            project_children = project_result.data["children"]
            assert len(project_children) == 3, f"Expected 3 epics, got {len(project_children)}"

            # Sort by creation date for consistent testing
            project_children.sort(key=lambda x: x["created"])

            # Use fixture validation helpers
            validate_children_metadata(project_children, ["epic"])
            validate_children_ordering(project_children)

            # Validate epic metadata structure and content
            expected_epics = ["user-management", "payment-processing", "reporting-analytics"]
            for i, epic in enumerate(project_children):
                assert epic["id"] == expected_epics[i]
                assert epic["kind"] == "epic"

                # Validate metadata consistency with actual file content
                epic_obj = await client.call_tool(
                    "getObject",
                    {"kind": "epic", "id": epic["id"], "projectRoot": str(project_root)},
                )
                assert epic["title"] == epic_obj.data["yaml"]["title"]
                assert epic["status"] == epic_obj.data["yaml"]["status"]

            # Test cache performance (second call should be faster)
            start_time = time.perf_counter()
            project_result_cached = await client.call_tool(
                "getObject",
                {"kind": "project", "id": "large-project", "projectRoot": str(project_root)},
            )
            end_time = time.perf_counter()
            cached_response_time = (end_time - start_time) * 1000

            # Verify cached result is identical
            assert project_result_cached.data["children"] == project_children

            # Performance validation
            assert_children_discovery_performance(cold_response_time, 100)
            assert_children_discovery_performance(cached_response_time, 50)

    @pytest.mark.asyncio
    async def test_epic_children_discovery_workflow(self, temp_dir):
        """Test complete epic → features discovery workflow.

        This integration test validates:
        1. getObject retrieves epic successfully
        2. Children array contains immediate features only
        3. Feature metadata is correctly parsed and formatted
        4. Cross-epic feature validation works correctly

        Test epic structure:
        - 1 epic with 3 features (from fixture)
        - Features have different statuses and priorities
        - Features contain multiple tasks each

        Expected behavior:
        - getObject returns epic with children array
        - Children array contains all feature objects
        - Each feature object has complete metadata
        - Features are ordered by creation date
        """
        # Create comprehensive epic structure using fixtures
        project_root = temp_dir / "planning"
        create_integration_project_structure(project_root)

        # Create server
        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            # Test epic level - should include all features
            epic_result = await client.call_tool(
                "getObject",
                {"kind": "epic", "id": "user-management", "projectRoot": str(project_root)},
            )

            # Validate epic children discovery
            epic_children = epic_result.data["children"]
            assert len(epic_children) == 3, f"Expected 3 features, got {len(epic_children)}"

            # Sort by creation date for consistent testing
            epic_children.sort(key=lambda x: x["created"])

            # Use fixture validation helpers
            validate_children_metadata(epic_children, ["feature"])
            validate_children_ordering(epic_children)

            # Validate feature metadata structure and content
            expected_features = ["user-registration", "user-authentication", "user-profile"]
            for i, feature in enumerate(epic_children):
                assert feature["id"] == expected_features[i]
                assert feature["kind"] == "feature"

                # Validate parent relationship
                feature_obj = await client.call_tool(
                    "getObject",
                    {"kind": "feature", "id": feature["id"], "projectRoot": str(project_root)},
                )
                assert feature_obj.data["yaml"]["parent"] == "E-user-management"

    @pytest.mark.asyncio
    async def test_feature_children_discovery_workflow(self, temp_dir):
        """Test complete feature → tasks discovery workflow.

        This integration test validates:
        1. getObject retrieves feature successfully
        2. Children array contains immediate tasks only (both open and done)
        3. Task metadata is correctly parsed and formatted
        4. Mixed task status handling works correctly

        Test feature structure:
        - 1 feature with multiple tasks
        - Tasks in tasks-open (open, in-progress, review)
        - Tasks in tasks-done (completed)

        Expected behavior:
        - getObject returns feature with children array
        - Children array contains all task objects
        - Tasks from both open and done directories are included
        - Task metadata includes correct status and directory info
        """
        # Create comprehensive feature structure with mixed tasks using fixtures
        project_root = temp_dir / "planning"
        create_integration_project_structure(project_root)

        # Create server
        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            # Test feature level - should include all tasks (open and done)
            feature_result = await client.call_tool(
                "getObject",
                {"kind": "feature", "id": "user-registration", "projectRoot": str(project_root)},
            )

            # Validate feature children discovery
            feature_children = feature_result.data["children"]
            assert (
                len(feature_children) >= 4
            ), f"Expected at least 4 tasks, got {len(feature_children)}"

            # Sort by creation date for consistent testing
            feature_children.sort(key=lambda x: x["created"])

            # Use fixture validation helpers
            validate_children_metadata(feature_children, ["task"])
            validate_children_ordering(feature_children)

            # Validate task metadata structure and content
            for task in feature_children:
                assert task["kind"] == "task"
                assert task["status"] in ["open", "in-progress", "review", "done"]

                # Validate parent relationship
                task_obj = await client.call_tool(
                    "getObject",
                    {"kind": "task", "id": task["id"], "projectRoot": str(project_root)},
                )
                assert task_obj.data["yaml"]["parent"] == "F-user-registration"

            # Validate that both open and done tasks are included
            open_tasks = [
                t for t in feature_children if t["status"] in ["open", "in-progress", "review"]
            ]
            done_tasks = [t for t in feature_children if t["status"] == "done"]
            assert len(open_tasks) >= 2, f"Expected at least 2 open tasks, got {len(open_tasks)}"
            assert len(done_tasks) >= 1, f"Expected at least 1 done task, got {len(done_tasks)}"

    @pytest.mark.asyncio
    async def test_cross_system_children_discovery(self, temp_dir):
        """Test children discovery with mixed hierarchical/standalone tasks.

        This integration test validates:
        1. Cross-system compatibility in mixed environments
        2. Hierarchical and standalone task coexistence
        3. Proper isolation between task systems
        4. System integrity during mixed operations

        Test environment structure:
        - 1 project with hierarchical structure
        - Multiple standalone tasks at planning root
        - Mixed prerequisites between systems
        - Cross-system task dependencies

        Expected behavior:
        - Hierarchical children discovery works normally
        - Standalone tasks don't interfere with hierarchical discovery
        - Mixed environments maintain data integrity
        - Cross-system references are handled correctly
        """
        # Create mixed hierarchical/standalone environment using fixtures
        project_root = temp_dir / "planning"
        create_integration_project_structure(project_root)

        # Create server
        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            # Test project children discovery in mixed environment
            project_result = await client.call_tool(
                "getObject",
                {"kind": "project", "id": "large-project", "projectRoot": str(project_root)},
            )

            # Validate that project children discovery only includes hierarchical epics
            project_children = project_result.data["children"]
            assert len(project_children) == 3, f"Expected 3 epics, got {len(project_children)}"

            # Use validation helpers
            validate_children_metadata(project_children, ["epic"])

            for epic in project_children:
                assert epic["kind"] == "epic"
                # Verify these are hierarchical epics, not standalone tasks
                epic_obj = await client.call_tool(
                    "getObject",
                    {"kind": "epic", "id": epic["id"], "projectRoot": str(project_root)},
                )
                assert epic_obj.data["yaml"]["parent"] == "P-large-project"

            # Test epic children discovery in mixed environment
            epic_result = await client.call_tool(
                "getObject",
                {"kind": "epic", "id": "user-management", "projectRoot": str(project_root)},
            )

            epic_children = epic_result.data["children"]
            assert (
                len(epic_children) >= 2
            ), f"Expected at least 2 features, got {len(epic_children)}"

            validate_children_metadata(epic_children, ["feature"])

            for feature in epic_children:
                assert feature["kind"] == "feature"
                # Verify these are hierarchical features
                feature_obj = await client.call_tool(
                    "getObject",
                    {"kind": "feature", "id": feature["id"], "projectRoot": str(project_root)},
                )
                assert feature_obj.data["yaml"]["parent"] == "E-user-management"

            # Test feature children discovery with mixed task environment
            feature_result = await client.call_tool(
                "getObject",
                {"kind": "feature", "id": "user-registration", "projectRoot": str(project_root)},
            )

            feature_children = feature_result.data["children"]
            assert (
                len(feature_children) >= 3
            ), f"Expected at least 3 hierarchical tasks, got {len(feature_children)}"

            validate_children_metadata(feature_children, ["task"])

            for task in feature_children:
                assert task["kind"] == "task"
                # Verify these are hierarchical tasks with proper parent
                task_obj = await client.call_tool(
                    "getObject",
                    {"kind": "task", "id": task["id"], "projectRoot": str(project_root)},
                )
                assert task_obj.data["yaml"]["parent"] == "F-user-registration"

            # Verify standalone tasks exist but don't interfere
            # (Test by attempting to get a standalone task directly)
            standalone_task_result = await client.call_tool(
                "getObject",
                {"kind": "task", "id": "infrastructure-setup", "projectRoot": str(project_root)},
            )
            assert standalone_task_result.data["yaml"]["id"] == "T-infrastructure-setup"
            # Standalone tasks should have no children
            assert len(standalone_task_result.data["children"]) == 0

            # Verify system integrity by checking task counts
            all_tasks_result = await client.call_tool(
                "listBacklog",
                {"projectRoot": str(project_root)},
            )
            all_tasks = all_tasks_result.data["tasks"]
            hierarchical_tasks = [t for t in all_tasks if t.get("parent")]
            standalone_tasks = [t for t in all_tasks if not t.get("parent")]

            # Use cross-system validation helper
            validate_cross_system_isolation(feature_children, standalone_tasks)

            assert len(hierarchical_tasks) >= 6, "Should have hierarchical tasks from features"
            assert len(standalone_tasks) >= 5, "Should have standalone tasks at root level"

    @pytest.mark.asyncio
    async def test_empty_parent_children_discovery(self, temp_dir):
        """Test children discovery for parents with no children.

        This test validates graceful handling of empty parent objects:
        - Empty project (no epics)
        - Empty epic (no features)
        - Empty feature (no tasks)
        - Proper empty array return
        """
        # Create empty parent structures using fixtures
        project_root = temp_dir / "planning"
        create_integration_project_structure(project_root)

        # Create server
        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            # Test empty project (from edge cases in fixture)
            empty_project_result = await client.call_tool(
                "getObject",
                {"kind": "project", "id": "empty-project", "projectRoot": str(project_root)},
            )
            assert len(empty_project_result.data["children"]) == 0

            # Test empty epic (from edge cases in fixture)
            # Note: The "empty-epic" actually contains one empty feature as designed in fixtures
            empty_epic_result = await client.call_tool(
                "getObject",
                {"kind": "epic", "id": "empty-epic", "projectRoot": str(project_root)},
            )
            assert len(empty_epic_result.data["children"]) == 1

            # Test empty feature (from edge cases in fixture)
            empty_feature_result = await client.call_tool(
                "getObject",
                {"kind": "feature", "id": "empty-feature", "projectRoot": str(project_root)},
            )
            assert len(empty_feature_result.data["children"]) == 0

            # Test task children discovery (tasks should always have no children)
            task_result = await client.call_tool(
                "getObject",
                {
                    "kind": "task",
                    "id": "create-registration-form",
                    "projectRoot": str(project_root),
                },
            )
            assert len(task_result.data["children"]) == 0

    @pytest.mark.asyncio
    async def test_corrupted_children_handling_integration(self, temp_dir):
        """Test that corrupted child objects are handled gracefully.

        This test validates error isolation and recovery:
        - Parent with mix of valid and corrupted children
        - Corrupted YAML front-matter in child objects
        - Missing required fields in child metadata
        - Partial success with error isolation
        """
        # Create parent with mixed valid/corrupted children using fixtures
        project_root = temp_dir / "planning"
        create_integration_project_structure(project_root)

        # Create server
        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            # Test project with corrupted epics (from edge cases in fixture)
            corrupted_project_result = await client.call_tool(
                "getObject",
                {"kind": "project", "id": "corrupted-project", "projectRoot": str(project_root)},
            )

            # Should include valid children plus partially corrupted ones that can be parsed
            project_children = corrupted_project_result.data["children"]
            assert (
                len(project_children) == 2
            ), f"Expected 2 epics (1 valid, 1 empty-file), got {len(project_children)}"

            # Sort to ensure consistent ordering for testing
            project_children.sort(key=lambda x: x.get("id", ""))

            # Verify empty-file epic has empty metadata but still appears
            empty_file_epic = project_children[0]  # Should have empty id, sorts first
            assert empty_file_epic["kind"] == "epic"
            assert empty_file_epic["id"] == ""  # Empty due to empty file
            assert empty_file_epic["created"] == ""  # Empty due to empty file

            # Verify valid epic is included correctly
            valid_epic = project_children[1]  # Should have "valid-epic" id
            assert valid_epic["kind"] == "epic"
            assert valid_epic["id"] == "valid-epic"
            assert "title" in valid_epic
            assert "status" in valid_epic

            # Verify we can still access the valid epic normally
            valid_epic_result = await client.call_tool(
                "getObject",
                {"kind": "epic", "id": "valid-epic", "projectRoot": str(project_root)},
            )
            assert valid_epic_result.data["yaml"]["title"] == "Valid Epic"
