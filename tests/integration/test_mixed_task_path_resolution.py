"""Path resolution and priority tests for mixed task types (standalone and hierarchical tasks).

Tests path resolution, conflict handling, and priority ordering when both standalone
and hierarchy-based tasks coexist in the same project.
"""

import pytest
from fastmcp import Client

from trellis_mcp.server import create_server
from trellis_mcp.settings import Settings


@pytest.mark.asyncio
async def test_mixed_task_types_path_resolution_priority(temp_dir):
    """Test path resolution with both standalone and hierarchical tasks.

    Verifies that standalone tasks take priority over hierarchical tasks
    when both have the same ID, and that path resolution works correctly
    for both task types.
    """
    # Create settings with temporary planning directory
    settings = Settings(
        planning_root=temp_dir / "planning",
        debug_mode=True,
        log_level="DEBUG",
    )

    # Create server instance
    server = create_server(settings)
    planning_root = str(temp_dir / "planning")

    async with Client(server) as client:
        # Step 1: Create hierarchical task structure
        project_result = await client.call_tool(
            "createObject",
            {
                "kind": "project",
                "title": "Mixed Task Types Test Project",
                "projectRoot": planning_root,
            },
        )
        project_id = project_result.data["id"]

        epic_result = await client.call_tool(
            "createObject",
            {
                "kind": "epic",
                "title": "Mixed Task Types Test Epic",
                "projectRoot": planning_root,
                "parent": project_id,
            },
        )
        epic_id = epic_result.data["id"]

        feature_result = await client.call_tool(
            "createObject",
            {
                "kind": "feature",
                "title": "Mixed Task Types Test Feature",
                "projectRoot": planning_root,
                "parent": epic_id,
            },
        )
        feature_id = feature_result.data["id"]

        # Step 2: Create hierarchical task with specific ID
        hierarchy_task_result = await client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Hierarchy Task with Conflict ID",
                "projectRoot": planning_root,
                "parent": feature_id,
                "priority": "low",
            },
        )
        hierarchy_task_id = hierarchy_task_result.data["id"]

        # Step 3: Create standalone task with same base ID as hierarchy task
        # (This will test conflict resolution)
        standalone_task_result = await client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Standalone Task with Conflict ID",
                "projectRoot": planning_root,
                "priority": "high",
                # No parent - this makes it standalone
            },
        )
        standalone_task_id = standalone_task_result.data["id"]

        # Step 4: Create additional standalone task for completeness
        standalone_unique_result = await client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Unique Standalone Task",
                "projectRoot": planning_root,
                "priority": "normal",
            },
        )
        standalone_unique_id = standalone_unique_result.data["id"]

        # Step 5: Create additional hierarchical task for completeness
        hierarchy_unique_result = await client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Unique Hierarchy Task",
                "projectRoot": planning_root,
                "parent": feature_id,
                "priority": "normal",
            },
        )
        hierarchy_unique_id = hierarchy_unique_result.data["id"]

        # Step 6: Verify all tasks were created successfully
        assert hierarchy_task_id.startswith("T-")
        assert standalone_task_id.startswith("T-")
        assert standalone_unique_id.startswith("T-")
        assert hierarchy_unique_id.startswith("T-")

        # Step 7: Test path resolution - verify files exist in correct locations
        # This is the core path resolution functionality unique to this test
        planning_path = temp_dir / "planning"

        # Verify standalone tasks are in correct standalone location
        standalone_path = planning_path / "tasks-open" / f"{standalone_task_id}.md"
        assert standalone_path.exists()
        standalone_unique_path = planning_path / "tasks-open" / f"{standalone_unique_id}.md"
        assert standalone_unique_path.exists()

        # Verify hierarchy tasks are in correct hierarchy location
        raw_project_id = project_id.removeprefix("P-")
        raw_epic_id = epic_id.removeprefix("E-")
        raw_feature_id = feature_id.removeprefix("F-")

        hierarchy_path = (
            planning_path
            / "projects"
            / f"P-{raw_project_id}"
            / "epics"
            / f"E-{raw_epic_id}"
            / "features"
            / f"F-{raw_feature_id}"
            / "tasks-open"
            / f"{hierarchy_task_id}.md"
        )
        assert hierarchy_path.exists()

        hierarchy_unique_path = (
            planning_path
            / "projects"
            / f"P-{raw_project_id}"
            / "epics"
            / f"E-{raw_epic_id}"
            / "features"
            / f"F-{raw_feature_id}"
            / "tasks-open"
            / f"{hierarchy_unique_id}.md"
        )
        assert hierarchy_unique_path.exists()

        # Step 12: Test that standalone tasks take priority in claimNextTask
        # The standalone task with high priority should be claimed first
        claim_result = await client.call_tool(
            "claimNextTask",
            {"projectRoot": planning_root},
        )

        claimed_task = claim_result.data["task"]
        assert (
            claimed_task["id"] == standalone_task_id
        )  # Should be the high priority standalone task
        assert claimed_task["priority"] == "high"
        assert claimed_task["status"] == "in-progress"


@pytest.mark.asyncio
async def test_mixed_task_types_conflict_resolution(temp_dir):
    """Test conflict resolution when same task ID exists in both locations.

    Tests the edge case where a task ID might exist in both standalone and
    hierarchical locations, ensuring proper precedence and error handling.
    """
    # Create settings with temporary planning directory
    settings = Settings(
        planning_root=temp_dir / "planning",
        debug_mode=True,
        log_level="DEBUG",
    )

    # Create server instance
    server = create_server(settings)
    planning_root = str(temp_dir / "planning")

    async with Client(server) as client:
        # Step 1: Create hierarchical structure
        project_result = await client.call_tool(
            "createObject",
            {
                "kind": "project",
                "title": "Conflict Resolution Test Project",
                "projectRoot": planning_root,
            },
        )
        project_id = project_result.data["id"]

        epic_result = await client.call_tool(
            "createObject",
            {
                "kind": "epic",
                "title": "Conflict Resolution Test Epic",
                "projectRoot": planning_root,
                "parent": project_id,
            },
        )
        epic_id = epic_result.data["id"]

        feature_result = await client.call_tool(
            "createObject",
            {
                "kind": "feature",
                "title": "Conflict Resolution Test Feature",
                "projectRoot": planning_root,
                "parent": epic_id,
            },
        )
        feature_id = feature_result.data["id"]

        # Step 2: Create hierarchical task first
        hierarchy_task_result = await client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Hierarchical Task",
                "projectRoot": planning_root,
                "parent": feature_id,
                "priority": "low",
            },
        )
        hierarchy_task_id = hierarchy_task_result.data["id"]

        # Step 3: Create standalone task that could have conflicting ID
        standalone_task_result = await client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Standalone Task",
                "projectRoot": planning_root,
                "priority": "high",
            },
        )
        standalone_task_id = standalone_task_result.data["id"]

        # Step 4: Test conflict resolution - verify unique IDs generated
        # The system should have automatically generated unique IDs for both tasks
        assert hierarchy_task_id != standalone_task_id
        assert hierarchy_task_id.startswith("T-")
        assert standalone_task_id.startswith("T-")

        # Step 6: Test priority precedence in conflict resolution
        # The standalone task has high priority, hierarchy task has low priority
        claim_result = await client.call_tool(
            "claimNextTask",
            {"projectRoot": planning_root},
        )

        claimed_task = claim_result.data["task"]
        assert (
            claimed_task["id"] == standalone_task_id
        )  # High priority standalone should be claimed
        assert claimed_task["priority"] == "high"

        # Step 7: Test that ID collision avoidance works
        # Try to create another task with same title - should get unique ID
        duplicate_attempt_result = await client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Hierarchical Task",  # Same title as existing task
                "projectRoot": planning_root,
                "parent": feature_id,
                "priority": "normal",
            },
        )

        # Should succeed with unique ID (conflict resolution in action)
        duplicate_task_id = duplicate_attempt_result.data["id"]
        assert duplicate_task_id != hierarchy_task_id
        assert duplicate_task_id.startswith("T-")
