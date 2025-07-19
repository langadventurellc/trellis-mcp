"""Task lifecycle and workflow tests for mixed task types.

Tests task claiming, completion, review workflows, and performance benchmarks
when both standalone and hierarchical tasks coexist in the same project.
"""

import asyncio

import pytest
from fastmcp import Client

from trellis_mcp.server import create_server
from trellis_mcp.settings import Settings


@pytest.mark.asyncio
async def test_comprehensive_review_workflow_mixed_tasks(temp_dir):
    """Test comprehensive review workflow functionality with mixed task environments.

    Enhanced test covering getNextReviewableTask with standalone and hierarchical tasks,
    ensuring correct priority ordering and timestamp handling across both task types.
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
                "title": "Review Workflow Test Project",
                "projectRoot": planning_root,
            },
        )
        project_id = project_result.data["id"]

        epic_result = await client.call_tool(
            "createObject",
            {
                "kind": "epic",
                "title": "Review Workflow Test Epic",
                "projectRoot": planning_root,
                "parent": project_id,
            },
        )
        epic_id = epic_result.data["id"]

        feature_result = await client.call_tool(
            "createObject",
            {
                "kind": "feature",
                "title": "Review Workflow Test Feature",
                "projectRoot": planning_root,
                "parent": epic_id,
            },
        )
        feature_id = feature_result.data["id"]

        # Step 2: Create mixed tasks with different priorities and timestamps
        # Strategy: Create tasks in specific order to test timestamp ordering

        # First, create standalone high priority task
        standalone_high_result = await client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Standalone High Priority Review Task",
                "projectRoot": planning_root,
                "priority": "high",
            },
        )
        standalone_high_id = standalone_high_result.data["id"]

        # Short delay to ensure different timestamps
        await asyncio.sleep(0.1)

        # Create hierarchy normal priority task
        hierarchy_normal_result = await client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Hierarchy Normal Priority Review Task",
                "projectRoot": planning_root,
                "parent": feature_id,
                "priority": "normal",
            },
        )
        hierarchy_normal_id = hierarchy_normal_result.data["id"]

        await asyncio.sleep(0.1)

        # Create standalone normal priority task
        standalone_normal_result = await client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Standalone Normal Priority Review Task",
                "projectRoot": planning_root,
                "priority": "normal",
            },
        )
        standalone_normal_id = standalone_normal_result.data["id"]

        await asyncio.sleep(0.1)

        # Create hierarchy high priority task (created last)
        hierarchy_high_result = await client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Hierarchy High Priority Review Task",
                "projectRoot": planning_root,
                "parent": feature_id,
                "priority": "high",
            },
        )
        hierarchy_high_id = hierarchy_high_result.data["id"]

        # Step 3: Transition all tasks to review status in reverse creation order
        # This ensures different updated timestamps while maintaining creation order

        # Update hierarchy high (created last, updated first)
        await client.call_tool(
            "updateObject",
            {
                "kind": "task",
                "id": hierarchy_high_id,
                "projectRoot": planning_root,
                "yamlPatch": {"status": "in-progress"},
            },
        )
        await client.call_tool(
            "updateObject",
            {
                "kind": "task",
                "id": hierarchy_high_id,
                "projectRoot": planning_root,
                "yamlPatch": {"status": "review"},
            },
        )

        await asyncio.sleep(0.1)

        # Update standalone normal (created third, updated second)
        await client.call_tool(
            "updateObject",
            {
                "kind": "task",
                "id": standalone_normal_id,
                "projectRoot": planning_root,
                "yamlPatch": {"status": "in-progress"},
            },
        )
        await client.call_tool(
            "updateObject",
            {
                "kind": "task",
                "id": standalone_normal_id,
                "projectRoot": planning_root,
                "yamlPatch": {"status": "review"},
            },
        )

        await asyncio.sleep(0.1)

        # Update hierarchy normal (created second, updated third)
        await client.call_tool(
            "updateObject",
            {
                "kind": "task",
                "id": hierarchy_normal_id,
                "projectRoot": planning_root,
                "yamlPatch": {"status": "in-progress"},
            },
        )
        await client.call_tool(
            "updateObject",
            {
                "kind": "task",
                "id": hierarchy_normal_id,
                "projectRoot": planning_root,
                "yamlPatch": {"status": "review"},
            },
        )

        await asyncio.sleep(0.1)

        # Update standalone high (created first, updated last)
        await client.call_tool(
            "updateObject",
            {
                "kind": "task",
                "id": standalone_high_id,
                "projectRoot": planning_root,
                "yamlPatch": {"status": "in-progress"},
            },
        )
        await client.call_tool(
            "updateObject",
            {
                "kind": "task",
                "id": standalone_high_id,
                "projectRoot": planning_root,
                "yamlPatch": {"status": "review"},
            },
        )

        # Step 4: Test getNextReviewableTask returns oldest updated task
        # Should return hierarchy_high_id (updated first, regardless of creation order)
        review_result = await client.call_tool(
            "getNextReviewableTask",
            {"projectRoot": planning_root},
        )

        assert review_result.data is not None
        assert review_result.data["task"] is not None
        first_task = review_result.data["task"]
        assert first_task["id"] == hierarchy_high_id
        assert first_task["status"] == "review"
        assert first_task["priority"] == "high"

        # Step 5: Complete first task and verify next one is returned
        await client.call_tool(
            "completeTask",
            {
                "taskId": hierarchy_high_id,
                "projectRoot": planning_root,
            },
        )

        # Next should be standalone_normal_id (updated second)
        review_result = await client.call_tool(
            "getNextReviewableTask",
            {"projectRoot": planning_root},
        )

        assert review_result.data is not None
        assert review_result.data["task"] is not None
        second_task = review_result.data["task"]
        assert second_task["id"] == standalone_normal_id
        assert second_task["status"] == "review"
        assert second_task["priority"] == "normal"

        # Step 6: Test that both standalone and hierarchy tasks appear in review queue
        # Complete second task
        await client.call_tool(
            "completeTask",
            {
                "taskId": standalone_normal_id,
                "projectRoot": planning_root,
            },
        )

        # Next should be hierarchy_normal_id (updated third)
        review_result = await client.call_tool(
            "getNextReviewableTask",
            {"projectRoot": planning_root},
        )

        assert review_result.data is not None
        assert review_result.data["task"] is not None
        third_task = review_result.data["task"]
        assert third_task["id"] == hierarchy_normal_id
        assert third_task["status"] == "review"
        assert third_task["priority"] == "normal"

        # Step 7: Complete third task and verify final standalone task
        await client.call_tool(
            "completeTask",
            {
                "taskId": hierarchy_normal_id,
                "projectRoot": planning_root,
            },
        )

        # Final should be standalone_high_id (updated last)
        review_result = await client.call_tool(
            "getNextReviewableTask",
            {"projectRoot": planning_root},
        )

        assert review_result.data is not None
        assert review_result.data["task"] is not None
        final_task = review_result.data["task"]
        assert final_task["id"] == standalone_high_id
        assert final_task["status"] == "review"
        assert final_task["priority"] == "high"

        # Step 8: Complete final task and verify no more reviewable tasks
        await client.call_tool(
            "completeTask",
            {
                "taskId": standalone_high_id,
                "projectRoot": planning_root,
            },
        )

        # Should return None
        review_result = await client.call_tool(
            "getNextReviewableTask",
            {"projectRoot": planning_root},
        )

        assert review_result.data is not None
        assert review_result.data["task"] is None


@pytest.mark.asyncio
async def test_comprehensive_task_lifecycle_mixed_environments(temp_dir):
    """Test complete task lifecycle across both standalone and hierarchical task types.

    Tests creation, claiming, status transitions, and completion for both task types
    to ensure consistency and proper file movement operations.
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
        # Step 1: Create hierarchical structure for hierarchy tasks
        project_result = await client.call_tool(
            "createObject",
            {
                "kind": "project",
                "title": "Task Lifecycle Test Project",
                "projectRoot": planning_root,
            },
        )
        project_id = project_result.data["id"]

        epic_result = await client.call_tool(
            "createObject",
            {
                "kind": "epic",
                "title": "Task Lifecycle Test Epic",
                "projectRoot": planning_root,
                "parent": project_id,
            },
        )
        epic_id = epic_result.data["id"]

        feature_result = await client.call_tool(
            "createObject",
            {
                "kind": "feature",
                "title": "Task Lifecycle Test Feature",
                "projectRoot": planning_root,
                "parent": epic_id,
            },
        )
        feature_id = feature_result.data["id"]

        # Step 2: Create mixed task types for lifecycle testing
        # Create standalone task
        standalone_task_result = await client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Standalone Lifecycle Task",
                "projectRoot": planning_root,
                "priority": "high",
            },
        )
        standalone_task_id = standalone_task_result.data["id"]

        # Create hierarchy task
        hierarchy_task_result = await client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Hierarchy Lifecycle Task",
                "projectRoot": planning_root,
                "parent": feature_id,
                "priority": "normal",
            },
        )
        hierarchy_task_id = hierarchy_task_result.data["id"]

        # Step 3: Verify initial state - both tasks should be in open status
        standalone_initial = await client.call_tool(
            "getObject",
            {
                "kind": "task",
                "id": standalone_task_id,
                "projectRoot": planning_root,
            },
        )
        assert standalone_initial.data["yaml"]["status"] == "open"
        assert standalone_initial.data["yaml"]["priority"] == "high"
        assert standalone_initial.data["yaml"].get("parent") is None

        hierarchy_initial = await client.call_tool(
            "getObject",
            {
                "kind": "task",
                "id": hierarchy_task_id,
                "projectRoot": planning_root,
            },
        )
        assert hierarchy_initial.data["yaml"]["status"] == "open"
        assert hierarchy_initial.data["yaml"]["priority"] == "normal"
        assert hierarchy_initial.data["yaml"]["parent"] == feature_id

        # Step 4: Test claiming - standalone task should be claimed first (higher priority)
        claim_result = await client.call_tool(
            "claimNextTask",
            {"projectRoot": planning_root, "worktree": "test-workspace-1"},
        )

        claimed_task = claim_result.data["task"]
        assert claimed_task["id"] == standalone_task_id
        assert claimed_task["status"] == "in-progress"
        assert claimed_task["priority"] == "high"
        assert claim_result.data["worktree"] == "test-workspace-1"

        # Step 5: Verify standalone task status updated to in-progress
        standalone_claimed = await client.call_tool(
            "getObject",
            {
                "kind": "task",
                "id": standalone_task_id,
                "projectRoot": planning_root,
            },
        )
        assert standalone_claimed.data["yaml"]["status"] == "in-progress"
        assert "worktree" in standalone_claimed.data["yaml"]

        # Step 6: Claim hierarchy task
        claim_result2 = await client.call_tool(
            "claimNextTask",
            {"projectRoot": planning_root, "worktree": "test-workspace-2"},
        )

        claimed_task2 = claim_result2.data["task"]
        assert claimed_task2["id"] == hierarchy_task_id
        assert claimed_task2["status"] == "in-progress"
        assert claimed_task2["priority"] == "normal"
        assert claim_result2.data["worktree"] == "test-workspace-2"

        # Step 7: Test status transitions - move both tasks to review
        # Update standalone task to review
        await client.call_tool(
            "updateObject",
            {
                "kind": "task",
                "id": standalone_task_id,
                "projectRoot": planning_root,
                "yamlPatch": {"status": "review"},
            },
        )

        # Update hierarchy task to review
        await client.call_tool(
            "updateObject",
            {
                "kind": "task",
                "id": hierarchy_task_id,
                "projectRoot": planning_root,
                "yamlPatch": {"status": "review"},
            },
        )

        # Step 8: Verify both tasks in review status
        standalone_review = await client.call_tool(
            "getObject",
            {
                "kind": "task",
                "id": standalone_task_id,
                "projectRoot": planning_root,
            },
        )
        assert standalone_review.data["yaml"]["status"] == "review"

        hierarchy_review = await client.call_tool(
            "getObject",
            {
                "kind": "task",
                "id": hierarchy_task_id,
                "projectRoot": planning_root,
            },
        )
        assert hierarchy_review.data["yaml"]["status"] == "review"

        # Step 9: Test getNextReviewableTask with mixed tasks
        reviewable_result = await client.call_tool(
            "getNextReviewableTask",
            {"projectRoot": planning_root},
        )

        assert reviewable_result.data is not None
        assert reviewable_result.data["task"] is not None
        reviewable_task = reviewable_result.data["task"]

        # Should return one of the review tasks (oldest updated timestamp)
        assert reviewable_task["id"] in [standalone_task_id, hierarchy_task_id]
        assert reviewable_task["status"] == "review"

        # Step 10: Complete standalone task
        complete_result = await client.call_tool(
            "completeTask",
            {
                "taskId": standalone_task_id,
                "projectRoot": planning_root,
                "summary": "Completed standalone task lifecycle test",
                "filesChanged": ["standalone_test.py", "config.yaml"],
            },
        )

        assert complete_result.data is not None

        # Step 11: Verify standalone task moved to done status
        standalone_completed = await client.call_tool(
            "getObject",
            {
                "kind": "task",
                "id": standalone_task_id,
                "projectRoot": planning_root,
            },
        )
        assert standalone_completed.data["yaml"]["status"] == "done"

        # Note: File movement to tasks-done is handled by completeTask internally
        # The important verification is that the task status is updated to "done"

        # Step 12: Complete hierarchy task
        complete_result2 = await client.call_tool(
            "completeTask",
            {
                "taskId": hierarchy_task_id,
                "projectRoot": planning_root,
                "summary": "Completed hierarchy task lifecycle test",
                "filesChanged": ["hierarchy_test.py"],
            },
        )

        assert complete_result2.data is not None

        # Step 13: Verify hierarchy task moved to done status
        hierarchy_completed = await client.call_tool(
            "getObject",
            {
                "kind": "task",
                "id": hierarchy_task_id,
                "projectRoot": planning_root,
            },
        )
        assert hierarchy_completed.data["yaml"]["status"] == "done"

        # Note: File movement to tasks-done is handled by completeTask internally
        # The important verification is that the task status is updated to "done"

        # Step 14: Verify both completed tasks still appear in listBacklog
        final_backlog = await client.call_tool(
            "listBacklog",
            {"projectRoot": planning_root},
        )
        assert final_backlog.structured_content is not None
        final_tasks = final_backlog.structured_content["tasks"]

        assert len(final_tasks) == 2
        final_task_ids = {task["id"] for task in final_tasks}
        assert final_task_ids == {standalone_task_id, hierarchy_task_id}

        # Verify both tasks have done status
        for task in final_tasks:
            assert task["status"] == "done"

        # Step 15: Verify no more reviewable tasks
        no_review_result = await client.call_tool(
            "getNextReviewableTask",
            {"projectRoot": planning_root},
        )
        assert no_review_result.data["task"] is None

        # Step 16: Verify no more claimable tasks
        with pytest.raises(Exception) as exc_info:
            await client.call_tool(
                "claimNextTask",
                {"projectRoot": planning_root},
            )
        assert "no" in str(exc_info.value).lower() and "available" in str(exc_info.value).lower()
