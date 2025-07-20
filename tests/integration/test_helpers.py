"""Shared test utilities and fixtures for integration tests."""

from pathlib import Path
from typing import Any

from fastmcp import Client, FastMCP

from trellis_mcp.server import create_server
from trellis_mcp.settings import Settings


async def create_test_hierarchy(
    client: Client,
    planning_root: str,
    project_title: str = "Test Project",
) -> dict[str, str]:
    """Create a standard project → epic → feature → task hierarchy for testing.

    Args:
        client: FastMCP client instance
        planning_root: Root path for planning files
        project_title: Title for the project (default: "Test Project")

    Returns:
        dict: Contains IDs for created objects with keys:
            - project_id, epic_id, feature_id
    """
    # Create project
    project_result = await client.call_tool(
        "createObject",
        {
            "kind": "project",
            "title": project_title,
            "projectRoot": planning_root,
        },
    )
    project_id = project_result.data["id"]

    # Create epic under project
    epic_result = await client.call_tool(
        "createObject",
        {
            "kind": "epic",
            "title": f"{project_title} Epic",
            "projectRoot": planning_root,
            "parent": project_id,
        },
    )
    epic_id = epic_result.data["id"]

    # Create feature under epic
    feature_result = await client.call_tool(
        "createObject",
        {
            "kind": "feature",
            "title": f"{project_title} Feature",
            "projectRoot": planning_root,
            "parent": epic_id,
        },
    )
    feature_id = feature_result.data["id"]

    return {
        "project_id": project_id,
        "epic_id": epic_id,
        "feature_id": feature_id,
    }


async def create_task_with_priority(
    client: Client,
    planning_root: str,
    parent_id: str,
    title: str,
    priority: str = "normal",
) -> dict[str, str]:
    """Create a task with specified priority.

    Args:
        client: FastMCP client instance
        planning_root: Root path for planning files
        parent_id: Parent feature ID
        title: Task title
        priority: Task priority (high, normal, low)

    Returns:
        dict: Task creation result data
    """
    task_result = await client.call_tool(
        "createObject",
        {
            "kind": "task",
            "title": title,
            "projectRoot": planning_root,
            "parent": parent_id,
            "priority": priority,
        },
    )
    return task_result.data


async def create_mixed_priority_tasks(
    client: Client,
    planning_root: str,
    parent_id: str,
) -> dict[str, list[str]]:
    """Create tasks with mixed priorities for testing priority ordering.

    Args:
        client: FastMCP client instance
        planning_root: Root path for planning files
        parent_id: Parent feature ID

    Returns:
        dict: Contains task IDs organized by priority
    """
    # Create high priority tasks
    high_task1 = await create_task_with_priority(
        client, planning_root, parent_id, "High Priority Task 1", "high"
    )
    high_task2 = await create_task_with_priority(
        client, planning_root, parent_id, "High Priority Task 2", "high"
    )

    # Create normal priority task
    normal_task = await create_task_with_priority(
        client, planning_root, parent_id, "Normal Priority Task", "normal"
    )

    # Create low priority task
    low_task = await create_task_with_priority(
        client, planning_root, parent_id, "Low Priority Task", "low"
    )

    return {
        "high_priority": [high_task1["id"], high_task2["id"]],
        "normal_priority": [normal_task["id"]],
        "low_priority": [low_task["id"]],
        "all_tasks": [high_task1["id"], high_task2["id"], normal_task["id"], low_task["id"]],
    }


async def update_task_status(
    client: Client,
    planning_root: str,
    task_id: str,
    target_status: str,
):
    """Update task status following proper state transitions.

    Args:
        client: FastMCP client instance
        planning_root: Root path for planning files
        task_id: Task ID to update
        target_status: Target status (open, in-progress, review, done)
    """
    if target_status == "open":
        # No update needed, tasks start as open
        return

    # First transition to in-progress
    await client.call_tool(
        "updateObject",
        {
            "id": task_id,
            "projectRoot": planning_root,
            "yamlPatch": {"status": "in-progress"},
        },
    )

    if target_status == "in-progress":
        return

    # Then transition to review
    await client.call_tool(
        "updateObject",
        {
            "id": task_id,
            "projectRoot": planning_root,
            "yamlPatch": {"status": "review"},
        },
    )

    if target_status == "review":
        return

    if target_status == "done":
        # Complete the task to move it to done status
        await client.call_tool(
            "completeTask",
            {
                "taskId": task_id,
                "projectRoot": planning_root,
            },
        )


async def create_mixed_status_tasks(
    client: Client,
    planning_root: str,
    parent_id: str,
) -> dict[str, list[str]]:
    """Create tasks with mixed statuses for testing status filtering.

    Args:
        client: FastMCP client instance
        planning_root: Root path for planning files
        parent_id: Parent feature ID

    Returns:
        dict: Contains task IDs organized by status
    """
    # Create tasks with different target statuses
    task_configs = [
        {"title": "Open Task", "status": "open"},
        {"title": "In Progress Task", "status": "in-progress"},
        {"title": "Review Task", "status": "review"},
        {"title": "Done Task", "status": "done"},
    ]

    tasks_by_status = {
        "open": [],
        "in-progress": [],
        "review": [],
        "done": [],
    }

    for config in task_configs:
        task_result = await client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": config["title"],
                "projectRoot": planning_root,
                "parent": parent_id,
                "priority": "normal",
            },
        )
        task_id = task_result.data["id"]

        # Update to target status
        await update_task_status(client, planning_root, task_id, config["status"])

        tasks_by_status[config["status"]].append(task_id)

    return tasks_by_status


def create_test_server(temp_dir: Path) -> tuple[FastMCP, str]:
    """Create a test server instance with temporary planning directory.

    Args:
        temp_dir: Temporary directory path

    Returns:
        tuple: (server, planning_root_str)
    """
    settings = Settings(
        planning_root=temp_dir / "planning",
        debug_mode=True,
        log_level="DEBUG",
    )
    server = create_server(settings)
    planning_root = str(temp_dir / "planning")

    return server, planning_root


def assert_task_structure(task_data: dict):
    """Assert that a task data structure contains all required fields.

    Args:
        task_data: Task data dictionary to validate
    """
    required_fields = [
        "id",
        "title",
        "status",
        "priority",
        "parent",
        "file_path",
        "created",
        "updated",
    ]

    for field in required_fields:
        assert field in task_data, f"Task missing required field: {field}"

    # Validate status values
    valid_statuses = ["open", "in-progress", "review", "done"]
    assert task_data["status"] in valid_statuses, f"Invalid status: {task_data['status']}"

    # Validate priority values
    valid_priorities = ["high", "normal", "low"]
    assert task_data["priority"] in valid_priorities, f"Invalid priority: {task_data['priority']}"


def assert_priority_ordering(tasks: list):
    """Assert that tasks are ordered by priority (high → medium → low).

    Args:
        tasks: List of task dictionaries
    """
    priority_order = {"high": 1, "normal": 2, "low": 3}

    for i in range(len(tasks) - 1):
        current_priority = priority_order[tasks[i]["priority"]]
        next_priority = priority_order[tasks[i + 1]["priority"]]
        assert current_priority <= next_priority, (
            f"Priority ordering failed at position {i}: "
            f"{tasks[i]['priority']} -> {tasks[i + 1]['priority']}"
        )


def extract_raw_id(prefixed_id: str) -> str:
    """Extract raw ID by removing prefix (P-, E-, F-, T-).

    Args:
        prefixed_id: ID with prefix (e.g., "P-test-project")

    Returns:
        str: Raw ID without prefix (e.g., "test-project")
    """
    prefixes = ["P-", "E-", "F-", "T-"]
    for prefix in prefixes:
        if prefixed_id.startswith(prefix):
            return prefixed_id.removeprefix(prefix)
    return prefixed_id


def build_task_path(
    temp_dir: Path,
    project_id: str,
    epic_id: str,
    feature_id: str,
    task_id: str,
    status: str = "open",
) -> Path:
    """Build expected task file path based on hierarchy and status.

    Args:
        temp_dir: Temporary directory path
        project_id: Project ID (with prefix)
        epic_id: Epic ID (with prefix)
        feature_id: Feature ID (with prefix)
        task_id: Task ID (with prefix)
        status: Task status (determines subdirectory)

    Returns:
        Path: Expected task file path
    """
    # Extract raw IDs
    raw_project_id = extract_raw_id(project_id)
    raw_epic_id = extract_raw_id(epic_id)
    raw_feature_id = extract_raw_id(feature_id)

    # Determine task subdirectory based on status
    task_dir = "tasks-done" if status == "done" else "tasks-open"

    return (
        temp_dir
        / "planning"
        / "projects"
        / f"P-{raw_project_id}"
        / "epics"
        / f"E-{raw_epic_id}"
        / "features"
        / f"F-{raw_feature_id}"
        / task_dir
        / f"{task_id}.md"
    )


def build_standalone_task_path(
    temp_dir: Path,
    task_id: str,
    status: str = "open",
) -> Path:
    """Build expected standalone task file path based on status.

    Args:
        temp_dir: Temporary directory path
        task_id: Task ID (with prefix)
        status: Task status (determines subdirectory)

    Returns:
        Path: Expected standalone task file path
    """
    # Determine task subdirectory based on status
    task_dir = "tasks-done" if status == "done" else "tasks-open"

    return temp_dir / "planning" / task_dir / f"{task_id}.md"


async def create_standalone_task(
    client: Client,
    planning_root: str,
    title: str,
    priority: str = "normal",
    description: str = "",
) -> dict[str, str]:
    """Create a standalone task (no parent).

    Args:
        client: FastMCP client instance
        planning_root: Root path for planning files
        title: Task title
        priority: Task priority (high, normal, low)
        description: Task description

    Returns:
        dict: Task creation result data
    """
    task_params = {
        "kind": "task",
        "title": title,
        "projectRoot": planning_root,
        "priority": priority,
    }

    if description:
        task_params["description"] = description

    task_result = await client.call_tool("createObject", task_params)
    return task_result.data


async def create_mixed_task_environment(
    client: Client,
    planning_root: str,
    project_title: str = "Mixed Task Test Project",
) -> dict[str, Any]:
    """Create a mixed environment with both standalone and hierarchical tasks.

    Args:
        client: FastMCP client instance
        planning_root: Root path for planning files
        project_title: Title for the project

    Returns:
        dict: Contains all created IDs and task information
    """
    # Create hierarchy
    hierarchy = await create_test_hierarchy(client, planning_root, project_title)

    # Create hierarchical tasks with different priorities
    hierarchy_tasks = []
    for i, priority in enumerate(["high", "normal", "low"]):
        task_result = await create_task_with_priority(
            client,
            planning_root,
            hierarchy["feature_id"],
            f"Hierarchy Task {priority.capitalize()}",
            priority,
        )
        hierarchy_tasks.append(
            {
                "id": task_result["id"],
                "title": f"Hierarchy Task {priority.capitalize()}",
                "priority": priority,
                "type": "hierarchy",
                "parent": hierarchy["feature_id"],
            }
        )

    # Create standalone tasks with different priorities
    standalone_tasks = []
    for i, priority in enumerate(["high", "normal", "low"]):
        task_result = await create_standalone_task(
            client,
            planning_root,
            f"Standalone Task {priority.capitalize()}",
            priority,
            f"Standalone task with {priority} priority for testing",
        )
        standalone_tasks.append(
            {
                "id": task_result["id"],
                "title": f"Standalone Task {priority.capitalize()}",
                "priority": priority,
                "type": "standalone",
                "parent": None,
            }
        )

    return {
        "hierarchy": hierarchy,
        "hierarchy_tasks": hierarchy_tasks,
        "standalone_tasks": standalone_tasks,
        "all_tasks": hierarchy_tasks + standalone_tasks,
    }


async def create_large_mixed_task_environment(
    client: Client,
    planning_root: str,
    num_projects: int = 2,
    num_epics_per_project: int = 2,
    num_features_per_epic: int = 2,
    num_hierarchy_tasks_per_feature: int = 3,
    num_standalone_tasks: int = 10,
) -> dict[str, Any]:
    """Create a large mixed environment for performance testing.

    Args:
        client: FastMCP client instance
        planning_root: Root path for planning files
        num_projects: Number of projects to create
        num_epics_per_project: Number of epics per project
        num_features_per_epic: Number of features per epic
        num_hierarchy_tasks_per_feature: Number of hierarchy tasks per feature
        num_standalone_tasks: Number of standalone tasks

    Returns:
        dict: Contains all created objects and statistics
    """
    created_objects = {
        "projects": [],
        "epics": [],
        "features": [],
        "hierarchy_tasks": [],
        "standalone_tasks": [],
    }

    # Create projects and hierarchy
    for i in range(num_projects):
        project_result = await client.call_tool(
            "createObject",
            {
                "kind": "project",
                "title": f"Performance Test Project {i + 1}",
                "projectRoot": planning_root,
            },
        )
        project_id = project_result.data["id"]
        created_objects["projects"].append(project_id)

        # Create epics
        for j in range(num_epics_per_project):
            epic_result = await client.call_tool(
                "createObject",
                {
                    "kind": "epic",
                    "title": f"Performance Test Epic {i + 1}-{j + 1}",
                    "projectRoot": planning_root,
                    "parent": project_id,
                },
            )
            epic_id = epic_result.data["id"]
            created_objects["epics"].append(epic_id)

            # Create features
            for k in range(num_features_per_epic):
                feature_result = await client.call_tool(
                    "createObject",
                    {
                        "kind": "feature",
                        "title": f"Performance Test Feature {i + 1}-{j + 1}-{k + 1}",
                        "projectRoot": planning_root,
                        "parent": epic_id,
                    },
                )
                feature_id = feature_result.data["id"]
                created_objects["features"].append(feature_id)

                # Create hierarchy tasks
                for task_idx in range(num_hierarchy_tasks_per_feature):
                    priority = ["high", "normal", "low"][task_idx % 3]
                    task_result = await create_task_with_priority(
                        client,
                        planning_root,
                        feature_id,
                        f"Hierarchy Task {i + 1}-{j + 1}-{k + 1}-{task_idx + 1}",
                        priority,
                    )
                    created_objects["hierarchy_tasks"].append(
                        {
                            "id": task_result["id"],
                            "type": "hierarchy",
                            "priority": priority,
                            "parent": feature_id,
                        }
                    )

    # Create standalone tasks
    for i in range(num_standalone_tasks):
        priority = ["high", "normal", "low"][i % 3]
        task_result = await create_standalone_task(
            client,
            planning_root,
            f"Standalone Task {i + 1}",
            priority,
            f"Standalone task {i + 1} for performance testing",
        )
        created_objects["standalone_tasks"].append(
            {
                "id": task_result["id"],
                "type": "standalone",
                "priority": priority,
                "parent": None,
            }
        )

    # Calculate statistics
    stats = {
        "total_projects": len(created_objects["projects"]),
        "total_epics": len(created_objects["epics"]),
        "total_features": len(created_objects["features"]),
        "total_hierarchy_tasks": len(created_objects["hierarchy_tasks"]),
        "total_standalone_tasks": len(created_objects["standalone_tasks"]),
        "total_tasks": len(created_objects["hierarchy_tasks"])
        + len(created_objects["standalone_tasks"]),
    }

    return {
        "objects": created_objects,
        "stats": stats,
    }


def assert_mixed_task_consistency(
    all_tasks: list,
    expected_hierarchy_count: int,
    expected_standalone_count: int,
):
    """Assert that mixed task results have correct counts and structure.

    Args:
        all_tasks: List of task dictionaries from listBacklog
        expected_hierarchy_count: Expected number of hierarchy tasks
        expected_standalone_count: Expected number of standalone tasks
    """
    # Count task types
    hierarchy_count = 0
    standalone_count = 0

    for task in all_tasks:
        if task["parent"]:  # Has parent = hierarchy task
            hierarchy_count += 1
        else:  # No parent = standalone task
            standalone_count += 1

    assert (
        hierarchy_count == expected_hierarchy_count
    ), f"Expected {expected_hierarchy_count} hierarchy tasks, got {hierarchy_count}"
    assert (
        standalone_count == expected_standalone_count
    ), f"Expected {expected_standalone_count} standalone tasks, got {standalone_count}"

    # Verify total count
    total_expected = expected_hierarchy_count + expected_standalone_count
    assert (
        len(all_tasks) == total_expected
    ), f"Expected {total_expected} total tasks, got {len(all_tasks)}"

    # Verify all tasks have required structure
    for task in all_tasks:
        assert_task_structure(task)


def assert_task_type(task_data: dict, expected_type: str):
    """Assert that a task is of the expected type (standalone or hierarchy).

    Args:
        task_data: Task data dictionary
        expected_type: Expected type ("standalone" or "hierarchy")
    """
    if expected_type == "standalone":
        assert not task_data[
            "parent"
        ], f"Expected standalone task, but task has parent: {task_data['parent']}"
    elif expected_type == "hierarchy":
        assert task_data["parent"], "Expected hierarchy task, but task has no parent"
    else:
        raise ValueError(f"Invalid expected_type: {expected_type}")


def get_task_type(task_data: dict) -> str:
    """Get the type of a task (standalone or hierarchy).

    Args:
        task_data: Task data dictionary

    Returns:
        str: "standalone" or "hierarchy"
    """
    return "standalone" if not task_data["parent"] else "hierarchy"
