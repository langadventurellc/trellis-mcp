"""Integration tests for Trellis MCP server.

Tests the complete server functionality by starting a FastMCP server
and hitting it with a FastMCP test client to verify end-to-end behavior.
"""

import pytest
from fastmcp import Client

from trellis_mcp.server import create_server
from trellis_mcp.settings import Settings


@pytest.mark.asyncio
async def test_server_startup_and_connectivity(temp_dir):
    """Test server starts and responds to basic connectivity checks."""
    # Create settings with temporary planning directory
    settings = Settings(
        planning_root=temp_dir / "planning",
        debug_mode=True,
        log_level="DEBUG",
    )

    # Create server instance
    server = create_server(settings)

    # Test connectivity using in-memory transport
    async with Client(server) as client:
        # Basic connectivity check
        await client.ping()

        # Verify client reports connected
        assert client.is_connected()


@pytest.mark.asyncio
async def test_health_check_tool_functionality(temp_dir):
    """Test health check tool returns expected status information."""
    # Create settings with temporary planning directory
    settings = Settings(
        planning_root=temp_dir / "planning",
        schema_version="1.0",
    )

    # Create server instance
    server = create_server(settings)

    # Test health check tool
    async with Client(server) as client:
        result = await client.call_tool("health_check")

        # Verify result structure and content
        assert result.data is not None
        assert result.data["status"] == "healthy"
        assert result.data["server"] == "Trellis MCP Server"
        assert result.data["schema_version"] == "1.0"
        assert result.data["planning_root"] == str(temp_dir / "planning")


@pytest.mark.asyncio
async def test_server_info_resource_accessibility(temp_dir):
    """Test server info resource provides correct configuration information."""
    # Create settings with custom configuration
    settings = Settings(
        planning_root=temp_dir / "planning",
        host="127.0.0.1",
        port=8080,
        log_level="INFO",
        debug_mode=False,
    )

    # Create server instance
    server = create_server(settings)

    # Test server info resource
    async with Client(server) as client:
        # List available resources
        resources = await client.list_resources()
        resource_uris = [str(resource.uri) for resource in resources]
        assert "info://server" in resource_uris

        # Read server info resource
        info = await client.read_resource("info://server")
        assert len(info) > 0

        # Verify info contains expected server configuration
        info_data = info[0]
        assert hasattr(info_data, "text") or hasattr(info_data, "data")


@pytest.mark.asyncio
async def test_available_tools_and_resources(temp_dir):
    """Test server exposes expected tools and resources."""
    # Create settings
    settings = Settings(planning_root=temp_dir / "planning")

    # Create server instance
    server = create_server(settings)

    # Test available tools and resources
    async with Client(server) as client:
        # List available tools
        tools = await client.list_tools()
        tool_names = [tool.name for tool in tools]

        # Verify expected tools are available
        assert "health_check" in tool_names

        # List available resources
        resources = await client.list_resources()
        resource_uris = [str(resource.uri) for resource in resources]

        # Verify expected resources are available
        assert "info://server" in resource_uris


@pytest.mark.asyncio
async def test_server_configuration_consistency(temp_dir):
    """Test server configuration is consistently reported across tools and resources."""
    # Create settings with specific configuration
    planning_root = temp_dir / "planning"
    settings = Settings(
        planning_root=planning_root,
        schema_version="1.0",
        host="localhost",
        port=9000,
        log_level="WARNING",
        debug_mode=True,
    )

    # Create server instance
    server = create_server(settings)

    # Test configuration consistency
    async with Client(server) as client:
        # Get configuration from health check tool
        health_result = await client.call_tool("health_check")
        health_data = health_result.data

        # Verify consistent planning root across both sources
        assert health_data["planning_root"] == str(planning_root)
        assert health_data["schema_version"] == "1.0"
        assert health_data["server"] == "Trellis MCP Server"


@pytest.mark.asyncio
async def test_concurrent_client_connections(temp_dir):
    """Test server handles multiple concurrent client connections."""
    import asyncio

    # Create settings
    settings = Settings(planning_root=temp_dir / "planning")

    # Create server instance
    server = create_server(settings)

    async def client_task():
        """Single client task for concurrent testing."""
        async with Client(server) as client:
            await client.ping()
            result = await client.call_tool("health_check")
            return result.data["status"]

    # Create multiple concurrent client connections
    tasks = [client_task() for _ in range(5)]
    results = await asyncio.gather(*tasks)

    # Verify all connections succeeded
    assert all(status == "healthy" for status in results)
    assert len(results) == 5


@pytest.mark.asyncio
async def test_create_duplicate_title_tasks_generates_unique_ids(temp_dir):
    """Test creating two tasks with identical titles generates unique IDs and correct paths."""
    # Create settings with temporary planning directory
    settings = Settings(
        planning_root=temp_dir / "planning",
        debug_mode=True,
        log_level="DEBUG",
    )

    # Create server instance
    server = create_server(settings)

    async with Client(server) as client:
        # First, create the project hierarchy: project → epic → feature

        # Create project
        project_result = await client.call_tool(
            "createObject",
            {
                "kind": "project",
                "title": "Test Project",
                "projectRoot": str(temp_dir / "planning"),
            },
        )
        project_id = project_result.data["id"]

        # Create epic under project
        epic_result = await client.call_tool(
            "createObject",
            {
                "kind": "epic",
                "title": "Test Epic",
                "projectRoot": str(temp_dir / "planning"),
                "parent": project_id,
            },
        )
        epic_id = epic_result.data["id"]

        # Create feature under epic
        feature_result = await client.call_tool(
            "createObject",
            {
                "kind": "feature",
                "title": "Test Feature",
                "projectRoot": str(temp_dir / "planning"),
                "parent": epic_id,
            },
        )
        feature_id = feature_result.data["id"]

        # Now create two tasks with identical titles under the same feature
        task_title = "Implement Authentication"

        # Create first task
        task1_result = await client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": task_title,
                "projectRoot": str(temp_dir / "planning"),
                "parent": feature_id,
            },
        )

        # Create second task with same title
        task2_result = await client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": task_title,
                "projectRoot": str(temp_dir / "planning"),
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
        # Extract raw IDs (without prefixes) for path construction
        raw_project_id = project_id.removeprefix("P-")
        raw_epic_id = epic_id.removeprefix("E-")
        raw_feature_id = feature_id.removeprefix("F-")

        planning_root = temp_dir / "planning"
        expected_task1_path = (
            planning_root
            / "projects"
            / f"P-{raw_project_id}"
            / "epics"
            / f"E-{raw_epic_id}"
            / "features"
            / f"F-{raw_feature_id}"
            / "tasks-open"
            / f"{task1_id}.md"
        )
        expected_task2_path = (
            planning_root
            / "projects"
            / f"P-{raw_project_id}"
            / "epics"
            / f"E-{raw_epic_id}"
            / "features"
            / f"F-{raw_feature_id}"
            / "tasks-open"
            / f"{task2_id}.md"
        )

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


@pytest.mark.asyncio
async def test_crud_epic_feature_tasks_workflow_with_yaml_verification(
    temp_dir,
):
    """Integration test: create epic → feature → tasks; list backlog; update statuses."""
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

        # Verify that attempting to set task status to done via updateObject is rejected
        from fastmcp.exceptions import ToolError

        try:
            await client.call_tool(
                "updateObject",
                {
                    "kind": "task",
                    "id": task3_id,
                    "projectRoot": planning_root,
                    "yamlPatch": {"status": "done"},
                },
            )
            assert False, "Expected updateObject to reject setting task status to done"
        except ToolError as e:
            assert "updateObject cannot set a Task to 'done'; use completeTask instead." in str(e)

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
        raw_project_id = project_id.removeprefix("P-")
        raw_epic_id = epic_id.removeprefix("E-")
        raw_feature_id = feature_id.removeprefix("F-")

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


@pytest.mark.asyncio
async def test_two_agents_claim_tasks_sequentially_verify_priority_order(
    temp_dir,
):
    """Integration test: two agents claim tasks sequentially, verify priority ordering."""
    # Create settings with temporary planning directory
    settings = Settings(
        planning_root=temp_dir / "planning",
        debug_mode=True,
        log_level="DEBUG",
    )

    # Create server instance
    server = create_server(settings)
    planning_root = str(temp_dir / "planning")

    # Setup: Create test hierarchy with mixed priority tasks
    async with Client(server) as setup_client:
        # Create project
        project_result = await setup_client.call_tool(
            "createObject",
            {
                "kind": "project",
                "title": "Multi-Agent Priority Test Project",
                "projectRoot": planning_root,
            },
        )
        project_id = project_result.data["id"]

        # Create epic
        epic_result = await setup_client.call_tool(
            "createObject",
            {
                "kind": "epic",
                "title": "Multi-Agent Test Epic",
                "projectRoot": planning_root,
                "parent": project_id,
            },
        )
        epic_id = epic_result.data["id"]

        # Create feature
        feature_result = await setup_client.call_tool(
            "createObject",
            {
                "kind": "feature",
                "title": "Multi-Agent Test Feature",
                "projectRoot": planning_root,
                "parent": epic_id,
            },
        )
        feature_id = feature_result.data["id"]

        # Create multiple tasks with different priorities
        # High priority tasks (should be claimed first)
        high_task1_result = await setup_client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "High Priority Task 1",
                "projectRoot": planning_root,
                "parent": feature_id,
                "priority": "high",
            },
        )
        high_task1_id = high_task1_result.data["id"]

        high_task2_result = await setup_client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "High Priority Task 2",
                "projectRoot": planning_root,
                "parent": feature_id,
                "priority": "high",
            },
        )
        high_task2_id = high_task2_result.data["id"]

        # Normal priority task
        normal_task_result = await setup_client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Normal Priority Task",
                "projectRoot": planning_root,
                "parent": feature_id,
                "priority": "normal",
            },
        )
        normal_task_id = normal_task_result.data["id"]

        # Low priority task
        low_task_result = await setup_client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Low Priority Task",
                "projectRoot": planning_root,
                "parent": feature_id,
                "priority": "low",
            },
        )
        low_task_id = low_task_result.data["id"]

    # Main test: Two agents claiming tasks sequentially
    claimed_tasks = []

    # Agent 1 claims first task
    async with Client(server) as agent1:
        result1 = await agent1.call_tool(
            "claimNextTask", {"projectRoot": planning_root, "worktree": "agent1-workspace"}
        )
        claimed_task1 = result1.data["task"]
        claimed_tasks.append((claimed_task1, "agent1"))

        # Verify agent1 claimed a high priority task
        assert claimed_task1["priority"] == "high"
        assert result1.data["worktree"] == "agent1-workspace"
        assert result1.data["claimed_status"] == "in-progress"

    # Agent 2 claims second task
    async with Client(server) as agent2:
        result2 = await agent2.call_tool(
            "claimNextTask", {"projectRoot": planning_root, "worktree": "agent2-workspace"}
        )
        claimed_task2 = result2.data["task"]
        claimed_tasks.append((claimed_task2, "agent2"))

        # Verify agent2 claimed the remaining high priority task
        assert claimed_task2["priority"] == "high"
        assert result2.data["worktree"] == "agent2-workspace"
        assert result2.data["claimed_status"] == "in-progress"

    # Agent 1 claims third task
    async with Client(server) as agent1:
        result3 = await agent1.call_tool(
            "claimNextTask", {"projectRoot": planning_root, "worktree": "agent1-workspace"}
        )
        claimed_task3 = result3.data["task"]
        claimed_tasks.append((claimed_task3, "agent1"))

        # Verify agent1 claimed the normal priority task (no more high priority available)
        assert claimed_task3["priority"] == "normal"

    # Agent 2 claims fourth task
    async with Client(server) as agent2:
        result4 = await agent2.call_tool(
            "claimNextTask", {"projectRoot": planning_root, "worktree": "agent2-workspace"}
        )
        claimed_task4 = result4.data["task"]
        claimed_tasks.append((claimed_task4, "agent2"))

        # Verify agent2 claimed the low priority task (last remaining)
        assert claimed_task4["priority"] == "low"

    # Verify overall priority ordering: high → high → normal → low
    priorities = [task["priority"] for task, _ in claimed_tasks]
    assert priorities == ["high", "high", "normal", "low"]

    # Verify all expected tasks were claimed
    claimed_ids = {task["id"] for task, _ in claimed_tasks}
    expected_ids = {high_task1_id, high_task2_id, normal_task_id, low_task_id}
    assert claimed_ids == expected_ids

    # Verify each task was claimed by exactly one agent
    assert len(claimed_tasks) == 4
    assert len(set(task["id"] for task, _ in claimed_tasks)) == 4

    # Verify alternating agent assignments
    agents = [agent for _, agent in claimed_tasks]
    assert agents == ["agent1", "agent2", "agent1", "agent2"]

    # Verify no more tasks available
    async with Client(server) as agent1:
        with pytest.raises(Exception) as exc_info:
            await agent1.call_tool("claimNextTask", {"projectRoot": planning_root})
        assert "No open tasks available" in str(exc_info.value)
