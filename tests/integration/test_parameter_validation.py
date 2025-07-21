"""Integration tests for comprehensive parameter validation.

Comprehensive end-to-end testing of the enhanced parameter validation system to
ensure all parameter combinations, error scenarios, and backward compatibility
requirements are thoroughly validated.
"""

import pytest
from fastmcp import Client

from ..fixtures.scope_test_data import (
    create_comprehensive_scope_test_environment,
)
from .test_helpers import create_task_with_priority, create_test_hierarchy, create_test_server


class TestValidParameterCombinations:
    """Test all valid parameter combinations work correctly."""

    @pytest.mark.asyncio
    async def test_project_root_only(self, temp_dir):
        """Test claimNextTask(projectRoot="path") works correctly."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create test hierarchy and task
            hierarchy = await create_test_hierarchy(client, planning_root, "Project Root Only")
            feature_id = hierarchy["feature_id"]

            # Create a task to claim
            task_result = await create_task_with_priority(
                client, planning_root, feature_id, "Project Root Only Task", "high"
            )
            task_id = task_result["id"]

            # Test project root only parameter
            result = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                },
            )

            # Verify successful claim
            claimed_task = result.data["task"]
            assert claimed_task["id"] == task_id
            assert claimed_task["status"] == "in-progress"
            assert result.data["claimed_status"] == "in-progress"
            assert result.data["worktree"] == ""

    @pytest.mark.asyncio
    async def test_with_worktree(self, temp_dir):
        """Test claimNextTask(projectRoot="path", worktree="branch") works."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create test hierarchy and task
            hierarchy = await create_test_hierarchy(client, planning_root, "Worktree Test")
            feature_id = hierarchy["feature_id"]

            # Create a task to claim
            task_result = await create_task_with_priority(
                client, planning_root, feature_id, "Worktree Task", "normal"
            )
            task_id = task_result["id"]

            # Test with worktree parameter
            result = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                    "worktree": "feature/test-branch",
                },
            )

            # Verify successful claim with worktree
            claimed_task = result.data["task"]
            assert claimed_task["id"] == task_id
            assert claimed_task["status"] == "in-progress"
            assert result.data["worktree"] == "feature/test-branch"

    @pytest.mark.asyncio
    async def test_with_scope(self, temp_dir):
        """Test claimNextTask(projectRoot="path", scope="P-project") works."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create test hierarchy and task
            hierarchy = await create_test_hierarchy(client, planning_root, "Scope Test")
            project_id = hierarchy["project_id"]
            feature_id = hierarchy["feature_id"]

            # Create a task to claim
            task_result = await create_task_with_priority(
                client, planning_root, feature_id, "Scope Task", "high"
            )
            task_id = task_result["id"]

            # Test with scope parameter
            result = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                    "scope": project_id,
                },
            )

            # Verify successful claim within scope
            claimed_task = result.data["task"]
            assert claimed_task["id"] == task_id
            assert claimed_task["status"] == "in-progress"

    @pytest.mark.asyncio
    async def test_scope_plus_worktree(self, temp_dir):
        """Test claimNextTask(projectRoot="path", scope="F-feature", worktree="branch") works."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create test hierarchy and task
            hierarchy = await create_test_hierarchy(client, planning_root, "Scope Worktree Test")
            feature_id = hierarchy["feature_id"]

            # Create a task to claim
            task_result = await create_task_with_priority(
                client, planning_root, feature_id, "Scope Worktree Task", "normal"
            )
            task_id = task_result["id"]

            # Test scope + worktree combination
            result = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                    "scope": feature_id,
                    "worktree": "feature/scoped-work",
                },
            )

            # Verify successful claim with both scope and worktree
            claimed_task = result.data["task"]
            assert claimed_task["id"] == task_id
            assert claimed_task["status"] == "in-progress"
            assert result.data["worktree"] == "feature/scoped-work"

    @pytest.mark.asyncio
    async def test_task_id_only(self, temp_dir):
        """Test claimNextTask(projectRoot="path", taskId="T-task") works."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create test hierarchy and task
            hierarchy = await create_test_hierarchy(client, planning_root, "Task ID Test")
            feature_id = hierarchy["feature_id"]

            # Create a task to claim
            task_result = await create_task_with_priority(
                client, planning_root, feature_id, "Direct Task", "low"
            )
            task_id = task_result["id"]

            # Test direct task claiming
            result = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                    "taskId": task_id,
                },
            )

            # Verify successful direct claim
            claimed_task = result.data["task"]
            assert claimed_task["id"] == task_id
            assert claimed_task["status"] == "in-progress"

    @pytest.mark.asyncio
    async def test_task_id_plus_force(self, temp_dir):
        """Test claimNextTask(projectRoot="path", taskId="T-task", force_claim=True) works."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create test hierarchy and task
            hierarchy = await create_test_hierarchy(client, planning_root, "Force Claim Test")
            feature_id = hierarchy["feature_id"]

            # Create a task and set it to in-progress (to test force claim)
            task_result = await create_task_with_priority(
                client, planning_root, feature_id, "Force Claim Task", "high"
            )
            task_id = task_result["id"]

            # Set task to in-progress
            await client.call_tool(
                "updateObject",
                {
                    "id": task_id,
                    "projectRoot": planning_root,
                    "yamlPatch": {"status": "in-progress"},
                },
            )

            # Test force claim
            result = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                    "taskId": task_id,
                    "force_claim": True,
                },
            )

            # Verify successful force claim
            claimed_task = result.data["task"]
            assert claimed_task["id"] == task_id
            assert claimed_task["status"] == "in-progress"

    @pytest.mark.asyncio
    async def test_task_id_plus_worktree(self, temp_dir):
        """Test claimNextTask(projectRoot="path", taskId="T-task", worktree="branch") works."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create test hierarchy and task
            hierarchy = await create_test_hierarchy(client, planning_root, "Task ID Worktree Test")
            feature_id = hierarchy["feature_id"]

            # Create a task to claim
            task_result = await create_task_with_priority(
                client, planning_root, feature_id, "Task ID Worktree Task", "normal"
            )
            task_id = task_result["id"]

            # Test task ID + worktree combination
            result = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                    "taskId": task_id,
                    "worktree": "task/specific-work",
                },
            )

            # Verify successful claim with worktree
            claimed_task = result.data["task"]
            assert claimed_task["id"] == task_id
            assert claimed_task["status"] == "in-progress"
            assert result.data["worktree"] == "task/specific-work"


class TestInvalidParameterCombinations:
    """Test all invalid parameter combinations produce appropriate errors."""

    @pytest.mark.asyncio
    async def test_mutual_exclusivity_scope_and_task_id(self, temp_dir):
        """Test scope="P-proj" + taskId="T-task" raises appropriate error."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create test hierarchy and task
            hierarchy = await create_test_hierarchy(
                client, planning_root, "Mutual Exclusivity Test"
            )
            project_id = hierarchy["project_id"]
            feature_id = hierarchy["feature_id"]

            task_result = await create_task_with_priority(
                client, planning_root, feature_id, "Mutual Exclusivity Task", "normal"
            )
            task_id = task_result["id"]

            # Test mutual exclusivity violation
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "claimNextTask",
                    {
                        "projectRoot": planning_root,
                        "scope": project_id,
                        "taskId": task_id,
                    },
                )

            error_message = str(exc_info.value)
            assert "cannot specify both scope and task_id" in error_message.lower()

    @pytest.mark.asyncio
    async def test_force_claim_without_task_id(self, temp_dir):
        """Test force_claim=True without taskId raises error."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Test force claim without task ID
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "claimNextTask",
                    {
                        "projectRoot": planning_root,
                        "force_claim": True,
                    },
                )

            error_message = str(exc_info.value)
            assert "force_claim" in error_message.lower()
            assert "requires task_id" in error_message.lower() or "taskid" in error_message.lower()

    @pytest.mark.asyncio
    async def test_force_claim_with_scope(self, temp_dir):
        """Test force_claim=True + scope="P-proj" raises error."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create test hierarchy
            hierarchy = await create_test_hierarchy(client, planning_root, "Force Claim Scope Test")
            project_id = hierarchy["project_id"]

            # Test force claim with scope (should fail due to mutual exclusivity)
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "claimNextTask",
                    {
                        "projectRoot": planning_root,
                        "scope": project_id,
                        "force_claim": True,
                    },
                )

            error_message = str(exc_info.value)
            # Either force_claim scope error or mutual exclusivity error is acceptable
            assert (
                "force_claim" in error_message.lower()
                or "cannot specify both scope and task_id" in error_message.lower()
            )

    @pytest.mark.asyncio
    async def test_empty_project_root(self, temp_dir):
        """Test projectRoot="" raises appropriate error."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Test empty project root
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "claimNextTask",
                    {
                        "projectRoot": "",
                    },
                )

            error_message = str(exc_info.value)
            assert "project root cannot be empty" in error_message.lower()

    @pytest.mark.asyncio
    async def test_invalid_scope_format(self, temp_dir):
        """Test scope="invalid-format" raises format error."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Test invalid scope format
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "claimNextTask",
                    {
                        "projectRoot": planning_root,
                        "scope": "invalid-format",
                    },
                )

            error_message = str(exc_info.value)
            assert "invalid scope id format" in error_message.lower()
            assert "must use p-, e-, or f- prefix" in error_message.lower()

    @pytest.mark.asyncio
    async def test_invalid_task_id_format(self, temp_dir):
        """Test taskId="invalid-format" raises task not found error."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Test invalid task ID (format might be valid but task doesn't exist)
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "claimNextTask",
                    {
                        "projectRoot": planning_root,
                        "taskId": "invalid-format",
                    },
                )

            error_message = str(exc_info.value)
            # The actual behavior is that the task is not found, not a format error
            # This is because the ClaimingParams validation may accept the format
            # but the task doesn't exist in the planning structure
            assert "task not found" in error_message.lower() or "not found" in error_message.lower()


class TestErrorMessageQuality:
    """Test error message quality and actionable guidance."""

    @pytest.mark.asyncio
    async def test_specific_error_messages_for_different_violations(self, temp_dir):
        """Test each error type has distinct, clear message."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create test hierarchy for some tests
            hierarchy = await create_test_hierarchy(client, planning_root, "Error Message Test")
            project_id = hierarchy["project_id"]
            feature_id = hierarchy["feature_id"]

            task_result = await create_task_with_priority(
                client, planning_root, feature_id, "Error Test Task", "normal"
            )
            task_id = task_result["id"]

            # Test different error scenarios and verify distinct messages

            # 1. Mutual exclusivity error
            with pytest.raises(Exception) as exc_info_1:
                await client.call_tool(
                    "claimNextTask",
                    {
                        "projectRoot": planning_root,
                        "scope": project_id,
                        "taskId": task_id,
                    },
                )
            mutual_exclusivity_error = str(exc_info_1.value)

            # 2. Force claim scope error
            with pytest.raises(Exception) as exc_info_2:
                await client.call_tool(
                    "claimNextTask",
                    {
                        "projectRoot": planning_root,
                        "force_claim": True,
                    },
                )
            force_claim_error = str(exc_info_2.value)

            # 3. Invalid scope format error
            with pytest.raises(Exception) as exc_info_3:
                await client.call_tool(
                    "claimNextTask",
                    {
                        "projectRoot": planning_root,
                        "scope": "bad-format",
                    },
                )
            scope_format_error = str(exc_info_3.value)

            # 4. Empty project root error
            with pytest.raises(Exception) as exc_info_4:
                await client.call_tool(
                    "claimNextTask",
                    {
                        "projectRoot": "",
                    },
                )
            empty_root_error = str(exc_info_4.value)

            # Verify all errors are distinct
            error_messages = [
                mutual_exclusivity_error,
                force_claim_error,
                scope_format_error,
                empty_root_error,
            ]
            for i, error1 in enumerate(error_messages):
                for j, error2 in enumerate(error_messages):
                    if i != j:
                        assert error1 != error2, f"Error messages {i} and {j} are identical"

    @pytest.mark.asyncio
    async def test_error_messages_include_parameter_context(self, temp_dir):
        """Test error messages include relevant parameter names and values."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Test scope format error includes the invalid value
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "claimNextTask",
                    {
                        "projectRoot": planning_root,
                        "scope": "INVALID-SCOPE-123",
                    },
                )

            error_message = str(exc_info.value)
            assert "INVALID-SCOPE-123" in error_message
            assert "scope" in error_message.lower()

    @pytest.mark.asyncio
    async def test_error_messages_provide_actionable_guidance(self, temp_dir):
        """Test error messages suggest how to fix the parameter issue."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Test mutual exclusivity error provides guidance
            hierarchy = await create_test_hierarchy(client, planning_root, "Guidance Test")
            project_id = hierarchy["project_id"]
            feature_id = hierarchy["feature_id"]

            task_result = await create_task_with_priority(
                client, planning_root, feature_id, "Guidance Task", "normal"
            )
            task_id = task_result["id"]

            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "claimNextTask",
                    {
                        "projectRoot": planning_root,
                        "scope": project_id,
                        "taskId": task_id,
                    },
                )

            error_message = str(exc_info.value)
            # Should provide guidance on how to fix the issue
            assert any(
                guidance in error_message.lower()
                for guidance in [
                    "use scope for filtering",
                    "or task_id for direct",
                    "choose either scope or task_id",
                ]
            )

    @pytest.mark.asyncio
    async def test_consistent_error_message_format(self, temp_dir):
        """Test all parameter validation errors follow consistent format."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Collect various parameter validation errors
            error_messages = []

            # Empty project root
            try:
                await client.call_tool("claimNextTask", {"projectRoot": ""})
            except Exception as e:
                error_messages.append(str(e))

            # Invalid scope format
            try:
                await client.call_tool(
                    "claimNextTask",
                    {"projectRoot": planning_root, "scope": "bad-format"},
                )
            except Exception as e:
                error_messages.append(str(e))

            # Force claim without task ID
            try:
                await client.call_tool(
                    "claimNextTask",
                    {"projectRoot": planning_root, "force_claim": True},
                )
            except Exception as e:
                error_messages.append(str(e))

            # Verify we collected error messages
            assert len(error_messages) >= 3

            # All should be validation errors (not internal server errors)
            for error_msg in error_messages:
                assert "validation" in error_msg.lower() or "invalid" in error_msg.lower()


class TestBackwardCompatibility:
    """Test existing claimNextTask usage patterns work unchanged."""

    @pytest.mark.asyncio
    async def test_legacy_project_root_only_calls(self, temp_dir):
        """Test claimNextTask(projectRoot, worktree) works unchanged."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create test hierarchy and task
            hierarchy = await create_test_hierarchy(client, planning_root, "Legacy Test")
            feature_id = hierarchy["feature_id"]

            # Create a task to claim
            task_result = await create_task_with_priority(
                client, planning_root, feature_id, "Legacy Task", "high"
            )
            task_id = task_result["id"]

            # Test legacy call pattern (positional-style usage)
            result = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                    "worktree": "legacy-workspace",
                },
            )

            # Verify it works exactly as before
            claimed_task = result.data["task"]
            assert claimed_task["id"] == task_id
            assert claimed_task["status"] == "in-progress"
            assert result.data["worktree"] == "legacy-workspace"

    @pytest.mark.asyncio
    async def test_return_format_unchanged(self, temp_dir):
        """Test tool returns same data structure as before."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create test hierarchy and task
            hierarchy = await create_test_hierarchy(client, planning_root, "Return Format Test")
            feature_id = hierarchy["feature_id"]

            # Create a task to claim
            await create_task_with_priority(
                client, planning_root, feature_id, "Return Format Task", "normal"
            )

            # Test claim
            result = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                },
            )

            # Verify return structure matches expected format
            assert "task" in result.data
            assert "claimed_status" in result.data
            assert "worktree" in result.data
            assert "file_path" in result.data

            # Verify task structure
            task = result.data["task"]
            required_task_fields = [
                "id",
                "title",
                "status",
                "priority",
                "parent",
                "file_path",
                "created",
                "updated",
            ]
            for field in required_task_fields:
                assert field in task, f"Missing required task field: {field}"

    @pytest.mark.asyncio
    async def test_no_regressions_in_existing_functionality(self, temp_dir):
        """Test no existing functionality broken by parameter validation."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create comprehensive test environment
            test_env = await create_comprehensive_scope_test_environment(client, planning_root)
            unblocked_tasks = test_env["unblocked_tasks"]

            # Ensure we have tasks to claim
            assert len(unblocked_tasks) > 0, "Need unblocked tasks for regression test"

            # Test standard claiming works exactly as before
            result = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                },
            )

            # Should claim highest priority task
            claimed_task = result.data["task"]
            assert claimed_task["id"] in unblocked_tasks
            assert claimed_task["status"] == "in-progress"

    @pytest.mark.asyncio
    async def test_performance_no_degradation(self, temp_dir):
        """Test parameter validation doesn't significantly impact performance."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create simple test environment
            hierarchy = await create_test_hierarchy(client, planning_root, "Performance Test")
            feature_id = hierarchy["feature_id"]

            # Create a task to claim
            await create_task_with_priority(
                client, planning_root, feature_id, "Performance Task", "high"
            )

            # Time the claiming operation (basic performance check)
            import time

            start_time = time.time()

            result = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                },
            )

            end_time = time.time()
            duration = end_time - start_time

            # Verify operation completed successfully
            assert result.data["task"]["status"] == "in-progress"

            # Basic performance check - should complete within reasonable time
            # (This is not a precise benchmark, just ensuring no major regression)
            assert duration < 5.0, f"Claiming took too long: {duration}s"


class TestEdgeCases:
    """Test boundary conditions and unusual input scenarios."""

    @pytest.mark.asyncio
    async def test_whitespace_handling_in_parameters(self, temp_dir):
        """Test parameters with whitespace handled correctly."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create test hierarchy and task
            hierarchy = await create_test_hierarchy(client, planning_root, "Whitespace Test")
            feature_id = hierarchy["feature_id"]

            # Create a task to claim
            task_result = await create_task_with_priority(
                client, planning_root, feature_id, "Whitespace Task", "normal"
            )
            task_id = task_result["id"]

            # Test claiming with whitespace in task ID
            result = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                    "taskId": f"  {task_id}  ",  # Whitespace around task ID
                },
            )

            # Should handle whitespace correctly
            claimed_task = result.data["task"]
            assert claimed_task["id"] == task_id
            assert claimed_task["status"] == "in-progress"

    @pytest.mark.asyncio
    async def test_none_values_for_optional_parameters(self, temp_dir):
        """Test None values for optional parameters work correctly."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create test hierarchy and task
            hierarchy = await create_test_hierarchy(client, planning_root, "None Values Test")
            feature_id = hierarchy["feature_id"]

            # Create a task to claim
            task_result = await create_task_with_priority(
                client, planning_root, feature_id, "None Values Task", "high"
            )
            task_id = task_result["id"]

            # Test with explicit None values (if the API accepts them)
            # Note: FastMCP may handle None differently, so this tests the actual behavior
            result = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                    "worktree": "",  # Empty string instead of None
                    "scope": "",  # Empty string instead of None
                    "taskId": "",  # Empty string instead of None
                    "force_claim": False,
                },
            )

            # Should work with explicit empty values
            claimed_task = result.data["task"]
            assert claimed_task["id"] == task_id
            assert claimed_task["status"] == "in-progress"

    @pytest.mark.asyncio
    async def test_empty_strings_vs_none_consistency(self, temp_dir):
        """Test empty strings vs None handled consistently."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Create test hierarchy and tasks
            hierarchy = await create_test_hierarchy(client, planning_root, "Empty String Test")
            feature_id = hierarchy["feature_id"]

            # Create two tasks to test different calls
            await create_task_with_priority(
                client, planning_root, feature_id, "Empty String Task 1", "high"
            )
            await create_task_with_priority(
                client, planning_root, feature_id, "Empty String Task 2", "high"
            )

            # Claim first task with minimal parameters
            result1 = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                },
            )

            # Claim second task with explicit empty strings
            result2 = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                    "worktree": "",
                    "scope": "",
                    "taskId": "",
                    "force_claim": False,
                },
            )

            # Both should work and have consistent behavior
            assert result1.data["task"]["status"] == "in-progress"
            assert result2.data["task"]["status"] == "in-progress"

    @pytest.mark.asyncio
    async def test_case_sensitivity_in_parameter_validation(self, temp_dir):
        """Test parameter validation handles case appropriately."""
        server, planning_root = create_test_server(temp_dir)

        async with Client(server) as client:
            # Test invalid scope format with wrong case prefix
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "claimNextTask",
                    {
                        "projectRoot": planning_root,
                        "scope": "p-lowercase-prefix",  # Should be P-, not p-
                    },
                )

            error_message = str(exc_info.value)
            assert "invalid scope id format" in error_message.lower()
            assert "must use p-, e-, or f- prefix" in error_message.lower()
