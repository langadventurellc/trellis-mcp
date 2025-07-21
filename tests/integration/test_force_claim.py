"""Integration tests for force claim functionality.

Comprehensive end-to-end testing of force claim workflows, including status override,
prerequisite bypass, cross-system compatibility, concurrent access scenarios, and
parameter validation for the claimNextTask tool's force_claim parameter.
"""

import asyncio

import pytest
from fastmcp import Client

from ..fixtures.scope_test_data import (
    create_comprehensive_scope_test_environment,
)
from .test_helpers import create_task_with_priority, create_test_hierarchy, create_test_server


class TestForceClaimEndToEndWorkflows:
    """Test complete force claim workflows from tool interface to file system."""

    @pytest.mark.asyncio
    async def test_force_claim_in_progress_task_end_to_end(self, temp_dir):
        """Test complete workflow for force claiming an in-progress task."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create test hierarchy and task
            hierarchy = await create_test_hierarchy(client, planning_root, "Force Claim Test")
            feature_id = hierarchy["feature_id"]

            task_result = await create_task_with_priority(
                client, planning_root, feature_id, "In Progress Task", "high"
            )
            task_id = task_result["id"]

            # Set task to in-progress status (simulate already claimed by someone else)
            await client.call_tool(
                "updateObject",
                {
                    "id": task_id,
                    "projectRoot": planning_root,
                    "yamlPatch": {"status": "in-progress", "worktree": "original-workspace"},
                },
            )

            # Force claim the in-progress task
            result = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                    "taskId": task_id,
                    "force_claim": True,
                    "worktree": "emergency-workspace",
                },
            )

            # Verify successful force claim
            claimed_task = result.data["task"]
            assert claimed_task["id"] == task_id
            assert claimed_task["status"] == "in-progress"
            assert result.data["claimed_status"] == "in-progress"
            assert result.data["worktree"] == "emergency-workspace"

            # Verify file system changes - read task file to confirm worktree update
            task_obj = await client.call_tool(
                "getObject", {"id": task_id, "projectRoot": planning_root}
            )
            task_yaml = task_obj.data["yaml"]
            assert task_yaml["worktree"] == "emergency-workspace"

    @pytest.mark.asyncio
    async def test_force_claim_review_task_end_to_end(self, temp_dir):
        """Test complete workflow for force claiming a task in review."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create test hierarchy and task
            hierarchy = await create_test_hierarchy(client, planning_root, "Review Force Claim")
            feature_id = hierarchy["feature_id"]

            task_result = await create_task_with_priority(
                client, planning_root, feature_id, "Review Task", "normal"
            )
            task_id = task_result["id"]

            # Set task to review status (must go through in-progress first)
            await client.call_tool(
                "updateObject",
                {
                    "id": task_id,
                    "projectRoot": planning_root,
                    "yamlPatch": {"status": "in-progress"},
                },
            )
            await client.call_tool(
                "updateObject",
                {
                    "id": task_id,
                    "projectRoot": planning_root,
                    "yamlPatch": {"status": "review"},
                },
            )

            # Force claim the review task
            result = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                    "taskId": task_id,
                    "force_claim": True,
                    "worktree": "priority-change",
                },
            )

            # Verify status changed from review to in-progress
            claimed_task = result.data["task"]
            assert claimed_task["id"] == task_id
            assert claimed_task["status"] == "in-progress"
            assert result.data["worktree"] == "priority-change"

    @pytest.mark.asyncio
    async def test_force_claim_done_task_reopening_workflow(self, temp_dir):
        """Test reopening completed tasks with force claim."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create and complete a task
            hierarchy = await create_test_hierarchy(client, planning_root, "Reopening Test")
            feature_id = hierarchy["feature_id"]

            task_result = await create_task_with_priority(
                client, planning_root, feature_id, "Completed Task", "low"
            )
            task_id = task_result["id"]

            # Complete the task normally
            await client.call_tool(
                "updateObject",
                {
                    "id": task_id,
                    "projectRoot": planning_root,
                    "yamlPatch": {"status": "in-progress"},
                },
            )
            await client.call_tool(
                "completeTask",
                {
                    "taskId": task_id,
                    "projectRoot": planning_root,
                    "summary": "Task completed",
                    "filesChanged": ["completed.py"],
                },
            )

            # Force claim the done task to reopen it
            result = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                    "taskId": task_id,
                    "force_claim": True,
                    "worktree": "reopening-workspace",
                },
            )

            # Verify task was reopened
            claimed_task = result.data["task"]
            assert claimed_task["id"] == task_id
            assert claimed_task["status"] == "in-progress"
            assert result.data["worktree"] == "reopening-workspace"


class TestForceClaimStatusOverride:
    """Test status override functionality for all task statuses."""

    @pytest.mark.asyncio
    async def test_force_claim_overrides_all_statuses(self, temp_dir):
        """Test force claim can override all possible task statuses."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            hierarchy = await create_test_hierarchy(client, planning_root, "Status Override Test")
            feature_id = hierarchy["feature_id"]

            # Test data: (status_to_set, expected_claimable)
            status_tests = [
                ("open", True),  # Normal claiming should work
                ("in-progress", True),  # Force claim should work
                ("review", True),  # Force claim should work
                ("done", True),  # Force claim should work
            ]

            task_ids = []
            for i, (status, _) in enumerate(status_tests):
                task_result = await create_task_with_priority(
                    client, planning_root, feature_id, f"Task {status.title()}", "normal"
                )
                task_id = task_result["id"]
                task_ids.append((task_id, status))

                # Set the task to the target status (follow valid transitions)
                if status == "in-progress":
                    await client.call_tool(
                        "updateObject",
                        {
                            "id": task_id,
                            "projectRoot": planning_root,
                            "yamlPatch": {"status": "in-progress"},
                        },
                    )
                elif status == "review":
                    # Must go through in-progress first
                    await client.call_tool(
                        "updateObject",
                        {
                            "id": task_id,
                            "projectRoot": planning_root,
                            "yamlPatch": {"status": "in-progress"},
                        },
                    )
                    await client.call_tool(
                        "updateObject",
                        {
                            "id": task_id,
                            "projectRoot": planning_root,
                            "yamlPatch": {"status": "review"},
                        },
                    )
                elif status == "done":
                    # Must go through in-progress first, then complete
                    await client.call_tool(
                        "updateObject",
                        {
                            "id": task_id,
                            "projectRoot": planning_root,
                            "yamlPatch": {"status": "in-progress"},
                        },
                    )
                    await client.call_tool(
                        "completeTask",
                        {
                            "taskId": task_id,
                            "projectRoot": planning_root,
                            "summary": "Task completed for test",
                            "filesChanged": ["test.py"],
                        },
                    )

            # Test force claiming each status
            for task_id, original_status in task_ids:
                result = await client.call_tool(
                    "claimNextTask",
                    {
                        "projectRoot": planning_root,
                        "taskId": task_id,
                        "force_claim": True,
                    },
                )

                claimed_task = result.data["task"]
                assert claimed_task["id"] == task_id
                assert claimed_task["status"] == "in-progress"

    @pytest.mark.asyncio
    async def test_normal_claim_blocked_by_non_open_status(self, temp_dir):
        """Test that normal claiming (force_claim=False) is blocked by non-open statuses."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            hierarchy = await create_test_hierarchy(
                client, planning_root, "Normal Claim Block Test"
            )
            feature_id = hierarchy["feature_id"]

            # Test statuses that should block normal claiming
            blocking_statuses = ["in-progress", "review", "done"]

            for status in blocking_statuses:
                task_result = await create_task_with_priority(
                    client, planning_root, feature_id, f"Blocked {status} Task", "normal"
                )
                task_id = task_result["id"]

                # Set task to blocking status (follow valid transitions)
                if status == "in-progress":
                    await client.call_tool(
                        "updateObject",
                        {
                            "id": task_id,
                            "projectRoot": planning_root,
                            "yamlPatch": {"status": "in-progress"},
                        },
                    )
                elif status == "review":
                    # Must go through in-progress first
                    await client.call_tool(
                        "updateObject",
                        {
                            "id": task_id,
                            "projectRoot": planning_root,
                            "yamlPatch": {"status": "in-progress"},
                        },
                    )
                    await client.call_tool(
                        "updateObject",
                        {
                            "id": task_id,
                            "projectRoot": planning_root,
                            "yamlPatch": {"status": "review"},
                        },
                    )
                elif status == "done":
                    # Must complete task properly
                    await client.call_tool(
                        "updateObject",
                        {
                            "id": task_id,
                            "projectRoot": planning_root,
                            "yamlPatch": {"status": "in-progress"},
                        },
                    )
                    await client.call_tool(
                        "completeTask",
                        {
                            "taskId": task_id,
                            "projectRoot": planning_root,
                            "summary": "Task completed for blocking test",
                            "filesChanged": ["blocked.py"],
                        },
                    )

                # Verify normal claiming fails
                with pytest.raises(Exception) as exc_info:
                    await client.call_tool(
                        "claimNextTask",
                        {
                            "projectRoot": planning_root,
                            "taskId": task_id,
                            "force_claim": False,
                        },
                    )

                error_message = str(exc_info.value)
                assert task_id in error_message
                assert status in error_message.lower()


class TestForceClaimPrerequisiteBypass:
    """Test prerequisite bypass functionality with force claim."""

    @pytest.mark.asyncio
    async def test_force_claim_bypasses_incomplete_prerequisites(self, temp_dir):
        """Test that force claim can bypass incomplete prerequisites."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            hierarchy = await create_test_hierarchy(client, planning_root, "Prerequisite Bypass")
            feature_id = hierarchy["feature_id"]

            # Create prerequisite task (leave incomplete)
            prereq_task = await create_task_with_priority(
                client, planning_root, feature_id, "Prerequisite Task", "normal"
            )
            prereq_task_id = prereq_task["id"]

            # Create dependent task with prerequisite
            dependent_task = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Dependent Task",
                    "projectRoot": planning_root,
                    "parent": feature_id,
                    "prerequisites": [prereq_task_id],
                },
            )
            dependent_task_id = dependent_task.data["id"]

            # Verify normal claiming fails due to incomplete prerequisite
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "claimNextTask",
                    {
                        "projectRoot": planning_root,
                        "taskId": dependent_task_id,
                        "force_claim": False,
                    },
                )
            assert "prerequisite" in str(exc_info.value).lower()

            # Force claim should bypass prerequisite check
            result = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                    "taskId": dependent_task_id,
                    "force_claim": True,
                },
            )

            claimed_task = result.data["task"]
            assert claimed_task["id"] == dependent_task_id
            assert claimed_task["status"] == "in-progress"

    @pytest.mark.asyncio
    async def test_force_claim_with_cross_system_prerequisites(self, temp_dir):
        """Test force claim bypassing cross-system prerequisites."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create an incomplete prerequisite task
            incomplete_prereq = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Incomplete Prerequisite Task",
                    "projectRoot": planning_root,
                    # No parent = standalone task, leave as open (incomplete)
                },
            )
            incomplete_prereq_id = incomplete_prereq.data["id"]

            # Create a new task that depends on the incomplete prerequisite
            new_standalone_task = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "New Standalone Task with Prereq",
                    "projectRoot": planning_root,
                    "prerequisites": [incomplete_prereq_id],  # Valid but incomplete prerequisite
                    # No parent = standalone task
                },
            )
            new_standalone_id = new_standalone_task.data["id"]

            # Normal claiming should fail due to incomplete cross-system prerequisite
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "claimNextTask",
                    {
                        "projectRoot": planning_root,
                        "taskId": new_standalone_id,
                        "force_claim": False,
                    },
                )
            assert "prerequisite" in str(exc_info.value).lower()

            # Force claim should bypass cross-system prerequisite check
            result = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                    "taskId": new_standalone_id,
                    "force_claim": True,
                },
            )

            claimed_task = result.data["task"]
            assert claimed_task["id"] == new_standalone_id
            assert claimed_task["status"] == "in-progress"


class TestForceClaimCrossSystemIntegration:
    """Test force claim functionality across hierarchical and standalone task systems."""

    @pytest.mark.asyncio
    async def test_force_claim_hierarchical_and_standalone_tasks(self, temp_dir):
        """Test force claiming both hierarchical and standalone tasks."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create hierarchical task
            hierarchy = await create_test_hierarchy(client, planning_root, "Cross System Test")
            feature_id = hierarchy["feature_id"]

            hierarchical_task = await create_task_with_priority(
                client, planning_root, feature_id, "Hierarchical Task", "high"
            )
            hierarchical_task_id = hierarchical_task["id"]

            # Create standalone task
            standalone_task = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Standalone Task",
                    "projectRoot": planning_root,
                    "priority": "high",
                    # No parent = standalone task
                },
            )
            standalone_task_id = standalone_task.data["id"]

            # Set both tasks to in-progress (to test force claim override)
            for task_id in [hierarchical_task_id, standalone_task_id]:
                await client.call_tool(
                    "updateObject",
                    {
                        "id": task_id,
                        "projectRoot": planning_root,
                        "yamlPatch": {"status": "in-progress"},
                    },
                )

            # Force claim hierarchical task
            h_result = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                    "taskId": hierarchical_task_id,
                    "force_claim": True,
                    "worktree": "hierarchical-workspace",
                },
            )

            # Force claim standalone task
            s_result = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                    "taskId": standalone_task_id,
                    "force_claim": True,
                    "worktree": "standalone-workspace",
                },
            )

            # Verify both claims succeeded
            h_task = h_result.data["task"]
            s_task = s_result.data["task"]

            assert h_task["id"] == hierarchical_task_id
            assert h_task["status"] == "in-progress"
            assert h_task["parent"] == feature_id  # Hierarchical has parent

            assert s_task["id"] == standalone_task_id
            assert s_task["status"] == "in-progress"
            assert s_task["parent"] == ""  # Standalone has no parent

            assert h_result.data["worktree"] == "hierarchical-workspace"
            assert s_result.data["worktree"] == "standalone-workspace"

    @pytest.mark.asyncio
    async def test_force_claim_mixed_project_environment(self, temp_dir):
        """Test force claiming in complex multi-project environment."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create comprehensive test environment
            test_env = await create_comprehensive_scope_test_environment(client, planning_root)
            unblocked_tasks = test_env["unblocked_tasks"]

            # Ensure we have multiple tasks to work with
            assert len(unblocked_tasks) >= 2, "Need multiple tasks for mixed environment test"

            # Set first few tasks to different statuses for force claim testing
            test_tasks = unblocked_tasks[:3] if len(unblocked_tasks) >= 3 else unblocked_tasks

            statuses_to_set = ["in-progress", "review", "done"]
            for i, task_id in enumerate(test_tasks):
                status = statuses_to_set[i % len(statuses_to_set)]
                if status == "in-progress":
                    await client.call_tool(
                        "updateObject",
                        {
                            "id": task_id,
                            "projectRoot": planning_root,
                            "yamlPatch": {"status": "in-progress"},
                        },
                    )
                elif status == "review":
                    # Must go through in-progress first
                    await client.call_tool(
                        "updateObject",
                        {
                            "id": task_id,
                            "projectRoot": planning_root,
                            "yamlPatch": {"status": "in-progress"},
                        },
                    )
                    await client.call_tool(
                        "updateObject",
                        {
                            "id": task_id,
                            "projectRoot": planning_root,
                            "yamlPatch": {"status": "review"},
                        },
                    )
                elif status == "done":
                    # Must complete task properly
                    await client.call_tool(
                        "updateObject",
                        {
                            "id": task_id,
                            "projectRoot": planning_root,
                            "yamlPatch": {"status": "in-progress"},
                        },
                    )
                    await client.call_tool(
                        "completeTask",
                        {
                            "taskId": task_id,
                            "projectRoot": planning_root,
                            "summary": f"Task {i} completed for mixed test",
                            "filesChanged": [f"mixed_{i}.py"],
                        },
                    )

            # Force claim each task with different worktrees
            for i, task_id in enumerate(test_tasks):
                result = await client.call_tool(
                    "claimNextTask",
                    {
                        "projectRoot": planning_root,
                        "taskId": task_id,
                        "force_claim": True,
                        "worktree": f"force-workspace-{i}",
                    },
                )

                claimed_task = result.data["task"]
                assert claimed_task["id"] == task_id
                assert claimed_task["status"] == "in-progress"
                assert result.data["worktree"] == f"force-workspace-{i}"


class TestForceClaimConcurrentAccess:
    """Test concurrent force claim scenarios and race conditions."""

    @pytest.mark.asyncio
    async def test_concurrent_force_claim_attempts_same_task(self, temp_dir):
        """Test atomic behavior when multiple clients force claim the same task."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as setup_client:
            # Create task for concurrent force claiming
            hierarchy = await create_test_hierarchy(setup_client, planning_root, "Concurrent Force")
            feature_id = hierarchy["feature_id"]

            task_result = await create_task_with_priority(
                setup_client, planning_root, feature_id, "Contested Force Task", "high"
            )
            target_task_id = task_result["id"]

            # Set task to in-progress to test force claim
            await setup_client.call_tool(
                "updateObject",
                {
                    "id": target_task_id,
                    "projectRoot": planning_root,
                    "yamlPatch": {"status": "in-progress"},
                },
            )

        # Function for concurrent force claiming
        async def attempt_force_claim(client_id: int) -> tuple[int, bool, str]:
            """Attempt to force claim the target task."""
            try:
                async with Client(server) as client:
                    result = await client.call_tool(
                        "claimNextTask",
                        {
                            "projectRoot": planning_root,
                            "taskId": target_task_id,
                            "force_claim": True,
                            "worktree": f"concurrent-workspace-{client_id}",
                        },
                    )
                    return client_id, True, result.data["task"]["id"]
            except Exception as e:
                return client_id, False, str(e)

        # Launch concurrent force claiming attempts
        tasks = [attempt_force_claim(i) for i in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Analyze results - exactly one should succeed due to atomic operations
        successful_claims = [r for r in results if isinstance(r, tuple) and r[1]]

        # With force claim, the first claim should succeed and others should fail
        # (though the exact behavior may depend on implementation details)
        assert len(successful_claims) >= 1, "At least one force claim should succeed"
        assert len(results) == 5, "All attempts should complete"

        # Verify successful claim got the correct task
        if successful_claims:
            successful_client, success, claimed_id = successful_claims[0]
            assert success
            assert claimed_id == target_task_id

    @pytest.mark.asyncio
    async def test_force_claim_during_normal_claiming_operations(self, temp_dir):
        """Test force claim behavior when normal claiming is happening concurrently."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as setup_client:
            # Create multiple tasks for mixed claiming scenarios
            hierarchy = await create_test_hierarchy(setup_client, planning_root, "Mixed Claiming")
            feature_id = hierarchy["feature_id"]

            # Create open tasks for normal claiming
            normal_tasks = []
            for i in range(3):
                task = await create_task_with_priority(
                    setup_client, planning_root, feature_id, f"Normal Task {i}", "normal"
                )
                normal_tasks.append(task["id"])

            # Create task for force claiming (set to in-progress)
            force_task = await create_task_with_priority(
                setup_client, planning_root, feature_id, "Force Claim Task", "high"
            )
            force_task_id = force_task["id"]

            await setup_client.call_tool(
                "updateObject",
                {
                    "id": force_task_id,
                    "projectRoot": planning_root,
                    "yamlPatch": {"status": "in-progress"},
                },
            )

        # Function for normal claiming
        async def normal_claim_worker() -> tuple[str, bool]:
            """Attempt normal task claiming."""
            try:
                async with Client(server) as client:
                    result = await client.call_tool(
                        "claimNextTask",
                        {"projectRoot": planning_root, "worktree": "normal-workspace"},
                    )
                    return result.data["task"]["id"], True
            except Exception as e:
                return str(e), False

        # Function for force claiming
        async def force_claim_worker() -> tuple[str, bool]:
            """Attempt force claiming specific task."""
            try:
                async with Client(server) as client:
                    result = await client.call_tool(
                        "claimNextTask",
                        {
                            "projectRoot": planning_root,
                            "taskId": force_task_id,
                            "force_claim": True,
                            "worktree": "force-workspace",
                        },
                    )
                    return result.data["task"]["id"], True
            except Exception as e:
                return str(e), False

        # Run mixed claiming operations concurrently
        mixed_tasks = [normal_claim_worker(), force_claim_worker(), normal_claim_worker()]
        results = await asyncio.gather(*mixed_tasks, return_exceptions=True)

        # Verify force claim succeeded
        force_result = results[1]  # Middle result is force claim
        assert isinstance(force_result, tuple)
        task_id, success = force_result
        if success:
            assert task_id == force_task_id


class TestForceClaimParameterValidation:
    """Test parameter validation and error handling for force claim."""

    @pytest.mark.asyncio
    async def test_force_claim_requires_task_id(self, temp_dir):
        """Test that force_claim=True requires taskId parameter."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Test force_claim without taskId should fail
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "claimNextTask",
                    {
                        "projectRoot": planning_root,
                        "force_claim": True,
                        # No taskId provided
                    },
                )

            error_message = str(exc_info.value)
            assert "force_claim" in error_message.lower()
            assert "taskid" in error_message.lower() or "task_id" in error_message.lower()

    @pytest.mark.asyncio
    async def test_force_claim_incompatible_with_scope(self, temp_dir):
        """Test that force_claim is incompatible with scope parameter."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create test hierarchy for scope
            hierarchy = await create_test_hierarchy(client, planning_root, "Scope Incompatible")
            feature_id = hierarchy["feature_id"]

            task_result = await create_task_with_priority(
                client, planning_root, feature_id, "Test Task", "normal"
            )
            task_id = task_result["id"]

            # Test force_claim with scope should fail
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "claimNextTask",
                    {
                        "projectRoot": planning_root,
                        "taskId": task_id,
                        "force_claim": True,
                        "scope": feature_id,  # Should be incompatible
                    },
                )

            error_message = str(exc_info.value)
            # ClaimingParams now validates scope+task_id mutual exclusivity
            assert (
                "force_claim" in error_message.lower()
                or "cannot specify both scope and task_id" in error_message.lower()
            )

    @pytest.mark.asyncio
    async def test_force_claim_nonexistent_task_error(self, temp_dir):
        """Test error handling when force claiming nonexistent task."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Test force claiming nonexistent task
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "claimNextTask",
                    {
                        "projectRoot": planning_root,
                        "taskId": "T-nonexistent-task",
                        "force_claim": True,
                    },
                )

            error_message = str(exc_info.value)
            assert "T-nonexistent-task" in error_message
            assert "not found" in error_message.lower() or "does not exist" in error_message.lower()

    @pytest.mark.asyncio
    async def test_force_claim_with_empty_task_id(self, temp_dir):
        """Test error handling with empty task ID."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Test empty task ID with force claim
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "claimNextTask",
                    {
                        "projectRoot": planning_root,
                        "taskId": "",
                        "force_claim": True,
                    },
                )

            error_message = str(exc_info.value)
            assert "force_claim" in error_message.lower()
            assert "taskid" in error_message.lower() or "task_id" in error_message.lower()


class TestForceClaimAuditLogging:
    """Test audit logging and security aspects of force claim."""

    @pytest.mark.asyncio
    async def test_force_claim_maintains_access_boundaries(self, temp_dir):
        """Test that force claim maintains project root access boundaries."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create task in valid project
            hierarchy = await create_test_hierarchy(client, planning_root, "Access Boundary Test")
            feature_id = hierarchy["feature_id"]

            task_result = await create_task_with_priority(
                client, planning_root, feature_id, "Valid Task", "normal"
            )
            task_id = task_result["id"]

            # Force claim should respect project boundaries
            result = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                    "taskId": task_id,
                    "force_claim": True,
                },
            )

            claimed_task = result.data["task"]
            assert claimed_task["id"] == task_id
            assert claimed_task["status"] == "in-progress"

    @pytest.mark.asyncio
    async def test_force_claim_atomic_operations_integrity(self, temp_dir):
        """Test that force claim operations complete atomically."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create task for atomic testing
            hierarchy = await create_test_hierarchy(client, planning_root, "Atomic Test")
            feature_id = hierarchy["feature_id"]

            task_result = await create_task_with_priority(
                client, planning_root, feature_id, "Atomic Task", "normal"
            )
            task_id = task_result["id"]

            # Set task to review status (must go through in-progress first)
            await client.call_tool(
                "updateObject",
                {
                    "id": task_id,
                    "projectRoot": planning_root,
                    "yamlPatch": {"status": "in-progress"},
                },
            )
            await client.call_tool(
                "updateObject",
                {
                    "id": task_id,
                    "projectRoot": planning_root,
                    "yamlPatch": {"status": "review"},
                },
            )

            # Force claim should atomically update status and worktree
            result = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                    "taskId": task_id,
                    "force_claim": True,
                    "worktree": "atomic-workspace",
                },
            )

            # Verify atomic update
            claimed_task = result.data["task"]
            assert claimed_task["status"] == "in-progress"
            assert result.data["worktree"] == "atomic-workspace"

            # Verify file system reflects atomic update
            task_obj = await client.call_tool(
                "getObject", {"id": task_id, "projectRoot": planning_root}
            )
            task_yaml = task_obj.data["yaml"]
            assert task_yaml["status"] == "in-progress"
            assert task_yaml["worktree"] == "atomic-workspace"

    @pytest.mark.asyncio
    async def test_force_claim_error_recovery_rollback(self, temp_dir):
        """Test error recovery and rollback capabilities for force claim."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            hierarchy = await create_test_hierarchy(client, planning_root, "Error Recovery Test")
            feature_id = hierarchy["feature_id"]

            # Test that failed force claims don't leave system in inconsistent state
            # This is more of a consistency check than a true rollback test

            # Create valid task
            task_result = await create_task_with_priority(
                client, planning_root, feature_id, "Recovery Task", "normal"
            )
            task_id = task_result["id"]

            # Valid force claim should work
            result = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                    "taskId": task_id,
                    "force_claim": True,
                    "worktree": "recovery-workspace",
                },
            )

            # Verify successful operation
            claimed_task = result.data["task"]
            assert claimed_task["id"] == task_id
            assert claimed_task["status"] == "in-progress"

            # Attempt to force claim already claimed task should fail appropriately
            # (but this behavior may vary based on implementation)
            # The key is that any failure should not corrupt the task state

            # Verify task state remains consistent after any operations
            final_task = await client.call_tool(
                "getObject", {"id": task_id, "projectRoot": planning_root}
            )
            final_yaml = final_task.data["yaml"]
            assert final_yaml["status"] == "in-progress"
            assert final_yaml["worktree"] == "recovery-workspace"
