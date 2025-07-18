"""Integration tests for enhanced validation error workflows.

This module tests complete validation error workflows with the enhanced error
handling system, including error collection, MCP tool error responses, security
validation, and real-world error scenarios.
"""

import pytest
from fastmcp import Client

from trellis_mcp.server import create_server
from trellis_mcp.settings import Settings


@pytest.mark.asyncio
async def test_error_collector_integration_multiple_errors(temp_dir):
    """Integration test: error collector aggregates multiple validation errors."""
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
        # Test multiple validation errors in a single create operation
        with pytest.raises(Exception) as exc_info:
            await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Test Task",  # Valid title
                    "description": "Task with multiple validation errors",
                    "projectRoot": planning_root,
                    "status": "invalid_status",  # Invalid status enum
                    "priority": "ultra_high",  # Invalid priority enum
                },
            )

        # Verify error collector aggregated all errors
        error_message = str(exc_info.value)

        # Should contain multiple error types
        assert "status" in error_message  # Invalid status
        assert "priority" in error_message  # Invalid priority

        # Verify no file was created due to validation failures
        planning_path = temp_dir / "planning"
        if planning_path.exists():
            task_files = list(planning_path.glob("tasks-open/T-*.md"))
            assert len(task_files) == 0

        # Test title validation separately
        with pytest.raises(Exception) as exc_info:
            await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "",  # Missing title (required field)
                    "description": "Task with missing title",
                    "projectRoot": planning_root,
                    "status": "open",
                    "priority": "high",
                },
            )

        # Verify title validation error
        error_message = str(exc_info.value)
        assert "Title cannot be empty" in error_message


@pytest.mark.asyncio
async def test_error_collector_integration_error_prioritization(temp_dir):
    """Integration test: error collector prioritizes errors by severity."""
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
        # Test error prioritization with multiple field validation errors
        with pytest.raises(Exception) as exc_info:
            await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Priority Test",
                    "description": "Task testing error prioritization",
                    "projectRoot": planning_root,
                    "status": "invalid_status",  # Invalid status
                    "priority": "ultra_high",  # Invalid priority
                },
            )

        # Verify multiple validation errors are reported
        error_message = str(exc_info.value)

        # Should contain both validation errors
        assert "status" in error_message
        assert "priority" in error_message


@pytest.mark.asyncio
async def test_mcp_tool_error_response_format(temp_dir):
    """Integration test: MCP tool error responses use enhanced format."""
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
        # Test enhanced error response format
        with pytest.raises(Exception) as exc_info:
            await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Error Format Test",
                    "description": "Task for testing error response format",
                    "projectRoot": planning_root,
                    "status": "invalid_status",
                    "priority": "high",
                },
            )

        # Verify enhanced error response contains structured information
        error_message = str(exc_info.value)

        # Check for enhanced error response elements
        assert "status" in error_message
        assert "invalid_status" in error_message
        # Should contain contextual information (object ID)
        assert "T-error-format-test" in error_message


@pytest.mark.asyncio
async def test_mcp_tool_error_response_context_preservation(temp_dir):
    """Integration test: MCP tool error responses preserve context information."""
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
        # Test context preservation in error responses
        with pytest.raises(Exception) as exc_info:
            await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Context Preservation Test",
                    "description": "Task for testing context preservation",
                    "projectRoot": planning_root,
                    "parent": "F-nonexistent-feature",  # Non-existent parent
                    "status": "open",
                    "priority": "high",
                },
            )

        # Verify context information is preserved in error response
        error_message = str(exc_info.value)

        # Should contain specific context about the failing validation
        assert "F-nonexistent-feature" in error_message
        assert "does not exist" in error_message
        # Context should indicate this is a parent validation error
        assert "parent" in error_message.lower()


@pytest.mark.asyncio
async def test_enhanced_validation_with_context_preservation(temp_dir):
    """Integration test: enhanced validation with context preservation."""
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
        # Test context preservation in validation errors
        with pytest.raises(Exception) as exc_info:
            await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Context Test",
                    "description": "Task testing context preservation",
                    "projectRoot": planning_root,
                    "parent": "F-nonexistent-feature",  # Non-existent parent
                    "status": "open",
                    "priority": "high",
                },
            )

        # Verify context information is preserved
        error_message = str(exc_info.value)
        assert "F-nonexistent-feature" in error_message
        assert "does not exist" in error_message


@pytest.mark.asyncio
async def test_real_world_error_scenario_complex_validation(temp_dir):
    """Integration test: complex real-world error scenarios with multiple validation layers."""
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
        # Step 1: Create valid hierarchy for testing
        project_result = await client.call_tool(
            "createObject",
            {
                "kind": "project",
                "title": "Complex Validation Test Project",
                "description": "Project for complex validation testing",
                "projectRoot": planning_root,
            },
        )
        project_id = project_result.data["id"]

        epic_result = await client.call_tool(
            "createObject",
            {
                "kind": "epic",
                "title": "Complex Validation Test Epic",
                "description": "Epic for complex validation testing",
                "projectRoot": planning_root,
                "parent": project_id,
            },
        )
        epic_id = epic_result.data["id"]

        feature_result = await client.call_tool(
            "createObject",
            {
                "kind": "feature",
                "title": "Complex Validation Test Feature",
                "description": "Feature for complex validation testing",
                "projectRoot": planning_root,
                "parent": epic_id,
            },
        )
        feature_id = feature_result.data["id"]

        # Step 2: Create tasks for dependency testing
        task_a_result = await client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Task A",
                "description": "First task for dependency testing",
                "projectRoot": planning_root,
                "parent": feature_id,
                "status": "open",
                "priority": "high",
            },
        )
        task_a_id = task_a_result.data["id"]

        task_b_result = await client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Task B",
                "description": "Second task for dependency testing",
                "projectRoot": planning_root,
                "parent": feature_id,
                "prerequisites": [task_a_id],
                "status": "open",
                "priority": "normal",
            },
        )
        task_b_id = task_b_result.data["id"]

        # Step 3: Test field validation failures first
        with pytest.raises(Exception) as exc_info:
            await client.call_tool(
                "updateObject",
                {
                    "kind": "task",
                    "id": task_a_id,
                    "projectRoot": planning_root,
                    "yamlPatch": {
                        "status": "invalid_status",  # Invalid status enum
                        "priority": "super_high",  # Invalid priority enum
                    },
                },
            )

        # Verify multiple validation errors are reported
        error_message = str(exc_info.value)

        # Should contain status validation error
        assert "status" in error_message
        # Should contain priority validation error
        assert "priority" in error_message

        # Step 4: Test circular dependency validation separately
        with pytest.raises(Exception) as exc_info:
            await client.call_tool(
                "updateObject",
                {
                    "kind": "task",
                    "id": task_a_id,
                    "projectRoot": planning_root,
                    "yamlPatch": {
                        "prerequisites": [task_b_id],  # Creates circular dependency
                    },
                },
            )

        # Verify circular dependency error
        error_message = str(exc_info.value)
        assert "circular" in error_message.lower() or "cycle" in error_message.lower()

        # Step 5: Verify original task remains unchanged (atomic operation)
        task_a_retrieved = await client.call_tool(
            "getObject",
            {
                "kind": "task",
                "id": task_a_id,
                "projectRoot": planning_root,
            },
        )

        # Task should remain in original state
        assert task_a_retrieved.data["yaml"]["prerequisites"] == []
        assert task_a_retrieved.data["yaml"]["status"] == "open"
        assert task_a_retrieved.data["yaml"]["priority"] == "high"


@pytest.mark.asyncio
async def test_real_world_error_scenario_concurrent_validation(temp_dir):
    """Integration test: concurrent validation failures in mixed environments."""
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
        # Step 1: Create hierarchy for hierarchy tasks
        project_result = await client.call_tool(
            "createObject",
            {
                "kind": "project",
                "title": "Concurrent Validation Test Project",
                "projectRoot": planning_root,
            },
        )
        project_id = project_result.data["id"]

        epic_result = await client.call_tool(
            "createObject",
            {
                "kind": "epic",
                "title": "Concurrent Validation Test Epic",
                "projectRoot": planning_root,
                "parent": project_id,
            },
        )
        epic_id = epic_result.data["id"]

        feature_result = await client.call_tool(
            "createObject",
            {
                "kind": "feature",
                "title": "Concurrent Validation Test Feature",
                "projectRoot": planning_root,
                "parent": epic_id,
            },
        )
        feature_id = feature_result.data["id"]

        # Step 2: Test standalone task with status validation failure
        with pytest.raises(Exception) as exc_info:
            await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Standalone Task Invalid",
                    "description": "Standalone task with validation failures",
                    "projectRoot": planning_root,
                    "status": "invalid_status",  # Invalid status
                    "priority": "high",
                },
            )

        # Verify status validation error
        error_message = str(exc_info.value)
        assert "status" in error_message

        # Step 2b: Test task with valid parent (should create in hierarchy)
        valid_task_result = await client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Valid Hierarchy Task",
                "description": "Valid task with parent",
                "projectRoot": planning_root,
                "parent": feature_id,  # Valid parent
                "status": "open",
                "priority": "high",
            },
        )

        # Verify task was created successfully
        assert valid_task_result.data is not None
        assert valid_task_result.data["status"] == "open"

        # Step 3: Test hierarchy task with validation failures
        with pytest.raises(Exception) as exc_info:
            await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Hierarchy Task Invalid",
                    "description": "Hierarchy task with validation failures",
                    "projectRoot": planning_root,
                    "parent": "F-nonexistent-feature",  # Non-existent parent
                    "status": "done",  # Invalid initial status
                    "priority": "high",
                },
            )

        # Verify hierarchy validation errors
        error_message = str(exc_info.value)
        assert "F-nonexistent-feature" in error_message
        assert "does not exist" in error_message

        # Step 4: Verify that invalid tasks were not created, but valid ones were
        planning_path = temp_dir / "planning"
        if planning_path.exists():
            standalone_tasks = list(planning_path.glob("tasks-open/T-*.md"))
            hierarchy_tasks = list(
                planning_path.glob("projects/*/epics/*/features/*/tasks-open/T-*.md")
            )
            # No invalid standalone tasks should be created
            assert len(standalone_tasks) == 0
            # One valid hierarchy task should be created
            assert len(hierarchy_tasks) == 1


@pytest.mark.asyncio
async def test_error_message_consistency_across_validation_paths(temp_dir):
    """Integration test: error message consistency across different validation paths."""
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
        # Test 1: Consistent error messages for missing required fields
        with pytest.raises(Exception) as exc_info:
            await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "description": "Task with missing title",
                    "projectRoot": planning_root,
                    "status": "open",
                    "priority": "high",
                },
            )

        # Verify consistent error message format for missing fields
        error_message = str(exc_info.value)
        assert "title" in error_message
        # Should have consistent format for missing required fields

        # Test 2: Consistent error messages for invalid enum values
        with pytest.raises(Exception) as exc_info:
            await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Invalid Status Test",
                    "description": "Task with invalid status",
                    "projectRoot": planning_root,
                    "status": "invalid_status",
                    "priority": "high",
                },
            )

        # Verify consistent error message format for invalid enums
        error_message = str(exc_info.value)
        assert "status" in error_message
        assert "invalid_status" in error_message

        # Test 3: Consistent error messages for mixed validation types
        with pytest.raises(Exception) as exc_info:
            await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Mixed Validation Test",
                    "description": "Task with mixed validation errors",
                    "projectRoot": planning_root,
                    "status": "invalid_status",
                    "priority": "ultra_high",
                },
            )

        # Verify consistent error message format for mixed validation errors
        error_message = str(exc_info.value)
        assert "status" in error_message
        assert "priority" in error_message

        # Test 4: Consistent error messages for relationship violations
        with pytest.raises(Exception) as exc_info:
            await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Relationship Test",
                    "description": "Task with relationship violation",
                    "projectRoot": planning_root,
                    "parent": "F-nonexistent-feature",
                    "status": "open",
                    "priority": "high",
                },
            )

        # Verify consistent error message format for relationship violations
        error_message = str(exc_info.value)
        assert "F-nonexistent-feature" in error_message
        assert "does not exist" in error_message


@pytest.mark.asyncio
async def test_error_workflow_rollback_and_recovery(temp_dir):
    """Integration test: error workflow rollback and recovery mechanisms."""
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
        # Step 1: Create hierarchy for testing
        project_result = await client.call_tool(
            "createObject",
            {
                "kind": "project",
                "title": "Rollback Test Project",
                "projectRoot": planning_root,
            },
        )
        project_id = project_result.data["id"]

        epic_result = await client.call_tool(
            "createObject",
            {
                "kind": "epic",
                "title": "Rollback Test Epic",
                "projectRoot": planning_root,
                "parent": project_id,
            },
        )
        epic_id = epic_result.data["id"]

        feature_result = await client.call_tool(
            "createObject",
            {
                "kind": "feature",
                "title": "Rollback Test Feature",
                "projectRoot": planning_root,
                "parent": epic_id,
            },
        )
        feature_id = feature_result.data["id"]

        # Step 2: Create valid task
        task_result = await client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Rollback Test Task",
                "description": "Task for rollback testing",
                "projectRoot": planning_root,
                "parent": feature_id,
                "status": "open",
                "priority": "high",
            },
        )
        task_id = task_result.data["id"]

        # Step 3: Record original task state
        original_task = await client.call_tool(
            "getObject",
            {
                "kind": "task",
                "id": task_id,
                "projectRoot": planning_root,
            },
        )
        original_status = original_task.data["yaml"]["status"]
        original_priority = original_task.data["yaml"]["priority"]
        original_title = original_task.data["yaml"]["title"]

        # Step 4: Attempt invalid update that should trigger rollback
        with pytest.raises(Exception) as exc_info:
            await client.call_tool(
                "updateObject",
                {
                    "kind": "task",
                    "id": task_id,
                    "projectRoot": planning_root,
                    "yamlPatch": {
                        "title": "Updated Title",
                        "status": "invalid_status",  # Invalid status should cause rollback
                        "priority": "normal",
                    },
                },
            )

        # Verify validation error occurred
        error_message = str(exc_info.value)
        assert "status" in error_message

        # Step 5: Verify task state was rolled back to original values
        rolled_back_task = await client.call_tool(
            "getObject",
            {
                "kind": "task",
                "id": task_id,
                "projectRoot": planning_root,
            },
        )

        # All fields should be unchanged due to rollback
        assert rolled_back_task.data["yaml"]["status"] == original_status
        assert rolled_back_task.data["yaml"]["priority"] == original_priority
        assert rolled_back_task.data["yaml"]["title"] == original_title

        # Step 6: Verify subsequent valid update works correctly
        valid_update_result = await client.call_tool(
            "updateObject",
            {
                "kind": "task",
                "id": task_id,
                "projectRoot": planning_root,
                "yamlPatch": {
                    "title": "Successfully Updated Title",
                    "priority": "normal",
                },
            },
        )

        # Verify valid update was applied
        assert valid_update_result.data is not None
        updated_task = await client.call_tool(
            "getObject",
            {
                "kind": "task",
                "id": task_id,
                "projectRoot": planning_root,
            },
        )
        assert updated_task.data["yaml"]["title"] == "Successfully Updated Title"
        assert updated_task.data["yaml"]["priority"] == "normal"


@pytest.mark.asyncio
async def test_error_workflow_performance_under_load(temp_dir):
    """Integration test: error workflow performance under multiple validation failures."""
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
        # Test performance with multiple rapid validation failures
        error_count = 0

        # Attempt to create multiple invalid tasks rapidly
        for i in range(10):
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "createObject",
                    {
                        "kind": "task",
                        "title": f"Performance Test Task {i}",
                        "description": f"Task {i} for performance testing",
                        "projectRoot": planning_root,
                        "status": "invalid_status",  # Invalid status
                        "priority": "ultra_high",  # Invalid priority
                    },
                )

            # Verify each error is properly handled
            error_message = str(exc_info.value)
            assert "status" in error_message
            assert "priority" in error_message
            error_count += 1

        # Verify all validation failures were handled
        assert error_count == 10

        # Verify no files were created despite multiple attempts
        planning_path = temp_dir / "planning"
        if planning_path.exists():
            task_files = list(planning_path.glob("tasks-open/T-*.md"))
            assert len(task_files) == 0

        # Test that valid task creation still works after error load
        valid_task_result = await client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Valid Task After Load",
                "description": "Valid task created after error load testing",
                "projectRoot": planning_root,
                "status": "open",
                "priority": "high",
            },
        )

        # Verify valid task was created successfully
        assert valid_task_result.data is not None
        assert valid_task_result.data["status"] == "open"

        # Verify file was created
        task_id = valid_task_result.data["id"]
        task_path = temp_dir / "planning" / "tasks-open" / f"{task_id}.md"
        assert task_path.exists()
