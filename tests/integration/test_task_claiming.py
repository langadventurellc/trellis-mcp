"""Task claiming tests.

Tests task claiming logic, priority ordering, and claim validation.
"""

import pytest
from fastmcp import Client

from .test_helpers import create_test_hierarchy, create_test_server


@pytest.mark.asyncio
async def test_claim_next_task_returns_high_priority_before_normal(temp_dir):
    """Integration test: create two tasks + satisfied prereqs, expect high priority first."""
    # Create server instance
    server, planning_root = create_test_server(temp_dir)

    # Setup: Create test hierarchy with high and normal priority tasks
    async with Client(server) as setup_client:
        hierarchy = await create_test_hierarchy(
            setup_client, planning_root, "Priority Test Project"
        )
        feature_id = hierarchy["feature_id"]

        # Create normal priority task (created first, should be older)
        await setup_client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Normal Priority Task",
                "projectRoot": planning_root,
                "parent": feature_id,
                "priority": "normal",
            },
        )

        # Create high priority task (created second, should be newer)
        high_task_result = await setup_client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "High Priority Task",
                "projectRoot": planning_root,
                "parent": feature_id,
                "priority": "high",
            },
        )
        high_task_id = high_task_result.data["id"]

    # Test: Call claimNextTask and verify high priority task is returned first
    async with Client(server) as client:
        result = await client.call_tool("claimNextTask", {"projectRoot": planning_root})

        # Verify the high priority task was claimed first (despite being created later)
        claimed_task = result.data["task"]
        assert claimed_task["priority"] == "high"
        assert claimed_task["title"] == "High Priority Task"
        assert claimed_task["id"] == high_task_id

        # Verify response structure
        assert result.data["claimed_status"] == "in-progress"
        assert "file_path" in result.data

        # Verify the task status was updated
        assert claimed_task["status"] == "in-progress"
