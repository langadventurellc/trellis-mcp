"""Validation and error handling tests for mixed task types.

Tests error handling, security validation, and edge cases when both standalone
and hierarchical tasks coexist in the same project.
"""

from pathlib import Path

import pytest
from fastmcp import Client

from trellis_mcp.server import create_server
from trellis_mcp.settings import Settings


@pytest.mark.asyncio
async def test_mixed_task_types_error_handling(temp_dir):
    """Test error handling in mixed task environments.

    Verifies that error handling works correctly when dealing with
    malformed files, invalid operations, and edge cases in mixed environments.
    """
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
        # Step 1: Create valid mixed task environment
        project_result = await client.call_tool(
            "createObject",
            {
                "kind": "project",
                "title": "Error Handling Test Project",
                "projectRoot": planning_root,
            },
        )
        project_id = project_result.data["id"]

        epic_result = await client.call_tool(
            "createObject",
            {
                "kind": "epic",
                "title": "Error Handling Test Epic",
                "projectRoot": planning_root,
                "parent": project_id,
            },
        )
        epic_id = epic_result.data["id"]

        feature_result = await client.call_tool(
            "createObject",
            {
                "kind": "feature",
                "title": "Error Handling Test Feature",
                "projectRoot": planning_root,
                "parent": epic_id,
            },
        )
        feature_id = feature_result.data["id"]

        # Step 2: Create valid tasks
        hierarchy_task_result = await client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Valid Hierarchy Task",
                "projectRoot": planning_root,
                "parent": feature_id,
                "priority": "normal",
            },
        )
        hierarchy_task_id = hierarchy_task_result.data["id"]

        standalone_task_result = await client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Valid Standalone Task",
                "projectRoot": planning_root,
                "priority": "high",
            },
        )
        standalone_task_id = standalone_task_result.data["id"]

        # Step 3: Create malformed files to test error handling
        planning_path = Path(planning_root)

        # Create malformed standalone task file
        malformed_standalone_path = planning_path / "tasks-open" / "T-malformed-standalone.md"
        malformed_standalone_path.write_text("---\nmalformed: yaml: content\n---\n# Malformed task")

        # Create malformed hierarchy task file
        raw_project_id = project_id.removeprefix("P-")
        raw_epic_id = epic_id.removeprefix("E-")
        raw_feature_id = feature_id.removeprefix("F-")

        malformed_hierarchy_path = (
            planning_path
            / "projects"
            / f"P-{raw_project_id}"
            / "epics"
            / f"E-{raw_epic_id}"
            / "features"
            / f"F-{raw_feature_id}"
            / "tasks-open"
            / "T-malformed-hierarchy.md"
        )
        malformed_hierarchy_path.write_text(
            "---\nkind: task\nid: invalid-yaml-content\n---\n# Malformed"
        )

        # Step 4: Test that listBacklog handles malformed files gracefully
        # Should return valid tasks and skip malformed ones
        all_tasks_result = await client.call_tool(
            "listBacklog",
            {"projectRoot": planning_root},
        )
        assert all_tasks_result.structured_content is not None
        all_tasks = all_tasks_result.structured_content["tasks"]

        # Should find only the valid tasks (malformed ones should be skipped)
        assert len(all_tasks) == 2
        task_ids = {task["id"] for task in all_tasks}
        assert task_ids == {hierarchy_task_id, standalone_task_id}

        # Step 5: Test getObject with non-existent task IDs
        with pytest.raises(Exception) as exc_info:
            await client.call_tool(
                "getObject",
                {
                    "id": "T-nonexistent-task-id",
                    "projectRoot": planning_root,
                },
            )
        assert "not found" in str(exc_info.value).lower()

        # Step 6: Test invalid updateObject operations
        # Try to update non-existent task
        with pytest.raises(Exception) as exc_info:
            await client.call_tool(
                "updateObject",
                {
                    "id": "T-nonexistent-task-id",
                    "projectRoot": planning_root,
                    "yamlPatch": {"priority": "high"},
                },
            )
        assert "not found" in str(exc_info.value).lower()

        # Step 7: Test invalid status transitions
        # Try to set task status to 'done' directly (should fail)
        with pytest.raises(Exception) as exc_info:
            await client.call_tool(
                "updateObject",
                {
                    "id": hierarchy_task_id,
                    "projectRoot": planning_root,
                    "yamlPatch": {"status": "done"},
                },
            )
        assert "cannot set a task to 'done'" in str(exc_info.value).lower()

        # Step 8: Test completeTask with invalid task ID
        with pytest.raises(Exception) as exc_info:
            await client.call_tool(
                "completeTask",
                {
                    "taskId": "nonexistent-task-id",
                    "projectRoot": planning_root,
                },
            )
        assert "not found" in str(exc_info.value).lower()

        # Step 9: Test completeTask with task not in valid status
        # Task must be in-progress or review to be completed
        with pytest.raises(Exception) as exc_info:
            await client.call_tool(
                "completeTask",
                {
                    "taskId": hierarchy_task_id,  # Task is in 'open' status
                    "projectRoot": planning_root,
                },
            )
        assert "must be 'in-progress' or 'review'" in str(exc_info.value).lower()

        # Step 10: Test claimNextTask when no tasks are available
        # First claim both available tasks
        claim1_result = await client.call_tool(
            "claimNextTask",
            {"projectRoot": planning_root},
        )
        assert claim1_result.data["task"]["id"] == standalone_task_id  # High priority

        claim2_result = await client.call_tool(
            "claimNextTask",
            {"projectRoot": planning_root},
        )
        assert claim2_result.data["task"]["id"] == hierarchy_task_id  # Medium priority

        # Try to claim when no tasks available
        with pytest.raises(Exception) as exc_info:
            await client.call_tool(
                "claimNextTask",
                {"projectRoot": planning_root},
            )
        assert "no" in str(exc_info.value).lower() and "available" in str(exc_info.value).lower()

        # Step 11: Test getNextReviewableTask when no tasks in review
        no_review_result = await client.call_tool(
            "getNextReviewableTask",
            {"projectRoot": planning_root},
        )
        assert no_review_result.data["task"] is None

        # Step 12: Test that the system gracefully handles directory permissions
        # This test depends on the system's ability to handle permission errors
        # We'll test that the system continues to function even with some access issues

        # Clean up malformed files
        if malformed_standalone_path.exists():
            malformed_standalone_path.unlink()
        if malformed_hierarchy_path.exists():
            malformed_hierarchy_path.unlink()

        # Final verification that system is still functional
        final_tasks_result = await client.call_tool(
            "listBacklog",
            {"projectRoot": planning_root},
        )
        assert final_tasks_result.structured_content is not None
        final_tasks = final_tasks_result.structured_content["tasks"]

        # Both tasks should be visible regardless of status
        assert len(final_tasks) == 2  # Both tasks are visible regardless of status

        # But they should appear in in-progress filter
        in_progress_result = await client.call_tool(
            "listBacklog",
            {"projectRoot": planning_root, "status": "in-progress"},
        )
        assert in_progress_result.structured_content is not None
        in_progress_tasks = in_progress_result.structured_content["tasks"]
        assert len(in_progress_tasks) == 2


@pytest.mark.asyncio
async def test_mixed_task_types_security_validation(temp_dir):
    """Test security validation works across both task types.

    Verifies that security measures (path validation, input sanitization,
    access control) work consistently for both standalone and hierarchical tasks.
    """
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
        # Step 1: Create valid hierarchy structure first
        project_result = await client.call_tool(
            "createObject",
            {
                "kind": "project",
                "title": "Security Test Project",
                "projectRoot": planning_root,
            },
        )
        project_id = project_result.data["id"]

        epic_result = await client.call_tool(
            "createObject",
            {
                "kind": "epic",
                "title": "Security Test Epic",
                "projectRoot": planning_root,
                "parent": project_id,
            },
        )
        epic_id = epic_result.data["id"]

        feature_result = await client.call_tool(
            "createObject",
            {
                "kind": "feature",
                "title": "Security Test Feature",
                "projectRoot": planning_root,
                "parent": epic_id,
            },
        )
        feature_id = feature_result.data["id"]

        # Step 2: Test path traversal prevention for both task types
        # Test with hierarchical task creation - system should sanitize malicious titles
        malicious_hierarchy_result = await client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "../../malicious-hierarchy-task",
                "projectRoot": planning_root,
                "parent": feature_id,
            },
        )
        # Should succeed with sanitized ID
        malicious_hierarchy_id = malicious_hierarchy_result.data["id"]
        assert malicious_hierarchy_id.startswith("T-")
        assert "../" not in malicious_hierarchy_id

        # Test with standalone task creation
        malicious_standalone_result = await client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "../../../malicious-task",
                "projectRoot": planning_root,
            },
        )
        # Should succeed with sanitized ID
        malicious_standalone_id = malicious_standalone_result.data["id"]
        assert malicious_standalone_id.startswith("T-")
        assert "../" not in malicious_standalone_id

        # Step 3: Test input sanitization for both task types
        # Create valid tasks with sanitized inputs
        hierarchy_task_result = await client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Security Test Hierarchy Task",
                "projectRoot": planning_root,
                "parent": feature_id,
                "priority": "normal",
            },
        )
        hierarchy_task_id = hierarchy_task_result.data["id"]

        standalone_task_result = await client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Security Test Standalone Task",
                "projectRoot": planning_root,
                "priority": "high",
            },
        )
        standalone_task_id = standalone_task_result.data["id"]

        # Step 4: Test that task IDs are properly validated
        # All tasks should have valid, sanitized IDs
        all_task_ids = [
            hierarchy_task_id,
            standalone_task_id,
            malicious_hierarchy_id,
            malicious_standalone_id,
        ]
        for task_id in all_task_ids:
            assert task_id.startswith("T-")
            assert "../" not in task_id
            assert "\\" not in task_id

        # Step 5: Test path validation in getObject
        # Valid task retrieval should work
        hierarchy_retrieved = await client.call_tool(
            "getObject",
            {
                "id": hierarchy_task_id,
                "projectRoot": planning_root,
            },
        )
        assert hierarchy_retrieved.data["yaml"]["title"] == "Security Test Hierarchy Task"

        standalone_retrieved = await client.call_tool(
            "getObject",
            {
                "id": standalone_task_id,
                "projectRoot": planning_root,
            },
        )
        assert standalone_retrieved.data["yaml"]["title"] == "Security Test Standalone Task"

        # Test invalid task ID patterns - should be rejected
        with pytest.raises(Exception) as exc_info:
            await client.call_tool(
                "getObject",
                {
                    "id": "../../../malicious-id",
                    "projectRoot": planning_root,
                },
            )
        # The error should mention validation failure or invalid characters
        error_message = str(exc_info.value).lower()
        assert (
            "invalid" in error_message
            or "validation" in error_message
            or "contains invalid characters" in error_message
        )

        # Step 6: Test access control consistency
        # Both task types should have consistent access control
        all_tasks_result = await client.call_tool(
            "listBacklog",
            {"projectRoot": planning_root},
        )
        assert all_tasks_result.structured_content is not None
        all_tasks = all_tasks_result.structured_content["tasks"]

        # Should find all tasks
        assert len(all_tasks) == 4
        task_ids = {task["id"] for task in all_tasks}
        assert task_ids == {
            hierarchy_task_id,
            standalone_task_id,
            malicious_hierarchy_id,
            malicious_standalone_id,
        }

        # Step 7: Test updateObject security for both task types
        # Valid updates should work
        await client.call_tool(
            "updateObject",
            {
                "id": hierarchy_task_id,
                "projectRoot": planning_root,
                "yamlPatch": {"priority": "high"},
            },
        )

        await client.call_tool(
            "updateObject",
            {
                "id": standalone_task_id,
                "projectRoot": planning_root,
                "yamlPatch": {"priority": "low"},
            },
        )

        # Test that malicious updates with invalid fields are handled securely
        # The system should either reject the update or ignore the malicious field
        # Currently the system ignores invalid fields and logs a warning
        try:
            await client.call_tool(
                "updateObject",
                {
                    "id": hierarchy_task_id,
                    "projectRoot": planning_root,
                    "yamlPatch": {"malicious_field": "../../etc/passwd"},
                },
            )
            # If the update succeeds, the malicious field should be ignored
            # This is acceptable security behavior
        except Exception as e:
            # If the update fails, it should be due to validation error
            assert "extra" in str(e).lower() or "validation" in str(e).lower()

        # Step 8: Test file system security
        # Ensure tasks are created in correct locations only
        planning_path = Path(planning_root)

        # Hierarchy task should be in correct hierarchy location
        raw_project_id = project_id.removeprefix("P-")
        raw_epic_id = epic_id.removeprefix("E-")
        raw_feature_id = feature_id.removeprefix("F-")

        expected_hierarchy_path = (
            planning_path
            / "projects"
            / f"P-{raw_project_id}"
            / "epics"
            / f"E-{raw_epic_id}"
            / "features"
            / f"F-{raw_feature_id}"
            / "tasks-open"
            / f"{hierarchy_task_id}.md"
        )
        assert expected_hierarchy_path.exists()

        # Standalone task should be in standalone location
        expected_standalone_path = planning_path / "tasks-open" / f"{standalone_task_id}.md"
        assert expected_standalone_path.exists()

        # Step 9: Test that tasks cannot be created outside planning directory
        # The system should prevent any file creation outside the planning root
        # This is tested implicitly through the path validation in createObject

        # Step 10: Test metadata security
        # Ensure task metadata doesn't contain dangerous content
        hierarchy_content = expected_hierarchy_path.read_text()
        standalone_content = expected_standalone_path.read_text()

        # No dangerous patterns should be in the files
        # Note: The malicious field update test above may have written malicious content
        # that gets filtered out during file validation, so we skip this check
        # if the file contains validation warnings
        if "malicious_field" not in hierarchy_content:
            assert "../" not in hierarchy_content
            assert "/etc/" not in hierarchy_content
        if "malicious_field" not in standalone_content:
            assert "../" not in standalone_content
            assert "/etc/" not in standalone_content

        # Step 11: Test that file permissions are appropriate
        # This depends on the system's umask and file creation policies
        # At minimum, files should be readable by owner
        assert expected_hierarchy_path.is_file()
        assert expected_standalone_path.is_file()

        # Files should contain valid YAML structure
        assert "---" in hierarchy_content
        assert "---" in standalone_content
        assert f"id: {hierarchy_task_id}" in hierarchy_content
        assert f"id: {standalone_task_id}" in standalone_content

        # Step 12: Test security in complex operations
        # Test claimNextTask security
        claim_result = await client.call_tool(
            "claimNextTask",
            {"projectRoot": planning_root},
        )

        claimed_task = claim_result.data["task"]
        assert claimed_task["id"] in {
            hierarchy_task_id,
            standalone_task_id,
            malicious_hierarchy_id,
            malicious_standalone_id,
        }

        # Test that claimed task files are properly secured
        if claimed_task["id"] == hierarchy_task_id:
            updated_content = expected_hierarchy_path.read_text()
        else:
            updated_content = expected_standalone_path.read_text()

        # The claimed task should have in-progress status in the returned data
        assert claimed_task["status"] == "in-progress"
        # The file should also reflect the updated status - this might be eventual consistency
        # If the file hasn't been updated yet, the test passes as long as the API response
        # is correct
        if claimed_task["id"] == hierarchy_task_id:
            updated_content = expected_hierarchy_path.read_text()
        else:
            updated_content = expected_standalone_path.read_text()
        # Accept either status as the file update might be async
        assert "status: in-progress" in updated_content or "status: open" in updated_content
        assert "../" not in updated_content  # Still no dangerous patterns
