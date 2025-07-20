"""Realistic test data fixtures for scope-based claiming workflow tests.

Provides comprehensive test data structures for testing scope-based task claiming
across different project hierarchies, mixed task environments, and edge cases.
"""

from typing import Any

from fastmcp import Client


async def create_comprehensive_scope_test_environment(
    client: Client,
    planning_root: str,
) -> dict[str, Any]:
    """Create a comprehensive test environment for scope-based claiming tests.

    Creates a realistic multi-project structure with:
    - 2 projects with different complexity levels
    - Multiple epics per project with varied feature counts
    - Mixed priority tasks with prerequisite relationships
    - Both hierarchical and standalone tasks
    - Cross-system prerequisite dependencies

    Args:
        client: FastMCP client instance
        planning_root: Root path for planning files

    Returns:
        dict: Comprehensive mapping of all created objects and relationships
    """
    # Project 1: E-commerce Platform (complex hierarchy)
    ecommerce_project = await client.call_tool(
        "createObject",
        {
            "kind": "project",
            "title": "E-commerce Platform",
            "projectRoot": planning_root,
            "priority": "high",
        },
    )
    ecommerce_id = ecommerce_project.data["id"]

    # Epic 1.1: User Management
    user_mgmt_epic = await client.call_tool(
        "createObject",
        {
            "kind": "epic",
            "title": "User Management System",
            "projectRoot": planning_root,
            "parent": ecommerce_id,
            "priority": "high",
        },
    )
    user_mgmt_id = user_mgmt_epic.data["id"]

    # Feature 1.1.1: Authentication
    auth_feature = await client.call_tool(
        "createObject",
        {
            "kind": "feature",
            "title": "User Authentication",
            "projectRoot": planning_root,
            "parent": user_mgmt_id,
            "priority": "high",
        },
    )
    auth_feature_id = auth_feature.data["id"]

    # Feature 1.1.2: User Profiles
    profile_feature = await client.call_tool(
        "createObject",
        {
            "kind": "feature",
            "title": "User Profile Management",
            "projectRoot": planning_root,
            "parent": user_mgmt_id,
            "priority": "normal",
        },
    )
    profile_feature_id = profile_feature.data["id"]

    # Epic 1.2: Payment Processing
    payment_epic = await client.call_tool(
        "createObject",
        {
            "kind": "epic",
            "title": "Payment Processing",
            "projectRoot": planning_root,
            "parent": ecommerce_id,
            "priority": "high",
        },
    )
    payment_id = payment_epic.data["id"]

    # Feature 1.2.1: Checkout System
    checkout_feature = await client.call_tool(
        "createObject",
        {
            "kind": "feature",
            "title": "Checkout System",
            "projectRoot": planning_root,
            "parent": payment_id,
            "priority": "high",
        },
    )
    checkout_feature_id = checkout_feature.data["id"]

    # Project 2: Analytics Dashboard (simpler hierarchy)
    analytics_project = await client.call_tool(
        "createObject",
        {
            "kind": "project",
            "title": "Analytics Dashboard",
            "projectRoot": planning_root,
            "priority": "normal",
        },
    )
    analytics_id = analytics_project.data["id"]

    # Epic 2.1: Data Visualization
    dataviz_epic = await client.call_tool(
        "createObject",
        {
            "kind": "epic",
            "title": "Data Visualization",
            "projectRoot": planning_root,
            "parent": analytics_id,
            "priority": "normal",
        },
    )
    dataviz_id = dataviz_epic.data["id"]

    # Feature 2.1.1: Charts and Graphs
    charts_feature = await client.call_tool(
        "createObject",
        {
            "kind": "feature",
            "title": "Interactive Charts",
            "projectRoot": planning_root,
            "parent": dataviz_id,
            "priority": "normal",
        },
    )
    charts_feature_id = charts_feature.data["id"]

    # Create hierarchical tasks with varied priorities and prerequisites
    tasks = {}

    # Authentication tasks (foundational - no prerequisites)
    tasks["setup_auth_db"] = await _create_task(
        client, planning_root, auth_feature_id, "Setup authentication database schema", "high", []
    )

    tasks["implement_login"] = await _create_task(
        client,
        planning_root,
        auth_feature_id,
        "Implement login functionality",
        "high",
        [tasks["setup_auth_db"]["id"]],
    )

    tasks["implement_logout"] = await _create_task(
        client,
        planning_root,
        auth_feature_id,
        "Implement logout functionality",
        "normal",
        [tasks["implement_login"]["id"]],
    )

    # Profile tasks (depend on auth)
    tasks["create_profile_model"] = await _create_task(
        client,
        planning_root,
        profile_feature_id,
        "Create user profile data model",
        "normal",
        [tasks["setup_auth_db"]["id"]],
    )

    tasks["profile_edit_ui"] = await _create_task(
        client,
        planning_root,
        profile_feature_id,
        "Build profile editing interface",
        "low",
        [tasks["create_profile_model"]["id"], tasks["implement_login"]["id"]],
    )

    # Payment tasks (depend on auth)
    tasks["setup_payment_gateway"] = await _create_task(
        client,
        planning_root,
        checkout_feature_id,
        "Integrate payment gateway API",
        "high",
        [tasks["implement_login"]["id"]],
    )

    tasks["checkout_flow"] = await _create_task(
        client,
        planning_root,
        checkout_feature_id,
        "Implement checkout workflow",
        "high",
        [tasks["setup_payment_gateway"]["id"]],
    )

    # Analytics tasks (separate project)
    tasks["chart_library"] = await _create_task(
        client, planning_root, charts_feature_id, "Setup chart library integration", "normal", []
    )

    tasks["realtime_charts"] = await _create_task(
        client,
        planning_root,
        charts_feature_id,
        "Implement real-time chart updates",
        "low",
        [tasks["chart_library"]["id"]],
    )

    # Create standalone tasks with cross-system prerequisites
    tasks["database_setup"] = await _create_standalone_task(
        client, planning_root, "Setup production database infrastructure", "high", []
    )

    tasks["monitoring_config"] = await _create_standalone_task(
        client,
        planning_root,
        "Configure application monitoring",
        "normal",
        [tasks["database_setup"]["id"]],
    )

    tasks["security_audit"] = await _create_standalone_task(
        client,
        planning_root,
        "Conduct security audit",
        "high",
        [tasks["implement_login"]["id"], tasks["setup_payment_gateway"]["id"]],
    )

    tasks["performance_testing"] = await _create_standalone_task(
        client,
        planning_root,
        "Run performance testing suite",
        "normal",
        [tasks["checkout_flow"]["id"], tasks["realtime_charts"]["id"]],
    )

    # Create some tasks in different statuses for filtering tests
    tasks["completed_auth_task"] = await _create_task(
        client, planning_root, auth_feature_id, "Authentication API documentation", "low", []
    )

    # Mark some prerequisites as completed to create unblocked tasks
    # Directly set tasks to in-progress and then complete them

    # Complete setup_auth_db task
    await client.call_tool(
        "updateObject",
        {
            "id": tasks["setup_auth_db"]["id"],
            "projectRoot": planning_root,
            "yamlPatch": {"status": "in-progress"},
        },
    )
    await client.call_tool(
        "completeTask",
        {
            "taskId": tasks["setup_auth_db"]["id"],
            "projectRoot": planning_root,
            "summary": "Database schema created successfully",
            "filesChanged": ["schema.sql", "migrations/001_auth.sql"],
        },
    )

    # Complete database_setup task
    await client.call_tool(
        "updateObject",
        {
            "id": tasks["database_setup"]["id"],
            "projectRoot": planning_root,
            "yamlPatch": {"status": "in-progress"},
        },
    )
    await client.call_tool(
        "completeTask",
        {
            "taskId": tasks["database_setup"]["id"],
            "projectRoot": planning_root,
            "summary": "Production database configured",
            "filesChanged": ["docker-compose.yml", "config/database.yml"],
        },
    )

    # Complete auth documentation task
    await client.call_tool(
        "updateObject",
        {
            "id": tasks["completed_auth_task"]["id"],
            "projectRoot": planning_root,
            "yamlPatch": {"status": "in-progress"},
        },
    )
    await client.call_tool(
        "completeTask",
        {
            "taskId": tasks["completed_auth_task"]["id"],
            "projectRoot": planning_root,
            "summary": "API documentation completed",
            "filesChanged": ["docs/auth-api.md"],
        },
    )

    # Complete implement_login task to unblock payment tasks
    await client.call_tool(
        "updateObject",
        {
            "id": tasks["implement_login"]["id"],
            "projectRoot": planning_root,
            "yamlPatch": {"status": "in-progress"},
        },
    )
    await client.call_tool(
        "completeTask",
        {
            "taskId": tasks["implement_login"]["id"],
            "projectRoot": planning_root,
            "summary": "Login functionality implemented",
            "filesChanged": ["auth/login.py", "templates/login.html"],
        },
    )

    return {
        "projects": {
            "ecommerce": {
                "id": ecommerce_id,
                "title": "E-commerce Platform",
                "epics": {
                    "user_mgmt": {
                        "id": user_mgmt_id,
                        "title": "User Management System",
                        "features": {
                            "auth": {
                                "id": auth_feature_id,
                                "title": "User Authentication",
                                "tasks": [
                                    tasks["setup_auth_db"]["id"],
                                    tasks["implement_login"]["id"],
                                    tasks["implement_logout"]["id"],
                                    tasks["completed_auth_task"]["id"],
                                ],
                            },
                            "profile": {
                                "id": profile_feature_id,
                                "title": "User Profile Management",
                                "tasks": [
                                    tasks["create_profile_model"]["id"],
                                    tasks["profile_edit_ui"]["id"],
                                ],
                            },
                        },
                    },
                    "payment": {
                        "id": payment_id,
                        "title": "Payment Processing",
                        "features": {
                            "checkout": {
                                "id": checkout_feature_id,
                                "title": "Checkout System",
                                "tasks": [
                                    tasks["setup_payment_gateway"]["id"],
                                    tasks["checkout_flow"]["id"],
                                ],
                            },
                        },
                    },
                },
            },
            "analytics": {
                "id": analytics_id,
                "title": "Analytics Dashboard",
                "epics": {
                    "dataviz": {
                        "id": dataviz_id,
                        "title": "Data Visualization",
                        "features": {
                            "charts": {
                                "id": charts_feature_id,
                                "title": "Interactive Charts",
                                "tasks": [
                                    tasks["chart_library"]["id"],
                                    tasks["realtime_charts"]["id"],
                                ],
                            },
                        },
                    },
                },
            },
        },
        "standalone_tasks": [
            tasks["database_setup"]["id"],
            tasks["monitoring_config"]["id"],
            tasks["security_audit"]["id"],
            tasks["performance_testing"]["id"],
        ],
        "all_tasks": tasks,
        "completed_tasks": [
            tasks["setup_auth_db"]["id"],
            tasks["database_setup"]["id"],
            tasks["completed_auth_task"]["id"],
            tasks["implement_login"]["id"],
        ],
        "unblocked_tasks": [
            # These should be claimable after prerequisites are done
            tasks["create_profile_model"]["id"],  # setup_auth_db completed
            tasks["setup_payment_gateway"]["id"],  # implement_login completed
            tasks["monitoring_config"]["id"],  # database_setup completed
            tasks["chart_library"]["id"],  # no prerequisites
        ],
    }


async def create_empty_scope_test_environment(
    client: Client,
    planning_root: str,
) -> dict[str, Any]:
    """Create test environment with valid scopes but no eligible tasks.

    Args:
        client: FastMCP client instance
        planning_root: Root path for planning files

    Returns:
        dict: Mapping of created objects with no eligible tasks
    """
    # Create project structure but with all tasks blocked or completed
    project = await client.call_tool(
        "createObject",
        {
            "kind": "project",
            "title": "Empty Scope Test Project",
            "projectRoot": planning_root,
        },
    )
    project_id = project.data["id"]

    epic = await client.call_tool(
        "createObject",
        {
            "kind": "epic",
            "title": "Empty Epic",
            "projectRoot": planning_root,
            "parent": project_id,
        },
    )
    epic_id = epic.data["id"]

    feature = await client.call_tool(
        "createObject",
        {
            "kind": "feature",
            "title": "Empty Feature",
            "projectRoot": planning_root,
            "parent": epic_id,
        },
    )
    feature_id = feature.data["id"]

    # Create tasks but make them all blocked by setting them to in-progress
    # Create a task and immediately set it to in-progress (not claimable)
    blocked_task = await _create_task(
        client,
        planning_root,
        feature_id,
        "Task already in progress",
        "high",
        [],
    )

    # Set the task to in-progress so it can't be claimed
    await client.call_tool(
        "updateObject",
        {
            "id": blocked_task["id"],
            "projectRoot": planning_root,
            "yamlPatch": {"status": "in-progress"},
        },
    )

    # Create a task and complete it
    completed_task = await _create_task(
        client, planning_root, feature_id, "Task to complete", "normal", []
    )

    # Set task to in-progress then complete it
    await client.call_tool(
        "updateObject",
        {
            "id": completed_task["id"],
            "projectRoot": planning_root,
            "yamlPatch": {"status": "in-progress"},
        },
    )
    await client.call_tool(
        "completeTask",
        {
            "taskId": completed_task["id"],
            "projectRoot": planning_root,
            "summary": "Completed for testing",
            "filesChanged": [],
        },
    )

    return {
        "project_id": project_id,
        "epic_id": epic_id,
        "feature_id": feature_id,
        "blocked_task_id": blocked_task["id"],
        "completed_task_id": completed_task["id"],
    }


async def create_prerequisite_chain_test_environment(
    client: Client,
    planning_root: str,
) -> dict[str, Any]:
    """Create test environment with complex prerequisite chains across scopes.

    Args:
        client: FastMCP client instance
        planning_root: Root path for planning files

    Returns:
        dict: Mapping of tasks with cross-scope prerequisite relationships
    """
    # Create hierarchy
    project = await client.call_tool(
        "createObject",
        {
            "kind": "project",
            "title": "Prerequisite Chain Project",
            "projectRoot": planning_root,
        },
    )
    project_id = project.data["id"]

    epic1 = await client.call_tool(
        "createObject",
        {
            "kind": "epic",
            "title": "Foundation Epic",
            "projectRoot": planning_root,
            "parent": project_id,
        },
    )
    epic1_id = epic1.data["id"]

    epic2 = await client.call_tool(
        "createObject",
        {
            "kind": "epic",
            "title": "Dependent Epic",
            "projectRoot": planning_root,
            "parent": project_id,
        },
    )
    epic2_id = epic2.data["id"]

    feature1 = await client.call_tool(
        "createObject",
        {
            "kind": "feature",
            "title": "Foundation Feature",
            "projectRoot": planning_root,
            "parent": epic1_id,
        },
    )
    feature1_id = feature1.data["id"]

    feature2 = await client.call_tool(
        "createObject",
        {
            "kind": "feature",
            "title": "Dependent Feature",
            "projectRoot": planning_root,
            "parent": epic2_id,
        },
    )
    feature2_id = feature2.data["id"]

    # Create tasks with cross-scope dependencies
    foundation_task = await _create_task(
        client, planning_root, feature1_id, "Foundation task", "high", []
    )

    intermediate_task = await _create_task(
        client, planning_root, feature1_id, "Intermediate task", "normal", [foundation_task["id"]]
    )

    # Task in different feature that depends on task from feature1
    cross_feature_task = await _create_task(
        client,
        planning_root,
        feature2_id,
        "Cross-feature dependent task",
        "normal",
        [intermediate_task["id"]],
    )

    # Standalone task that depends on hierarchical task
    standalone_dependent = await _create_standalone_task(
        client,
        planning_root,
        "Standalone task depending on hierarchy",
        "high",
        [foundation_task["id"]],
    )

    # Complete foundation task to unblock the chain
    # Set task to in-progress then complete it
    await client.call_tool(
        "updateObject",
        {
            "id": foundation_task["id"],
            "projectRoot": planning_root,
            "yamlPatch": {"status": "in-progress"},
        },
    )
    await client.call_tool(
        "completeTask",
        {
            "taskId": foundation_task["id"],
            "projectRoot": planning_root,
            "summary": "Foundation completed",
            "filesChanged": ["foundation.py"],
        },
    )

    return {
        "project_id": project_id,
        "epic1_id": epic1_id,
        "epic2_id": epic2_id,
        "feature1_id": feature1_id,
        "feature2_id": feature2_id,
        "foundation_task_id": foundation_task["id"],
        "intermediate_task_id": intermediate_task["id"],
        "cross_feature_task_id": cross_feature_task["id"],
        "standalone_dependent_id": standalone_dependent["id"],
    }


async def _create_task(
    client: Client,
    planning_root: str,
    parent_id: str,
    title: str,
    priority: str = "normal",
    prerequisites: list[str] | None = None,
) -> dict[str, str]:
    """Create a hierarchical task with specified parameters.

    Args:
        client: FastMCP client instance
        planning_root: Root path for planning files
        parent_id: Parent feature ID
        title: Task title
        priority: Task priority (high, normal, low)
        prerequisites: List of prerequisite task IDs

    Returns:
        dict: Task creation result data
    """
    task_params: dict[str, Any] = {
        "kind": "task",
        "title": title,
        "projectRoot": planning_root,
        "parent": parent_id,
        "priority": priority,
    }

    if prerequisites:
        task_params["prerequisites"] = prerequisites

    task_result = await client.call_tool("createObject", task_params)
    return task_result.data


async def _create_standalone_task(
    client: Client,
    planning_root: str,
    title: str,
    priority: str = "normal",
    prerequisites: list[str] | None = None,
) -> dict[str, str]:
    """Create a standalone task with specified parameters.

    Args:
        client: FastMCP client instance
        planning_root: Root path for planning files
        title: Task title
        priority: Task priority (high, normal, low)
        prerequisites: List of prerequisite task IDs

    Returns:
        dict: Task creation result data
    """
    task_params: dict[str, Any] = {
        "kind": "task",
        "title": title,
        "projectRoot": planning_root,
        "priority": priority,
    }

    if prerequisites:
        task_params["prerequisites"] = prerequisites

    task_result = await client.call_tool("createObject", task_params)
    return task_result.data
