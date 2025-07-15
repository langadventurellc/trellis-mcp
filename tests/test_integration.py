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


@pytest.mark.asyncio
async def test_claim_next_task_returns_high_priority_before_normal(temp_dir):
    """Integration test: create two tasks + satisfied prereqs, expect high priority first."""
    # Create settings with temporary planning directory
    settings = Settings(
        planning_root=temp_dir / "planning",
        debug_mode=True,
        log_level="DEBUG",
    )

    # Create server instance
    server = create_server(settings)
    planning_root = str(temp_dir / "planning")

    # Setup: Create test hierarchy with high and normal priority tasks
    async with Client(server) as setup_client:
        # Create project
        project_result = await setup_client.call_tool(
            "createObject",
            {
                "kind": "project",
                "title": "Priority Test Project",
                "projectRoot": planning_root,
            },
        )
        project_id = project_result.data["id"]

        # Create epic
        epic_result = await setup_client.call_tool(
            "createObject",
            {
                "kind": "epic",
                "title": "Priority Test Epic",
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
                "title": "Priority Test Feature",
                "projectRoot": planning_root,
                "parent": epic_id,
            },
        )
        feature_id = feature_result.data["id"]

        # Create normal priority task (created first, should be older)
        await setup_client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Normal Priority Task",
                "projectRoot": planning_root,
                "parent": feature_id,
                "priority": "normal",
            },
        )

        # Create high priority task (created second, should be newer)
        high_task_result = await setup_client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "High Priority Task",
                "projectRoot": planning_root,
                "parent": feature_id,
                "priority": "high",
            },
        )
        high_task_id = high_task_result.data["id"]

    # Test: Call claimNextTask and verify high priority task is returned first
    async with Client(server) as client:
        result = await client.call_tool("claimNextTask", {"projectRoot": planning_root})

        # Verify the high priority task was claimed first (despite being created later)
        claimed_task = result.data["task"]
        assert claimed_task["priority"] == "high"
        assert claimed_task["title"] == "High Priority Task"
        assert claimed_task["id"] == high_task_id

        # Verify response structure
        assert result.data["claimed_status"] == "in-progress"
        assert "file_path" in result.data

        # Verify the task status was updated
        assert claimed_task["status"] == "in-progress"


@pytest.mark.asyncio
async def test_two_sequential_claims_with_different_worktree_values_persist_to_disk(temp_dir):
    """Integration test: two sequential claimNextTask calls with different worktreePath values.

    Verify each task gets unique worktree stamp and persists to disk.
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

    # Setup: Create test hierarchy with two tasks
    async with Client(server) as setup_client:
        # Create project
        project_result = await setup_client.call_tool(
            "createObject",
            {
                "kind": "project",
                "title": "Worktree Test Project",
                "projectRoot": planning_root,
            },
        )
        project_id = project_result.data["id"]

        # Create epic
        epic_result = await setup_client.call_tool(
            "createObject",
            {
                "kind": "epic",
                "title": "Worktree Test Epic",
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
                "title": "Worktree Test Feature",
                "projectRoot": planning_root,
                "parent": epic_id,
            },
        )
        feature_id = feature_result.data["id"]

        # Create first task
        task1_result = await setup_client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "First Task",
                "projectRoot": planning_root,
                "parent": feature_id,
                "priority": "high",
            },
        )
        task1_id = task1_result.data["id"]

        # Create second task
        task2_result = await setup_client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Second Task",
                "projectRoot": planning_root,
                "parent": feature_id,
                "priority": "normal",
            },
        )
        task2_id = task2_result.data["id"]

    # Test: Two sequential claimNextTask calls with different worktree values

    # First claim with worktree="workspace-1"
    async with Client(server) as client1:
        result1 = await client1.call_tool(
            "claimNextTask", {"projectRoot": planning_root, "worktree": "workspace-1"}
        )
        claimed_task1 = result1.data["task"]

        # Verify first task claimed (high priority first)
        assert claimed_task1["id"] == task1_id
        assert claimed_task1["priority"] == "high"
        assert claimed_task1["status"] == "in-progress"

        # Verify API response contains worktree value
        assert result1.data["worktree"] == "workspace-1"

    # Second claim with worktree="workspace-2"
    async with Client(server) as client2:
        result2 = await client2.call_tool(
            "claimNextTask", {"projectRoot": planning_root, "worktree": "workspace-2"}
        )
        claimed_task2 = result2.data["task"]

        # Verify second task claimed (normal priority second)
        assert claimed_task2["id"] == task2_id
        assert claimed_task2["priority"] == "normal"
        assert claimed_task2["status"] == "in-progress"

        # Verify API response contains different worktree value
        assert result2.data["worktree"] == "workspace-2"

    # Critical: Verify worktree values persist to disk in YAML files
    planning_path = temp_dir / "planning"

    # Extract raw IDs for path construction
    raw_project_id = project_id.removeprefix("P-")
    raw_epic_id = epic_id.removeprefix("E-")
    raw_feature_id = feature_id.removeprefix("F-")

    # Construct expected task file paths
    task_base_path = (
        planning_path
        / "projects"
        / f"P-{raw_project_id}"
        / "epics"
        / f"E-{raw_epic_id}"
        / "features"
        / f"F-{raw_feature_id}"
        / "tasks-open"
    )

    task1_file = task_base_path / f"{task1_id}.md"
    task2_file = task_base_path / f"{task2_id}.md"

    # Verify both task files exist
    assert task1_file.exists(), f"Task 1 file not found: {task1_file}"
    assert task2_file.exists(), f"Task 2 file not found: {task2_file}"

    # Read task file contents and verify worktree values persist in YAML
    task1_content = task1_file.read_text()
    task2_content = task2_file.read_text()

    # Verify task1 YAML contains worktree: "workspace-1"
    assert 'worktree: "workspace-1"' in task1_content or "worktree: workspace-1" in task1_content
    assert f"id: {task1_id}" in task1_content
    assert "status: in-progress" in task1_content

    # Verify task2 YAML contains worktree: "workspace-2"
    assert 'worktree: "workspace-2"' in task2_content or "worktree: workspace-2" in task2_content
    assert f"id: {task2_id}" in task2_content
    assert "status: in-progress" in task2_content

    # Verify each task has unique worktree stamp
    assert (
        'worktree: "workspace-1"' not in task2_content
        and "worktree: workspace-1" not in task2_content
    )
    assert (
        'worktree: "workspace-2"' not in task1_content
        and "worktree: workspace-2" not in task1_content
    )


@pytest.mark.asyncio
async def test_getNextReviewableTask_integration_with_mixed_status_tasks(temp_dir):
    """Integration test: create sample repo with mixed status tasks.

    Call getNextReviewableTask RPC via FastMCP test client, assert correct task ID returned.
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

    # Setup: Create test hierarchy with mixed status tasks
    async with Client(server) as setup_client:
        # Create project
        project_result = await setup_client.call_tool(
            "createObject",
            {
                "kind": "project",
                "title": "Review Test Project",
                "projectRoot": planning_root,
            },
        )
        project_id = project_result.data["id"]

        # Create epic
        epic_result = await setup_client.call_tool(
            "createObject",
            {
                "kind": "epic",
                "title": "Review Test Epic",
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
                "title": "Review Test Feature",
                "projectRoot": planning_root,
                "parent": epic_id,
            },
        )
        feature_id = feature_result.data["id"]

        # Create tasks with mixed statuses
        # 1. Open task (should not be returned)
        await setup_client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Open Task",
                "projectRoot": planning_root,
                "parent": feature_id,
                "priority": "normal",
            },
        )

        # 2. In-progress task (should not be returned)
        in_progress_task_result = await setup_client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "In Progress Task",
                "projectRoot": planning_root,
                "parent": feature_id,
                "priority": "high",
            },
        )
        in_progress_task_id = in_progress_task_result.data["id"]

        # Update to in-progress status
        await setup_client.call_tool(
            "updateObject",
            {
                "kind": "task",
                "id": in_progress_task_id,
                "projectRoot": planning_root,
                "yamlPatch": {"status": "in-progress"},
            },
        )

        # 3. Review task with high priority (should be returned since it will be updated first)
        review_task_high_result = await setup_client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Review Task High Priority",
                "projectRoot": planning_root,
                "parent": feature_id,
                "priority": "high",
            },
        )
        review_task_high_id = review_task_high_result.data["id"]

        # Update to in-progress status first, then review
        await setup_client.call_tool(
            "updateObject",
            {
                "kind": "task",
                "id": review_task_high_id,
                "projectRoot": planning_root,
                "yamlPatch": {"status": "in-progress"},
            },
        )

        await setup_client.call_tool(
            "updateObject",
            {
                "kind": "task",
                "id": review_task_high_id,
                "projectRoot": planning_root,
                "yamlPatch": {"status": "review"},
            },
        )

        # 4. Review task with normal priority (returned second due to newer timestamp)
        review_task_normal_result = await setup_client.call_tool(
            "createObject",
            {
                "kind": "task",
                "title": "Review Task Normal Priority",
                "projectRoot": planning_root,
                "parent": feature_id,
                "priority": "normal",
            },
        )
        review_task_normal_id = review_task_normal_result.data["id"]

        # Update to in-progress status first, then review
        await setup_client.call_tool(
            "updateObject",
            {
                "kind": "task",
                "id": review_task_normal_id,
                "projectRoot": planning_root,
                "yamlPatch": {"status": "in-progress"},
            },
        )

        await setup_client.call_tool(
            "updateObject",
            {
                "kind": "task",
                "id": review_task_normal_id,
                "projectRoot": planning_root,
                "yamlPatch": {"status": "review"},
            },
        )

    # Test 1: Call getNextReviewableTask and verify high priority review task is returned
    async with Client(server) as client:
        result = await client.call_tool(
            "getNextReviewableTask",
            {
                "projectRoot": planning_root,
            },
        )

        # Verify response structure
        assert result.data is not None
        assert "task" in result.data
        task_data = result.data["task"]

        # Verify correct task returned (high priority review task due to oldest update timestamp)
        assert task_data is not None
        assert task_data["id"] == review_task_high_id
        assert task_data["title"] == "Review Task High Priority"
        assert task_data["status"] == "review"
        assert task_data["priority"] == "high"
        assert task_data["parent"] == feature_id

        # Verify additional required fields
        assert "file_path" in task_data
        assert "created" in task_data
        assert "updated" in task_data

        # Verify file_path is a valid path string
        assert task_data["file_path"].endswith(f"{review_task_high_id}.md")

    # Test 2: Complete the high priority task and verify normal priority task is returned next
    async with Client(server) as client:
        # Mark high priority task as done using completeTask
        await client.call_tool(
            "completeTask",
            {
                "taskId": review_task_high_id,
                "projectRoot": planning_root,
            },
        )

        # Now call getNextReviewableTask again
        result = await client.call_tool(
            "getNextReviewableTask",
            {
                "projectRoot": planning_root,
            },
        )

        # Verify normal priority review task is now returned
        assert result.data is not None
        task_data = result.data["task"]
        assert task_data is not None
        assert task_data["id"] == review_task_normal_id
        assert task_data["title"] == "Review Task Normal Priority"
        assert task_data["priority"] == "normal"

    # Test 3: Complete remaining review task and verify no more reviewable tasks
    async with Client(server) as client:
        # Complete the normal priority task
        await client.call_tool(
            "completeTask",
            {
                "taskId": review_task_normal_id,
                "projectRoot": planning_root,
            },
        )

        # Call getNextReviewableTask - should return None
        result = await client.call_tool(
            "getNextReviewableTask",
            {
                "projectRoot": planning_root,
            },
        )

        # Verify no reviewable tasks remaining
        assert result.data is not None
        assert result.data["task"] is None


@pytest.mark.asyncio
async def test_listBacklog_comprehensive_integration_with_hierarchy_and_sorting(
    temp_dir,
):
    """S-09 Integration test: comprehensive sample hierarchy, call RPC, assert correct list & order.

    Creates a complex project hierarchy with multiple projects, epics, features, and tasks.
    Tests all listBacklog filtering combinations and validates comprehensive sorting behavior.
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
                if config["status"] in ["in-progress", "review", "done"]:
                    # First transition to in-progress
                    await setup_client.call_tool(
                        "updateObject",
                        {
                            "kind": "task",
                            "id": task_id,
                            "projectRoot": planning_root,
                            "yamlPatch": {"status": "in-progress"},
                        },
                    )

                    if config["status"] in ["review", "done"]:
                        # Then transition to review
                        await setup_client.call_tool(
                            "updateObject",
                            {
                                "kind": "task",
                                "id": task_id,
                                "projectRoot": planning_root,
                                "yamlPatch": {"status": "review"},
                            },
                        )

                        if config["status"] == "done":
                            # Complete the task to move it to done status
                            await setup_client.call_tool(
                                "completeTask",
                                {
                                    "taskId": task_id,
                                    "projectRoot": planning_root,
                                },
                            )

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
            assert "id" in task
            assert "title" in task
            assert "status" in task
            assert "priority" in task
            assert "parent" in task
            assert "file_path" in task
            assert "created" in task
            assert "updated" in task

        # Verify priority sorting: high → normal → low
        priority_order = {"high": 1, "normal": 2, "low": 3}
        for i in range(len(all_tasks) - 1):
            current_priority = priority_order[all_tasks[i]["priority"]]
            next_priority = priority_order[all_tasks[i + 1]["priority"]]
            assert current_priority <= next_priority, f"Priority sorting failed at position {i}"

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
        # Expected order based on our config:
        # 1. High priority tasks (older first): "Create registration form",
        #    "Implement password rules"
        # 2. Normal priority tasks: "Add email validation"
        # 3. Low priority tasks: "Add user profile creation"

        titles = [task["title"] for task in feature_tasks]

        # Verify overall priority ordering
        priority_order = {"high": 1, "normal": 2, "low": 3}
        for i in range(len(feature_tasks) - 1):
            current_priority = priority_order[feature_tasks[i]["priority"]]
            next_priority = priority_order[feature_tasks[i + 1]["priority"]]
            assert (
                current_priority <= next_priority
            ), f"Priority sorting failed: {titles[i]} -> {titles[i + 1]}"

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
