"""Integration test for S-09: claim → modify file list → complete → verify move & YAML.

Tests the complete task lifecycle from claiming through completion using
the MCP server RPC calls to verify end-to-end functionality.
"""

import pytest
from fastmcp import Client
from pathlib import Path

from trellis_mcp.server import create_server
from trellis_mcp.settings import Settings
from trellis_mcp.io_utils import read_markdown


@pytest.mark.asyncio
async def test_s09_claim_complete_workflow_with_file_movement_and_yaml_verification(temp_dir):
    """Integration test: claim → modify file list → complete → verify move & YAML.

    This test covers the S-09 requirement by:
    1. Creating a complete project hierarchy via MCP calls
    2. Using claimNextTask to claim a task (open → in-progress)
    3. Using completeTask with summary and filesChanged
    4. Verifying the task file moves from tasks-open to tasks-done
    5. Verifying YAML front-matter updates (status=done, worktree=null)
    6. Verifying log entry is appended with summary and filesChanged
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
        # Step 1: Create complete project hierarchy via MCP calls
        # Create project
        project_result = await client.call_tool(
            "createObject",
            {
                "kind": "project",
                "title": "S-09 Integration Test Project",
                "description": "Project for testing claim → complete workflow",
                "projectRoot": planning_root,
            },
        )
        project_id = project_result.data["id"]
        assert project_id.startswith("P-")

        # Create epic under project
        epic_result = await client.call_tool(
            "createObject",
            {
                "kind": "epic",
                "title": "S-09 Test Epic",
                "description": "Epic for claim completion workflow test",
                "projectRoot": planning_root,
                "parent": project_id,
            },
        )
        epic_id = epic_result.data["id"]
        assert epic_id.startswith("E-")

        # Create feature under epic
        feature_result = await client.call_tool(
            "createObject",
            {
                "kind": "feature",
                "title": "S-09 Test Feature",
                "description": "Feature for testing task completion workflow",
                "projectRoot": planning_root,
                "parent": epic_id,
            },
        )
        feature_id = feature_result.data["id"]
        assert feature_id.startswith("F-")

        # Create task under feature with high priority
        task_result = await client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Implement authentication system",
                "description": "Task to test the complete claim → complete workflow",
                "projectRoot": planning_root,
                "parent": feature_id,
                "priority": "high",
            },
        )
        task_id = task_result.data["id"]
        assert task_id.startswith("T-")

        # Verify task was created in open status in tasks-open directory
        assert task_result.data["file_path"] is not None
        initial_task_path = Path(task_result.data["file_path"])
        assert initial_task_path.exists()
        assert "tasks-open" in str(initial_task_path)

        # Read initial task YAML to verify open status
        initial_yaml, initial_body = read_markdown(initial_task_path)
        assert initial_yaml["status"] == "open"
        assert initial_yaml["id"] == task_id
        assert initial_yaml["title"] == "Implement authentication system"
        assert initial_yaml.get("worktree") is None

        # Step 2: Claim the task using claimNextTask RPC call
        claim_result = await client.call_tool(
            "claimNextTask",
            {
                "projectRoot": planning_root,
                "worktree": "/workspace/auth-feature-branch",
            },
        )

        # Verify claim response structure
        assert claim_result.data is not None
        claimed_task = claim_result.data["task"]
        assert claimed_task["id"] == task_id
        assert claimed_task["status"] == "in-progress"
        assert claim_result.data["claimed_status"] == "in-progress"
        assert claim_result.data["worktree"] == "/workspace/auth-feature-branch"

        # Verify task file was updated in-place (still in tasks-open but with new status)
        claim_yaml, claim_body = read_markdown(initial_task_path)
        assert claim_yaml["status"] == "in-progress"
        assert claim_yaml["worktree"] == "/workspace/auth-feature-branch"
        assert initial_task_path.exists()  # Should still be in tasks-open

        # Step 3: Complete the task using completeTask RPC call with summary and filesChanged
        summary_text = "Implemented JWT authentication with bcrypt password hashing"
        files_changed = [
            "src/auth/jwt_manager.py",
            "src/auth/password_hasher.py",
            "tests/test_auth.py",
            "requirements.txt",
        ]

        complete_result = await client.call_tool(
            "completeTask",
            {
                "projectRoot": planning_root,
                "taskId": task_id,
                "summary": summary_text,
                "filesChanged": files_changed,
            },
        )

        # Verify completion response
        assert complete_result.data is not None
        completed_task = complete_result.data["task"]
        assert completed_task["status"] == "done"

        # Step 4: Verify file movement from tasks-open to tasks-done
        planning_path = temp_dir / "planning"

        # Extract raw IDs for path construction
        raw_project_id = project_id.removeprefix("P-")
        raw_epic_id = epic_id.removeprefix("E-")
        raw_feature_id = feature_id.removeprefix("F-")

        # Original file should be removed from tasks-open
        assert not initial_task_path.exists()

        # New file should exist in tasks-done with timestamp prefix
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
        assert tasks_done_dir.exists()

        # Find the completed task file (should have timestamp prefix)
        done_files = list(tasks_done_dir.glob(f"*-{task_id}.md"))
        assert len(done_files) == 1

        done_file_path = done_files[0]
        assert done_file_path.exists()

        # Verify timestamp prefix format (YYYYMMDD_HHMMSS-T-taskid.md)
        filename = done_file_path.name
        assert filename.endswith(f"-{task_id}.md")
        timestamp_part = filename.split(f"-{task_id}.md")[0]
        assert len(timestamp_part) == 15  # YYYYMMDD_HHMMSS format
        assert timestamp_part.count("_") == 1  # One underscore between date and time

        # Step 5: Verify YAML front-matter updates in completed task file
        done_yaml, done_body = read_markdown(done_file_path)

        # Verify status was updated to done
        assert done_yaml["status"] == "done"

        # Verify worktree was cleared (S-06 requirement)
        assert done_yaml["worktree"] is None

        # Verify other fields preserved correctly
        assert done_yaml["id"] == task_id
        assert done_yaml["title"] == "Implement authentication system"
        assert done_yaml["parent"] == feature_id
        assert done_yaml["priority"] == 1  # HIGH priority = 1
        assert done_yaml["kind"] == "task"

        # Step 6: Verify log entry was appended with summary and filesChanged (S-04 requirement)
        assert "### Log" in done_body

        # Verify log entry contains summary
        assert summary_text in done_body

        # Verify log entry contains filesChanged list
        for file_path in files_changed:
            assert f'"{file_path}"' in done_body

        # Verify log entry has timestamp format (**YYYY-MM-DDTHH:MM:SS.sssssZ** with microseconds)
        import re

        log_timestamp_pattern = r"\*\*\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{6}Z\*\*"
        assert re.search(log_timestamp_pattern, done_body) is not None

        # Step 7: Verify task completion response includes correct file path
        completed_file_path = complete_result.data["file_path"]
        assert completed_file_path == str(done_file_path)

        # Step 8: Additional verification - ensure task cannot be claimed again
        # Try to claim next task and verify this completed task is not returned
        with pytest.raises(Exception) as exc_info:
            await client.call_tool("claimNextTask", {"projectRoot": planning_root})

        # Should fail because no open tasks remain
        assert "No open tasks available" in str(
            exc_info.value
        ) or "No unblocked tasks available" in str(exc_info.value)
