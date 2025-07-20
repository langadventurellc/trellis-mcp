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
                "id": project_id,
                "projectRoot": planning_root,
            },
        )
        assert retrieved_project.data["yaml"]["title"] == "Integration Test Project"

        retrieved_epic = await client.call_tool(
            "getObject",
            {
                "id": epic_id,
                "projectRoot": planning_root,
            },
        )
        assert retrieved_epic.data["yaml"]["title"] == "Authentication Epic"

        retrieved_feature = await client.call_tool(
            "getObject",
            {
                "id": feature_id,
                "projectRoot": planning_root,
            },
        )
        assert retrieved_feature.data["yaml"]["title"] == "User Login Feature"

        retrieved_task1 = await client.call_tool(
            "getObject",
            {
                "id": task1_id,
                "projectRoot": planning_root,
            },
        )
        assert retrieved_task1.data["yaml"]["title"] == "Implement JWT authentication"
        assert retrieved_task1.data["yaml"]["status"] == "in-progress"


@pytest.mark.asyncio
async def test_parent_deletion_cascade_integration(temp_dir):
    """Integration test: create nested Project→Epic→Feature→Task tree, delete Epic,
    verify no orphan files/folders."""
    # Create server instance
    server, planning_root = create_test_server(temp_dir)

    async with Client(server) as client:
        # Step 1: Create project as foundation
        project_result = await client.call_tool(
            "createObject",
            {
                "kind": "project",
                "title": "Test Project for Deletion",
                "description": "Project to test cascade deletion",
                "projectRoot": planning_root,
            },
        )
        project_id = project_result.data["id"]

        # Step 2: Create epic under project
        epic_result = await client.call_tool(
            "createObject",
            {
                "kind": "epic",
                "title": "Test Epic for Deletion",
                "description": "Epic to be deleted with cascade",
                "projectRoot": planning_root,
                "parent": project_id,
            },
        )
        epic_id = epic_result.data["id"]

        # Step 3: Create feature under epic
        feature_result = await client.call_tool(
            "createObject",
            {
                "kind": "feature",
                "title": "Test Feature for Deletion",
                "description": "Feature to be deleted with cascade",
                "projectRoot": planning_root,
                "parent": epic_id,
            },
        )
        feature_id = feature_result.data["id"]

        # Step 4: Create multiple tasks under feature with different statuses
        # Task 1 - will remain as "open"
        task1_result = await client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Open Task",
                "description": "Task that will remain open",
                "projectRoot": planning_root,
                "parent": feature_id,
                "priority": "high",
            },
        )
        task1_id = task1_result.data["id"]

        # Task 2 - will be set to "done" and moved to tasks-done
        task2_result = await client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Done Task",
                "description": "Task that will be completed",
                "projectRoot": planning_root,
                "parent": feature_id,
                "priority": "normal",
            },
        )
        task2_id = task2_result.data["id"]

        # Step 5: Complete task2 using completeTask to move it to tasks-done
        # First transition to in-progress
        await client.call_tool(
            "updateObject",
            {
                "kind": "task",
                "id": task2_id,
                "projectRoot": planning_root,
                "yamlPatch": {"status": "in-progress"},
            },
        )

        # Then complete the task
        await client.call_tool(
            "completeTask",
            {
                "taskId": task2_id,
                "projectRoot": planning_root,
            },
        )

        # Step 6: Verify the hierarchy is properly created in filesystem
        planning_path = temp_dir / "planning"
        raw_project_id = extract_raw_id(project_id)
        raw_epic_id = extract_raw_id(epic_id)
        raw_feature_id = extract_raw_id(feature_id)

        # Verify all files exist before deletion
        project_file = planning_path / "projects" / f"P-{raw_project_id}" / "project.md"
        epic_file = (
            planning_path
            / "projects"
            / f"P-{raw_project_id}"
            / "epics"
            / f"E-{raw_epic_id}"
            / "epic.md"
        )
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
        task1_file = (
            planning_path
            / "projects"
            / f"P-{raw_project_id}"
            / "epics"
            / f"E-{raw_epic_id}"
            / "features"
            / f"F-{raw_feature_id}"
            / "tasks-open"
            / f"{task1_id}.md"
        )

        assert project_file.exists()
        assert epic_file.exists()
        assert feature_file.exists()
        assert task1_file.exists()

        # Check what files are in tasks-done directory
        tasks_done_dir = (
            planning_path
            / "projects"
            / f"P-{raw_project_id}"
            / "epics"
            / f"E-{raw_epic_id}"
            / "features"
            / f"F-{raw_feature_id}"
            / "tasks-done"
        )
        assert tasks_done_dir.exists(), f"tasks-done directory does not exist: {tasks_done_dir}"

        # List all files in tasks-done
        done_files = list(tasks_done_dir.glob("*.md"))
        assert (
            len(done_files) == 1
        ), f"Expected 1 file in tasks-done, found {len(done_files)}: {done_files}"

        # Use the actual file found instead of assuming the name
        task2_file = done_files[0]

        # Verify directory structure exists
        epic_dir = planning_path / "projects" / f"P-{raw_project_id}" / "epics" / f"E-{raw_epic_id}"
        feature_dir = epic_dir / "features" / f"F-{raw_feature_id}"
        tasks_open_dir = feature_dir / "tasks-open"
        tasks_done_dir = feature_dir / "tasks-done"

        assert epic_dir.exists() and epic_dir.is_dir()
        assert feature_dir.exists() and feature_dir.is_dir()
        assert tasks_open_dir.exists() and tasks_open_dir.is_dir()
        assert tasks_done_dir.exists() and tasks_done_dir.is_dir()

        # Step 7: Use updateObject directly via client instead of CLI to avoid event loop issues
        delete_result = await client.call_tool(
            "updateObject",
            {
                "kind": "epic",
                "id": epic_id,
                "projectRoot": planning_root,
                "yamlPatch": {"status": "deleted"},
            },
        )

        # Verify the deletion succeeded
        assert delete_result.data["changes"]["status"] == "deleted"
        cascade_deleted = delete_result.data["changes"].get("cascade_deleted", [])
        assert len(cascade_deleted) > 0, "Should have cascade deleted some files"

        # Step 8: Verify complete cascade deletion - no orphan files/folders remain
        # Epic file should be deleted
        assert not epic_file.exists()

        # Feature file should be deleted
        assert not feature_file.exists()

        # All task files should be deleted
        assert not task1_file.exists()
        assert not task2_file.exists()

        # Verify directories are empty (files are gone but empty dirs may remain)
        # This is expected behavior - recursive_delete removes files but may leave empty directories

        # Check that no .md files remain in the epic directory tree
        epic_md_files = list(epic_dir.rglob("*.md")) if epic_dir.exists() else []
        assert len(epic_md_files) == 0, f"Found orphan .md files: {epic_md_files}"

        # Step 9: Verify parent project remains intact
        assert project_file.exists()
        project_content = project_file.read_text()
        assert f"id: {project_id}" in project_content
        assert "title: Test Project for Deletion" in project_content

        # Step 10: Verify no orphan .md files exist anywhere in the planning structure
        all_md_files = list(planning_path.rglob("*.md"))

        # Only the project.md file should remain
        assert len(all_md_files) == 1
        assert all_md_files[0] == project_file

        # Step 11: Verify we can still interact with the remaining project
        retrieved_project = await client.call_tool(
            "getObject",
            {
                "id": project_id,
                "projectRoot": planning_root,
            },
        )
        assert retrieved_project.data["yaml"]["title"] == "Test Project for Deletion"

        # Step 12: Verify we can still list backlog (should be empty now)
        backlog_result = await client.call_tool(
            "listBacklog",
            {
                "projectRoot": planning_root,
                "scope": project_id,
            },
        )
        assert backlog_result.structured_content is not None
        assert len(backlog_result.structured_content["tasks"]) == 0

        # Step 13: Verify the cascade deletion worked properly
        # All expected files should be in the cascade_deleted list
        expected_files = [
            str(epic_file),
            str(feature_file),
            str(task1_file),
            str(task2_file),
        ]

        for expected_file in expected_files:
            assert any(
                expected_file in deleted_path for deleted_path in cascade_deleted
            ), f"Expected {expected_file} to be in cascade_deleted list: {cascade_deleted}"
