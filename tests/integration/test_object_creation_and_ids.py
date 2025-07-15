"""Object creation and ID management tests.

Tests object creation mechanics, ID generation, collision handling,
and file system operations for creating objects.
"""

import pytest
from fastmcp import Client

from .test_helpers import build_task_path, create_test_hierarchy, create_test_server


@pytest.mark.asyncio
async def test_create_duplicate_title_tasks_generates_unique_ids(temp_dir):
    """Test creating two tasks with identical titles generates unique IDs and correct paths."""
    # Create server instance
    server, planning_root = create_test_server(temp_dir)

    async with Client(server) as client:
        # First, create the project hierarchy: project → epic → feature
        hierarchy = await create_test_hierarchy(client, planning_root, "Test Project")
        project_id = hierarchy["project_id"]
        epic_id = hierarchy["epic_id"]
        feature_id = hierarchy["feature_id"]

        # Now create two tasks with identical titles under the same feature
        task_title = "Implement Authentication"

        # Create first task
        task1_result = await client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": task_title,
                "projectRoot": planning_root,
                "parent": feature_id,
            },
        )

        # Create second task with same title
        task2_result = await client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": task_title,
                "projectRoot": planning_root,
                "parent": feature_id,
            },
        )

        # Verify both tasks were created successfully
        assert task1_result.data is not None
        assert task2_result.data is not None

        # Verify both tasks have the same title
        assert task1_result.data["title"] == task_title
        assert task2_result.data["title"] == task_title

        # Verify tasks have unique IDs (collision detection working)
        task1_id = task1_result.data["id"]
        task2_id = task2_result.data["id"]
        assert task1_id != task2_id

        # Verify first task gets base slug, second gets suffix (with T- prefix)
        assert task1_id == "T-implement-authentication"
        assert task2_id == "T-implement-authentication-1"

        # Verify both tasks have correct file paths
        task1_path = task1_result.data["file_path"]
        task2_path = task2_result.data["file_path"]
        assert task1_path != task2_path

        # Verify paths follow expected structure
        expected_task1_path = build_task_path(temp_dir, project_id, epic_id, feature_id, task1_id)
        expected_task2_path = build_task_path(temp_dir, project_id, epic_id, feature_id, task2_id)

        assert task1_path == str(expected_task1_path)
        assert task2_path == str(expected_task2_path)

        # Verify both task files actually exist on filesystem
        assert expected_task1_path.exists()
        assert expected_task2_path.exists()

        # Verify files have correct content structure (basic YAML front-matter check)
        task1_content = expected_task1_path.read_text()
        task2_content = expected_task2_path.read_text()

        # Both should contain YAML front-matter with correct IDs and titles
        assert f"id: {task1_id}" in task1_content
        assert f"title: {task_title}" in task1_content
        assert f"id: {task2_id}" in task2_content
        assert f"title: {task_title}" in task2_content
