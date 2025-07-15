"""Concurrent operations tests.

Tests server's ability to handle multiple simultaneous client connections,
concurrent task claiming, and multi-agent scenarios.
"""

import asyncio

import pytest
from fastmcp import Client

from .test_helpers import create_test_hierarchy, create_test_server


@pytest.mark.asyncio
async def test_concurrent_client_connections(temp_dir):
    """Test server handles multiple concurrent client connections."""
    # Create server instance
    server, planning_root = create_test_server(temp_dir)

    async def client_task():
        """Single client task for concurrent testing."""
        async with Client(server) as client:
            await client.ping()
            result = await client.call_tool("health_check")
            return result.data["status"]

    # Create multiple concurrent client connections
    tasks = [client_task() for _ in range(5)]
    results = await asyncio.gather(*tasks)

    # Verify all connections succeeded
    assert all(status == "healthy" for status in results)
    assert len(results) == 5


@pytest.mark.asyncio
async def test_two_agents_claim_tasks_sequentially_verify_priority_order(temp_dir):
    """Integration test: two agents claim tasks sequentially, verify priority ordering."""
    # Create server instance
    server, planning_root = create_test_server(temp_dir)

    # Setup: Create test hierarchy with mixed priority tasks
    async with Client(server) as setup_client:
        hierarchy = await create_test_hierarchy(
            setup_client, planning_root, "Multi-Agent Priority Test Project"
        )
        feature_id = hierarchy["feature_id"]

        # Create multiple tasks with different priorities
        # High priority tasks (should be claimed first)
        high_task1_result = await setup_client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "High Priority Task 1",
                "projectRoot": planning_root,
                "parent": feature_id,
                "priority": "high",
            },
        )
        high_task1_id = high_task1_result.data["id"]

        high_task2_result = await setup_client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "High Priority Task 2",
                "projectRoot": planning_root,
                "parent": feature_id,
                "priority": "high",
            },
        )
        high_task2_id = high_task2_result.data["id"]

        # Normal priority task
        normal_task_result = await setup_client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Normal Priority Task",
                "projectRoot": planning_root,
                "parent": feature_id,
                "priority": "normal",
            },
        )
        normal_task_id = normal_task_result.data["id"]

        # Low priority task
        low_task_result = await setup_client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Low Priority Task",
                "projectRoot": planning_root,
                "parent": feature_id,
                "priority": "low",
            },
        )
        low_task_id = low_task_result.data["id"]

    # Main test: Two agents claiming tasks sequentially
    claimed_tasks = []

    # Agent 1 claims first task
    async with Client(server) as agent1:
        result1 = await agent1.call_tool(
            "claimNextTask", {"projectRoot": planning_root, "worktree": "agent1-workspace"}
        )
        claimed_task1 = result1.data["task"]
        claimed_tasks.append((claimed_task1, "agent1"))

        # Verify agent1 claimed a high priority task
        assert claimed_task1["priority"] == "high"
        assert result1.data["worktree"] == "agent1-workspace"
        assert result1.data["claimed_status"] == "in-progress"

    # Agent 2 claims second task
    async with Client(server) as agent2:
        result2 = await agent2.call_tool(
            "claimNextTask", {"projectRoot": planning_root, "worktree": "agent2-workspace"}
        )
        claimed_task2 = result2.data["task"]
        claimed_tasks.append((claimed_task2, "agent2"))

        # Verify agent2 claimed the remaining high priority task
        assert claimed_task2["priority"] == "high"
        assert result2.data["worktree"] == "agent2-workspace"
        assert result2.data["claimed_status"] == "in-progress"

    # Agent 1 claims third task
    async with Client(server) as agent1:
        result3 = await agent1.call_tool(
            "claimNextTask", {"projectRoot": planning_root, "worktree": "agent1-workspace"}
        )
        claimed_task3 = result3.data["task"]
        claimed_tasks.append((claimed_task3, "agent1"))

        # Verify agent1 claimed the normal priority task (no more high priority available)
        assert claimed_task3["priority"] == "normal"

    # Agent 2 claims fourth task
    async with Client(server) as agent2:
        result4 = await agent2.call_tool(
            "claimNextTask", {"projectRoot": planning_root, "worktree": "agent2-workspace"}
        )
        claimed_task4 = result4.data["task"]
        claimed_tasks.append((claimed_task4, "agent2"))

        # Verify agent2 claimed the low priority task (last remaining)
        assert claimed_task4["priority"] == "low"

    # Verify overall priority ordering: high → high → normal → low
    priorities = [task["priority"] for task, _ in claimed_tasks]
    assert priorities == ["high", "high", "normal", "low"]

    # Verify all expected tasks were claimed
    claimed_ids = {task["id"] for task, _ in claimed_tasks}
    expected_ids = {high_task1_id, high_task2_id, normal_task_id, low_task_id}
    assert claimed_ids == expected_ids

    # Verify each task was claimed by exactly one agent
    assert len(claimed_tasks) == 4
    assert len(set(task["id"] for task, _ in claimed_tasks)) == 4

    # Verify alternating agent assignments
    agents = [agent for _, agent in claimed_tasks]
    assert agents == ["agent1", "agent2", "agent1", "agent2"]

    # Verify no more tasks available
    async with Client(server) as agent1:
        with pytest.raises(Exception) as exc_info:
            await agent1.call_tool("claimNextTask", {"projectRoot": planning_root})
        assert "No open tasks available" in str(exc_info.value)


@pytest.mark.asyncio
async def test_two_sequential_claims_with_different_worktree_values_persist_to_disk(temp_dir):
    """Integration test: two sequential claimNextTask calls with different worktreePath values.

    Verify each task gets unique worktree stamp and persists to disk.
    """
    # Create server instance
    server, planning_root = create_test_server(temp_dir)

    # Setup: Create test hierarchy with two tasks
    async with Client(server) as setup_client:
        hierarchy = await create_test_hierarchy(
            setup_client, planning_root, "Worktree Test Project"
        )
        feature_id = hierarchy["feature_id"]

        # Create first task
        task1_result = await setup_client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "First Task",
                "projectRoot": planning_root,
                "parent": feature_id,
                "priority": "high",
            },
        )
        task1_id = task1_result.data["id"]

        # Create second task
        task2_result = await setup_client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Second Task",
                "projectRoot": planning_root,
                "parent": feature_id,
                "priority": "normal",
            },
        )
        task2_id = task2_result.data["id"]

    # Test: Two sequential claimNextTask calls with different worktree values

    # First claim with worktree="workspace-1"
    async with Client(server) as client1:
        result1 = await client1.call_tool(
            "claimNextTask", {"projectRoot": planning_root, "worktree": "workspace-1"}
        )
        claimed_task1 = result1.data["task"]

        # Verify first task claimed (high priority first)
        assert claimed_task1["id"] == task1_id
        assert claimed_task1["priority"] == "high"
        assert claimed_task1["status"] == "in-progress"

        # Verify API response contains worktree value
        assert result1.data["worktree"] == "workspace-1"

    # Second claim with worktree="workspace-2"
    async with Client(server) as client2:
        result2 = await client2.call_tool(
            "claimNextTask", {"projectRoot": planning_root, "worktree": "workspace-2"}
        )
        claimed_task2 = result2.data["task"]

        # Verify second task claimed (normal priority second)
        assert claimed_task2["id"] == task2_id
        assert claimed_task2["priority"] == "normal"
        assert claimed_task2["status"] == "in-progress"

        # Verify API response contains different worktree value
        assert result2.data["worktree"] == "workspace-2"

    # Critical: Verify worktree values persist to disk in YAML files
    from .test_helpers import build_task_path

    project_id = hierarchy["project_id"]
    epic_id = hierarchy["epic_id"]

    task1_file = build_task_path(temp_dir, project_id, epic_id, feature_id, task1_id)
    task2_file = build_task_path(temp_dir, project_id, epic_id, feature_id, task2_id)

    # Verify both task files exist
    assert task1_file.exists(), f"Task 1 file not found: {task1_file}"
    assert task2_file.exists(), f"Task 2 file not found: {task2_file}"

    # Read task file contents and verify worktree values persist in YAML
    task1_content = task1_file.read_text()
    task2_content = task2_file.read_text()

    # Verify task1 YAML contains worktree: "workspace-1"
    assert 'worktree: "workspace-1"' in task1_content or "worktree: workspace-1" in task1_content
    assert f"id: {task1_id}" in task1_content
    assert "status: in-progress" in task1_content

    # Verify task2 YAML contains worktree: "workspace-2"
    assert 'worktree: "workspace-2"' in task2_content or "worktree: workspace-2" in task2_content
    assert f"id: {task2_id}" in task2_content
    assert "status: in-progress" in task2_content

    # Verify each task has unique worktree stamp
    assert (
        'worktree: "workspace-1"' not in task2_content
        and "worktree: workspace-1" not in task2_content
    )
    assert (
        'worktree: "workspace-2"' not in task1_content
        and "worktree: workspace-2" not in task1_content
    )
