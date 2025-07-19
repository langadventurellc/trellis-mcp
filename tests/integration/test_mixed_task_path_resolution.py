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

        # Step 7: Verify tasks exist in correct locations
        planning_path = temp_dir / "planning"

        # Standalone tasks should be in tasks-open directory
        standalone_path = planning_path / "tasks-open" / f"{standalone_task_id}.md"
        assert standalone_path.exists()

        standalone_unique_path = planning_path / "tasks-open" / f"{standalone_unique_id}.md"
        assert standalone_unique_path.exists()

        # Hierarchy tasks should be in feature directory
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

        # Step 8: Test getObject retrieval for all tasks
        # Both standalone and hierarchy tasks should be retrievable
        standalone_retrieved = await client.call_tool(
            "getObject",
            {
                "kind": "task",
                "id": standalone_task_id,
                "projectRoot": planning_root,
            },
        )
        assert standalone_retrieved.data["yaml"]["title"] == "Standalone Task with Conflict ID"
        assert standalone_retrieved.data["yaml"].get("parent") is None

        hierarchy_retrieved = await client.call_tool(
            "getObject",
            {
                "kind": "task",
                "id": hierarchy_task_id,
                "projectRoot": planning_root,
            },
        )
        assert hierarchy_retrieved.data["yaml"]["title"] == "Hierarchy Task with Conflict ID"
        assert hierarchy_retrieved.data["yaml"]["parent"] == feature_id

        # Step 9: Test that both task types appear in listBacklog
        all_tasks_result = await client.call_tool(
            "listBacklog",
            {"projectRoot": planning_root},
        )
        assert all_tasks_result.structured_content is not None
        all_tasks = all_tasks_result.structured_content["tasks"]

        # Should find all 4 tasks (2 standalone + 2 hierarchy)
        assert len(all_tasks) == 4

        # Verify task IDs are present
        task_ids = {task["id"] for task in all_tasks}
        expected_ids = {
            standalone_task_id,
            standalone_unique_id,
            hierarchy_task_id,
            hierarchy_unique_id,
        }
        assert task_ids == expected_ids

        # Step 10: Test feature-scoped listing (should only show hierarchy tasks)
        feature_tasks_result = await client.call_tool(
            "listBacklog",
            {"projectRoot": planning_root, "scope": feature_id},
        )
        assert feature_tasks_result.structured_content is not None
        feature_tasks = feature_tasks_result.structured_content["tasks"]

        # Should only find hierarchy tasks (2 tasks)
        assert len(feature_tasks) == 2
        feature_task_ids = {task["id"] for task in feature_tasks}
        assert feature_task_ids == {hierarchy_task_id, hierarchy_unique_id}

        # Step 11: Test priority ordering with mixed task types
        # Verify that priority ordering works across both task types
        priorities = [task["priority"] for task in all_tasks]
        priority_order = {"high": 1, "normal": 2, "low": 3}

        for i in range(len(all_tasks) - 1):
            current_priority = priority_order[priorities[i]]
            next_priority = priority_order[priorities[i + 1]]
            assert current_priority <= next_priority, f"Priority ordering failed at position {i}"

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

        # Step 4: Verify both tasks exist and have different IDs
        # (The system should have generated unique IDs automatically)
        assert hierarchy_task_id != standalone_task_id
        assert hierarchy_task_id.startswith("T-")
        assert standalone_task_id.startswith("T-")

        # Step 5: Test path resolution for both tasks
        hierarchy_retrieved = await client.call_tool(
            "getObject",
            {
                "kind": "task",
                "id": hierarchy_task_id,
                "projectRoot": planning_root,
            },
        )
        assert hierarchy_retrieved.data["yaml"]["title"] == "Hierarchical Task"
        assert hierarchy_retrieved.data["yaml"]["parent"] == feature_id

        standalone_retrieved = await client.call_tool(
            "getObject",
            {
                "kind": "task",
                "id": standalone_task_id,
                "projectRoot": planning_root,
            },
        )
        assert standalone_retrieved.data["yaml"]["title"] == "Standalone Task"
        assert standalone_retrieved.data["yaml"].get("parent") is None

        # Step 6: Test that listBacklog finds both tasks
        all_tasks_result = await client.call_tool(
            "listBacklog",
            {"projectRoot": planning_root},
        )
        assert all_tasks_result.structured_content is not None
        all_tasks = all_tasks_result.structured_content["tasks"]

        assert len(all_tasks) == 2
        task_ids = {task["id"] for task in all_tasks}
        assert task_ids == {hierarchy_task_id, standalone_task_id}

        # Step 7: Test priority precedence in claimNextTask
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

        # Step 8: Test scoped filtering works correctly
        # Feature scope should only show hierarchy task
        feature_tasks_result = await client.call_tool(
            "listBacklog",
            {"projectRoot": planning_root, "scope": feature_id},
        )
        assert feature_tasks_result.structured_content is not None
        feature_tasks = feature_tasks_result.structured_content["tasks"]

        assert len(feature_tasks) == 1
        assert feature_tasks[0]["id"] == hierarchy_task_id

        # Step 9: Test that updates work correctly for both task types
        # Update hierarchy task
        await client.call_tool(
            "updateObject",
            {
                "kind": "task",
                "id": hierarchy_task_id,
                "projectRoot": planning_root,
                "yamlPatch": {"priority": "normal"},
            },
        )

        # Update standalone task
        await client.call_tool(
            "updateObject",
            {
                "kind": "task",
                "id": standalone_task_id,
                "projectRoot": planning_root,
                "yamlPatch": {"status": "review"},
            },
        )

        # Verify updates
        updated_hierarchy = await client.call_tool(
            "getObject",
            {
                "kind": "task",
                "id": hierarchy_task_id,
                "projectRoot": planning_root,
            },
        )
        assert updated_hierarchy.data["yaml"]["priority"] == "normal"

        updated_standalone = await client.call_tool(
            "getObject",
            {
                "kind": "task",
                "id": standalone_task_id,
                "projectRoot": planning_root,
            },
        )
        assert updated_standalone.data["yaml"]["status"] == "review"

        # Step 10: Test error handling - try to create task with existing ID
        # This should still work as the system generates unique IDs
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

        # Should succeed with unique ID
        duplicate_task_id = duplicate_attempt_result.data["id"]
        assert duplicate_task_id != hierarchy_task_id
        assert duplicate_task_id.startswith("T-")

        # Verify the new task exists
        duplicate_retrieved = await client.call_tool(
            "getObject",
            {
                "kind": "task",
                "id": duplicate_task_id,
                "projectRoot": planning_root,
            },
        )
        assert duplicate_retrieved.data["yaml"]["title"] == "Hierarchical Task"
