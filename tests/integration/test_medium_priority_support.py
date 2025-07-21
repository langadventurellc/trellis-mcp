"""Integration tests for medium priority support in createObject tool.

Tests that the createObject tool properly handles "medium" priority values,
converts them to "normal" internally, and stores "normal" in YAML front-matter.
"""

import pytest
from fastmcp import Client

from .test_helpers import create_test_server


@pytest.mark.asyncio
async def test_create_object_with_medium_priority(temp_dir):
    """Test createObject converts 'medium' priority to 'normal' in storage."""
    # Create server instance
    server, planning_root = create_test_server(temp_dir)

    async with Client(server) as client:
        # Test creating a project with medium priority
        result = await client.call_tool(
            "createObject",
            {
                "kind": "project",
                "title": "Test Project with Medium Priority",
                "projectRoot": planning_root,
                "priority": "medium",
            },
        )

        # Verify object was created successfully
        assert result.data is not None
        assert result.data["title"] == "Test Project with Medium Priority"

        # Get the file path and verify file exists
        file_path = result.data["file_path"]
        assert file_path is not None

        # Read the file content and verify priority is stored as "normal"
        with open(file_path, "r") as f:
            content = f.read()

        # YAML front-matter should contain "priority: normal" (not "medium")
        assert "priority: normal" in content
        assert "priority: medium" not in content

        # Verify we can retrieve the object and it shows normal priority
        object_id = result.data["id"]
        get_result = await client.call_tool(
            "getObject",
            {
                "id": object_id,
                "projectRoot": planning_root,
            },
        )

        assert get_result.data is not None
        assert get_result.data["yaml"]["priority"] == "normal"


@pytest.mark.asyncio
async def test_create_object_medium_priority_case_variations(temp_dir):
    """Test createObject handles case variations of 'medium' priority."""
    server, planning_root = create_test_server(temp_dir)

    async with Client(server) as client:
        # Test different case variations of "medium"
        test_cases = ["medium", "Medium", "MEDIUM", "MeDiUm"]

        for i, medium_variant in enumerate(test_cases):
            result = await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": f"Test Project {i + 1}",
                    "projectRoot": planning_root,
                    "priority": medium_variant,
                },
            )

            # Verify object was created successfully
            assert result.data is not None

            # Read the file content and verify priority is stored as "normal"
            file_path = result.data["file_path"]
            with open(file_path, "r") as f:
                content = f.read()

            # All variations should result in "priority: normal" storage
            assert "priority: normal" in content
            assert f"priority: {medium_variant}" not in content


@pytest.mark.asyncio
async def test_create_object_standard_priorities_unchanged(temp_dir):
    """Test createObject still handles standard priorities correctly."""
    server, planning_root = create_test_server(temp_dir)

    async with Client(server) as client:
        # Test standard priority values are unchanged
        standard_priorities = ["high", "normal", "low"]

        for priority in standard_priorities:
            result = await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": f"Test Project {priority.title()}",
                    "projectRoot": planning_root,
                    "priority": priority,
                },
            )

            # Verify object was created successfully
            assert result.data is not None

            # Read the file content and verify priority is stored correctly
            file_path = result.data["file_path"]
            with open(file_path, "r") as f:
                content = f.read()

            # Standard priorities should be stored as-is
            assert f"priority: {priority}" in content


@pytest.mark.asyncio
async def test_create_object_invalid_priority_error_includes_medium(temp_dir):
    """Test createObject error message for invalid priority includes 'medium'."""
    server, planning_root = create_test_server(temp_dir)

    async with Client(server) as client:
        # Test with an invalid priority value
        with pytest.raises(Exception) as exc_info:
            await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Test Project",
                    "projectRoot": planning_root,
                    "priority": "invalid_priority",
                },
            )

        # Error message should include "medium" as a valid option
        error_message = str(exc_info.value)
        assert "medium" in error_message
        assert "high" in error_message
        assert "normal" in error_message
        assert "low" in error_message


@pytest.mark.asyncio
async def test_create_task_with_medium_priority(temp_dir):
    """Test createObject handles medium priority for tasks specifically."""
    server, planning_root = create_test_server(temp_dir)

    async with Client(server) as client:
        # First create a project
        project_result = await client.call_tool(
            "createObject",
            {
                "kind": "project",
                "title": "Test Project",
                "projectRoot": planning_root,
            },
        )
        project_id = project_result.data["id"]

        # Create an epic under the project
        epic_result = await client.call_tool(
            "createObject",
            {
                "kind": "epic",
                "title": "Test Epic",
                "projectRoot": planning_root,
                "parent": project_id,
            },
        )
        epic_id = epic_result.data["id"]

        # Create a feature under the epic
        feature_result = await client.call_tool(
            "createObject",
            {
                "kind": "feature",
                "title": "Test Feature",
                "projectRoot": planning_root,
                "parent": epic_id,
            },
        )
        feature_id = feature_result.data["id"]

        # Create a task with medium priority
        task_result = await client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Test Task with Medium Priority",
                "projectRoot": planning_root,
                "parent": feature_id,
                "priority": "medium",
            },
        )

        # Verify task was created successfully
        assert task_result.data is not None
        assert task_result.data["title"] == "Test Task with Medium Priority"

        # Read the file content and verify priority is stored as "normal"
        file_path = task_result.data["file_path"]
        with open(file_path, "r") as f:
            content = f.read()

        # Task should have "priority: normal" (not "medium")
        assert "priority: normal" in content
        assert "priority: medium" not in content
