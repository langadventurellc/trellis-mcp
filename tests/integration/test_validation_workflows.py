"""Integration tests for complete validation workflows.

This module tests end-to-end validation workflows for both standalone and
hierarchy-based tasks, ensuring the entire validation pipeline works correctly.
"""

import pytest
from fastmcp import Client

from trellis_mcp.server import create_server
from trellis_mcp.settings import Settings


@pytest.mark.asyncio
async def test_standalone_task_validation_workflow_success(temp_dir):
    """Integration test: standalone task validation workflow with valid data."""
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
        # Test successful standalone task creation
        task_result = await client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Standalone Task Valid",
                "description": "Valid standalone task for testing",
                "projectRoot": planning_root,
                "priority": "high",
                "status": "open",
            },
        )

        # Verify task was created successfully
        assert task_result.data is not None
        assert task_result.data["id"].startswith("T-")
        assert task_result.data["status"] == "open"

        # Verify file exists in standalone tasks directory
        task_id = task_result.data["id"]
        expected_path = temp_dir / "planning" / "tasks-open" / f"{task_id}.md"
        assert expected_path.exists()

        # Verify file contains correct YAML structure
        content = expected_path.read_text()
        assert f"id: {task_id}" in content
        assert "title: Standalone Task Valid" in content
        assert "kind: task" in content
        assert "priority: high" in content
        assert "status: open" in content

        # Verify no parent field in standalone task
        assert "parent:" not in content


@pytest.mark.asyncio
async def test_standalone_task_validation_workflow_security_failure(temp_dir):
    """Integration test: standalone task validation workflow with security violations."""
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
        # Test security validation failure - path traversal attempt
        with pytest.raises(Exception) as exc_info:
            await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Malicious Task",
                    "description": "Task with path traversal attempt",
                    "projectRoot": planning_root,
                    "parent": "../../../etc/passwd",
                    "priority": "high",
                },
            )

        # Verify security validation error
        error_message = str(exc_info.value)
        assert "Security validation failed" in error_message
        assert "suspicious pattern" in error_message

        # Verify no file was created
        planning_path = temp_dir / "planning"
        if planning_path.exists():
            task_files = list(planning_path.glob("tasks-open/T-*.md"))
            assert len(task_files) == 0


@pytest.mark.asyncio
async def test_standalone_task_validation_workflow_privileged_field_failure(temp_dir):
    """Integration test: standalone task validation workflow with privileged field attempt."""
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
        # Test security validation failure - privileged field attempt
        # Create a task with control characters in parent field to trigger security validation
        with pytest.raises(Exception) as exc_info:
            await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Privileged Task",
                    "description": "Task with privileged field",
                    "projectRoot": planning_root,
                    "parent": "test\x00parent",  # Control character
                    "priority": "high",
                },
            )

        # Verify security validation error
        error_message = str(exc_info.value)
        assert "Security validation failed" in error_message
        assert "control characters" in error_message


@pytest.mark.asyncio
async def test_hierarchy_task_validation_workflow_success(temp_dir):
    """Integration test: hierarchy task validation workflow with valid data."""
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
        # Step 1: Create complete hierarchy (project → epic → feature)
        project_result = await client.call_tool(
            "createObject",
            {
                "kind": "project",
                "title": "Hierarchy Test Project",
                "description": "Project for hierarchy validation testing",
                "projectRoot": planning_root,
            },
        )
        project_id = project_result.data["id"]

        epic_result = await client.call_tool(
            "createObject",
            {
                "kind": "epic",
                "title": "Hierarchy Test Epic",
                "description": "Epic for hierarchy validation testing",
                "projectRoot": planning_root,
                "parent": project_id,
            },
        )
        epic_id = epic_result.data["id"]

        feature_result = await client.call_tool(
            "createObject",
            {
                "kind": "feature",
                "title": "Hierarchy Test Feature",
                "description": "Feature for hierarchy validation testing",
                "projectRoot": planning_root,
                "parent": epic_id,
            },
        )
        feature_id = feature_result.data["id"]

        # Step 2: Test successful hierarchy task creation
        task_result = await client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Hierarchy Task Valid",
                "description": "Valid hierarchy task for testing",
                "projectRoot": planning_root,
                "parent": feature_id,
                "priority": "normal",
                "status": "open",
            },
        )

        # Verify task was created successfully
        assert task_result.data is not None
        assert task_result.data["id"].startswith("T-")
        assert task_result.data["status"] == "open"

        # Verify file exists in hierarchy tasks directory
        task_id = task_result.data["id"]

        # Extract raw IDs for path construction
        raw_project_id = project_id.removeprefix("P-")
        raw_epic_id = epic_id.removeprefix("E-")
        raw_feature_id = feature_id.removeprefix("F-")

        expected_path = (
            temp_dir
            / "planning"
            / "projects"
            / f"P-{raw_project_id}"
            / "epics"
            / f"E-{raw_epic_id}"
            / "features"
            / f"F-{raw_feature_id}"
            / "tasks-open"
            / f"{task_id}.md"
        )
        assert expected_path.exists()

        # Verify file contains correct YAML structure
        content = expected_path.read_text()
        assert f"id: {task_id}" in content
        assert "title: Hierarchy Task Valid" in content
        assert "kind: task" in content
        assert "priority: normal" in content
        assert "status: open" in content
        assert f"parent: {feature_id}" in content


@pytest.mark.asyncio
async def test_hierarchy_task_validation_workflow_invalid_parent_failure(temp_dir):
    """Integration test: hierarchy task validation workflow with invalid parent."""
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
        # Test parent existence validation failure - non-existent parent
        with pytest.raises(Exception) as exc_info:
            await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Invalid Parent Task",
                    "description": "Task with non-existent parent",
                    "projectRoot": planning_root,
                    "parent": "F-nonexistent-feature",
                    "priority": "high",
                },
            )

        # Verify parent existence validation error
        error_message = str(exc_info.value)
        assert "does not exist" in error_message
        assert "F-nonexistent-feature" in error_message

        # Verify no file was created
        planning_path = temp_dir / "planning"
        if planning_path.exists():
            # Check both standalone and hierarchy task locations
            standalone_tasks = list(planning_path.glob("tasks-open/T-*.md"))
            hierarchy_tasks = list(
                planning_path.glob("projects/*/epics/*/features/*/tasks-open/T-*.md")
            )
            assert len(standalone_tasks) == 0
            assert len(hierarchy_tasks) == 0


@pytest.mark.asyncio
async def test_validation_workflow_circular_dependency_detection(temp_dir):
    """Integration test: validation workflow with circular dependency detection."""
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
        # Step 1: Create complete hierarchy
        project_result = await client.call_tool(
            "createObject",
            {
                "kind": "project",
                "title": "Circular Dependency Test Project",
                "projectRoot": planning_root,
            },
        )
        project_id = project_result.data["id"]

        epic_result = await client.call_tool(
            "createObject",
            {
                "kind": "epic",
                "title": "Circular Dependency Test Epic",
                "projectRoot": planning_root,
                "parent": project_id,
            },
        )
        epic_id = epic_result.data["id"]

        feature_result = await client.call_tool(
            "createObject",
            {
                "kind": "feature",
                "title": "Circular Dependency Test Feature",
                "projectRoot": planning_root,
                "parent": epic_id,
            },
        )
        feature_id = feature_result.data["id"]

        # Step 2: Create valid task chain A → B → C
        task_a_result = await client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Task A",
                "projectRoot": planning_root,
                "parent": feature_id,
                "prerequisites": [],
            },
        )
        task_a_id = task_a_result.data["id"]

        task_b_result = await client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Task B",
                "projectRoot": planning_root,
                "parent": feature_id,
                "prerequisites": [task_a_id],
            },
        )
        task_b_id = task_b_result.data["id"]

        task_c_result = await client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Task C",
                "projectRoot": planning_root,
                "parent": feature_id,
                "prerequisites": [task_b_id],
            },
        )
        task_c_id = task_c_result.data["id"]

        # Step 3: Attempt to create circular dependency by updating Task A
        # This would create: A → C → B → A (cycle)
        with pytest.raises(Exception) as exc_info:
            await client.call_tool(
                "updateObject",
                {
                    "id": task_a_id,
                    "projectRoot": planning_root,
                    "yamlPatch": {"prerequisites": [task_c_id]},
                },
            )

        # Verify circular dependency validation error
        error_message = str(exc_info.value)
        assert "circular dependencies" in error_message or "cycle" in error_message

        # Verify original task structure remains intact
        task_a_retrieved = await client.call_tool(
            "getObject",
            {
                "id": task_a_id,
                "projectRoot": planning_root,
            },
        )
        assert task_a_retrieved.data["yaml"]["prerequisites"] == []


@pytest.mark.asyncio
async def test_validation_workflow_mixed_task_types(temp_dir):
    """Integration test: validation workflow with mixed standalone and hierarchy tasks."""
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
                "title": "Mixed Task Test Project",
                "projectRoot": planning_root,
            },
        )
        project_id = project_result.data["id"]

        epic_result = await client.call_tool(
            "createObject",
            {
                "kind": "epic",
                "title": "Mixed Task Test Epic",
                "projectRoot": planning_root,
                "parent": project_id,
            },
        )
        epic_id = epic_result.data["id"]

        feature_result = await client.call_tool(
            "createObject",
            {
                "kind": "feature",
                "title": "Mixed Task Test Feature",
                "projectRoot": planning_root,
                "parent": epic_id,
            },
        )
        feature_id = feature_result.data["id"]

        # Step 2: Create standalone task (successful)
        standalone_task_result = await client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Standalone Task Mixed",
                "description": "Standalone task in mixed environment",
                "projectRoot": planning_root,
                "priority": "high",
                "status": "open",
            },
        )
        standalone_task_id = standalone_task_result.data["id"]

        # Step 3: Create hierarchy task (successful)
        hierarchy_task_result = await client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Hierarchy Task Mixed",
                "description": "Hierarchy task in mixed environment",
                "projectRoot": planning_root,
                "parent": feature_id,
                "priority": "normal",
                "status": "open",
            },
        )
        hierarchy_task_id = hierarchy_task_result.data["id"]

        # Step 4: Verify both tasks exist in correct locations
        # Standalone task should be in tasks-open directory
        standalone_path = temp_dir / "planning" / "tasks-open" / f"{standalone_task_id}.md"
        assert standalone_path.exists()

        # Hierarchy task should be in hierarchy directory
        raw_project_id = project_id.removeprefix("P-")
        raw_epic_id = epic_id.removeprefix("E-")
        raw_feature_id = feature_id.removeprefix("F-")

        hierarchy_path = (
            temp_dir
            / "planning"
            / "projects"
            / f"P-{raw_project_id}"
            / "epics"
            / f"E-{raw_epic_id}"
            / "features"
            / f"F-{raw_feature_id}"
            / "tasks-open"
            / f"{hierarchy_task_id}.md"
        )
        assert hierarchy_path.exists()

        # Step 5: Verify both tasks appear in listBacklog
        backlog_result = await client.call_tool(
            "listBacklog",
            {
                "projectRoot": planning_root,
            },
        )
        assert backlog_result.structured_content is not None
        tasks = backlog_result.structured_content["tasks"]
        assert len(tasks) == 2

        # Verify both task IDs are present
        task_ids = {task["id"] for task in tasks}
        assert standalone_task_id in task_ids
        assert hierarchy_task_id in task_ids


@pytest.mark.asyncio
async def test_validation_workflow_contextual_error_messages(temp_dir):
    """Integration test: validation workflow with contextual error message generation."""
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
        # Test 1: Standalone task with invalid status
        with pytest.raises(Exception) as exc_info:
            await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Invalid Status Standalone",
                    "description": "Standalone task with invalid status",
                    "projectRoot": planning_root,
                    "status": "invalid_status",
                },
            )

        # Verify contextual error message for standalone task
        error_message = str(exc_info.value)
        assert "status" in error_message
        assert "invalid_status" in error_message

        # Test 2: Hierarchy task with missing parent (after creating hierarchy)
        project_result = await client.call_tool(
            "createObject",
            {
                "kind": "project",
                "title": "Error Message Test Project",
                "projectRoot": planning_root,
            },
        )
        project_id = project_result.data["id"]

        epic_result = await client.call_tool(
            "createObject",
            {
                "kind": "epic",
                "title": "Error Message Test Epic",
                "projectRoot": planning_root,
                "parent": project_id,
            },
        )
        epic_id = epic_result.data["id"]

        feature_result = await client.call_tool(
            "createObject",
            {
                "kind": "feature",
                "title": "Error Message Test Feature",
                "projectRoot": planning_root,
                "parent": epic_id,
            },
        )
        feature_id = feature_result.data["id"]

        # Test hierarchy task with non-existent parent
        with pytest.raises(Exception) as exc_info:
            await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Invalid Parent Hierarchy",
                    "description": "Hierarchy task with non-existent parent",
                    "projectRoot": planning_root,
                    "parent": "F-nonexistent-feature",
                },
            )

        # Verify contextual error message for hierarchy task
        error_message = str(exc_info.value)
        assert "does not exist" in error_message
        assert "F-nonexistent-feature" in error_message

        # Test 3: Valid hierarchy task for comparison
        valid_task_result = await client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Valid Hierarchy Task",
                "description": "Valid hierarchy task for comparison",
                "projectRoot": planning_root,
                "parent": feature_id,
                "priority": "normal",
                "status": "open",
            },
        )

        # Verify valid task was created successfully
        assert valid_task_result.data is not None
        assert valid_task_result.data["status"] == "open"


@pytest.mark.asyncio
async def test_validation_workflow_status_transitions(temp_dir):
    """Integration test: validation workflow with status transitions."""
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
                "title": "Status Transition Test Project",
                "projectRoot": planning_root,
            },
        )
        project_id = project_result.data["id"]

        epic_result = await client.call_tool(
            "createObject",
            {
                "kind": "epic",
                "title": "Status Transition Test Epic",
                "projectRoot": planning_root,
                "parent": project_id,
            },
        )
        epic_id = epic_result.data["id"]

        feature_result = await client.call_tool(
            "createObject",
            {
                "kind": "feature",
                "title": "Status Transition Test Feature",
                "projectRoot": planning_root,
                "parent": epic_id,
            },
        )
        feature_id = feature_result.data["id"]

        # Step 2: Create task for status transition testing
        task_result = await client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Status Transition Task",
                "description": "Task for status transition testing",
                "projectRoot": planning_root,
                "parent": feature_id,
                "priority": "high",
                "status": "open",
            },
        )
        task_id = task_result.data["id"]

        # Step 3: Test valid status transition (open → in-progress)
        transition_result = await client.call_tool(
            "updateObject",
            {
                "id": task_id,
                "projectRoot": planning_root,
                "yamlPatch": {"status": "in-progress"},
            },
        )
        assert transition_result.data is not None

        # Verify status was updated
        retrieved_task = await client.call_tool(
            "getObject",
            {
                "id": task_id,
                "projectRoot": planning_root,
            },
        )
        assert retrieved_task.data["yaml"]["status"] == "in-progress"

        # Step 4: Test valid status transition (in-progress → review)
        await client.call_tool(
            "updateObject",
            {
                "id": task_id,
                "projectRoot": planning_root,
                "yamlPatch": {"status": "review"},
            },
        )

        # Verify status was updated
        retrieved_task = await client.call_tool(
            "getObject",
            {
                "id": task_id,
                "projectRoot": planning_root,
            },
        )
        assert retrieved_task.data["yaml"]["status"] == "review"

        # Step 5: Test invalid status transition (review → open)
        with pytest.raises(Exception) as exc_info:
            await client.call_tool(
                "updateObject",
                {
                    "id": task_id,
                    "projectRoot": planning_root,
                    "yamlPatch": {"status": "open"},
                },
            )

        # Verify invalid transition error
        error_message = str(exc_info.value)
        assert "status" in error_message.lower()


@pytest.mark.asyncio
async def test_validation_workflow_comprehensive_integration(temp_dir):
    """Integration test: comprehensive validation workflow covering all components."""
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
        # Step 1: Create comprehensive hierarchy
        project_result = await client.call_tool(
            "createObject",
            {
                "kind": "project",
                "title": "Comprehensive Validation Test Project",
                "description": "Project for comprehensive validation testing",
                "projectRoot": planning_root,
            },
        )
        project_id = project_result.data["id"]

        epic_result = await client.call_tool(
            "createObject",
            {
                "kind": "epic",
                "title": "Comprehensive Validation Test Epic",
                "description": "Epic for comprehensive validation testing",
                "projectRoot": planning_root,
                "parent": project_id,
            },
        )
        epic_id = epic_result.data["id"]

        feature_result = await client.call_tool(
            "createObject",
            {
                "kind": "feature",
                "title": "Comprehensive Validation Test Feature",
                "description": "Feature for comprehensive validation testing",
                "projectRoot": planning_root,
                "parent": epic_id,
            },
        )
        feature_id = feature_result.data["id"]

        # Step 2: Create standalone task (full validation workflow)
        standalone_task_result = await client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Comprehensive Standalone Task",
                "description": "Standalone task for comprehensive validation",
                "projectRoot": planning_root,
                "priority": "high",
                "status": "open",
            },
        )
        standalone_task_id = standalone_task_result.data["id"]

        # Step 3: Create hierarchy task (full validation workflow)
        hierarchy_task_result = await client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Comprehensive Hierarchy Task",
                "description": "Hierarchy task for comprehensive validation",
                "projectRoot": planning_root,
                "parent": feature_id,
                "priority": "normal",
                "status": "open",
            },
        )
        hierarchy_task_id = hierarchy_task_result.data["id"]

        # Step 4: Create task with prerequisites (dependency validation)
        prerequisite_task_result = await client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Prerequisite Task",
                "description": "Task with prerequisites for validation",
                "projectRoot": planning_root,
                "parent": feature_id,
                "prerequisites": [hierarchy_task_id],
                "priority": "low",
                "status": "open",
            },
        )
        prerequisite_task_id = prerequisite_task_result.data["id"]

        # Step 5: Test complete status transition workflow
        # Transition hierarchy task through valid states
        await client.call_tool(
            "updateObject",
            {
                "id": hierarchy_task_id,
                "projectRoot": planning_root,
                "yamlPatch": {"status": "in-progress"},
            },
        )

        await client.call_tool(
            "updateObject",
            {
                "id": hierarchy_task_id,
                "projectRoot": planning_root,
                "yamlPatch": {"status": "review"},
            },
        )

        # Complete the hierarchy task to satisfy prerequisites
        await client.call_tool(
            "completeTask",
            {
                "taskId": hierarchy_task_id,
                "projectRoot": planning_root,
                "summary": "Hierarchy task completed to satisfy prerequisites",
                "filesChanged": ["hierarchy_test.py"],
            },
        )

        # Step 6: Test task claiming workflow
        # Check if there are available tasks first
        available_tasks = await client.call_tool(
            "listBacklog",
            {
                "projectRoot": planning_root,
                "status": "open",
            },
        )

        claimed_task = None
        if available_tasks.structured_content and available_tasks.structured_content["tasks"]:
            claimed_task_result = await client.call_tool(
                "claimNextTask",
                {
                    "projectRoot": planning_root,
                    "worktree": "comprehensive-test-workspace",
                },
            )

            # Verify task was claimed (should be highest priority available)
            assert claimed_task_result.data is not None
            claimed_task = claimed_task_result.data["task"]
            assert claimed_task["status"] == "in-progress"
            # Task priority should be high (standalone) or low (prerequisite, now available)
            assert claimed_task["priority"] in ["high", "low"]

        # Step 7: Test complete task workflow (using claimed task if available)
        if (
            available_tasks.structured_content
            and available_tasks.structured_content["tasks"]
            and claimed_task is not None
        ):
            claimed_task_id = claimed_task["id"]

            # Complete the claimed task
            await client.call_tool(
                "completeTask",
                {
                    "taskId": claimed_task_id,
                    "projectRoot": planning_root,
                    "summary": "Comprehensive validation test completed successfully",
                    "filesChanged": ["test_file.py", "validation_test.md"],
                },
            )

        # Verify task was completed and moved to tasks-done
        raw_project_id = project_id.removeprefix("P-")
        raw_epic_id = epic_id.removeprefix("E-")
        raw_feature_id = feature_id.removeprefix("F-")

        done_path = (
            temp_dir
            / "planning"
            / "projects"
            / f"P-{raw_project_id}"
            / "epics"
            / f"E-{raw_epic_id}"
            / "features"
            / f"F-{raw_feature_id}"
            / "tasks-done"
        )

        # Check that task was moved to tasks-done directory
        done_files = list(done_path.glob(f"*{hierarchy_task_id}.md"))
        assert len(done_files) == 1

        # Step 8: Verify all created objects still exist and are valid
        final_backlog = await client.call_tool(
            "listBacklog",
            {
                "projectRoot": planning_root,
            },
        )
        assert final_backlog.structured_content is not None

        # We should have standalone task (claimed but not completed),
        # prerequisite task (still open), and completed hierarchy task
        tasks = final_backlog.structured_content["tasks"]
        assert len(tasks) >= 2  # At least the remaining open tasks

        # Verify task IDs are present
        task_ids = {task["id"] for task in tasks}
        assert standalone_task_id in task_ids or prerequisite_task_id in task_ids
        # At least one of our created tasks should be present
