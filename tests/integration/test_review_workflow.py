"""Review workflow tests.

Tests review process, task status transitions, and getNextReviewableTask functionality.
"""

import pytest
from fastmcp import Client

from .test_helpers import create_test_hierarchy, create_test_server


@pytest.mark.asyncio
async def test_getNextReviewableTask_integration_with_mixed_status_tasks(temp_dir):
    """Integration test: create sample repo with mixed status tasks.

    Call getNextReviewableTask RPC via FastMCP test client, assert correct task ID returned.
    """
    # Create server instance
    server, planning_root = create_test_server(temp_dir)

    # Setup: Create test hierarchy with mixed status tasks
    async with Client(server) as setup_client:
        hierarchy = await create_test_hierarchy(setup_client, planning_root, "Review Test Project")
        feature_id = hierarchy["feature_id"]

        # Create tasks with mixed statuses
        # 1. Open task (should not be returned)
        await setup_client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Open Task",
                "projectRoot": planning_root,
                "parent": feature_id,
                "priority": "normal",
            },
        )

        # 2. In-progress task (should not be returned)
        in_progress_task_result = await setup_client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "In Progress Task",
                "projectRoot": planning_root,
                "parent": feature_id,
                "priority": "high",
            },
        )
        in_progress_task_id = in_progress_task_result.data["id"]

        # Update to in-progress status
        await setup_client.call_tool(
            "updateObject",
            {
                "id": in_progress_task_id,
                "projectRoot": planning_root,
                "yamlPatch": {"status": "in-progress"},
            },
        )

        # 3. Review task with high priority (should be returned since it will be updated first)
        review_task_high_result = await setup_client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Review Task High Priority",
                "projectRoot": planning_root,
                "parent": feature_id,
                "priority": "high",
            },
        )
        review_task_high_id = review_task_high_result.data["id"]

        # Update to in-progress status first, then review
        await setup_client.call_tool(
            "updateObject",
            {
                "id": review_task_high_id,
                "projectRoot": planning_root,
                "yamlPatch": {"status": "in-progress"},
            },
        )

        await setup_client.call_tool(
            "updateObject",
            {
                "id": review_task_high_id,
                "projectRoot": planning_root,
                "yamlPatch": {"status": "review"},
            },
        )

        # 4. Review task with normal priority (returned second due to newer timestamp)
        review_task_normal_result = await setup_client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Review Task Normal Priority",
                "projectRoot": planning_root,
                "parent": feature_id,
                "priority": "normal",
            },
        )
        review_task_normal_id = review_task_normal_result.data["id"]

        # Update to in-progress status first, then review
        await setup_client.call_tool(
            "updateObject",
            {
                "id": review_task_normal_id,
                "projectRoot": planning_root,
                "yamlPatch": {"status": "in-progress"},
            },
        )

        await setup_client.call_tool(
            "updateObject",
            {
                "id": review_task_normal_id,
                "projectRoot": planning_root,
                "yamlPatch": {"status": "review"},
            },
        )

    # Test 1: Call getNextReviewableTask and verify high priority review task is returned
    async with Client(server) as client:
        result = await client.call_tool(
            "getNextReviewableTask",
            {
                "projectRoot": planning_root,
            },
        )

        # Verify response structure
        assert result.data is not None
        assert "task" in result.data
        task_data = result.data["task"]

        # Verify correct task returned (high priority review task due to oldest update timestamp)
        assert task_data is not None
        assert task_data["id"] == review_task_high_id
        assert task_data["title"] == "Review Task High Priority"
        assert task_data["status"] == "review"
        assert task_data["priority"] == "high"
        assert task_data["parent"] == feature_id

        # Verify additional required fields
        assert "file_path" in task_data
        assert "created" in task_data
        assert "updated" in task_data

        # Verify file_path is a valid path string
        assert task_data["file_path"].endswith(f"{review_task_high_id}.md")

    # Test 2: Complete the high priority task and verify normal priority task is returned next
    async with Client(server) as client:
        # Mark high priority task as done using completeTask
        await client.call_tool(
            "completeTask",
            {
                "taskId": review_task_high_id,
                "projectRoot": planning_root,
            },
        )

        # Now call getNextReviewableTask again
        result = await client.call_tool(
            "getNextReviewableTask",
            {
                "projectRoot": planning_root,
            },
        )

        # Verify normal priority review task is now returned
        assert result.data is not None
        task_data = result.data["task"]
        assert task_data is not None
        assert task_data["id"] == review_task_normal_id
        assert task_data["title"] == "Review Task Normal Priority"
        assert task_data["priority"] == "normal"

    # Test 3: Complete remaining review task and verify no more reviewable tasks
    async with Client(server) as client:
        # Complete the normal priority task
        await client.call_tool(
            "completeTask",
            {
                "taskId": review_task_normal_id,
                "projectRoot": planning_root,
            },
        )

        # Call getNextReviewableTask - should return None
        result = await client.call_tool(
            "getNextReviewableTask",
            {
                "projectRoot": planning_root,
            },
        )

        # Verify no reviewable tasks remaining
        assert result.data is not None
        assert result.data["task"] is None
