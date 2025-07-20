"""Integration tests for scope-based task claiming workflow.

Comprehensive end-to-end testing of the scope-based claiming functionality,
including cross-system compatibility, error handling, and edge cases.
"""

import pytest
from fastmcp import Client

from ..fixtures.scope_test_data import (
    create_comprehensive_scope_test_environment,
    create_empty_scope_test_environment,
    create_prerequisite_chain_test_environment,
)
from .test_helpers import create_test_server


class TestScopeClaimingWorkflow:
    """Integration tests for scope-based task claiming workflow."""

    @pytest.mark.asyncio
    async def test_project_scope_claiming(self, temp_dir):
        """Test claiming tasks within project scope boundaries."""
        # Create server and test environment
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Setup comprehensive test environment
            test_env = await create_comprehensive_scope_test_environment(client, planning_root)
            ecommerce_project_id = test_env["projects"]["ecommerce"]["id"]
            analytics_project_id = test_env["projects"]["analytics"]["id"]

            # Test claiming within e-commerce project scope
            result = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                    "scope": ecommerce_project_id,
                },
            )

            claimed_task = result.data["task"]

            # Should claim highest priority unblocked task from e-commerce project
            assert claimed_task["status"] == "in-progress"
            assert claimed_task["priority"] == "high"
            assert result.data["claimed_status"] == "in-progress"

            # Verify task belongs to e-commerce project hierarchy or is standalone
            task_id = claimed_task["id"]
            ecommerce_task_ids = []
            for epic_data in test_env["projects"]["ecommerce"]["epics"].values():
                for feature_data in epic_data["features"].values():
                    ecommerce_task_ids.extend(feature_data["tasks"])

            # Task should be from e-commerce hierarchy or standalone
            # (standalone included in project scope)
            is_ecommerce_hierarchical = task_id in ecommerce_task_ids
            is_standalone = task_id in test_env["standalone_tasks"]
            assert is_ecommerce_hierarchical or is_standalone

            # Test claiming within analytics project scope
            result2 = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                    "scope": analytics_project_id,
                },
            )

            claimed_task2 = result2.data["task"]
            task_id2 = claimed_task2["id"]

            # Should not claim the same task twice
            assert task_id2 != task_id

            # Analytics project tasks or standalone tasks
            analytics_task_ids = []
            for epic_data in test_env["projects"]["analytics"]["epics"].values():
                for feature_data in epic_data["features"].values():
                    analytics_task_ids.extend(feature_data["tasks"])

            is_analytics_hierarchical = task_id2 in analytics_task_ids
            is_standalone2 = task_id2 in test_env["standalone_tasks"]
            assert is_analytics_hierarchical or is_standalone2

    @pytest.mark.asyncio
    async def test_epic_scope_claiming(self, temp_dir):
        """Test claiming tasks within epic scope boundaries."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            test_env = await create_comprehensive_scope_test_environment(client, planning_root)
            user_mgmt_epic_id = test_env["projects"]["ecommerce"]["epics"]["user_mgmt"]["id"]
            payment_epic_id = test_env["projects"]["ecommerce"]["epics"]["payment"]["id"]

            # Test claiming within user management epic scope
            result = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                    "scope": user_mgmt_epic_id,
                },
            )

            claimed_task = result.data["task"]
            task_id = claimed_task["id"]

            # Should only claim tasks from user management epic features
            user_mgmt_task_ids = []
            for feature_data in test_env["projects"]["ecommerce"]["epics"]["user_mgmt"][
                "features"
            ].values():
                user_mgmt_task_ids.extend(feature_data["tasks"])

            assert task_id in user_mgmt_task_ids
            assert claimed_task["status"] == "in-progress"

            # Should NOT include standalone tasks (epic scope excludes standalone)
            assert task_id not in test_env["standalone_tasks"]

            # Test claiming within payment epic scope
            result2 = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                    "scope": payment_epic_id,
                },
            )

            claimed_task2 = result2.data["task"]
            task_id2 = claimed_task2["id"]

            # Should claim different task from payment epic
            assert task_id2 != task_id

            payment_task_ids = []
            for feature_data in test_env["projects"]["ecommerce"]["epics"]["payment"][
                "features"
            ].values():
                payment_task_ids.extend(feature_data["tasks"])

            assert task_id2 in payment_task_ids

    @pytest.mark.asyncio
    async def test_feature_scope_claiming(self, temp_dir):
        """Test claiming tasks within feature scope boundaries."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            test_env = await create_comprehensive_scope_test_environment(client, planning_root)
            auth_feature_id = test_env["projects"]["ecommerce"]["epics"]["user_mgmt"]["features"][
                "auth"
            ]["id"]
            profile_feature_id = test_env["projects"]["ecommerce"]["epics"]["user_mgmt"][
                "features"
            ]["profile"]["id"]

            # Test claiming within auth feature scope
            result = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                    "scope": auth_feature_id,
                },
            )

            claimed_task = result.data["task"]
            task_id = claimed_task["id"]

            # Should only claim tasks directly from auth feature
            auth_task_ids = test_env["projects"]["ecommerce"]["epics"]["user_mgmt"]["features"][
                "auth"
            ]["tasks"]
            assert task_id in auth_task_ids
            assert claimed_task["status"] == "in-progress"

            # Should NOT include tasks from other features or standalone tasks
            profile_task_ids = test_env["projects"]["ecommerce"]["epics"]["user_mgmt"]["features"][
                "profile"
            ]["tasks"]
            assert task_id not in profile_task_ids
            assert task_id not in test_env["standalone_tasks"]

            # Test claiming within profile feature scope
            result2 = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                    "scope": profile_feature_id,
                },
            )

            claimed_task2 = result2.data["task"]
            task_id2 = claimed_task2["id"]

            # Should claim different task from profile feature
            assert task_id2 != task_id
            assert task_id2 in profile_task_ids

    @pytest.mark.asyncio
    async def test_scope_with_prerequisites(self, temp_dir):
        """Test claiming with prerequisites across scope boundaries."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            test_env = await create_prerequisite_chain_test_environment(client, planning_root)
            feature1_id = test_env["feature1_id"]
            feature2_id = test_env["feature2_id"]

            # Test claiming within feature1 scope - should get intermediate task
            # (foundation task is completed, so intermediate should be unblocked)
            result = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                    "scope": feature1_id,
                },
            )

            claimed_task = result.data["task"]

            # Should claim the intermediate task since foundation is completed
            assert claimed_task["id"] == test_env["intermediate_task_id"]
            assert claimed_task["status"] == "in-progress"

            # Complete the intermediate task to unblock cross-feature dependencies
            await client.call_tool(
                "completeTask",
                {
                    "taskId": test_env["intermediate_task_id"],
                    "projectRoot": planning_root,
                    "summary": "Intermediate task completed",
                    "filesChanged": ["intermediate.py"],
                },
            )

            # Now test claiming within feature2 scope - should get cross-feature task
            result2 = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                    "scope": feature2_id,
                },
            )

            claimed_task2 = result2.data["task"]

            # Should claim the cross-feature dependent task
            assert claimed_task2["id"] == test_env["cross_feature_task_id"]
            assert claimed_task2["status"] == "in-progress"

    @pytest.mark.asyncio
    async def test_empty_scope_handling(self, temp_dir):
        """Test graceful handling when scope contains no eligible tasks."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            test_env = await create_empty_scope_test_environment(client, planning_root)
            project_id = test_env["project_id"]
            epic_id = test_env["epic_id"]
            feature_id = test_env["feature_id"]

            # Test project scope with no eligible tasks
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "claimNextTask",
                    {
                        "projectRoot": planning_root,
                        "scope": project_id,
                    },
                )

            error_message = str(exc_info.value)
            assert (
                "No open tasks available within scope" in error_message
                or "No unblocked tasks available within scope" in error_message
            )
            assert project_id in error_message

            # Test epic scope with no eligible tasks
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "claimNextTask",
                    {
                        "projectRoot": planning_root,
                        "scope": epic_id,
                    },
                )

            error_message = str(exc_info.value)
            assert (
                "No open tasks available within scope" in error_message
                or "No unblocked tasks available within scope" in error_message
            )
            assert epic_id in error_message

            # Test feature scope with no eligible tasks
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "claimNextTask",
                    {
                        "projectRoot": planning_root,
                        "scope": feature_id,
                    },
                )

            error_message = str(exc_info.value)
            assert (
                "No open tasks available within scope" in error_message
                or "No unblocked tasks available within scope" in error_message
            )
            assert feature_id in error_message


class TestCrossSystemCompatibility:
    """Test scope filtering with mixed hierarchical/standalone task environments."""

    @pytest.mark.asyncio
    async def test_mixed_environment_project_scope(self, temp_dir):
        """Test project scope includes both hierarchical and standalone tasks."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            test_env = await create_comprehensive_scope_test_environment(client, planning_root)
            project_id = test_env["projects"]["ecommerce"]["id"]

            # Claim multiple tasks from project scope
            claimed_tasks = []
            for _ in range(3):  # Try to claim several tasks
                try:
                    result = await client.call_tool(
                        "claimNextTask",
                        {
                            "projectRoot": planning_root,
                            "scope": project_id,
                        },
                    )
                    claimed_tasks.append(result.data["task"])
                except Exception:
                    # Stop when no more tasks available
                    break

            # Should have claimed some tasks
            assert len(claimed_tasks) > 0

            # Verify mix of hierarchical and standalone tasks
            hierarchical_count = 0
            standalone_count = 0

            for task in claimed_tasks:
                if task["parent"]:  # Has parent = hierarchical
                    hierarchical_count += 1
                else:  # No parent = standalone
                    standalone_count += 1

            # Should include both types (depending on test data structure)
            # At minimum, should respect scope boundaries properly
            for task in claimed_tasks:
                task_id = task["id"]

                if task["parent"]:  # Hierarchical task
                    # Should belong to the scoped project hierarchy
                    project_task_ids = []
                    for epic_data in test_env["projects"]["ecommerce"]["epics"].values():
                        for feature_data in epic_data["features"].values():
                            project_task_ids.extend(feature_data["tasks"])
                    assert task_id in project_task_ids
                else:  # Standalone task
                    # Should be in standalone tasks list
                    assert task_id in test_env["standalone_tasks"]

    @pytest.mark.asyncio
    async def test_epic_scope_excludes_standalone_tasks(self, temp_dir):
        """Test that epic scope filtering excludes standalone tasks."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            test_env = await create_comprehensive_scope_test_environment(client, planning_root)
            epic_id = test_env["projects"]["ecommerce"]["epics"]["user_mgmt"]["id"]

            # Claim all available tasks from epic scope
            claimed_tasks = []
            for _ in range(10):  # Try to claim many tasks
                try:
                    result = await client.call_tool(
                        "claimNextTask",
                        {
                            "projectRoot": planning_root,
                            "scope": epic_id,
                        },
                    )
                    claimed_tasks.append(result.data["task"])
                except Exception:
                    # Stop when no more tasks available
                    break

            # All claimed tasks should be hierarchical (have parents)
            for task in claimed_tasks:
                assert task["parent"] is not None and task["parent"] != ""

                # Should belong to the epic's features
                epic_task_ids = []
                for feature_data in test_env["projects"]["ecommerce"]["epics"]["user_mgmt"][
                    "features"
                ].values():
                    epic_task_ids.extend(feature_data["tasks"])
                assert task["id"] in epic_task_ids

                # Should NOT be standalone
                assert task["id"] not in test_env["standalone_tasks"]

    @pytest.mark.asyncio
    async def test_cross_system_prerequisite_validation(self, temp_dir):
        """Test prerequisite validation across hierarchical and standalone systems."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            test_env = await create_prerequisite_chain_test_environment(client, planning_root)
            project_id = test_env["project_id"]

            # Test claiming standalone task that depends on hierarchical task
            # The foundation task should be completed, so standalone dependent should be unblocked
            result = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                    "scope": project_id,  # Project scope includes standalone tasks
                },
            )

            claimed_task = result.data["task"]

            # Should be able to claim a task (either hierarchical or standalone)
            assert claimed_task["status"] == "in-progress"

            # If it's the standalone dependent task, verify cross-system prerequisite was validated
            if claimed_task["id"] == test_env["standalone_dependent_id"]:
                # This validates that cross-system prerequisite checking worked
                # (standalone task had hierarchical prerequisite that was completed)
                assert claimed_task["parent"] is None or claimed_task["parent"] == ""


class TestErrorConditions:
    """Test error handling for invalid scopes and edge cases."""

    @pytest.mark.asyncio
    async def test_invalid_scope_ids(self, temp_dir):
        """Test error handling for malformed and non-existent scope IDs."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Test malformed scope ID
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "claimNextTask",
                    {
                        "projectRoot": planning_root,
                        "scope": "invalid-scope-format",
                    },
                )

            error_message = str(exc_info.value)
            assert "Invalid scope ID format" in error_message

            # Test task ID as scope (should be rejected)
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "claimNextTask",
                    {
                        "projectRoot": planning_root,
                        "scope": "T-task-id",
                    },
                )

            error_message = str(exc_info.value)
            assert "Invalid scope ID format" in error_message

            # Test scope with invalid characters
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "claimNextTask",
                    {
                        "projectRoot": planning_root,
                        "scope": "P-invalid@scope#",
                    },
                )

            error_message = str(exc_info.value)
            assert "Invalid scope ID format" in error_message

    @pytest.mark.asyncio
    async def test_nonexistent_scope_objects(self, temp_dir):
        """Test error handling for valid format but non-existent scope objects."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create minimal environment
            await create_comprehensive_scope_test_environment(client, planning_root)

            # Test non-existent project
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "claimNextTask",
                    {
                        "projectRoot": planning_root,
                        "scope": "P-nonexistent-project",
                    },
                )

            error_message = str(exc_info.value)
            assert "Scope object not found" in error_message
            assert "P-nonexistent-project" in error_message

            # Test non-existent epic
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "claimNextTask",
                    {
                        "projectRoot": planning_root,
                        "scope": "E-nonexistent-epic",
                    },
                )

            error_message = str(exc_info.value)
            assert "Scope object not found" in error_message
            assert "E-nonexistent-epic" in error_message

            # Test non-existent feature
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "claimNextTask",
                    {
                        "projectRoot": planning_root,
                        "scope": "F-nonexistent-feature",
                    },
                )

            error_message = str(exc_info.value)
            assert "Scope object not found" in error_message
            assert "F-nonexistent-feature" in error_message

    @pytest.mark.asyncio
    async def test_scope_with_incomplete_prerequisites(self, temp_dir):
        """Test scope filtering when all tasks have incomplete prerequisites."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create hierarchy with blocked tasks
            project = await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Blocked Tasks Project",
                    "projectRoot": planning_root,
                },
            )
            project_id = project.data["id"]

            epic = await client.call_tool(
                "createObject",
                {
                    "kind": "epic",
                    "title": "Blocked Epic",
                    "projectRoot": planning_root,
                    "parent": project_id,
                },
            )
            epic_id = epic.data["id"]

            feature = await client.call_tool(
                "createObject",
                {
                    "kind": "feature",
                    "title": "Blocked Feature",
                    "projectRoot": planning_root,
                    "parent": epic_id,
                },
            )
            feature_id = feature.data["id"]

            # Create prerequisite tasks but set them to in-progress (not claimable)
            prereq1_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Incomplete Prerequisite 1",
                    "projectRoot": planning_root,
                    "parent": feature_id,
                },
            )

            prereq2_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Incomplete Prerequisite 2",
                    "projectRoot": planning_root,
                    "parent": feature_id,
                },
            )

            # Set prerequisite tasks to in-progress so they're not claimable
            await client.call_tool(
                "updateObject",
                {
                    "id": prereq1_result.data["id"],
                    "projectRoot": planning_root,
                    "yamlPatch": {"status": "in-progress"},
                },
            )

            await client.call_tool(
                "updateObject",
                {
                    "id": prereq2_result.data["id"],
                    "projectRoot": planning_root,
                    "yamlPatch": {"status": "in-progress"},
                },
            )

            # Create tasks with incomplete prerequisites
            await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Blocked Task 1",
                    "projectRoot": planning_root,
                    "parent": feature_id,
                    "prerequisites": [prereq1_result.data["id"]],
                },
            )

            await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Blocked Task 2",
                    "projectRoot": planning_root,
                    "parent": feature_id,
                    "prerequisites": [prereq2_result.data["id"]],
                },
            )

            # Test claiming with all tasks blocked
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "claimNextTask",
                    {
                        "projectRoot": planning_root,
                        "scope": project_id,
                    },
                )

            error_message = str(exc_info.value)
            assert (
                "No open tasks available within scope" in error_message
                or "No unblocked tasks available within scope" in error_message
            )
            # Note: "incomplete prerequisites" may not be in message for "no open tasks" case

    @pytest.mark.asyncio
    async def test_integration_error_propagation(self, temp_dir):
        """Test error propagation from scanner through core to tool interface."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Test with empty planning root (no tasks exist)
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "claimNextTask",
                    {
                        "projectRoot": planning_root,
                        "scope": "P-any-project",
                    },
                )

            error_message = str(exc_info.value)
            # Should get scope validation error first (scope doesn't exist)
            assert "Scope object not found" in error_message

            # Test with invalid project root
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "claimNextTask",
                    {
                        "projectRoot": "",  # Empty project root
                        "scope": "P-test-project",
                    },
                )

            error_message = str(exc_info.value)
            assert "Project root cannot be empty" in error_message


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    @pytest.mark.asyncio
    async def test_scope_with_only_completed_tasks(self, temp_dir):
        """Test scope that contains only completed tasks."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create minimal hierarchy
            project = await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Completed Tasks Project",
                    "projectRoot": planning_root,
                },
            )
            project_id = project.data["id"]

            epic = await client.call_tool(
                "createObject",
                {
                    "kind": "epic",
                    "title": "Completed Epic",
                    "projectRoot": planning_root,
                    "parent": project_id,
                },
            )
            epic_id = epic.data["id"]

            feature = await client.call_tool(
                "createObject",
                {
                    "kind": "feature",
                    "title": "Completed Feature",
                    "projectRoot": planning_root,
                    "parent": epic_id,
                },
            )
            feature_id = feature.data["id"]

            # Create and complete a task
            task_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Task to Complete",
                    "projectRoot": planning_root,
                    "parent": feature_id,
                },
            )

            # Set task to in-progress then complete it
            await client.call_tool(
                "updateObject",
                {
                    "id": task_result.data["id"],
                    "projectRoot": planning_root,
                    "yamlPatch": {"status": "in-progress"},
                },
            )

            await client.call_tool(
                "completeTask",
                {
                    "taskId": task_result.data["id"],
                    "projectRoot": planning_root,
                    "summary": "Completed for testing",
                    "filesChanged": [],
                },
            )

            # Try to claim from scope with only completed tasks
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "claimNextTask",
                    {
                        "projectRoot": planning_root,
                        "scope": feature_id,
                    },
                )

            error_message = str(exc_info.value)
            assert (
                "No open tasks available within scope" in error_message
                or "No unblocked tasks available within scope" in error_message
            )

    @pytest.mark.asyncio
    async def test_backward_compatibility_no_scope(self, temp_dir):
        """Test that claiming without scope parameter maintains existing behavior."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            test_env = await create_comprehensive_scope_test_environment(client, planning_root)

            # Claim task without scope (should work as before)
            result = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                    # No scope parameter
                },
            )

            claimed_task = result.data["task"]

            # Should claim highest priority unblocked task from anywhere
            assert claimed_task["status"] == "in-progress"
            assert claimed_task["priority"] == "high"  # Should prioritize high priority tasks
            assert result.data["claimed_status"] == "in-progress"

            # Task should be from the unblocked tasks list
            assert claimed_task["id"] in test_env["unblocked_tasks"]

    @pytest.mark.asyncio
    async def test_empty_scope_parameter(self, temp_dir):
        """Test claiming with empty scope parameter (should act like no scope)."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            test_env = await create_comprehensive_scope_test_environment(client, planning_root)

            # Claim task with empty scope
            result = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                    "scope": "",  # Empty scope
                },
            )

            claimed_task = result.data["task"]

            # Should claim highest priority unblocked task from anywhere (no scope filtering)
            assert claimed_task["status"] == "in-progress"
            assert claimed_task["priority"] == "high"
            assert result.data["claimed_status"] == "in-progress"

            # Task should be from the unblocked tasks list
            assert claimed_task["id"] in test_env["unblocked_tasks"]
