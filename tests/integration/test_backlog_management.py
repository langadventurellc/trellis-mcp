"""Backlog management tests.

Tests comprehensive backlog listing functionality including filtering, sorting,
and hierarchy traversal.
"""

import pytest
from fastmcp import Client

from .test_helpers import (
    assert_priority_ordering,
    assert_task_structure,
    create_test_server,
    update_task_status,
)


@pytest.mark.asyncio
async def test_listBacklog_comprehensive_integration_with_hierarchy_and_sorting(temp_dir):
    """S-09 Integration test: comprehensive sample hierarchy, call RPC, assert correct list & order.

    Creates a complex project hierarchy with multiple projects, epics, features, and tasks.
    Tests all listBacklog filtering combinations and validates comprehensive sorting behavior.
    """
    # Create server instance
    server, planning_root = create_test_server(temp_dir)

    # Setup: Create comprehensive test hierarchy
    async with Client(server) as setup_client:
        # Project 1: Authentication System
        project1_result = await setup_client.call_tool(
            "createObject",
            {
                "kind": "project",
                "title": "Authentication System",
                "projectRoot": planning_root,
            },
        )
        project1_id = project1_result.data["id"]

        # Epic 1.1: User Management
        epic1_1_result = await setup_client.call_tool(
            "createObject",
            {
                "kind": "epic",
                "title": "User Management",
                "projectRoot": planning_root,
                "parent": project1_id,
            },
        )
        epic1_1_id = epic1_1_result.data["id"]

        # Feature 1.1.1: User Registration
        feature1_1_1_result = await setup_client.call_tool(
            "createObject",
            {
                "kind": "feature",
                "title": "User Registration",
                "projectRoot": planning_root,
                "parent": epic1_1_id,
            },
        )
        feature1_1_1_id = feature1_1_1_result.data["id"]

        # Feature 1.1.2: User Login
        feature1_1_2_result = await setup_client.call_tool(
            "createObject",
            {
                "kind": "feature",
                "title": "User Login",
                "projectRoot": planning_root,
                "parent": epic1_1_id,
            },
        )
        feature1_1_2_id = feature1_1_2_result.data["id"]

        # Epic 1.2: Security
        epic1_2_result = await setup_client.call_tool(
            "createObject",
            {
                "kind": "epic",
                "title": "Security",
                "projectRoot": planning_root,
                "parent": project1_id,
            },
        )
        epic1_2_id = epic1_2_result.data["id"]

        # Feature 1.2.1: JWT Authentication
        feature1_2_1_result = await setup_client.call_tool(
            "createObject",
            {
                "kind": "feature",
                "title": "JWT Authentication",
                "projectRoot": planning_root,
                "parent": epic1_2_id,
            },
        )
        feature1_2_1_id = feature1_2_1_result.data["id"]

        # Project 2: Data Processing
        project2_result = await setup_client.call_tool(
            "createObject",
            {
                "kind": "project",
                "title": "Data Processing",
                "projectRoot": planning_root,
            },
        )
        project2_id = project2_result.data["id"]

        # Epic 2.1: Data Ingestion
        epic2_1_result = await setup_client.call_tool(
            "createObject",
            {
                "kind": "epic",
                "title": "Data Ingestion",
                "projectRoot": planning_root,
                "parent": project2_id,
            },
        )
        epic2_1_id = epic2_1_result.data["id"]

        # Feature 2.1.1: File Upload
        feature2_1_1_result = await setup_client.call_tool(
            "createObject",
            {
                "kind": "feature",
                "title": "File Upload",
                "projectRoot": planning_root,
                "parent": epic2_1_id,
            },
        )
        feature2_1_1_id = feature2_1_1_result.data["id"]

        # Create comprehensive task set with systematic variations
        # We'll create tasks with different priorities, statuses, and spaced creation times

        task_configs = [
            # Feature 1.1.1 tasks (User Registration)
            {
                "parent": feature1_1_1_id,
                "title": "Create registration form",
                "priority": "high",
                "status": "open",
            },
            {
                "parent": feature1_1_1_id,
                "title": "Add email validation",
                "priority": "normal",
                "status": "in-progress",
            },
            {
                "parent": feature1_1_1_id,
                "title": "Implement password rules",
                "priority": "high",
                "status": "review",
            },
            {
                "parent": feature1_1_1_id,
                "title": "Add user profile creation",
                "priority": "low",
                "status": "open",
            },
            # Feature 1.1.2 tasks (User Login)
            {
                "parent": feature1_1_2_id,
                "title": "Design login interface",
                "priority": "normal",
                "status": "done",
            },
            {
                "parent": feature1_1_2_id,
                "title": "Implement authentication logic",
                "priority": "high",
                "status": "in-progress",
            },
            {
                "parent": feature1_1_2_id,
                "title": "Add remember me feature",
                "priority": "low",
                "status": "open",
            },
            # Feature 1.2.1 tasks (JWT Authentication)
            {
                "parent": feature1_2_1_id,
                "title": "JWT token generation",
                "priority": "high",
                "status": "review",
            },
            {
                "parent": feature1_2_1_id,
                "title": "Token validation middleware",
                "priority": "normal",
                "status": "open",
            },
            {
                "parent": feature1_2_1_id,
                "title": "Refresh token logic",
                "priority": "normal",
                "status": "in-progress",
            },
            {
                "parent": feature1_2_1_id,
                "title": "Token expiration handling",
                "priority": "low",
                "status": "done",
            },
            # Feature 2.1.1 tasks (File Upload)
            {
                "parent": feature2_1_1_id,
                "title": "File upload API",
                "priority": "high",
                "status": "open",
            },
            {
                "parent": feature2_1_1_id,
                "title": "File type validation",
                "priority": "normal",
                "status": "review",
            },
            {
                "parent": feature2_1_1_id,
                "title": "Progress tracking",
                "priority": "low",
                "status": "in-progress",
            },
            {
                "parent": feature2_1_1_id,
                "title": "Error handling",
                "priority": "normal",
                "status": "done",
            },
        ]

        # Create all tasks
        created_tasks = []
        for i, config in enumerate(task_configs):
            task_result = await setup_client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": config["title"],
                    "projectRoot": planning_root,
                    "parent": config["parent"],
                    "priority": config["priority"],
                },
            )

            task_id = task_result.data["id"]
            created_tasks.append(
                {
                    "id": task_id,
                    "title": config["title"],
                    "priority": config["priority"],
                    "target_status": config["status"],
                    "parent": config["parent"],
                }
            )

            # Update status if not default "open"
            if config["status"] != "open":
                await update_task_status(setup_client, planning_root, task_id, config["status"])

    # Test 1: List all tasks with no filters - verify comprehensive count and basic sorting
    async with Client(server) as client:
        result = await client.call_tool(
            "listBacklog",
            {"projectRoot": planning_root},
        )

        assert result.structured_content is not None
        all_tasks = result.structured_content["tasks"]

        # Should return all tasks across all projects/epics/features
        assert len(all_tasks) == len(
            task_configs
        ), f"Expected {len(task_configs)} tasks, got {len(all_tasks)}"

        # Verify basic task structure
        for task in all_tasks:
            assert_task_structure(task)

        # Verify priority sorting: high → normal → low
        assert_priority_ordering(all_tasks)

    # Test 2: Project scope filtering
    async with Client(server) as client:
        # Test project 1 scope
        result = await client.call_tool(
            "listBacklog",
            {"projectRoot": planning_root, "scope": project1_id},
        )
        assert result.structured_content is not None
        project1_tasks = result.structured_content["tasks"]

        # Should include all tasks from project 1 (11 tasks)
        expected_project1_count = 11  # 4 + 3 + 4 from the three features
        assert len(project1_tasks) == expected_project1_count

        # Verify all tasks belong to project 1
        for task in project1_tasks:
            assert project1_id.removeprefix("P-") in task["file_path"]

    # Test 3: Epic scope filtering
    async with Client(server) as client:
        # Test epic 1.1 scope (User Management)
        result = await client.call_tool(
            "listBacklog",
            {"projectRoot": planning_root, "scope": epic1_1_id},
        )
        assert result.structured_content is not None
        epic_tasks = result.structured_content["tasks"]

        # Should include tasks from features 1.1.1 and 1.1.2 (7 tasks)
        expected_epic_count = 7  # 4 + 3
        assert len(epic_tasks) == expected_epic_count

        # Verify all tasks belong to this epic
        for task in epic_tasks:
            assert epic1_1_id.removeprefix("E-") in task["file_path"]

    # Test 4: Feature scope filtering
    async with Client(server) as client:
        # Test feature 1.1.1 scope (User Registration)
        result = await client.call_tool(
            "listBacklog",
            {"projectRoot": planning_root, "scope": feature1_1_1_id},
        )
        assert result.structured_content is not None
        feature_tasks = result.structured_content["tasks"]

        # Should include only tasks from feature 1.1.1 (4 tasks)
        assert len(feature_tasks) == 4

        # Verify all tasks belong to this feature
        for task in feature_tasks:
            assert task["parent"] == feature1_1_1_id

    # Test 5: Status filtering
    async with Client(server) as client:
        # Test open status filter
        result = await client.call_tool(
            "listBacklog",
            {"projectRoot": planning_root, "status": "open"},
        )
        assert result.structured_content is not None
        open_tasks = result.structured_content["tasks"]

        # Count expected open tasks from our config
        expected_open_count = sum(1 for config in task_configs if config["status"] == "open")
        assert len(open_tasks) == expected_open_count

        # Verify all returned tasks have open status
        for task in open_tasks:
            assert task["status"] == "open"

    # Test 6: Priority filtering
    async with Client(server) as client:
        # Test high priority filter
        result = await client.call_tool(
            "listBacklog",
            {"projectRoot": planning_root, "priority": "high"},
        )
        assert result.structured_content is not None
        high_priority_tasks = result.structured_content["tasks"]

        # Count expected high priority tasks
        expected_high_count = sum(1 for config in task_configs if config["priority"] == "high")
        assert len(high_priority_tasks) == expected_high_count

        # Verify all returned tasks have high priority
        for task in high_priority_tasks:
            assert task["priority"] == "high"

    # Test 7: Combined filtering (scope + status + priority)
    async with Client(server) as client:
        # Test feature 1.1.1 + open status + high priority
        result = await client.call_tool(
            "listBacklog",
            {
                "projectRoot": planning_root,
                "scope": feature1_1_1_id,
                "status": "open",
                "priority": "high",
            },
        )
        assert result.structured_content is not None
        filtered_tasks = result.structured_content["tasks"]

        # Should find tasks that match ALL criteria
        # From feature 1.1.1: "Create registration form" (high priority, open status)
        assert len(filtered_tasks) == 1
        assert filtered_tasks[0]["title"] == "Create registration form"
        assert filtered_tasks[0]["status"] == "open"
        assert filtered_tasks[0]["priority"] == "high"
        assert filtered_tasks[0]["parent"] == feature1_1_1_id

    # Test 8: Comprehensive sorting validation with mixed priorities and creation times
    async with Client(server) as client:
        # Get tasks from a single feature to test sorting within controlled scope
        result = await client.call_tool(
            "listBacklog",
            {"projectRoot": planning_root, "scope": feature1_1_1_id},
        )
        assert result.structured_content is not None
        feature_tasks = result.structured_content["tasks"]

        # Verify priority-based sorting within this feature
        assert_priority_ordering(feature_tasks)

        # Verify that high priority tasks come first
        high_priority_tasks = [task for task in feature_tasks if task["priority"] == "high"]
        normal_priority_tasks = [task for task in feature_tasks if task["priority"] == "normal"]
        low_priority_tasks = [task for task in feature_tasks if task["priority"] == "low"]

        assert (
            len(high_priority_tasks) == 2
        )  # "Create registration form", "Implement password rules"
        assert len(normal_priority_tasks) == 1  # "Add email validation"
        assert len(low_priority_tasks) == 1  # "Add user profile creation"

        # Verify the first task is high priority
        assert feature_tasks[0]["priority"] == "high"
        assert feature_tasks[1]["priority"] == "high"
        # Verify normal priority comes after high
        assert feature_tasks[2]["priority"] == "normal"
        # Verify low priority comes last
        assert feature_tasks[3]["priority"] == "low"

    # Test 9: Cross-directory search (tasks-open and tasks-done)
    async with Client(server) as client:
        result = await client.call_tool(
            "listBacklog",
            {"projectRoot": planning_root},
        )
        assert result.structured_content is not None
        all_tasks = result.structured_content["tasks"]

        # Check that we have tasks from both tasks-open and tasks-done directories
        file_paths = [task["file_path"] for task in all_tasks]
        has_open_tasks = any("tasks-open" in path for path in file_paths)
        has_done_tasks = any("tasks-done" in path for path in file_paths)

        assert has_open_tasks, "Should find tasks from tasks-open directory"
        assert has_done_tasks, "Should find tasks from tasks-done directory"

    # Test 10: Verify empty results for non-existent filters
    async with Client(server) as client:
        result = await client.call_tool(
            "listBacklog",
            {"projectRoot": planning_root, "status": "nonexistent"},
        )
        assert result.structured_content is not None
        empty_tasks = result.structured_content["tasks"]
        assert len(empty_tasks) == 0

    # Test 11: Verify all status types are represented
    async with Client(server) as client:
        for status in ["open", "in-progress", "review", "done"]:
            result = await client.call_tool(
                "listBacklog",
                {"projectRoot": planning_root, "status": status},
            )
            assert result.structured_content is not None
            status_tasks = result.structured_content["tasks"]

            # We should have at least one task of each status based on our config
            assert len(status_tasks) > 0, f"No tasks found with status: {status}"

            # Verify all returned tasks have the correct status
            for task in status_tasks:
                assert task["status"] == status

    # Test 12: Verify all priority types are represented
    async with Client(server) as client:
        for priority in ["high", "normal", "low"]:
            result = await client.call_tool(
                "listBacklog",
                {"projectRoot": planning_root, "priority": priority},
            )
            assert result.structured_content is not None
            priority_tasks = result.structured_content["tasks"]

            # We should have at least one task of each priority based on our config
            assert len(priority_tasks) > 0, f"No tasks found with priority: {priority}"

            # Verify all returned tasks have the correct priority
            for task in priority_tasks:
                assert task["priority"] == priority
