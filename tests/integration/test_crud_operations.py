"""CRUD operations tests.

Tests comprehensive CRUD lifecycle including object creation, retrieval,
updates, hierarchy management, and YAML file persistence.
"""

import pytest
from fastmcp import Client

from .test_helpers import (
    create_test_server,
    extract_raw_id,
)


@pytest.mark.asyncio
async def test_crud_epic_feature_tasks_workflow_with_yaml_verification(temp_dir):
    """Integration test: create epic → feature → tasks; list backlog; update statuses."""
    # Create server instance
    server, planning_root = create_test_server(temp_dir)

    async with Client(server) as client:
        # Step 1: Create project as foundation for hierarchy
        project_result = await client.call_tool(
            "createObject",
            {
                "kind": "project",
                "title": "Integration Test Project",
                "description": "Test project for integration workflow",
                "projectRoot": planning_root,
            },
        )
        project_id = project_result.data["id"]
        assert project_id.startswith("P-")

        # Step 2: Create epic under project
        epic_result = await client.call_tool(
            "createObject",
            {
                "kind": "epic",
                "title": "Authentication Epic",
                "description": "Epic for authentication functionality",
                "projectRoot": planning_root,
                "parent": project_id,
            },
        )
        epic_id = epic_result.data["id"]
        assert epic_id.startswith("E-")

        # Step 3: Create feature under epic
        feature_result = await client.call_tool(
            "createObject",
            {
                "kind": "feature",
                "title": "User Login Feature",
                "description": "Feature for user login functionality",
                "projectRoot": planning_root,
                "parent": epic_id,
            },
        )
        feature_id = feature_result.data["id"]
        assert feature_id.startswith("F-")

        # Step 4: Create multiple tasks under feature with different priorities
        task1_result = await client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Implement JWT authentication",
                "description": "Task to implement JWT token authentication",
                "projectRoot": planning_root,
                "parent": feature_id,
                "priority": "high",
            },
        )
        task1_id = task1_result.data["id"]
        assert task1_id.startswith("T-")

        task2_result = await client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Add password validation",
                "description": "Task to add password validation rules",
                "projectRoot": planning_root,
                "parent": feature_id,
                "priority": "normal",
            },
        )
        task2_id = task2_result.data["id"]
        assert task2_id.startswith("T-")

        task3_result = await client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Create login form UI",
                "description": "Task to create user interface for login",
                "projectRoot": planning_root,
                "parent": feature_id,
                "priority": "low",
            },
        )
        task3_id = task3_result.data["id"]
        assert task3_id.startswith("T-")

        # Step 5: List backlog to verify all tasks are found
        backlog_result = await client.call_tool(
            "listBacklog",
            {
                "projectRoot": planning_root,
                "scope": feature_id,
            },
        )
        assert backlog_result.structured_content is not None
        tasks = backlog_result.structured_content["tasks"]
        assert len(tasks) == 3

        # Verify tasks are sorted by priority (high → normal → low)
        task_priorities = [task["priority"] for task in tasks]
        assert task_priorities == ["high", "normal", "low"]

        # Step 6: Test status filtering in listBacklog
        # All tasks should be "open" initially
        open_tasks_result = await client.call_tool(
            "listBacklog",
            {
                "projectRoot": planning_root,
                "scope": feature_id,
                "status": "open",
            },
        )
        assert open_tasks_result.structured_content is not None
        assert len(open_tasks_result.structured_content["tasks"]) == 3

        # No tasks should be "done" initially
        done_tasks_result = await client.call_tool(
            "listBacklog",
            {
                "projectRoot": planning_root,
                "scope": feature_id,
                "status": "done",
            },
        )
        assert done_tasks_result.structured_content is not None
        assert len(done_tasks_result.structured_content["tasks"]) == 0

        # Step 7: Update task statuses to test status transitions
        # Update task1 to in-progress
        await client.call_tool(
            "updateObject",
            {
                "kind": "task",
                "id": task1_id,
                "projectRoot": planning_root,
                "yamlPatch": {"status": "in-progress"},
            },
        )

        # Update task2 to review
        await client.call_tool(
            "updateObject",
            {
                "kind": "task",
                "id": task2_id,
                "projectRoot": planning_root,
                "yamlPatch": {"status": "in-progress"},
            },
        )
        await client.call_tool(
            "updateObject",
            {
                "kind": "task",
                "id": task2_id,
                "projectRoot": planning_root,
                "yamlPatch": {"status": "review"},
            },
        )

        # Note: Validation testing for setting task status to 'done' is covered in
        # tests/test_server.py::TestUpdateObject::test_update_task_cannot_set_done_status
        # We'll skip that validation test here to avoid duplication

        # Step 8: Verify status updates via listBacklog
        # Test in-progress filter
        in_progress_result = await client.call_tool(
            "listBacklog",
            {
                "projectRoot": planning_root,
                "scope": feature_id,
                "status": "in-progress",
            },
        )
        assert in_progress_result.structured_content is not None
        assert len(in_progress_result.structured_content["tasks"]) == 1
        assert in_progress_result.structured_content["tasks"][0]["id"] == task1_id

        # Test review filter
        review_result = await client.call_tool(
            "listBacklog",
            {
                "projectRoot": planning_root,
                "scope": feature_id,
                "status": "review",
            },
        )
        assert review_result.structured_content is not None
        assert len(review_result.structured_content["tasks"]) == 1
        assert review_result.structured_content["tasks"][0]["id"] == task2_id

        # Test done filter - no tasks should be done since we can't use updateObject
        done_result = await client.call_tool(
            "listBacklog",
            {
                "projectRoot": planning_root,
                "scope": feature_id,
                "status": "done",
            },
        )
        assert done_result.structured_content is not None
        assert len(done_result.structured_content["tasks"]) == 0

        # Step 9: Verify YAML files exist on disk with correct content
        planning_path = temp_dir / "planning"

        # Extract raw IDs (without prefixes) for path construction
        raw_project_id = extract_raw_id(project_id)
        raw_epic_id = extract_raw_id(epic_id)
        raw_feature_id = extract_raw_id(feature_id)

        # Verify project file exists and has correct content
        project_file = planning_path / "projects" / f"P-{raw_project_id}" / "project.md"
        assert project_file.exists()
        project_content = project_file.read_text()
        assert f"id: {project_id}" in project_content
        assert "title: Integration Test Project" in project_content
        assert "kind: project" in project_content

        # Verify epic file exists and has correct content
        epic_file = (
            planning_path
            / "projects"
            / f"P-{raw_project_id}"
            / "epics"
            / f"E-{raw_epic_id}"
            / "epic.md"
        )
        assert epic_file.exists()
        epic_content = epic_file.read_text()
        assert f"id: {epic_id}" in epic_content
        assert "title: Authentication Epic" in epic_content
        assert f"parent: {project_id}" in epic_content
        assert "kind: epic" in epic_content

        # Verify feature file exists and has correct content
        feature_file = (
            planning_path
            / "projects"
            / f"P-{raw_project_id}"
            / "epics"
            / f"E-{raw_epic_id}"
            / "features"
            / f"F-{raw_feature_id}"
            / "feature.md"
        )
        assert feature_file.exists()
        feature_content = feature_file.read_text()
        assert f"id: {feature_id}" in feature_content
        assert "title: User Login Feature" in feature_content
        assert f"parent: {epic_id}" in feature_content
        assert "kind: feature" in feature_content

        # Verify task files exist and have correct content and status
        task_base_path = (
            planning_path
            / "projects"
            / f"P-{raw_project_id}"
            / "epics"
            / f"E-{raw_epic_id}"
            / "features"
            / f"F-{raw_feature_id}"
        )

        # Task1 should be in tasks-open with in-progress status
        task1_file = task_base_path / "tasks-open" / f"{task1_id}.md"
        assert task1_file.exists()
        task1_content = task1_file.read_text()
        assert f"id: {task1_id}" in task1_content
        assert "title: Implement JWT authentication" in task1_content
        assert f"parent: {feature_id}" in task1_content
        assert "status: in-progress" in task1_content
        assert "priority: high" in task1_content
        assert "kind: task" in task1_content

        # Task2 should be in tasks-open with review status
        task2_file = task_base_path / "tasks-open" / f"{task2_id}.md"
        assert task2_file.exists()
        task2_content = task2_file.read_text()
        assert f"id: {task2_id}" in task2_content
        assert "title: Add password validation" in task2_content
        assert f"parent: {feature_id}" in task2_content
        assert "status: review" in task2_content
        assert "priority: normal" in task2_content
        assert "kind: task" in task2_content

        # Task3 should be in tasks-open with open status (we didn't complete it)
        task3_file = task_base_path / "tasks-open" / f"{task3_id}.md"
        assert task3_file.exists()
        task3_content = task3_file.read_text()
        assert f"id: {task3_id}" in task3_content
        assert "title: Create login form UI" in task3_content
        assert f"parent: {feature_id}" in task3_content
        assert "status: open" in task3_content
        assert "priority: low" in task3_content
        assert "kind: task" in task3_content

        # Step 10: Test priority filtering in listBacklog
        high_priority_result = await client.call_tool(
            "listBacklog",
            {
                "projectRoot": planning_root,
                "scope": feature_id,
                "priority": "high",
            },
        )
        assert high_priority_result.structured_content is not None
        assert len(high_priority_result.structured_content["tasks"]) == 1
        assert high_priority_result.structured_content["tasks"][0]["id"] == task1_id

        # Step 11: Test broader scope filters (epic and project level)
        # List backlog at epic level should include all tasks
        epic_backlog_result = await client.call_tool(
            "listBacklog",
            {
                "projectRoot": planning_root,
                "scope": epic_id,
            },
        )
        assert epic_backlog_result.structured_content is not None
        assert len(epic_backlog_result.structured_content["tasks"]) == 3

        # List backlog at project level should include all tasks
        project_backlog_result = await client.call_tool(
            "listBacklog",
            {
                "projectRoot": planning_root,
                "scope": project_id,
            },
        )
        assert project_backlog_result.structured_content is not None
        assert len(project_backlog_result.structured_content["tasks"]) == 3

        # Step 12: Verify object retrieval works correctly
        # Test getObject for each created object
        retrieved_project = await client.call_tool(
            "getObject",
            {
                "kind": "project",
                "id": project_id,
                "projectRoot": planning_root,
            },
        )
        assert retrieved_project.data["yaml"]["title"] == "Integration Test Project"

        retrieved_epic = await client.call_tool(
            "getObject",
            {
                "kind": "epic",
                "id": epic_id,
                "projectRoot": planning_root,
            },
        )
        assert retrieved_epic.data["yaml"]["title"] == "Authentication Epic"

        retrieved_feature = await client.call_tool(
            "getObject",
            {
                "kind": "feature",
                "id": feature_id,
                "projectRoot": planning_root,
            },
        )
        assert retrieved_feature.data["yaml"]["title"] == "User Login Feature"

        retrieved_task1 = await client.call_tool(
            "getObject",
            {
                "kind": "task",
                "id": task1_id,
                "projectRoot": planning_root,
            },
        )
        assert retrieved_task1.data["yaml"]["title"] == "Implement JWT authentication"
        assert retrieved_task1.data["yaml"]["status"] == "in-progress"
