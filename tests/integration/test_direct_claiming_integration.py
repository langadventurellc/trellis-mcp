"""Integration tests for direct task claiming functionality.

Comprehensive end-to-end testing of direct task claiming workflows,
including cross-system compatibility, concurrent access, performance validation,
and realistic development scenarios with mixed hierarchical and standalone tasks.
"""

import asyncio
import time
from typing import Any

import pytest
from fastmcp import Client

from ..fixtures.scope_test_data import (
    create_comprehensive_scope_test_environment,
    create_prerequisite_chain_test_environment,
)
from .test_helpers import create_task_with_priority, create_test_hierarchy, create_test_server


class TestDirectClaimingCrossSystemWorkflows:
    """Test direct claiming workflows in mixed hierarchical/standalone environments."""

    @pytest.mark.asyncio
    async def test_direct_claim_hierarchical_task_by_id(self, temp_dir):
        """Test directly claiming a hierarchical task by its ID."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create test hierarchy
            hierarchy = await create_test_hierarchy(client, planning_root, "Direct Claim Test")
            feature_id = hierarchy["feature_id"]

            # Create specific task to claim directly
            task_result = await create_task_with_priority(
                client, planning_root, feature_id, "Target Task for Direct Claim", "high"
            )
            target_task_id = task_result["id"]

            # Create other tasks to ensure we're not just getting the only task
            await create_task_with_priority(
                client, planning_root, feature_id, "Other High Priority Task", "high"
            )
            await create_task_with_priority(
                client, planning_root, feature_id, "Normal Priority Task", "normal"
            )

            # Test direct claiming by task ID
            result = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                    "taskId": target_task_id,
                },
            )

            # Verify correct task was claimed
            claimed_task = result.data["task"]
            assert claimed_task["id"] == target_task_id
            assert claimed_task["title"] == "Target Task for Direct Claim"
            assert claimed_task["status"] == "in-progress"
            assert claimed_task["priority"] == "high"
            assert result.data["claimed_status"] == "in-progress"

    @pytest.mark.asyncio
    async def test_direct_claim_standalone_task_by_id(self, temp_dir):
        """Test directly claiming a standalone task by its ID."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create standalone task
            standalone_task = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Standalone Task for Direct Claim",
                    "projectRoot": planning_root,
                    "priority": "high",
                    # No parent = standalone task
                },
            )
            standalone_task_id = standalone_task.data["id"]

            # Create some hierarchical tasks as well
            hierarchy = await create_test_hierarchy(client, planning_root, "Mixed Environment")
            feature_id = hierarchy["feature_id"]
            await create_task_with_priority(
                client, planning_root, feature_id, "Hierarchical Task", "high"
            )

            # Test direct claiming standalone task by ID
            result = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                    "taskId": standalone_task_id,
                },
            )

            # Verify correct standalone task was claimed
            claimed_task = result.data["task"]
            assert claimed_task["id"] == standalone_task_id
            assert claimed_task["title"] == "Standalone Task for Direct Claim"
            assert claimed_task["status"] == "in-progress"
            assert claimed_task["parent"] == ""  # Standalone task has no parent

    @pytest.mark.asyncio
    async def test_direct_claim_with_cross_system_prerequisites(self, temp_dir):
        """Test direct claiming with prerequisites spanning hierarchical and standalone systems."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create test environment with cross-system prerequisites
            # Note: The fixture already completes the foundation task to unblock dependent tasks
            test_env = await create_prerequisite_chain_test_environment(client, planning_root)

            # Try to directly claim intermediate task (should work since foundation is already done)
            intermediate_task_id = test_env["intermediate_task_id"]
            result = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                    "taskId": intermediate_task_id,
                },
            )

            claimed_task = result.data["task"]
            assert claimed_task["id"] == intermediate_task_id
            assert claimed_task["status"] == "in-progress"

            # Complete intermediate task
            await client.call_tool(
                "completeTask",
                {
                    "taskId": intermediate_task_id,
                    "projectRoot": planning_root,
                    "summary": "Intermediate task completed",
                    "filesChanged": ["intermediate.py"],
                },
            )

            # Now try to directly claim cross-feature task that depends on intermediate task
            cross_feature_task_id = test_env["cross_feature_task_id"]
            result2 = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                    "taskId": cross_feature_task_id,
                },
            )

            claimed_task2 = result2.data["task"]
            assert claimed_task2["id"] == cross_feature_task_id
            assert claimed_task2["status"] == "in-progress"

            # Also try to claim standalone task that depends on foundation task
            # This should work since foundation is already completed
            standalone_dependent_id = test_env["standalone_dependent_id"]
            result3 = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                    "taskId": standalone_dependent_id,
                },
            )

            claimed_task3 = result3.data["task"]
            assert claimed_task3["id"] == standalone_dependent_id
            assert claimed_task3["status"] == "in-progress"
            # Should be standalone (no parent)
            assert claimed_task3["parent"] == "" or claimed_task3["parent"] is None

    @pytest.mark.asyncio
    async def test_direct_claim_across_multiple_projects(self, temp_dir):
        """Test direct claiming tasks from different projects."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create comprehensive multi-project environment
            test_env = await create_comprehensive_scope_test_environment(client, planning_root)

            # Use unblocked tasks that are available for claiming
            unblocked_tasks = test_env["unblocked_tasks"]

            # Ensure we have enough unblocked tasks for the test
            assert (
                len(unblocked_tasks) >= 2
            ), "Need at least 2 unblocked tasks for multi-project test"

            # Claim first unblocked task
            first_task_id = unblocked_tasks[0]
            result1 = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                    "taskId": first_task_id,
                },
            )

            claimed_task1 = result1.data["task"]
            assert claimed_task1["id"] == first_task_id
            assert claimed_task1["status"] == "in-progress"

            # Claim second unblocked task (should be different)
            second_task_id = unblocked_tasks[1]
            result2 = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                    "taskId": second_task_id,
                },
            )

            claimed_task2 = result2.data["task"]
            assert claimed_task2["id"] == second_task_id
            assert claimed_task2["status"] == "in-progress"
            assert claimed_task2["id"] != claimed_task1["id"]

            # Verify both tasks were claimed successfully and are from potentially
            # different projects
            claimed_ids = {claimed_task1["id"], claimed_task2["id"]}
            expected_ids = {first_task_id, second_task_id}
            assert claimed_ids == expected_ids

    @pytest.mark.asyncio
    async def test_direct_claim_error_for_non_existent_task(self, temp_dir):
        """Test error handling when trying to claim non-existent task."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Try to claim non-existent hierarchical task
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "claimNextTask",
                    {
                        "projectRoot": planning_root,
                        "taskId": "T-nonexistent-task",
                    },
                )

            error_message = str(exc_info.value)
            assert "T-nonexistent-task" in error_message
            assert "not found" in error_message.lower() or "does not exist" in error_message.lower()

    @pytest.mark.asyncio
    async def test_direct_claim_error_for_task_with_incomplete_prerequisites(self, temp_dir):
        """Test error when directly claiming task with incomplete prerequisites."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create hierarchy
            hierarchy = await create_test_hierarchy(client, planning_root, "Blocked Task Test")
            feature_id = hierarchy["feature_id"]

            # Create prerequisite task (but don't complete it)
            prereq_task = await create_task_with_priority(
                client, planning_root, feature_id, "Prerequisite Task", "normal"
            )
            prereq_task_id = prereq_task["id"]

            # Create dependent task
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

            # Try to claim dependent task while prerequisite is incomplete
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "claimNextTask",
                    {
                        "projectRoot": planning_root,
                        "taskId": dependent_task_id,
                    },
                )

            error_message = str(exc_info.value)
            assert (
                "prerequisite" in error_message.lower()
                or "blocked" in error_message.lower()
                or "dependencies" in error_message.lower()
            )


class TestDirectClaimingConcurrentAccess:
    """Test concurrent access scenarios for direct task claiming."""

    @pytest.mark.asyncio
    async def test_simultaneous_direct_claim_attempts(self, temp_dir):
        """Test atomic behavior when multiple clients try to claim same task simultaneously."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as setup_client:
            # Create test task
            hierarchy = await create_test_hierarchy(setup_client, planning_root, "Concurrent Test")
            feature_id = hierarchy["feature_id"]
            task_result = await create_task_with_priority(
                setup_client, planning_root, feature_id, "Contested Task", "high"
            )
            target_task_id = task_result["id"]

        # Function for concurrent claiming attempt
        async def attempt_claim(client_id: int) -> tuple[int, bool, str]:
            """Attempt to claim the target task."""
            try:
                async with Client(server) as client:
                    result = await client.call_tool(
                        "claimNextTask",
                        {
                            "projectRoot": planning_root,
                            "taskId": target_task_id,
                        },
                    )
                    return client_id, True, result.data["task"]["id"]
            except Exception as e:
                return client_id, False, str(e)

        # Launch concurrent claiming attempts
        tasks = [attempt_claim(i) for i in range(5)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Analyze results
        successful_claims = [r for r in results if isinstance(r, tuple) and r[1]]
        failed_claims = [r for r in results if isinstance(r, tuple) and not r[1]]

        # Exactly one claim should succeed
        assert len(successful_claims) == 1, f"Expected 1 success, got {len(successful_claims)}"
        assert len(failed_claims) == 4, f"Expected 4 failures, got {len(failed_claims)}"

        # Successful claim should be for the correct task
        successful_client, success, claimed_id = successful_claims[0]
        assert success
        assert claimed_id == target_task_id

        # Failed claims should have appropriate error messages
        for client_id, success, error_msg in failed_claims:
            assert not success
            assert (
                "already claimed" in error_msg.lower()
                or "in-progress" in error_msg.lower()
                or "not available" in error_msg.lower()
            )

    @pytest.mark.asyncio
    async def test_claim_during_prerequisite_completion(self, temp_dir):
        """Test claiming behavior when prerequisites are being completed concurrently."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as setup_client:
            # Create prerequisite chain
            hierarchy = await create_test_hierarchy(
                setup_client, planning_root, "Concurrent Prereq"
            )
            feature_id = hierarchy["feature_id"]

            # Create prerequisite task
            prereq_task = await create_task_with_priority(
                setup_client, planning_root, feature_id, "Prerequisite Task", "normal"
            )
            prereq_task_id = prereq_task["id"]

            # Set prerequisite to in-progress
            await setup_client.call_tool(
                "updateObject",
                {
                    "id": prereq_task_id,
                    "projectRoot": planning_root,
                    "yamlPatch": {"status": "in-progress"},
                },
            )

            # Create dependent task
            dependent_task = await setup_client.call_tool(
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

        # Function to complete prerequisite
        async def complete_prerequisite():
            async with Client(server) as client:
                await asyncio.sleep(0.1)  # Small delay
                await client.call_tool(
                    "completeTask",
                    {
                        "taskId": prereq_task_id,
                        "projectRoot": planning_root,
                        "summary": "Prerequisite completed",
                        "filesChanged": ["prereq.py"],
                    },
                )

        # Function to attempt claiming dependent task
        async def attempt_claim_dependent() -> tuple[bool, str]:
            async with Client(server) as client:
                # Try multiple times with small delays
                for attempt in range(10):
                    try:
                        result = await client.call_tool(
                            "claimNextTask",
                            {
                                "projectRoot": planning_root,
                                "taskId": dependent_task_id,
                            },
                        )
                        return True, result.data["task"]["id"]
                    except Exception as e:
                        if attempt < 9:  # Not the last attempt
                            await asyncio.sleep(0.05)
                        else:
                            return False, str(e)
                # This should never be reached, but satisfies type checker
                return False, "All attempts failed"

        # Run prerequisite completion and claiming concurrently
        completion_task = asyncio.create_task(complete_prerequisite())
        claim_task = asyncio.create_task(attempt_claim_dependent())

        await completion_task
        claim_success, claim_result = await claim_task

        # Should eventually succeed once prerequisite is completed
        assert claim_success, f"Claiming failed: {claim_result}"
        assert claim_result == dependent_task_id

    @pytest.mark.asyncio
    async def test_atomic_operations_under_concurrent_load(self, temp_dir):
        """Test system integrity under high concurrent claiming load."""
        server, planning_root = create_test_server(temp_dir)

        # Create multiple tasks for concurrent claiming
        task_ids = []
        async with Client(server) as setup_client:
            hierarchy = await create_test_hierarchy(setup_client, planning_root, "Load Test")
            feature_id = hierarchy["feature_id"]

            # Create 20 tasks for load testing
            for i in range(20):
                task_result = await create_task_with_priority(
                    setup_client, planning_root, feature_id, f"Load Test Task {i}", "normal"
                )
                task_ids.append(task_result["id"])

        # Function for aggressive claiming
        async def claim_multiple_tasks(client_id: int) -> list[tuple[str, bool]]:
            """Attempt to claim multiple tasks rapidly."""
            results = []
            async with Client(server) as client:
                for task_id in task_ids:
                    try:
                        await client.call_tool(
                            "claimNextTask",
                            {
                                "projectRoot": planning_root,
                                "taskId": task_id,
                            },
                        )
                        results.append((task_id, True))
                    except Exception:
                        results.append((task_id, False))

                    # Small delay between attempts
                    await asyncio.sleep(0.001)
            return results

        # Launch multiple aggressive clients
        client_tasks = [claim_multiple_tasks(i) for i in range(10)]
        all_results = await asyncio.gather(*client_tasks)

        # Analyze results for consistency
        successful_claims = {}
        total_successes = 0

        for client_results in all_results:
            for task_id, success in client_results:
                if success:
                    if task_id in successful_claims:
                        # This should never happen - indicates race condition
                        pytest.fail(f"Task {task_id} claimed by multiple clients!")
                    successful_claims[task_id] = True
                    total_successes += 1

        # Should have claimed some tasks but not more than exist
        assert 0 < total_successes <= len(task_ids)
        assert len(successful_claims) == total_successes


class TestDirectClaimingRealisticWorkflows:
    """Test realistic development workflows using direct task claiming."""

    @pytest.mark.asyncio
    async def test_complete_development_workflow_with_direct_claiming(self, temp_dir):
        """Test complete workflow: direct claim → work → complete → claim next specific task."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create feature with ordered tasks
            hierarchy = await create_test_hierarchy(client, planning_root, "Workflow Test")
            feature_id = hierarchy["feature_id"]

            # Create ordered tasks representing a development workflow
            task1 = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Setup Database Schema",
                    "projectRoot": planning_root,
                    "parent": feature_id,
                },
            )
            task1_id = task1.data["id"]

            task2 = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Create API Endpoints",
                    "projectRoot": planning_root,
                    "parent": feature_id,
                    "prerequisites": [task1_id],
                },
            )
            task2_id = task2.data["id"]

            task3 = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Add Frontend Integration",
                    "projectRoot": planning_root,
                    "parent": feature_id,
                    "prerequisites": [task2_id],
                },
            )
            task3_id = task3.data["id"]

            # Step 1: Direct claim first task
            result1 = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                    "taskId": task1_id,
                    "worktree": "feature/database-setup",
                },
            )

            claimed_task1 = result1.data["task"]
            assert claimed_task1["id"] == task1_id
            assert claimed_task1["status"] == "in-progress"
            assert result1.data["worktree"] == "feature/database-setup"

            # Step 2: Complete first task
            await client.call_tool(
                "completeTask",
                {
                    "taskId": task1_id,
                    "projectRoot": planning_root,
                    "summary": "Database schema created with user tables",
                    "filesChanged": ["schema.sql", "migrations/001_create_users.sql"],
                },
            )

            # Step 3: Direct claim second task (now unblocked)
            result2 = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                    "taskId": task2_id,
                    "worktree": "feature/api-endpoints",
                },
            )

            claimed_task2 = result2.data["task"]
            assert claimed_task2["id"] == task2_id
            assert claimed_task2["status"] == "in-progress"

            # Step 4: Complete second task
            await client.call_tool(
                "completeTask",
                {
                    "taskId": task2_id,
                    "projectRoot": planning_root,
                    "summary": "REST API endpoints implemented",
                    "filesChanged": ["api/users.py", "api/auth.py", "tests/test_api.py"],
                },
            )

            # Step 5: Direct claim third task (now unblocked)
            result3 = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                    "taskId": task3_id,
                    "worktree": "feature/frontend-integration",
                },
            )

            claimed_task3 = result3.data["task"]
            assert claimed_task3["id"] == task3_id
            assert claimed_task3["status"] == "in-progress"

            # Verify complete workflow integrity
            assert all(
                task["status"] == "in-progress"
                for task in [claimed_task1, claimed_task2, claimed_task3]
            )

    @pytest.mark.asyncio
    async def test_parallel_development_with_direct_claiming(self, temp_dir):
        """Test parallel development.

        Test where developers claim specific tasks from different features.
        """
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create project with multiple features for parallel development
            hierarchy = await create_test_hierarchy(client, planning_root, "Parallel Dev Test")
            epic_id = hierarchy["epic_id"]

            # Create Feature A: Authentication
            feature_a = await client.call_tool(
                "createObject",
                {
                    "kind": "feature",
                    "title": "Authentication Feature",
                    "projectRoot": planning_root,
                    "parent": epic_id,
                },
            )
            feature_a_id = feature_a.data["id"]

            # Create Feature B: User Management
            feature_b = await client.call_tool(
                "createObject",
                {
                    "kind": "feature",
                    "title": "User Management Feature",
                    "projectRoot": planning_root,
                    "parent": epic_id,
                },
            )
            feature_b_id = feature_b.data["id"]

            # Create tasks for Feature A
            auth_task1 = await create_task_with_priority(
                client, planning_root, feature_a_id, "Login Component", "high"
            )
            auth_task2 = await create_task_with_priority(
                client, planning_root, feature_a_id, "Password Reset", "normal"
            )

            # Create tasks for Feature B
            user_task1 = await create_task_with_priority(
                client, planning_root, feature_b_id, "User Profile Edit", "high"
            )
            user_task2 = await create_task_with_priority(
                client, planning_root, feature_b_id, "User Settings", "normal"
            )

            # Simulate parallel development - different developers claim specific tasks

            # Developer 1: Focus on authentication
            auth_result1 = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                    "taskId": auth_task1["id"],
                    "worktree": "feature/auth-login",
                },
            )

            # Developer 2: Focus on user management
            user_result1 = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                    "taskId": user_task1["id"],
                    "worktree": "feature/user-profile",
                },
            )

            # Developer 1: Claim second auth task
            auth_result2 = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                    "taskId": auth_task2["id"],
                    "worktree": "feature/auth-password-reset",
                },
            )

            # Developer 2: Claim second user task
            user_result2 = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                    "taskId": user_task2["id"],
                    "worktree": "feature/user-settings",
                },
            )

            # Verify all tasks claimed correctly
            claimed_tasks = [
                auth_result1.data["task"],
                user_result1.data["task"],
                auth_result2.data["task"],
                user_result2.data["task"],
            ]

            # All should be in-progress with correct IDs
            assert all(task["status"] == "in-progress" for task in claimed_tasks)

            claimed_ids = [task["id"] for task in claimed_tasks]
            expected_ids = [auth_task1["id"], user_task1["id"], auth_task2["id"], user_task2["id"]]
            assert set(claimed_ids) == set(expected_ids)

            # Verify worktree assignments are correct
            assert auth_result1.data["worktree"] == "feature/auth-login"
            assert user_result1.data["worktree"] == "feature/user-profile"
            assert auth_result2.data["worktree"] == "feature/auth-password-reset"
            assert user_result2.data["worktree"] == "feature/user-settings"


class TestDirectClaimingPerformanceAndScale:
    """Test performance and scalability of direct task claiming."""

    @pytest.mark.asyncio
    async def test_large_hierarchy_direct_claiming_performance(self, temp_dir):
        """Test direct claiming performance with large task hierarchies."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create large hierarchy (5 projects, 3 epics each, 3 features each,
            # 5 tasks each = 225 tasks)
            task_ids = []

            for project_num in range(5):
                project = await client.call_tool(
                    "createObject",
                    {
                        "kind": "project",
                        "title": f"Performance Test Project {project_num}",
                        "projectRoot": planning_root,
                    },
                )
                project_id = project.data["id"]

                for epic_num in range(3):
                    epic = await client.call_tool(
                        "createObject",
                        {
                            "kind": "epic",
                            "title": f"Epic {epic_num} in Project {project_num}",
                            "projectRoot": planning_root,
                            "parent": project_id,
                        },
                    )
                    epic_id = epic.data["id"]

                    for feature_num in range(3):
                        feature = await client.call_tool(
                            "createObject",
                            {
                                "kind": "feature",
                                "title": f"Feature {feature_num} in Epic {epic_num}",
                                "projectRoot": planning_root,
                                "parent": epic_id,
                            },
                        )
                        feature_id = feature.data["id"]

                        for task_num in range(5):
                            task = await create_task_with_priority(
                                client,
                                planning_root,
                                feature_id,
                                f"Task {task_num} in Feature {feature_num}",
                                "normal",
                            )
                            task_ids.append(task["id"])

            # Test direct claiming performance
            sample_task_ids = task_ids[::10]  # Every 10th task for performance testing

            start_time = time.time()

            for task_id in sample_task_ids[:10]:  # Test 10 direct claims
                result = await client.call_tool(
                    "claimNextTask",
                    {
                        "projectRoot": planning_root,
                        "taskId": task_id,
                    },
                )
                assert result.data["task"]["id"] == task_id
                assert result.data["task"]["status"] == "in-progress"

            end_time = time.time()
            total_time = end_time - start_time
            average_time = total_time / 10

            # Performance requirement: Average claim time should be < 200ms in large hierarchy
            assert (
                average_time < 0.2
            ), f"Average claiming time {average_time:.3f}s exceeds 200ms limit"

    @pytest.mark.asyncio
    async def test_complex_prerequisite_chain_resolution_performance(self, temp_dir):
        """Test performance with complex cross-system prerequisite chains."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create complex prerequisite chain spanning hierarchical and standalone tasks
            hierarchy = await create_test_hierarchy(client, planning_root, "Complex Prereq Test")
            feature_id = hierarchy["feature_id"]

            # Create chain: standalone → hierarchical → standalone → hierarchical
            task_ids = []

            # Level 1: Standalone foundation task
            foundation_task = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Foundation Standalone Task",
                    "projectRoot": planning_root,
                    # No parent = standalone
                },
            )
            foundation_id = foundation_task.data["id"]
            task_ids.append(foundation_id)

            # Level 2: Hierarchical task depending on standalone
            level2_task = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Level 2 Hierarchical Task",
                    "projectRoot": planning_root,
                    "parent": feature_id,
                    "prerequisites": [foundation_id],
                },
            )
            level2_id = level2_task.data["id"]
            task_ids.append(level2_id)

            # Level 3: Another standalone depending on hierarchical
            level3_task = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Level 3 Standalone Task",
                    "projectRoot": planning_root,
                    "prerequisites": [level2_id],
                    # No parent = standalone
                },
            )
            level3_id = level3_task.data["id"]
            task_ids.append(level3_id)

            # Level 4: Final hierarchical task depending on multiple prerequisites
            level4_task = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Level 4 Final Task",
                    "projectRoot": planning_root,
                    "parent": feature_id,
                    "prerequisites": [level2_id, level3_id],
                },
            )
            level4_id = level4_task.data["id"]
            task_ids.append(level4_id)

            # Complete the prerequisite chain and measure performance
            start_time = time.time()

            # Complete foundation task
            await client.call_tool(
                "updateObject",
                {
                    "id": foundation_id,
                    "projectRoot": planning_root,
                    "yamlPatch": {"status": "in-progress"},
                },
            )
            await client.call_tool(
                "completeTask",
                {
                    "taskId": foundation_id,
                    "projectRoot": planning_root,
                    "summary": "Foundation completed",
                    "filesChanged": ["foundation.py"],
                },
            )

            # Claim level 2 task (should be unblocked)
            result2 = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                    "taskId": level2_id,
                },
            )
            assert result2.data["task"]["id"] == level2_id

            # Complete level 2 task
            await client.call_tool(
                "completeTask",
                {
                    "taskId": level2_id,
                    "projectRoot": planning_root,
                    "summary": "Level 2 completed",
                    "filesChanged": ["level2.py"],
                },
            )

            # Claim level 3 task (should be unblocked)
            result3 = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                    "taskId": level3_id,
                },
            )
            assert result3.data["task"]["id"] == level3_id

            # Complete level 3 task
            await client.call_tool(
                "completeTask",
                {
                    "taskId": level3_id,
                    "projectRoot": planning_root,
                    "summary": "Level 3 completed",
                    "filesChanged": ["level3.py"],
                },
            )

            # Claim final task (should be unblocked)
            result4 = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                    "taskId": level4_id,
                },
            )
            assert result4.data["task"]["id"] == level4_id

            end_time = time.time()
            total_time = end_time - start_time

            # Performance requirement: Complex prerequisite resolution should complete < 2 seconds
            assert (
                total_time < 2.0
            ), f"Complex prerequisite chain resolution took {total_time:.3f}s, exceeds 2s limit"

    @pytest.mark.asyncio
    async def test_high_volume_concurrent_direct_claiming(self, temp_dir):
        """Test system behavior under high concurrent direct claiming load."""
        server, planning_root = create_test_server(temp_dir)

        # Create many tasks for load testing
        task_ids = []
        async with Client(server) as setup_client:
            hierarchy = await create_test_hierarchy(setup_client, planning_root, "High Volume Test")
            feature_id = hierarchy["feature_id"]

            # Create 50 tasks for high-volume testing
            for i in range(50):
                task = await create_task_with_priority(
                    setup_client, planning_root, feature_id, f"Volume Test Task {i}", "normal"
                )
                task_ids.append(task["id"])

            # Also create standalone tasks
            for i in range(25):
                standalone_task = await setup_client.call_tool(
                    "createObject",
                    {
                        "kind": "task",
                        "title": f"Standalone Volume Task {i}",
                        "projectRoot": planning_root,
                        # No parent = standalone
                    },
                )
                task_ids.append(standalone_task.data["id"])

        # Function for high-volume claiming
        async def rapid_claiming_worker(worker_id: int, task_subset: list[str]) -> dict[str, Any]:
            """Worker that rapidly claims tasks from its assigned subset."""
            successes = 0
            failures = 0
            start_time = time.time()

            async with Client(server) as client:
                for task_id in task_subset:
                    try:
                        result = await client.call_tool(
                            "claimNextTask",
                            {
                                "projectRoot": planning_root,
                                "taskId": task_id,
                            },
                        )
                        if result.data["task"]["id"] == task_id:
                            successes += 1
                    except Exception:
                        failures += 1

            end_time = time.time()
            return {
                "worker_id": worker_id,
                "successes": successes,
                "failures": failures,
                "duration": end_time - start_time,
            }

        # Distribute tasks among workers
        num_workers = 15
        tasks_per_worker = len(task_ids) // num_workers
        worker_tasks = []
        for i in range(num_workers):
            start_idx = i * tasks_per_worker
            end_idx = start_idx + tasks_per_worker if i < num_workers - 1 else len(task_ids)
            worker_tasks.append(task_ids[start_idx:end_idx])

        # Launch high-volume concurrent claiming
        start_time = time.time()
        worker_results = await asyncio.gather(
            *[rapid_claiming_worker(i, worker_tasks[i]) for i in range(num_workers)]
        )
        total_time = time.time() - start_time

        # Analyze results
        total_successes = sum(r["successes"] for r in worker_results)
        total_failures = sum(r["failures"] for r in worker_results)
        total_attempts = total_successes + total_failures

        # Verify system integrity under load
        assert total_successes <= len(task_ids), "More successes than tasks available"
        assert total_successes > 0, "No tasks were successfully claimed"

        # Performance requirements
        success_rate = total_successes / total_attempts if total_attempts > 0 else 0
        assert success_rate > 0.5, f"Success rate {success_rate:.2%} too low under load"

        throughput = total_successes / total_time
        assert throughput > 10, f"Throughput {throughput:.1f} claims/sec too low"

        # Verify no task was claimed multiple times (system integrity)
        assert total_successes == len(set(task_ids[:total_successes])), "Duplicate claims detected"
