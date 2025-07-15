"""Dependency management tests.

Tests prerequisite handling, cycle detection, and dependency validation.
"""

import pytest
from fastmcp import Client

from .test_helpers import create_test_hierarchy, create_test_server


@pytest.mark.asyncio
async def test_cycle_detection_integration_with_updateObject(temp_dir):
    """Integration test: create three tasks, attempt invalid update that introduces cycle.

    Assert error & original graph intact.
    """
    # Create server instance
    server, planning_root = create_test_server(temp_dir)

    async with Client(server) as client:
        # Step 1: Create complete hierarchy (project → epic → feature)
        hierarchy = await create_test_hierarchy(
            client, planning_root, "Cycle Detection Test Project"
        )
        feature_id = hierarchy["feature_id"]

        # Step 2: Create three tasks with valid prerequisites (A → B → C, no cycle)
        task_a_result = await client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Task A",
                "projectRoot": planning_root,
                "parent": feature_id,
                "prerequisites": [],  # No prerequisites
            },
        )
        task_a_id = task_a_result.data["id"]

        task_b_result = await client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Task B",
                "projectRoot": planning_root,
                "parent": feature_id,
                "prerequisites": [task_a_id],  # B depends on A
            },
        )
        task_b_id = task_b_result.data["id"]

        task_c_result = await client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Task C",
                "projectRoot": planning_root,
                "parent": feature_id,
                "prerequisites": [task_b_id],  # C depends on B
            },
        )
        task_c_id = task_c_result.data["id"]

        # Step 3: Verify initial state - no cycle exists
        initial_task_a = await client.call_tool(
            "getObject",
            {
                "kind": "task",
                "id": task_a_id,
                "projectRoot": planning_root,
            },
        )
        initial_task_b = await client.call_tool(
            "getObject",
            {
                "kind": "task",
                "id": task_b_id,
                "projectRoot": planning_root,
            },
        )
        initial_task_c = await client.call_tool(
            "getObject",
            {
                "kind": "task",
                "id": task_c_id,
                "projectRoot": planning_root,
            },
        )

        # Verify initial prerequisites are correct
        assert initial_task_a.data["yaml"]["prerequisites"] == []
        assert initial_task_b.data["yaml"]["prerequisites"] == [task_a_id]
        assert initial_task_c.data["yaml"]["prerequisites"] == [task_b_id]

        # Step 4: Attempt to create a cycle by updating Task A to depend on Task C
        # This would create: A → C → B → A (cycle)
        with pytest.raises(Exception) as exc_info:
            await client.call_tool(
                "updateObject",
                {
                    "kind": "task",
                    "id": task_a_id,
                    "projectRoot": planning_root,
                    "yamlPatch": {"prerequisites": [task_c_id]},
                },
            )

        # Step 5: Verify the error message indicates circular dependencies
        error_message = str(exc_info.value)
        assert "circular dependencies in prerequisites" in error_message

        # Step 6: Verify original graph remains intact after failed cycle creation
        # Check that Task A still has no prerequisites (rollback successful)
        restored_task_a = await client.call_tool(
            "getObject",
            {
                "kind": "task",
                "id": task_a_id,
                "projectRoot": planning_root,
            },
        )
        assert restored_task_a.data["yaml"]["prerequisites"] == []

        # Check that Task B still depends on Task A (unchanged)
        restored_task_b = await client.call_tool(
            "getObject",
            {
                "kind": "task",
                "id": task_b_id,
                "projectRoot": planning_root,
            },
        )
        assert restored_task_b.data["yaml"]["prerequisites"] == [task_a_id]

        # Check that Task C still depends on Task B (unchanged)
        restored_task_c = await client.call_tool(
            "getObject",
            {
                "kind": "task",
                "id": task_c_id,
                "projectRoot": planning_root,
            },
        )
        assert restored_task_c.data["yaml"]["prerequisites"] == [task_b_id]

        # Step 7: Final verification - entire graph remains valid
        # Verify no files were corrupted by attempting to list backlog
        backlog_result = await client.call_tool(
            "listBacklog",
            {
                "projectRoot": planning_root,
                "scope": feature_id,
            },
        )
        assert backlog_result.structured_content is not None
        tasks = backlog_result.structured_content["tasks"]
        assert len(tasks) == 3  # All three tasks should still exist

        # Verify all task IDs are present and correct
        task_ids = {task["id"] for task in tasks}
        assert task_ids == {task_a_id, task_b_id, task_c_id}

        # Note: listBacklog doesn't include prerequisites in response
        # Prerequisites integrity was already verified via getObject calls above
