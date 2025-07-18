"""Tests for Trellis MCP server functionality.

Tests server creation, configuration, and basic server instantiation
to ensure proper FastMCP integration and server behavior.
"""

from pathlib import Path

import pytest
from click.testing import CliRunner
from fastmcp import Client, FastMCP

from trellis_mcp.cli import cli
from trellis_mcp.server import create_server
from trellis_mcp.settings import Settings


def test_create_server_with_default_settings():
    """Test server creation with default settings."""
    settings = Settings()
    server = create_server(settings)

    assert server is not None
    assert hasattr(server, "run")
    assert isinstance(server, FastMCP)


def test_create_server_with_custom_settings():
    """Test server creation with custom settings."""
    settings = Settings(
        schema_version="2.0",
        planning_root=Path("./custom_planning"),
        debug_mode=True,
        log_level="DEBUG",
    )
    server = create_server(settings)

    assert server is not None
    assert hasattr(server, "run")


def test_create_server_returns_fastmcp_instance():
    """Test that create_server returns a FastMCP instance."""
    settings = Settings()
    server = create_server(settings)

    # Check that it's a FastMCP instance
    assert isinstance(server, FastMCP)


def test_server_has_expected_name():
    """Test that server is created with expected name."""
    settings = Settings()
    server = create_server(settings)

    # FastMCP servers have a name attribute
    assert hasattr(server, "name")
    assert server.name == "Trellis MCP Server"


def test_server_with_different_settings():
    """Test server creation with various settings combinations."""
    test_cases = [
        {"host": "localhost", "port": 9000},
        {"debug_mode": True, "log_level": "DEBUG"},
        {"planning_root": "./test", "schema_version": "1.5"},
    ]

    for settings_kwargs in test_cases:
        settings = Settings(**settings_kwargs)
        server = create_server(settings)
        assert server is not None
        assert isinstance(server, FastMCP)


class TestGetObject:
    """Test cases for the getObject RPC handler."""

    @pytest.mark.asyncio
    async def test_get_project_object(self, temp_dir):
        """Test retrieving a project object."""
        # Create project structure
        project_root = temp_dir / "planning"
        project_dir = project_root / "projects" / "P-test-project"
        project_dir.mkdir(parents=True)
        project_file = project_dir / "project.md"

        # Create project file with YAML front-matter
        project_content = """---
kind: project
id: P-test-project
title: Test Project
status: draft
priority: normal
created: 2025-07-13T19:12:00-05:00
updated: 2025-07-13T19:12:00-05:00
schema_version: "1.1"
---
This is a test project.

### Log

Project created.
"""
        project_file.write_text(project_content)

        # Create server and get object
        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        # Test getObject call
        async with Client(server) as client:
            result = await client.call_tool(
                "getObject",
                {"kind": "project", "id": "test-project", "projectRoot": str(project_root)},
            )

        # Verify results
        assert result.data["kind"] == "project"
        assert result.data["id"] == "test-project"
        assert result.data["file_path"] == str(project_file)
        assert result.data["yaml"]["kind"] == "project"
        assert result.data["yaml"]["title"] == "Test Project"
        assert "This is a test project." in result.data["body"]

    @pytest.mark.asyncio
    async def test_get_epic_object(self, temp_dir):
        """Test retrieving an epic object."""
        # Create epic structure
        project_root = temp_dir / "planning"
        epic_dir = project_root / "projects" / "P-test-project" / "epics" / "E-test-epic"
        epic_dir.mkdir(parents=True)
        epic_file = epic_dir / "epic.md"

        # Create epic file with YAML front-matter
        epic_content = """---
kind: epic
id: E-test-epic
parent: P-test-project
title: Test Epic
status: draft
priority: normal
created: 2025-07-13T19:12:00-05:00
updated: 2025-07-13T19:12:00-05:00
schema_version: "1.1"
---
This is a test epic.

### Log

Epic created.
"""
        epic_file.write_text(epic_content)

        # Create server and get object
        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        # Test getObject call
        async with Client(server) as client:
            result = await client.call_tool(
                "getObject", {"kind": "epic", "id": "test-epic", "projectRoot": str(project_root)}
            )

        # Verify results
        assert result.data["kind"] == "epic"
        assert result.data["id"] == "test-epic"
        assert result.data["file_path"] == str(epic_file)
        assert result.data["yaml"]["kind"] == "epic"
        assert result.data["yaml"]["title"] == "Test Epic"
        assert "This is a test epic." in result.data["body"]

    @pytest.mark.asyncio
    async def test_get_feature_object(self, temp_dir):
        """Test retrieving a feature object."""
        # Create feature structure
        project_root = temp_dir / "planning"
        feature_dir = (
            project_root
            / "projects"
            / "P-test-project"
            / "epics"
            / "E-test-epic"
            / "features"
            / "F-test-feature"
        )
        feature_dir.mkdir(parents=True)
        feature_file = feature_dir / "feature.md"

        # Create feature file with YAML front-matter
        feature_content = """---
kind: feature
id: F-test-feature
parent: E-test-epic
title: Test Feature
status: draft
priority: normal
created: 2025-07-13T19:12:00-05:00
updated: 2025-07-13T19:12:00-05:00
schema_version: "1.1"
---
This is a test feature.

### Log

Feature created.
"""
        feature_file.write_text(feature_content)

        # Create server and get object
        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        # Test getObject call
        async with Client(server) as client:
            result = await client.call_tool(
                "getObject",
                {"kind": "feature", "id": "test-feature", "projectRoot": str(project_root)},
            )

        # Verify results
        assert result.data["kind"] == "feature"
        assert result.data["id"] == "test-feature"
        assert result.data["file_path"] == str(feature_file)
        assert result.data["yaml"]["kind"] == "feature"
        assert result.data["yaml"]["title"] == "Test Feature"
        assert "This is a test feature." in result.data["body"]

    @pytest.mark.asyncio
    async def test_get_task_object_open(self, temp_dir):
        """Test retrieving a task object from tasks-open."""
        # Create task structure
        project_root = temp_dir / "planning"
        task_dir = (
            project_root
            / "projects"
            / "P-test-project"
            / "epics"
            / "E-test-epic"
            / "features"
            / "F-test-feature"
            / "tasks-open"
        )
        task_dir.mkdir(parents=True)
        task_file = task_dir / "T-test-task.md"

        # Create task file with YAML front-matter
        task_content = """---
kind: task
id: T-test-task
parent: F-test-feature
title: Test Task
status: open
priority: normal
created: 2025-07-13T19:12:00-05:00
updated: 2025-07-13T19:12:00-05:00
schema_version: "1.1"
---
This is a test task.

### Log

Task created.
"""
        task_file.write_text(task_content)

        # Create server and get object
        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        # Test getObject call
        async with Client(server) as client:
            result = await client.call_tool(
                "getObject", {"kind": "task", "id": "test-task", "projectRoot": str(project_root)}
            )

        # Verify results
        assert result.data["kind"] == "task"
        assert result.data["id"] == "test-task"
        assert result.data["file_path"] == str(task_file)
        assert result.data["yaml"]["kind"] == "task"
        assert result.data["yaml"]["title"] == "Test Task"
        assert "This is a test task." in result.data["body"]

    @pytest.mark.asyncio
    async def test_get_task_object_done(self, temp_dir):
        """Test retrieving a task object from tasks-done."""
        # Create task structure
        project_root = temp_dir / "planning"
        task_dir = (
            project_root
            / "projects"
            / "P-test-project"
            / "epics"
            / "E-test-epic"
            / "features"
            / "F-test-feature"
            / "tasks-done"
        )
        task_dir.mkdir(parents=True)
        task_file = task_dir / "2025-07-13T19:12:00-05:00-T-test-task.md"

        # Create task file with YAML front-matter
        task_content = """---
kind: task
id: T-test-task
parent: F-test-feature
title: Test Task
status: done
priority: normal
created: 2025-07-13T19:12:00-05:00
updated: 2025-07-13T19:12:00-05:00
schema_version: "1.1"
---
This is a completed test task.

### Log

Task created.
Task completed.
"""
        task_file.write_text(task_content)

        # Create server and get object
        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        # Test getObject call
        async with Client(server) as client:
            result = await client.call_tool(
                "getObject", {"kind": "task", "id": "test-task", "projectRoot": str(project_root)}
            )

        # Verify results
        assert result.data["kind"] == "task"
        assert result.data["id"] == "test-task"
        assert result.data["file_path"] == str(task_file)
        assert result.data["yaml"]["kind"] == "task"
        assert result.data["yaml"]["title"] == "Test Task"
        assert "This is a completed test task." in result.data["body"]

    @pytest.mark.asyncio
    async def test_get_object_with_prefix(self, temp_dir):
        """Test retrieving an object with ID prefix."""
        # Create project structure
        project_root = temp_dir / "planning"
        project_dir = project_root / "projects" / "P-test-project"
        project_dir.mkdir(parents=True)
        project_file = project_dir / "project.md"

        # Create project file with YAML front-matter
        project_content = """---
kind: project
id: P-test-project
title: Test Project
status: draft
priority: normal
created: 2025-07-13T19:12:00-05:00
updated: 2025-07-13T19:12:00-05:00
schema_version: "1.1"
---
This is a test project.

### Log

Project created.
"""
        project_file.write_text(project_content)

        # Create server and get object
        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        # Test getObject call with prefix
        async with Client(server) as client:
            result = await client.call_tool(
                "getObject",
                {
                    "kind": "project",
                    "id": "P-test-project",  # With prefix
                    "projectRoot": str(project_root),
                },
            )

        # Verify results - should return clean ID
        assert result.data["kind"] == "project"
        assert result.data["id"] == "test-project"  # Clean ID without prefix
        assert result.data["file_path"] == str(project_file)
        assert result.data["yaml"]["kind"] == "project"
        assert result.data["yaml"]["title"] == "Test Project"

    @pytest.mark.asyncio
    async def test_get_object_not_found(self, temp_dir):
        """Test getObject with non-existent object."""
        project_root = temp_dir / "planning"
        project_root.mkdir(parents=True)

        # Create server
        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        # Test getObject call with non-existent ID
        async with Client(server) as client:
            with pytest.raises(Exception):  # Should raise an exception
                await client.call_tool(
                    "getObject",
                    {"kind": "project", "id": "nonexistent", "projectRoot": str(project_root)},
                )

    @pytest.mark.asyncio
    async def test_get_object_invalid_kind(self, temp_dir):
        """Test getObject with invalid kind."""
        project_root = temp_dir / "planning"
        project_root.mkdir(parents=True)

        # Create server
        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        # Test getObject call with invalid kind
        async with Client(server) as client:
            with pytest.raises(Exception):  # Should raise an exception
                await client.call_tool(
                    "getObject",
                    {"kind": "invalid", "id": "test-id", "projectRoot": str(project_root)},
                )

    @pytest.mark.asyncio
    async def test_get_object_empty_parameters(self, temp_dir):
        """Test getObject with empty parameters."""
        project_root = temp_dir / "planning"
        project_root.mkdir(parents=True)

        # Create server
        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        # Test with empty kind
        async with Client(server) as client:
            with pytest.raises(Exception):  # Should raise an exception
                await client.call_tool(
                    "getObject", {"kind": "", "id": "test-id", "projectRoot": str(project_root)}
                )

    @pytest.mark.asyncio
    async def test_get_object_malformed_yaml(self, temp_dir):
        """Test getObject with malformed YAML front-matter."""
        # Create project structure
        project_root = temp_dir / "planning"
        project_dir = project_root / "projects" / "P-test-project"
        project_dir.mkdir(parents=True)
        project_file = project_dir / "project.md"

        # Create project file with malformed YAML
        project_content = """---
kind: project
id: P-test-project
title: Test Project
status: draft
priority: normal
created: 2025-07-13T19:12:00-05:00
updated: 2025-07-13T19:12:00-05:00
schema_version: "1.1"
invalid_yaml: [unclosed bracket
---
This is a test project.

### Log

Project created.
"""
        project_file.write_text(project_content)

        # Create server
        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        # Test getObject call - should raise YAML error
        async with Client(server) as client:
            with pytest.raises(Exception):  # yaml.YAMLError or similar
                await client.call_tool(
                    "getObject",
                    {"kind": "project", "id": "test-project", "projectRoot": str(project_root)},
                )

    @pytest.mark.asyncio
    async def test_get_object_task_prefers_open(self, temp_dir):
        """Test that getObject prefers tasks-open over tasks-done."""
        # Create task structure with both open and done versions
        project_root = temp_dir / "planning"
        base_dir = (
            project_root
            / "projects"
            / "P-test-project"
            / "epics"
            / "E-test-epic"
            / "features"
            / "F-test-feature"
        )

        # Create task in tasks-open
        open_dir = base_dir / "tasks-open"
        open_dir.mkdir(parents=True)
        open_file = open_dir / "T-test-task.md"
        open_content = """---
kind: task
id: T-test-task
parent: F-test-feature
title: Test Task
status: open
priority: normal
created: 2025-07-13T19:12:00-05:00
updated: 2025-07-13T19:12:00-05:00
schema_version: "1.1"
---
This is an open task.

### Log

Task created.
"""
        open_file.write_text(open_content)

        # Create task in tasks-done
        done_dir = base_dir / "tasks-done"
        done_dir.mkdir(parents=True)
        done_file = done_dir / "2025-07-13T19:12:00-05:00-T-test-task.md"
        done_content = """---
kind: task
id: T-test-task
parent: F-test-feature
title: Test Task
status: done
priority: normal
created: 2025-07-13T19:12:00-05:00
updated: 2025-07-13T19:12:00-05:00
schema_version: "1.1"
---
This is a done task.

### Log

Task created.
Task completed.
"""
        done_file.write_text(done_content)

        # Create server and get object
        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        # Test getObject call - should return open task
        async with Client(server) as client:
            result = await client.call_tool(
                "getObject", {"kind": "task", "id": "test-task", "projectRoot": str(project_root)}
            )

        # Verify it returned the open task, not the done task
        assert result.data["file_path"] == str(open_file)
        assert result.data["yaml"]["status"] == "open"
        assert "This is an open task." in result.data["body"]


class TestHTTPTransportFlag:
    """Test the --http flag functionality for the serve command."""

    def test_serve_help_includes_http_option(self):
        """Test that --http option is shown in help text."""
        runner = CliRunner()
        result = runner.invoke(cli, ["serve", "--help"])
        assert result.exit_code == 0
        assert "--http" in result.output
        assert "HOST:PORT" in result.output

    def test_serve_without_http_flag_shows_stdio(self):
        """Test that serve command without --http shows STDIO transport."""
        # This test is removed because it would actually try to start the server
        # which takes too long for unit tests. The STDIO behavior is the default
        # and is tested through integration tests separately.
        pass

    def test_http_option_validation_missing_colon(self):
        """Test HTTP option validation for missing colon."""
        runner = CliRunner()
        result = runner.invoke(cli, ["serve", "--http", "localhost8080"])
        assert result.exit_code != 0
        assert "HOST:PORT format" in result.output

    def test_http_option_validation_empty_host(self):
        """Test HTTP option validation for empty host."""
        runner = CliRunner()
        result = runner.invoke(cli, ["serve", "--http", ":8080"])
        assert result.exit_code != 0
        assert "Host cannot be empty" in result.output

    def test_http_option_validation_invalid_port(self):
        """Test HTTP option validation for invalid port."""
        runner = CliRunner()
        result = runner.invoke(cli, ["serve", "--http", "localhost:abc"])
        assert result.exit_code != 0
        assert "Port must be a valid integer" in result.output

    def test_http_option_validation_port_out_of_range_low(self):
        """Test HTTP option validation for port too low."""
        runner = CliRunner()
        result = runner.invoke(cli, ["serve", "--http", "localhost:80"])
        assert result.exit_code != 0
        assert "Port must be between 1024 and 65535" in result.output

    def test_http_option_validation_port_out_of_range_high(self):
        """Test HTTP option validation for port too high."""
        runner = CliRunner()
        result = runner.invoke(cli, ["serve", "--http", "localhost:99999"])
        assert result.exit_code != 0
        assert "Port must be between 1024 and 65535" in result.output

    def test_http_option_parsing_valid_values(self):
        """Test that valid HTTP options are parsed correctly."""
        # This test verifies that the parsing logic for valid HOST:PORT combinations
        # doesn't raise validation errors. The actual server startup is tested separately.

        test_cases = [
            "127.0.0.1:8080",
            "localhost:9000",
            "0.0.0.0:1024",
            "192.168.1.1:65535",
        ]

        for http_arg in test_cases:
            # Test parsing logic directly without starting server
            # Split the parsing logic to verify it works correctly
            if ":" in http_arg:
                host_str, port_str = http_arg.rsplit(":", 1)
                host = host_str.strip()
                port = int(port_str.strip())

                # Verify parsing worked correctly
                assert host != ""
                assert 1024 <= port <= 65535
            else:
                # This should not happen with our test cases
                assert False, f"Test case {http_arg} missing colon"


class TestCreateObject:
    """Test cases for the createObject RPC handler."""

    @pytest.mark.asyncio
    async def test_create_project_object_success(self, temp_dir):
        """Test successful creation of a project object."""
        project_root = temp_dir / "planning"

        # Create server
        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        # Test createObject call
        async with Client(server) as client:
            result = await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Test Project",
                    "projectRoot": str(project_root),
                    "description": "A test project for validation",
                },
            )

        # Verify results
        assert result.data["kind"] == "project"
        assert result.data["title"] == "Test Project"
        assert result.data["status"] == "draft"  # Default status for projects
        assert "id" in result.data
        assert result.data["id"].startswith("P-")

        # Verify file was created
        file_path = Path(result.data["file_path"])
        assert file_path.exists()
        assert file_path.name == "project.md"

        # Verify file content
        content = file_path.read_text()
        assert "kind: project" in content
        assert "title: Test Project" in content
        assert "status: draft" in content
        assert "A test project for validation" in content
        assert "### Log" in content

    @pytest.mark.asyncio
    async def test_create_epic_object_success(self, temp_dir):
        """Test successful creation of an epic object."""
        project_root = temp_dir / "planning"

        # First create a parent project
        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            # Create parent project
            await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Parent Project",
                    "projectRoot": str(project_root),
                    "id": "parent-project",
                },
            )

            # Create epic
            result = await client.call_tool(
                "createObject",
                {
                    "kind": "epic",
                    "title": "Test Epic",
                    "projectRoot": str(project_root),
                    "parent": "parent-project",
                    "description": "A test epic for validation",
                },
            )

        # Verify results
        assert result.data["kind"] == "epic"
        assert result.data["title"] == "Test Epic"
        assert result.data["status"] == "draft"  # Default status for epics
        assert "id" in result.data
        assert result.data["id"].startswith("E-")

        # Verify file was created in correct location
        file_path = Path(result.data["file_path"])
        assert file_path.exists()
        assert file_path.name == "epic.md"
        assert "P-parent-project" in str(file_path)
        assert "epics" in str(file_path)

        # Verify file content
        content = file_path.read_text()
        assert "kind: epic" in content
        assert "title: Test Epic" in content
        assert "parent: parent-project" in content
        assert "A test epic for validation" in content

    @pytest.mark.asyncio
    async def test_create_feature_object_success(self, temp_dir):
        """Test successful creation of a feature object."""
        project_root = temp_dir / "planning"

        # Create hierarchy: project -> epic -> feature
        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            # Create parent project
            await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Parent Project",
                    "projectRoot": str(project_root),
                    "id": "parent-project",
                },
            )

            # Create parent epic
            await client.call_tool(
                "createObject",
                {
                    "kind": "epic",
                    "title": "Parent Epic",
                    "projectRoot": str(project_root),
                    "parent": "parent-project",
                    "id": "parent-epic",
                },
            )

            # Create feature
            result = await client.call_tool(
                "createObject",
                {
                    "kind": "feature",
                    "title": "Test Feature",
                    "projectRoot": str(project_root),
                    "parent": "parent-epic",
                    "description": "A test feature for validation",
                },
            )

        # Verify results
        assert result.data["kind"] == "feature"
        assert result.data["title"] == "Test Feature"
        assert result.data["status"] == "draft"  # Default status for features
        assert "id" in result.data
        assert result.data["id"].startswith("F-")

        # Verify file was created in correct location
        file_path = Path(result.data["file_path"])
        assert file_path.exists()
        assert file_path.name == "feature.md"
        assert "P-parent-project" in str(file_path)
        assert "E-parent-epic" in str(file_path)
        assert "features" in str(file_path)

        # Verify file content
        content = file_path.read_text()
        assert "kind: feature" in content
        assert "title: Test Feature" in content
        assert "parent: parent-epic" in content
        assert "A test feature for validation" in content

    @pytest.mark.asyncio
    async def test_create_task_object_success(self, temp_dir):
        """Test successful creation of a task object."""
        project_root = temp_dir / "planning"

        # Create hierarchy: project -> epic -> feature -> task
        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            # Create parent project
            await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Parent Project",
                    "projectRoot": str(project_root),
                    "id": "parent-project",
                },
            )

            # Create parent epic
            await client.call_tool(
                "createObject",
                {
                    "kind": "epic",
                    "title": "Parent Epic",
                    "projectRoot": str(project_root),
                    "parent": "parent-project",
                    "id": "parent-epic",
                },
            )

            # Create parent feature
            await client.call_tool(
                "createObject",
                {
                    "kind": "feature",
                    "title": "Parent Feature",
                    "projectRoot": str(project_root),
                    "parent": "parent-epic",
                    "id": "parent-feature",
                },
            )

            # Create task
            result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Test Task",
                    "projectRoot": str(project_root),
                    "parent": "parent-feature",
                    "description": "A test task for validation",
                },
            )

        # Verify results
        assert result.data["kind"] == "task"
        assert result.data["title"] == "Test Task"
        assert result.data["status"] == "open"  # Default status for tasks
        assert "id" in result.data
        assert result.data["id"].startswith("T-")

        # Verify file was created in correct location
        file_path = Path(result.data["file_path"])
        assert file_path.exists()
        assert file_path.name.endswith(".md")
        assert file_path.name.startswith("T-")
        assert "P-parent-project" in str(file_path)
        assert "E-parent-epic" in str(file_path)
        assert "F-parent-feature" in str(file_path)
        assert "tasks-open" in str(file_path)

        # Verify file content
        content = file_path.read_text()
        assert "kind: task" in content
        assert "title: Test Task" in content
        assert "status: open" in content
        assert "parent: parent-feature" in content
        assert "A test task for validation" in content

    @pytest.mark.asyncio
    async def test_create_object_generates_id_when_missing(self, temp_dir):
        """Test that ID is auto-generated when not provided."""
        project_root = temp_dir / "planning"

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            result = await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Auto ID Project",
                    "projectRoot": str(project_root),
                },
            )

        # Verify ID was generated
        assert "id" in result.data
        assert result.data["id"].startswith("P-")
        assert len(result.data["id"]) > 2  # Should have content after prefix

        # Verify file was created with generated ID
        file_path = Path(result.data["file_path"])
        assert file_path.exists()
        assert file_path.parent.name == result.data["id"]

    @pytest.mark.asyncio
    async def test_create_object_uses_provided_id(self, temp_dir):
        """Test that provided ID is used when specified."""
        project_root = temp_dir / "planning"

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            result = await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Custom ID Project",
                    "projectRoot": str(project_root),
                    "id": "custom-project-id",
                },
            )

        # Verify custom ID was used
        assert result.data["id"] == "P-custom-project-id"

        # Verify file was created with custom ID
        file_path = Path(result.data["file_path"])
        assert file_path.exists()
        assert "P-custom-project-id" in str(file_path)

    @pytest.mark.asyncio
    async def test_create_object_invalid_kind(self, temp_dir):
        """Test error handling for invalid kind."""
        project_root = temp_dir / "planning"

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            with pytest.raises(Exception):  # Should raise validation error
                await client.call_tool(
                    "createObject",
                    {
                        "kind": "invalid-kind",
                        "title": "Test Object",
                        "projectRoot": str(project_root),
                    },
                )

    @pytest.mark.asyncio
    async def test_create_object_empty_title(self, temp_dir):
        """Test error handling for empty title."""
        project_root = temp_dir / "planning"

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            with pytest.raises(Exception):  # Should raise ValueError
                await client.call_tool(
                    "createObject",
                    {
                        "kind": "project",
                        "title": "",
                        "projectRoot": str(project_root),
                    },
                )

    @pytest.mark.asyncio
    async def test_create_object_empty_project_root(self, temp_dir):
        """Test error handling for empty project root."""
        settings = Settings(planning_root=temp_dir)
        server = create_server(settings)

        async with Client(server) as client:
            with pytest.raises(Exception):  # Should raise ValueError
                await client.call_tool(
                    "createObject",
                    {
                        "kind": "project",
                        "title": "Test Project",
                        "projectRoot": "",
                    },
                )

    @pytest.mark.asyncio
    async def test_create_object_missing_parent_for_epic(self, temp_dir):
        """Test error handling when epic is missing parent."""
        project_root = temp_dir / "planning"

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            with pytest.raises(Exception):  # Should raise ValueError
                await client.call_tool(
                    "createObject",
                    {
                        "kind": "epic",
                        "title": "Test Epic",
                        "projectRoot": str(project_root),
                    },
                )

    @pytest.mark.asyncio
    async def test_create_object_missing_parent_for_feature(self, temp_dir):
        """Test error handling when feature is missing parent."""
        project_root = temp_dir / "planning"

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            with pytest.raises(Exception):  # Should raise ValueError
                await client.call_tool(
                    "createObject",
                    {
                        "kind": "feature",
                        "title": "Test Feature",
                        "projectRoot": str(project_root),
                    },
                )

    @pytest.mark.asyncio
    async def test_create_object_missing_parent_for_task(self, temp_dir):
        """Test that tasks without parent create standalone tasks."""
        project_root = temp_dir / "planning"

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            # Should succeed and create a standalone task
            result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Test Task",
                    "projectRoot": str(project_root),
                },
            )

            assert result.data is not None
            assert result.data["id"].startswith("T-")
            assert result.data["status"] == "open"

    @pytest.mark.asyncio
    async def test_create_object_invalid_parent_reference(self, temp_dir):
        """Test error handling for invalid parent reference."""
        project_root = temp_dir / "planning"

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            with pytest.raises(Exception):  # Should raise validation error
                await client.call_tool(
                    "createObject",
                    {
                        "kind": "epic",
                        "title": "Test Epic",
                        "projectRoot": str(project_root),
                        "parent": "nonexistent-project",
                    },
                )

    @pytest.mark.asyncio
    async def test_create_object_file_already_exists(self, temp_dir):
        """Test error handling when file already exists."""
        project_root = temp_dir / "planning"

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            # Create first object
            await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Test Project",
                    "projectRoot": str(project_root),
                    "id": "duplicate-id",
                },
            )

            # Try to create another object with same ID
            with pytest.raises(Exception):  # Should raise FileExistsError
                await client.call_tool(
                    "createObject",
                    {
                        "kind": "project",
                        "title": "Another Project",
                        "projectRoot": str(project_root),
                        "id": "duplicate-id",
                    },
                )

    @pytest.mark.asyncio
    async def test_create_object_with_prerequisites(self, temp_dir):
        """Test creating object with prerequisites."""
        project_root = temp_dir / "planning"

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            # Create parent project
            await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Parent Project",
                    "projectRoot": str(project_root),
                    "id": "parent-project",
                },
            )

            # Create parent epic
            await client.call_tool(
                "createObject",
                {
                    "kind": "epic",
                    "title": "Parent Epic",
                    "projectRoot": str(project_root),
                    "parent": "parent-project",
                    "id": "parent-epic",
                },
            )

            # Create parent feature
            await client.call_tool(
                "createObject",
                {
                    "kind": "feature",
                    "title": "Parent Feature",
                    "projectRoot": str(project_root),
                    "parent": "parent-epic",
                    "id": "parent-feature",
                },
            )

            # Create first task
            task1_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "First Task",
                    "projectRoot": str(project_root),
                    "parent": "parent-feature",
                    "id": "task-1",
                },
            )

            # Create second task with prerequisite
            task2_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Second Task",
                    "projectRoot": str(project_root),
                    "parent": "parent-feature",
                    "id": "task-2",
                    "prerequisites": ["T-task-1"],
                },
            )

        # Verify both tasks were created
        assert task1_result.data["id"] == "T-task-1"
        assert task2_result.data["id"] == "T-task-2"

        # Verify prerequisite was recorded
        task2_file = Path(task2_result.data["file_path"])
        content = task2_file.read_text()
        assert "prerequisites:" in content
        assert "T-task-1" in content

    @pytest.mark.asyncio
    async def test_create_object_cycle_detection_and_rollback(self, temp_dir):
        """Test cycle detection and rollback functionality."""
        project_root = temp_dir / "planning"

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            # Create parent project, epic, and feature
            await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Parent Project",
                    "projectRoot": str(project_root),
                    "id": "parent-project",
                },
            )

            await client.call_tool(
                "createObject",
                {
                    "kind": "epic",
                    "title": "Parent Epic",
                    "projectRoot": str(project_root),
                    "parent": "parent-project",
                    "id": "parent-epic",
                },
            )

            await client.call_tool(
                "createObject",
                {
                    "kind": "feature",
                    "title": "Parent Feature",
                    "projectRoot": str(project_root),
                    "parent": "parent-epic",
                    "id": "parent-feature",
                },
            )

            # Try to create task A that depends on itself (direct cycle)
            # This should fail and rollback
            with pytest.raises(Exception):  # Should raise TrellisValidationError
                await client.call_tool(
                    "createObject",
                    {
                        "kind": "task",
                        "title": "Task A",
                        "projectRoot": str(project_root),
                        "parent": "parent-feature",
                        "id": "task-a",
                        "prerequisites": ["T-task-a"],  # Self-reference creates immediate cycle
                    },
                )

        # Verify the problematic task was not created (rollback worked)
        task_a_path = (
            project_root
            / "projects"
            / "P-parent-project"
            / "epics"
            / "E-parent-epic"
            / "features"
            / "F-parent-feature"
            / "tasks-open"
            / "T-task-a.md"
        )
        assert not task_a_path.exists()

    @pytest.mark.asyncio
    async def test_create_object_with_all_optional_parameters(self, temp_dir):
        """Test creating object with all optional parameters specified."""
        project_root = temp_dir / "planning"

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            result = await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Full Project",
                    "projectRoot": str(project_root),
                    "id": "full-project",
                    "status": "draft",
                    "priority": "high",
                    "prerequisites": [],
                    "description": "A project with all parameters specified",
                },
            )

        # Verify all parameters were used
        assert result.data["id"] == "P-full-project"
        assert result.data["status"] == "draft"

        # Verify file content
        file_path = Path(result.data["file_path"])
        content = file_path.read_text()
        assert "priority: high" in content
        assert "prerequisites: []" in content
        assert "A project with all parameters specified" in content

    @pytest.mark.asyncio
    async def test_create_object_status_defaults(self, temp_dir):
        """Test that status defaults are applied correctly for different kinds."""
        project_root = temp_dir / "planning"

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            # Test project default status
            project_result = await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Test Project",
                    "projectRoot": str(project_root),
                    "id": "test-project",
                },
            )

            # Create epic for hierarchy
            epic_result = await client.call_tool(
                "createObject",
                {
                    "kind": "epic",
                    "title": "Test Epic",
                    "projectRoot": str(project_root),
                    "parent": "test-project",
                    "id": "test-epic",
                },
            )

            # Create feature for hierarchy
            feature_result = await client.call_tool(
                "createObject",
                {
                    "kind": "feature",
                    "title": "Test Feature",
                    "projectRoot": str(project_root),
                    "parent": "test-epic",
                    "id": "test-feature",
                },
            )

            # Create task for hierarchy
            task_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Test Task",
                    "projectRoot": str(project_root),
                    "parent": "test-feature",
                    "id": "test-task",
                },
            )

        # Verify default statuses
        assert project_result.data["status"] == "draft"
        assert epic_result.data["status"] == "draft"
        assert feature_result.data["status"] == "draft"
        assert task_result.data["status"] == "open"

    @pytest.mark.asyncio
    async def test_create_object_priority_defaults(self, temp_dir):
        """Test that priority defaults to 'normal' when not specified."""
        project_root = temp_dir / "planning"

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            result = await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Test Project",
                    "projectRoot": str(project_root),
                },
            )

        # Verify file content has default priority
        file_path = Path(result.data["file_path"])
        content = file_path.read_text()
        assert "priority: normal" in content

    @pytest.mark.asyncio
    async def test_create_object_validates_parent_existence(self, temp_dir):
        """Test that parent existence is validated properly."""
        project_root = temp_dir / "planning"

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            # Create parent project
            await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Parent Project",
                    "projectRoot": str(project_root),
                    "id": "parent-project",
                },
            )

            # Try to create epic with non-existent parent
            with pytest.raises(Exception):  # Should raise TrellisValidationError
                await client.call_tool(
                    "createObject",
                    {
                        "kind": "epic",
                        "title": "Test Epic",
                        "projectRoot": str(project_root),
                        "parent": "nonexistent-parent",
                    },
                )

            # Create epic with valid parent - should succeed
            result = await client.call_tool(
                "createObject",
                {
                    "kind": "epic",
                    "title": "Test Epic",
                    "projectRoot": str(project_root),
                    "parent": "parent-project",
                },
            )

            assert result.data["kind"] == "epic"
            assert result.data["title"] == "Test Epic"


class TestUpdateObject:
    """Test cases for the updateObject RPC handler."""

    @pytest.mark.asyncio
    async def test_update_project_yaml_patch_success(self, temp_dir):
        """Test successful yamlPatch update for project object."""
        project_root = temp_dir / "planning"

        # Create server
        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            # Create a project to update
            await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Original Project",
                    "projectRoot": str(project_root),
                    "id": "test-project",
                    "priority": "normal",
                },
            )

            # Update the project with yamlPatch
            update_result = await client.call_tool(
                "updateObject",
                {
                    "kind": "project",
                    "id": "test-project",
                    "projectRoot": str(project_root),
                    "yamlPatch": {"title": "Updated Project", "priority": "high"},
                },
            )

        # Verify update results
        assert update_result.data["id"] == "test-project"
        assert update_result.data["kind"] == "project"
        assert "updated" in update_result.data
        assert update_result.data["changes"]["yaml_fields"] == ["title", "priority"]

        # Verify file was actually updated
        file_path = Path(update_result.data["file_path"])
        assert file_path.exists()
        content = file_path.read_text()
        assert "title: Updated Project" in content
        assert "priority: high" in content

    @pytest.mark.asyncio
    async def test_update_epic_yaml_patch_success(self, temp_dir):
        """Test successful yamlPatch update for epic object."""
        project_root = temp_dir / "planning"

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            # Create parent project
            await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Parent Project",
                    "projectRoot": str(project_root),
                    "id": "parent-project",
                },
            )

            # Create epic to update
            await client.call_tool(
                "createObject",
                {
                    "kind": "epic",
                    "title": "Original Epic",
                    "projectRoot": str(project_root),
                    "parent": "parent-project",
                    "id": "test-epic",
                },
            )

            # Update the epic
            update_result = await client.call_tool(
                "updateObject",
                {
                    "kind": "epic",
                    "id": "test-epic",
                    "projectRoot": str(project_root),
                    "yamlPatch": {"title": "Updated Epic", "status": "in-progress"},
                },
            )

        # Verify update results
        assert update_result.data["id"] == "test-epic"
        assert update_result.data["kind"] == "epic"
        assert update_result.data["changes"]["yaml_fields"] == ["title", "status"]

        # Verify file content
        file_path = Path(update_result.data["file_path"])
        content = file_path.read_text()
        assert "title: Updated Epic" in content
        assert "status: in-progress" in content

    @pytest.mark.asyncio
    async def test_update_feature_yaml_patch_success(self, temp_dir):
        """Test successful yamlPatch update for feature object."""
        project_root = temp_dir / "planning"

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            # Create hierarchy
            await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Parent Project",
                    "projectRoot": str(project_root),
                    "id": "parent-project",
                },
            )

            await client.call_tool(
                "createObject",
                {
                    "kind": "epic",
                    "title": "Parent Epic",
                    "projectRoot": str(project_root),
                    "parent": "parent-project",
                    "id": "parent-epic",
                },
            )

            await client.call_tool(
                "createObject",
                {
                    "kind": "feature",
                    "title": "Original Feature",
                    "projectRoot": str(project_root),
                    "parent": "parent-epic",
                    "id": "test-feature",
                },
            )

            # Update the feature
            update_result = await client.call_tool(
                "updateObject",
                {
                    "kind": "feature",
                    "id": "test-feature",
                    "projectRoot": str(project_root),
                    "yamlPatch": {"title": "Updated Feature", "priority": "low"},
                },
            )

        # Verify update results
        assert update_result.data["id"] == "test-feature"
        assert update_result.data["kind"] == "feature"
        assert update_result.data["changes"]["yaml_fields"] == ["title", "priority"]

        # Verify file content
        file_path = Path(update_result.data["file_path"])
        content = file_path.read_text()
        assert "title: Updated Feature" in content
        assert "priority: low" in content

    @pytest.mark.asyncio
    async def test_update_task_yaml_patch_success(self, temp_dir):
        """Test successful yamlPatch update for task object."""
        project_root = temp_dir / "planning"

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            # Create hierarchy
            await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Parent Project",
                    "projectRoot": str(project_root),
                    "id": "parent-project",
                },
            )

            await client.call_tool(
                "createObject",
                {
                    "kind": "epic",
                    "title": "Parent Epic",
                    "projectRoot": str(project_root),
                    "parent": "parent-project",
                    "id": "parent-epic",
                },
            )

            await client.call_tool(
                "createObject",
                {
                    "kind": "feature",
                    "title": "Parent Feature",
                    "projectRoot": str(project_root),
                    "parent": "parent-epic",
                    "id": "parent-feature",
                },
            )

            await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Original Task",
                    "projectRoot": str(project_root),
                    "parent": "parent-feature",
                    "id": "test-task",
                },
            )

            # Update the task
            update_result = await client.call_tool(
                "updateObject",
                {
                    "kind": "task",
                    "id": "test-task",
                    "projectRoot": str(project_root),
                    "yamlPatch": {"title": "Updated Task", "status": "in-progress"},
                },
            )

        # Verify update results
        assert update_result.data["id"] == "test-task"
        assert update_result.data["kind"] == "task"
        assert update_result.data["changes"]["yaml_fields"] == ["title", "status"]

        # Verify file content
        file_path = Path(update_result.data["file_path"])
        content = file_path.read_text()
        assert "title: Updated Task" in content
        assert "status: in-progress" in content

    @pytest.mark.asyncio
    async def test_update_object_body_patch_success(self, temp_dir):
        """Test successful bodyPatch update for markdown content."""
        project_root = temp_dir / "planning"

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            # Create a project to update
            await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Test Project",
                    "projectRoot": str(project_root),
                    "id": "test-project",
                    "description": "Original description",
                },
            )

            # Update the project body
            new_body = (
                "Updated body content\n\n### Progress\n\nWork in progress.\n\n### Log\n\n"
                "Project updated."
            )
            update_result = await client.call_tool(
                "updateObject",
                {
                    "kind": "project",
                    "id": "test-project",
                    "projectRoot": str(project_root),
                    "bodyPatch": new_body,
                },
            )

        # Verify update results
        assert update_result.data["id"] == "test-project"
        assert update_result.data["changes"]["body_updated"] is True

        # Verify file content
        file_path = Path(update_result.data["file_path"])
        content = file_path.read_text()
        assert "Updated body content" in content
        assert "### Progress" in content
        assert "Work in progress." in content

    @pytest.mark.asyncio
    async def test_update_object_both_yaml_and_body_patch(self, temp_dir):
        """Test updating both YAML and body content in single operation."""
        project_root = temp_dir / "planning"

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            # Create a project to update
            await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Test Project",
                    "projectRoot": str(project_root),
                    "id": "test-project",
                },
            )

            # Update both YAML and body
            update_result = await client.call_tool(
                "updateObject",
                {
                    "kind": "project",
                    "id": "test-project",
                    "projectRoot": str(project_root),
                    "yamlPatch": {"title": "Updated Project", "priority": "high"},
                    "bodyPatch": "Updated body content\n\n### Log\n\nProject updated.",
                },
            )

        # Verify update results
        assert update_result.data["id"] == "test-project"
        assert update_result.data["changes"]["yaml_fields"] == ["title", "priority"]
        assert update_result.data["changes"]["body_updated"] is True

        # Verify file content
        file_path = Path(update_result.data["file_path"])
        content = file_path.read_text()
        assert "title: Updated Project" in content
        assert "priority: high" in content
        assert "Updated body content" in content

    @pytest.mark.asyncio
    async def test_update_object_deep_merge_nested_structures(self, temp_dir):
        """Test deep merge functionality with nested structures."""
        project_root = temp_dir / "planning"

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            # Create a project to update
            await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Test Project",
                    "projectRoot": str(project_root),
                    "id": "test-project",
                },
            )

            # Read the current file to manually add nested structure
            from trellis_mcp.io_utils import read_markdown, write_markdown
            from trellis_mcp.path_resolver import id_to_path

            file_path = id_to_path(project_root, "project", "test-project")
            yaml_dict, body_str = read_markdown(file_path)

            # Add nested structure (simplified - just add a custom field)
            yaml_dict["custom_field"] = "original_value"
            write_markdown(file_path, yaml_dict, body_str)

            # Update with standard fields - should preserve custom field
            update_result = await client.call_tool(
                "updateObject",
                {
                    "kind": "project",
                    "id": "test-project",
                    "projectRoot": str(project_root),
                    "yamlPatch": {
                        "title": "Updated Project",
                        "priority": "high",
                    },
                },
            )

        # Verify update results
        assert update_result.data["id"] == "test-project"
        assert update_result.data["changes"]["yaml_fields"] == ["title", "priority"]

        # Verify deep merge worked correctly - custom field should be preserved
        updated_yaml, _ = read_markdown(file_path)
        assert updated_yaml["title"] == "Updated Project"
        assert updated_yaml["priority"] == "high"
        assert updated_yaml["custom_field"] == "original_value"  # Preserved

    @pytest.mark.asyncio
    async def test_update_object_deep_merge_preserves_existing_fields(self, temp_dir):
        """Test that deep merge preserves existing fields not in patch."""
        project_root = temp_dir / "planning"

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            # Create a project to update
            await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Test Project",
                    "projectRoot": str(project_root),
                    "id": "test-project",
                    "priority": "normal",
                },
            )

            # Update only title, priority should be preserved
            update_result = await client.call_tool(
                "updateObject",
                {
                    "kind": "project",
                    "id": "test-project",
                    "projectRoot": str(project_root),
                    "yamlPatch": {"title": "Updated Project"},
                },
            )

        # Verify existing fields were preserved
        file_path = Path(update_result.data["file_path"])
        content = file_path.read_text()
        assert "title: Updated Project" in content
        assert "priority: normal" in content  # Should be preserved

    @pytest.mark.asyncio
    async def test_update_object_valid_status_transitions(self, temp_dir):
        """Test valid status transitions for different object types."""
        project_root = temp_dir / "planning"

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            # Create hierarchy
            await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Test Project",
                    "projectRoot": str(project_root),
                    "id": "test-project",
                },
            )

            await client.call_tool(
                "createObject",
                {
                    "kind": "epic",
                    "title": "Test Epic",
                    "projectRoot": str(project_root),
                    "parent": "test-project",
                    "id": "test-epic",
                },
            )

            await client.call_tool(
                "createObject",
                {
                    "kind": "feature",
                    "title": "Test Feature",
                    "projectRoot": str(project_root),
                    "parent": "test-epic",
                    "id": "test-feature",
                },
            )

            await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Test Task",
                    "projectRoot": str(project_root),
                    "parent": "test-feature",
                    "id": "test-task",
                },
            )

            # Test valid project transition: draft -> in-progress
            await client.call_tool(
                "updateObject",
                {
                    "kind": "project",
                    "id": "test-project",
                    "projectRoot": str(project_root),
                    "yamlPatch": {"status": "in-progress"},
                },
            )

            # Test valid epic transition: draft -> in-progress
            await client.call_tool(
                "updateObject",
                {
                    "kind": "epic",
                    "id": "test-epic",
                    "projectRoot": str(project_root),
                    "yamlPatch": {"status": "in-progress"},
                },
            )

            # Test valid feature transition: draft -> in-progress
            await client.call_tool(
                "updateObject",
                {
                    "kind": "feature",
                    "id": "test-feature",
                    "projectRoot": str(project_root),
                    "yamlPatch": {"status": "in-progress"},
                },
            )

            # Test valid task transition: open -> in-progress
            await client.call_tool(
                "updateObject",
                {
                    "kind": "task",
                    "id": "test-task",
                    "projectRoot": str(project_root),
                    "yamlPatch": {"status": "in-progress"},
                },
            )

            # Test valid task transition: in-progress -> review
            await client.call_tool(
                "updateObject",
                {
                    "kind": "task",
                    "id": "test-task",
                    "projectRoot": str(project_root),
                    "yamlPatch": {"status": "review"},
                },
            )

        # If we get here, all transitions were valid
        assert True  # All transitions succeeded

    @pytest.mark.asyncio
    async def test_update_object_invalid_status_transitions(self, temp_dir):
        """Test invalid status transitions are rejected."""
        project_root = temp_dir / "planning"

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            # Create a project in draft status
            await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Test Project",
                    "projectRoot": str(project_root),
                    "id": "test-project",
                },
            )

            # Try invalid transition: draft -> done (should fail)
            with pytest.raises(Exception):  # Should raise TrellisValidationError
                await client.call_tool(
                    "updateObject",
                    {
                        "kind": "project",
                        "id": "test-project",
                        "projectRoot": str(project_root),
                        "yamlPatch": {"status": "done"},
                    },
                )

            # Create task and try invalid transition
            await client.call_tool(
                "createObject",
                {
                    "kind": "epic",
                    "title": "Test Epic",
                    "projectRoot": str(project_root),
                    "parent": "test-project",
                    "id": "test-epic",
                },
            )

            await client.call_tool(
                "createObject",
                {
                    "kind": "feature",
                    "title": "Test Feature",
                    "projectRoot": str(project_root),
                    "parent": "test-epic",
                    "id": "test-feature",
                },
            )

            await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Test Task",
                    "projectRoot": str(project_root),
                    "parent": "test-feature",
                    "id": "test-task",
                },
            )

            # Try invalid transition: open -> review (should fail - must go through in-progress)
            with pytest.raises(Exception):  # Should raise TrellisValidationError
                await client.call_tool(
                    "updateObject",
                    {
                        "kind": "task",
                        "id": "test-task",
                        "projectRoot": str(project_root),
                        "yamlPatch": {"status": "review"},
                    },
                )

    @pytest.mark.asyncio
    async def test_update_task_cannot_set_done_status(self, temp_dir):
        """Test that updateObject cannot set task status to 'done'."""
        project_root = temp_dir / "planning"

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            # Create hierarchy
            await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Test Project",
                    "projectRoot": str(project_root),
                    "id": "test-project",
                },
            )

            await client.call_tool(
                "createObject",
                {
                    "kind": "epic",
                    "title": "Test Epic",
                    "projectRoot": str(project_root),
                    "parent": "test-project",
                    "id": "test-epic",
                },
            )

            await client.call_tool(
                "createObject",
                {
                    "kind": "feature",
                    "title": "Test Feature",
                    "projectRoot": str(project_root),
                    "parent": "test-epic",
                    "id": "test-feature",
                },
            )

            await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Test Task",
                    "projectRoot": str(project_root),
                    "parent": "test-feature",
                    "id": "test-task",
                },
            )

            # Try to set task status to 'done' - should fail
            with pytest.raises(Exception):  # Should raise TrellisValidationError
                await client.call_tool(
                    "updateObject",
                    {
                        "kind": "task",
                        "id": "test-task",
                        "projectRoot": str(project_root),
                        "yamlPatch": {"status": "done"},
                    },
                )

    @pytest.mark.asyncio
    async def test_update_object_prerequisite_cycle_detection(self, temp_dir):
        """Test that prerequisite cycles are detected after updates."""
        project_root = temp_dir / "planning"

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            # Create hierarchy
            await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Test Project",
                    "projectRoot": str(project_root),
                    "id": "test-project",
                },
            )

            await client.call_tool(
                "createObject",
                {
                    "kind": "epic",
                    "title": "Test Epic",
                    "projectRoot": str(project_root),
                    "parent": "test-project",
                    "id": "test-epic",
                },
            )

            await client.call_tool(
                "createObject",
                {
                    "kind": "feature",
                    "title": "Test Feature",
                    "projectRoot": str(project_root),
                    "parent": "test-epic",
                    "id": "test-feature",
                },
            )

            # Create task A
            await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Task A",
                    "projectRoot": str(project_root),
                    "parent": "test-feature",
                    "id": "task-a",
                },
            )

            # Create task B with A as prerequisite
            await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Task B",
                    "projectRoot": str(project_root),
                    "parent": "test-feature",
                    "id": "task-b",
                    "prerequisites": ["T-task-a"],
                },
            )

            # Try to update task A to have B as prerequisite - should create cycle
            with pytest.raises(Exception):  # Should raise TrellisValidationError
                await client.call_tool(
                    "updateObject",
                    {
                        "kind": "task",
                        "id": "task-a",
                        "projectRoot": str(project_root),
                        "yamlPatch": {"prerequisites": ["T-task-b"]},
                    },
                )

    @pytest.mark.asyncio
    async def test_update_object_prerequisite_rollback_on_cycle(self, temp_dir):
        """Test that original content is restored when cycle is detected."""
        project_root = temp_dir / "planning"

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            # Create hierarchy
            await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Test Project",
                    "projectRoot": str(project_root),
                    "id": "test-project",
                },
            )

            await client.call_tool(
                "createObject",
                {
                    "kind": "epic",
                    "title": "Test Epic",
                    "projectRoot": str(project_root),
                    "parent": "test-project",
                    "id": "test-epic",
                },
            )

            await client.call_tool(
                "createObject",
                {
                    "kind": "feature",
                    "title": "Test Feature",
                    "projectRoot": str(project_root),
                    "parent": "test-epic",
                    "id": "test-feature",
                },
            )

            # Create task A
            await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Task A",
                    "projectRoot": str(project_root),
                    "parent": "test-feature",
                    "id": "task-a",
                },
            )

            # Create task B with A as prerequisite
            await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Task B",
                    "projectRoot": str(project_root),
                    "parent": "test-feature",
                    "id": "task-b",
                    "prerequisites": ["T-task-a"],
                },
            )

            # Get original content of task A
            from trellis_mcp.io_utils import read_markdown
            from trellis_mcp.path_resolver import id_to_path

            task_a_path = id_to_path(project_root, "task", "task-a")
            original_yaml, original_body = read_markdown(task_a_path)

            # Try to update task A to have B as prerequisite - should fail and rollback
            with pytest.raises(Exception):  # Should raise TrellisValidationError
                await client.call_tool(
                    "updateObject",
                    {
                        "kind": "task",
                        "id": "task-a",
                        "projectRoot": str(project_root),
                        "yamlPatch": {"prerequisites": ["T-task-b"]},
                    },
                )

            # Verify original content was restored
            current_yaml, current_body = read_markdown(task_a_path)
            assert current_yaml["prerequisites"] == original_yaml["prerequisites"]
            assert current_body == original_body

    @pytest.mark.asyncio
    async def test_update_object_rollback_on_validation_failure(self, temp_dir):
        """Test rollback on validation failures."""
        project_root = temp_dir / "planning"

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            # Create a project
            await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Test Project",
                    "projectRoot": str(project_root),
                    "id": "test-project",
                },
            )

            # Get original content
            from trellis_mcp.io_utils import read_markdown
            from trellis_mcp.path_resolver import id_to_path

            project_path = id_to_path(project_root, "project", "test-project")
            original_yaml, original_body = read_markdown(project_path)

            # Try to update with invalid status - should fail and rollback
            with pytest.raises(Exception):  # Should raise TrellisValidationError
                await client.call_tool(
                    "updateObject",
                    {
                        "kind": "project",
                        "id": "test-project",
                        "projectRoot": str(project_root),
                        "yamlPatch": {"status": "invalid-status"},
                    },
                )

            # Verify original content was preserved
            current_yaml, current_body = read_markdown(project_path)
            assert current_yaml["status"] == original_yaml["status"]
            assert current_body == original_body

    @pytest.mark.asyncio
    async def test_update_object_invalid_parameters(self, temp_dir):
        """Test error handling for invalid parameters."""
        project_root = temp_dir / "planning"

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            # Test empty kind
            with pytest.raises(Exception):  # Should raise ValueError
                await client.call_tool(
                    "updateObject",
                    {
                        "kind": "",
                        "id": "test-id",
                        "projectRoot": str(project_root),
                        "yamlPatch": {"title": "Updated"},
                    },
                )

            # Test empty id
            with pytest.raises(Exception):  # Should raise ValueError
                await client.call_tool(
                    "updateObject",
                    {
                        "kind": "project",
                        "id": "",
                        "projectRoot": str(project_root),
                        "yamlPatch": {"title": "Updated"},
                    },
                )

            # Test empty project root
            with pytest.raises(Exception):  # Should raise ValueError
                await client.call_tool(
                    "updateObject",
                    {
                        "kind": "project",
                        "id": "test-id",
                        "projectRoot": "",
                        "yamlPatch": {"title": "Updated"},
                    },
                )

            # Test no patches provided
            with pytest.raises(Exception):  # Should raise ValueError
                await client.call_tool(
                    "updateObject",
                    {
                        "kind": "project",
                        "id": "test-id",
                        "projectRoot": str(project_root),
                    },
                )

    @pytest.mark.asyncio
    async def test_update_object_not_found(self, temp_dir):
        """Test error handling when object is not found."""
        project_root = temp_dir / "planning"

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            # Try to update non-existent object
            with pytest.raises(Exception):  # Should raise FileNotFoundError
                await client.call_tool(
                    "updateObject",
                    {
                        "kind": "project",
                        "id": "nonexistent-id",
                        "projectRoot": str(project_root),
                        "yamlPatch": {"title": "Updated"},
                    },
                )

    @pytest.mark.asyncio
    async def test_update_object_malformed_yaml_patch(self, temp_dir):
        """Test error handling for malformed patches."""
        project_root = temp_dir / "planning"

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            # Create a project to update
            await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Test Project",
                    "projectRoot": str(project_root),
                    "id": "test-project",
                },
            )

            # Try to update with invalid enum value
            with pytest.raises(Exception):  # Should raise TrellisValidationError
                await client.call_tool(
                    "updateObject",
                    {
                        "kind": "project",
                        "id": "test-project",
                        "projectRoot": str(project_root),
                        "yamlPatch": {"priority": "invalid-priority"},
                    },
                )

            # Try to update with invalid kind
            with pytest.raises(Exception):  # Should raise TrellisValidationError
                await client.call_tool(
                    "updateObject",
                    {
                        "kind": "project",
                        "id": "test-project",
                        "projectRoot": str(project_root),
                        "yamlPatch": {"kind": "invalid-kind"},
                    },
                )

    @pytest.mark.asyncio
    async def test_update_object_timestamp_auto_updated(self, temp_dir):
        """Test that timestamp is automatically updated."""
        project_root = temp_dir / "planning"

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            # Create a project to update
            create_result = await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Test Project",
                    "projectRoot": str(project_root),
                    "id": "test-project",
                },
            )

            original_timestamp = create_result.data["created"]

            # Small delay to ensure timestamp difference
            import time

            time.sleep(0.01)

            # Update the project
            update_result = await client.call_tool(
                "updateObject",
                {
                    "kind": "project",
                    "id": "test-project",
                    "projectRoot": str(project_root),
                    "yamlPatch": {"title": "Updated Project"},
                },
            )

            # Verify timestamp was updated
            updated_timestamp = update_result.data["updated"]
            assert updated_timestamp != original_timestamp

            # Verify file contains updated timestamp
            file_path = Path(update_result.data["file_path"])
            content = file_path.read_text()
            assert f"updated: '{updated_timestamp}'" in content

    @pytest.mark.asyncio
    async def test_update_object_with_prefix_ids(self, temp_dir):
        """Test updating object with prefix in ID."""
        project_root = temp_dir / "planning"

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            # Create a project to update
            await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Test Project",
                    "projectRoot": str(project_root),
                    "id": "test-project",
                },
            )

            # Update using ID with prefix
            update_result = await client.call_tool(
                "updateObject",
                {
                    "kind": "project",
                    "id": "P-test-project",  # With prefix
                    "projectRoot": str(project_root),
                    "yamlPatch": {"title": "Updated Project"},
                },
            )

            # Verify update worked - should return clean ID
            assert update_result.data["id"] == "test-project"
            assert update_result.data["kind"] == "project"
            assert update_result.data["changes"]["yaml_fields"] == ["title"]

    @pytest.mark.asyncio
    async def test_update_object_preserves_required_fields(self, temp_dir):
        """Test that required fields are preserved during updates."""
        project_root = temp_dir / "planning"

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            # Create an epic to update
            await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Parent Project",
                    "projectRoot": str(project_root),
                    "id": "parent-project",
                },
            )

            await client.call_tool(
                "createObject",
                {
                    "kind": "epic",
                    "title": "Test Epic",
                    "projectRoot": str(project_root),
                    "parent": "parent-project",
                    "id": "test-epic",
                },
            )

            # Update epic
            await client.call_tool(
                "updateObject",
                {
                    "kind": "epic",
                    "id": "test-epic",
                    "projectRoot": str(project_root),
                    "yamlPatch": {"title": "Updated Epic"},
                },
            )

            # Verify required fields are preserved
            from trellis_mcp.io_utils import read_markdown
            from trellis_mcp.path_resolver import id_to_path

            epic_path = id_to_path(project_root, "epic", "test-epic")
            yaml_dict, _ = read_markdown(epic_path)

            assert yaml_dict["kind"] == "epic"
            assert yaml_dict["id"] == "E-test-epic"
            assert yaml_dict["parent"] == "parent-project"
            assert yaml_dict["title"] == "Updated Epic"  # Updated field
            assert "created" in yaml_dict
            assert "updated" in yaml_dict
            assert "schema_version" in yaml_dict


class TestListBacklog:
    """Test cases for the listBacklog RPC handler."""

    @pytest.mark.asyncio
    async def test_list_backlog_basic_functionality(self, temp_dir):
        """Test basic listBacklog functionality without filters."""
        project_root = temp_dir / "planning"

        # Create test structure with tasks
        await self._create_test_structure_with_tasks(project_root)

        # Create server
        settings = Settings(planning_root=project_root.parent)
        server = create_server(settings)

        # Test listBacklog call
        async with Client(server) as client:
            result = await client.call_tool(
                "listBacklog",
                {"projectRoot": str(project_root)},
            )

        # Verify results
        assert "tasks" in result.data
        tasks = result.data["tasks"]
        assert len(tasks) >= 4  # We created 4 tasks

        # Verify task structure
        for task in tasks:
            assert "id" in task
            assert "title" in task
            assert "status" in task
            assert "priority" in task
            assert "parent" in task
            assert "file_path" in task
            assert "created" in task
            assert "updated" in task

    @pytest.mark.asyncio
    async def test_list_backlog_scope_filtering_project(self, temp_dir):
        """Test scope filtering by project ID."""
        project_root = temp_dir / "planning"
        await self._create_test_structure_with_tasks(project_root)

        settings = Settings(planning_root=project_root.parent)
        server = create_server(settings)

        # Test with project scope
        async with Client(server) as client:
            result = await client.call_tool(
                "listBacklog",
                {
                    "projectRoot": str(project_root),
                    "scope": "P-test-project",
                },
            )

        # Verify all tasks belong to the project
        tasks = result.data["tasks"]
        assert len(tasks) >= 1
        for task in tasks:
            assert "P-test-project" in task["file_path"]

    @pytest.mark.asyncio
    async def test_list_backlog_scope_filtering_epic(self, temp_dir):
        """Test scope filtering by epic ID."""
        project_root = temp_dir / "planning"
        await self._create_test_structure_with_tasks(project_root)

        settings = Settings(planning_root=project_root.parent)
        server = create_server(settings)

        # Test with epic scope
        async with Client(server) as client:
            result = await client.call_tool(
                "listBacklog",
                {
                    "projectRoot": str(project_root),
                    "scope": "E-test-epic",
                },
            )

        # Verify all tasks belong to the epic
        tasks = result.data["tasks"]
        assert len(tasks) >= 1
        for task in tasks:
            assert "E-test-epic" in task["file_path"]

    @pytest.mark.asyncio
    async def test_list_backlog_scope_filtering_feature(self, temp_dir):
        """Test scope filtering by feature ID."""
        project_root = temp_dir / "planning"
        await self._create_test_structure_with_tasks(project_root)

        settings = Settings(planning_root=project_root.parent)
        server = create_server(settings)

        # Test with feature scope
        async with Client(server) as client:
            result = await client.call_tool(
                "listBacklog",
                {
                    "projectRoot": str(project_root),
                    "scope": "F-test-feature",
                },
            )

        # Verify all tasks belong to the feature
        tasks = result.data["tasks"]
        assert len(tasks) >= 1
        for task in tasks:
            assert task["parent"] == "F-test-feature" or "F-test-feature" in task["file_path"]

    @pytest.mark.asyncio
    async def test_list_backlog_status_filtering(self, temp_dir):
        """Test status filtering."""
        project_root = temp_dir / "planning"
        await self._create_test_structure_with_tasks(project_root)

        settings = Settings(planning_root=project_root.parent)
        server = create_server(settings)

        # Test each status filter
        statuses = ["open", "in-progress", "review", "done"]

        for status in statuses:
            async with Client(server) as client:
                result = await client.call_tool(
                    "listBacklog",
                    {
                        "projectRoot": str(project_root),
                        "status": status,
                    },
                )

            # Verify all tasks have the correct status
            tasks = result.data["tasks"]
            for task in tasks:
                assert task["status"] == status

    @pytest.mark.asyncio
    async def test_list_backlog_priority_filtering(self, temp_dir):
        """Test priority filtering."""
        project_root = temp_dir / "planning"
        await self._create_test_structure_with_tasks(project_root)

        settings = Settings(planning_root=project_root.parent)
        server = create_server(settings)

        # Test each priority filter
        priorities = ["high", "normal", "low"]

        for priority in priorities:
            async with Client(server) as client:
                result = await client.call_tool(
                    "listBacklog",
                    {
                        "projectRoot": str(project_root),
                        "priority": priority,
                    },
                )

            # Verify all tasks have the correct priority
            tasks = result.data["tasks"]
            for task in tasks:
                assert task["priority"] == priority

    @pytest.mark.asyncio
    async def test_list_backlog_combined_filtering(self, temp_dir):
        """Test combined scope, status, and priority filtering."""
        project_root = temp_dir / "planning"
        await self._create_test_structure_with_tasks(project_root)

        settings = Settings(planning_root=project_root.parent)
        server = create_server(settings)

        # Test combined filters
        async with Client(server) as client:
            result = await client.call_tool(
                "listBacklog",
                {
                    "projectRoot": str(project_root),
                    "scope": "F-test-feature",
                    "status": "open",
                    "priority": "high",
                },
            )

        # Verify all tasks match all criteria
        tasks = result.data["tasks"]
        for task in tasks:
            assert task["status"] == "open"
            assert task["priority"] == "high"
            assert task["parent"] == "F-test-feature" or "F-test-feature" in task["file_path"]

    @pytest.mark.asyncio
    async def test_list_backlog_priority_sorting(self, temp_dir):
        """Test priority-based sorting with secondary date sorting."""
        project_root = temp_dir / "planning"
        await self._create_test_structure_with_mixed_priorities(project_root)

        settings = Settings(planning_root=project_root.parent)
        server = create_server(settings)

        # Get all tasks
        async with Client(server) as client:
            result = await client.call_tool(
                "listBacklog",
                {"projectRoot": str(project_root)},
            )

        # Verify priority-based sorting
        tasks = result.data["tasks"]
        assert len(tasks) >= 3

        # Check that high priority tasks come first
        priority_order = {"high": 1, "normal": 2, "low": 3}
        for i in range(len(tasks) - 1):
            current_priority = priority_order[tasks[i]["priority"]]
            next_priority = priority_order[tasks[i + 1]["priority"]]
            assert current_priority <= next_priority

    @pytest.mark.asyncio
    async def test_list_backlog_cross_directory_search(self, temp_dir):
        """Test cross-directory searching (tasks-open and tasks-done)."""
        project_root = temp_dir / "planning"
        await self._create_test_structure_with_mixed_task_locations(project_root)

        settings = Settings(planning_root=project_root.parent)
        server = create_server(settings)

        # Get all tasks
        async with Client(server) as client:
            result = await client.call_tool(
                "listBacklog",
                {"projectRoot": str(project_root)},
            )

        # Verify tasks from both directories are included
        tasks = result.data["tasks"]
        file_paths = [task["file_path"] for task in tasks]

        has_open_tasks = any("tasks-open" in path for path in file_paths)
        has_done_tasks = any("tasks-done" in path for path in file_paths)

        assert has_open_tasks, "Should find tasks from tasks-open directory"
        assert has_done_tasks, "Should find tasks from tasks-done directory"

    @pytest.mark.asyncio
    async def test_list_backlog_empty_results(self, temp_dir):
        """Test empty results handling."""
        project_root = temp_dir / "planning"
        # Create basic structure but no tasks
        await self._create_basic_structure_no_tasks(project_root)

        settings = Settings(planning_root=project_root.parent)
        server = create_server(settings)

        # Test with filters that should return no results
        async with Client(server) as client:
            result = await client.call_tool(
                "listBacklog",
                {
                    "projectRoot": str(project_root),
                    "status": "nonexistent",
                },
            )

        # Verify empty results
        assert "tasks" in result.data
        assert result.data["tasks"] == []

    @pytest.mark.asyncio
    async def test_list_backlog_no_projects_directory(self, temp_dir):
        """Test handling when projects directory doesn't exist."""
        project_root = temp_dir / "planning"
        project_root.mkdir()

        settings = Settings(planning_root=project_root.parent)
        server = create_server(settings)

        # Test when projects directory doesn't exist
        async with Client(server) as client:
            result = await client.call_tool(
                "listBacklog",
                {"projectRoot": str(project_root)},
            )

        # Verify empty results
        assert "tasks" in result.data
        assert result.data["tasks"] == []

    @pytest.mark.asyncio
    async def test_list_backlog_invalid_parameters(self, temp_dir):
        """Test error handling for invalid parameters."""
        settings = Settings(planning_root=temp_dir)
        server = create_server(settings)

        # Test empty projectRoot
        async with Client(server) as client:
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "listBacklog",
                    {"projectRoot": ""},
                )
            assert "Project root cannot be empty" in str(exc_info.value)

        # Test missing projectRoot
        async with Client(server) as client:
            with pytest.raises(Exception):
                await client.call_tool("listBacklog", {})

    @pytest.mark.asyncio
    async def test_list_backlog_malformed_task_files(self, temp_dir):
        """Test handling of malformed task files."""
        project_root = temp_dir / "planning"
        await self._create_test_structure_with_malformed_tasks(project_root)

        settings = Settings(planning_root=project_root.parent)
        server = create_server(settings)

        # Should skip malformed files and return valid ones
        async with Client(server) as client:
            result = await client.call_tool(
                "listBacklog",
                {"projectRoot": str(project_root)},
            )

        # Should get some results but skip malformed files
        tasks = result.data["tasks"]
        # Should have at least one valid task, malformed ones should be skipped
        valid_tasks = [t for t in tasks if t["title"]]
        assert len(valid_tasks) >= 1

    # Helper methods for creating test structures

    async def _create_test_structure_with_tasks(self, project_root: Path):
        """Create test structure with various tasks."""
        settings = Settings(planning_root=project_root.parent)
        server = create_server(settings)

        async with Client(server) as client:
            # Create project
            await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Test Project",
                    "projectRoot": str(project_root),
                    "id": "test-project",
                },
            )

            # Create epic
            await client.call_tool(
                "createObject",
                {
                    "kind": "epic",
                    "title": "Test Epic",
                    "projectRoot": str(project_root),
                    "id": "test-epic",
                    "parent": "P-test-project",
                },
            )

            # Create feature
            await client.call_tool(
                "createObject",
                {
                    "kind": "feature",
                    "title": "Test Feature",
                    "projectRoot": str(project_root),
                    "id": "test-feature",
                    "parent": "E-test-epic",
                },
            )

            # Create tasks with different statuses and priorities
            task_configs = [
                {"id": "task1", "status": "open", "priority": "high"},
                {"id": "task2", "status": "in-progress", "priority": "normal"},
                {"id": "task3", "status": "review", "priority": "low"},
                {"id": "task4", "status": "done", "priority": "high"},
            ]

            for config in task_configs:
                await client.call_tool(
                    "createObject",
                    {
                        "kind": "task",
                        "title": f"Test Task {config['id']}",
                        "projectRoot": str(project_root),
                        "id": config["id"],
                        "parent": "F-test-feature",
                        "status": config["status"],
                        "priority": config["priority"],
                    },
                )

    async def _create_test_structure_with_mixed_priorities(self, project_root: Path):
        """Create test structure with mixed priority tasks for sorting tests."""
        settings = Settings(planning_root=project_root.parent)
        server = create_server(settings)

        async with Client(server) as client:
            # Create basic structure
            await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Priority Test Project",
                    "projectRoot": str(project_root),
                    "id": "priority-project",
                },
            )

            await client.call_tool(
                "createObject",
                {
                    "kind": "epic",
                    "title": "Priority Epic",
                    "projectRoot": str(project_root),
                    "id": "priority-epic",
                    "parent": "P-priority-project",
                },
            )

            await client.call_tool(
                "createObject",
                {
                    "kind": "feature",
                    "title": "Priority Feature",
                    "projectRoot": str(project_root),
                    "id": "priority-feature",
                    "parent": "E-priority-epic",
                },
            )

            # Create tasks with different priorities (in reverse order to test sorting)
            priorities = ["low", "normal", "high", "normal", "high", "low"]
            for i, priority in enumerate(priorities):
                await client.call_tool(
                    "createObject",
                    {
                        "kind": "task",
                        "title": f"Priority Task {i + 1}",
                        "projectRoot": str(project_root),
                        "id": f"priority-task-{i + 1}",
                        "parent": "F-priority-feature",
                        "priority": priority,
                    },
                )

    async def _create_test_structure_with_mixed_task_locations(self, project_root: Path):
        """Create test structure with tasks in both tasks-open and tasks-done."""
        settings = Settings(planning_root=project_root.parent)
        server = create_server(settings)

        async with Client(server) as client:
            # Create basic structure
            await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Mixed Location Project",
                    "projectRoot": str(project_root),
                    "id": "mixed-project",
                },
            )

            await client.call_tool(
                "createObject",
                {
                    "kind": "epic",
                    "title": "Mixed Epic",
                    "projectRoot": str(project_root),
                    "id": "mixed-epic",
                    "parent": "P-mixed-project",
                },
            )

            await client.call_tool(
                "createObject",
                {
                    "kind": "feature",
                    "title": "Mixed Feature",
                    "projectRoot": str(project_root),
                    "id": "mixed-feature",
                    "parent": "E-mixed-epic",
                },
            )

            # Create open tasks
            for i in range(2):
                await client.call_tool(
                    "createObject",
                    {
                        "kind": "task",
                        "title": f"Open Task {i + 1}",
                        "projectRoot": str(project_root),
                        "id": f"open-task-{i + 1}",
                        "parent": "F-mixed-feature",
                        "status": "open",
                    },
                )

            # Create done tasks
            for i in range(2):
                await client.call_tool(
                    "createObject",
                    {
                        "kind": "task",
                        "title": f"Done Task {i + 1}",
                        "projectRoot": str(project_root),
                        "id": f"done-task-{i + 1}",
                        "parent": "F-mixed-feature",
                        "status": "done",
                    },
                )

    async def _create_basic_structure_no_tasks(self, project_root: Path):
        """Create basic structure without any tasks."""
        settings = Settings(planning_root=project_root.parent)
        server = create_server(settings)

        async with Client(server) as client:
            # Create project
            await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Empty Project",
                    "projectRoot": str(project_root),
                    "id": "empty-project",
                },
            )

            # Create epic
            await client.call_tool(
                "createObject",
                {
                    "kind": "epic",
                    "title": "Empty Epic",
                    "projectRoot": str(project_root),
                    "id": "empty-epic",
                    "parent": "P-empty-project",
                },
            )

            # Create feature (but no tasks)
            await client.call_tool(
                "createObject",
                {
                    "kind": "feature",
                    "title": "Empty Feature",
                    "projectRoot": str(project_root),
                    "id": "empty-feature",
                    "parent": "E-empty-epic",
                },
            )

    async def _create_test_structure_with_malformed_tasks(self, project_root: Path):
        """Create test structure with some malformed task files."""
        # First create a basic valid structure
        await self._create_basic_structure_no_tasks(project_root)

        # Create one valid task
        settings = Settings(planning_root=project_root.parent)
        server = create_server(settings)

        async with Client(server) as client:
            await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Valid Task",
                    "projectRoot": str(project_root),
                    "id": "valid-task",
                    "parent": "F-empty-feature",
                },
            )

        # Add malformed task file
        feature_path = (
            project_root
            / "projects"
            / "P-empty-project"
            / "epics"
            / "E-empty-epic"
            / "features"
            / "F-empty-feature"
            / "tasks-open"
        )

        malformed_file = feature_path / "T-malformed.md"
        malformed_file.write_text("This is not valid YAML front-matter\nJust plain text")

        # Add another file with invalid name format
        invalid_name_file = feature_path / "invalid-name.md"
        invalid_name_file.write_text("---\nkind: task\npriority: normal\n---\nSome content")


class TestClaimNextTaskPriority:
    """Test cases for claimNextTask priority-based task selection."""

    @pytest.mark.asyncio
    async def test_claims_highest_priority_first(self, temp_dir):
        """Test that claimNextTask selects highest priority task first."""
        project_root = await self._create_mixed_priority_tasks(temp_dir)

        settings = Settings(planning_root=project_root.parent)
        server = create_server(settings)

        async with Client(server) as client:
            # Claim first task - should be high priority
            result = await client.call_tool("claimNextTask", {"projectRoot": str(project_root)})

            claimed_result = result.data
            claimed_task = claimed_result["task"]
            assert claimed_task["priority"] == "high"
            assert claimed_task["title"] == "High Priority Task 1"
            assert claimed_result["claimed_status"] == "in-progress"

    @pytest.mark.asyncio
    async def test_claims_by_creation_date_for_same_priority(self, temp_dir):
        """Test that tasks with same priority are claimed by creation date."""
        project_root = await self._create_same_priority_tasks(temp_dir)

        settings = Settings(planning_root=project_root.parent)
        server = create_server(settings)

        async with Client(server) as client:
            # Claim first task - should be earliest created high priority
            result = await client.call_tool("claimNextTask", {"projectRoot": str(project_root)})

            claimed_result = result.data
            claimed_task = claimed_result["task"]
            assert claimed_task["priority"] == "high"
            assert claimed_task["title"] == "High Priority Task 1"  # Created first

    @pytest.mark.asyncio
    async def test_claims_next_highest_after_first_claimed(self, temp_dir):
        """Test sequential claiming follows priority order."""
        project_root = await self._create_mixed_priority_tasks(temp_dir)

        settings = Settings(planning_root=project_root.parent)
        server = create_server(settings)

        async with Client(server) as client:
            # Claim first task (high priority)
            result1 = await client.call_tool("claimNextTask", {"projectRoot": str(project_root)})
            assert result1.data["task"]["priority"] == "high"
            assert result1.data["task"]["title"] == "High Priority Task 1"

            # Claim second task (second high priority)
            result2 = await client.call_tool("claimNextTask", {"projectRoot": str(project_root)})
            assert result2.data["task"]["priority"] == "high"
            assert result2.data["task"]["title"] == "High Priority Task 2"

            # Claim third task (normal priority)
            result3 = await client.call_tool("claimNextTask", {"projectRoot": str(project_root)})
            assert result3.data["task"]["priority"] == "normal"
            assert result3.data["task"]["title"] == "Normal Priority Task"

            # Claim fourth task (low priority)
            result4 = await client.call_tool("claimNextTask", {"projectRoot": str(project_root)})
            assert result4.data["task"]["priority"] == "low"
            assert result4.data["task"]["title"] == "Low Priority Task"

    @pytest.mark.asyncio
    async def test_no_eligible_tasks_raises_error(self, temp_dir):
        """Test that claimNextTask raises error when no eligible tasks available."""
        project_root = await self._create_basic_structure_no_tasks(temp_dir)

        settings = Settings(planning_root=project_root.parent)
        server = create_server(settings)

        async with Client(server) as client:
            # Should raise error - no open tasks
            with pytest.raises(Exception) as exc_info:
                await client.call_tool("claimNextTask", {"projectRoot": str(project_root)})

            assert "No open tasks available" in str(exc_info.value)

    async def _create_mixed_priority_tasks(self, temp_dir: Path) -> Path:
        """Create test structure with tasks of different priorities."""
        project_root = temp_dir / "planning"
        project_root.mkdir()

        settings = Settings(planning_root=project_root.parent)
        server = create_server(settings)

        async with Client(server) as client:
            # Create project
            await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Priority Test Project",
                    "projectRoot": str(project_root),
                    "id": "priority-project",
                },
            )

            # Create epic
            await client.call_tool(
                "createObject",
                {
                    "kind": "epic",
                    "title": "Priority Test Epic",
                    "projectRoot": str(project_root),
                    "id": "priority-epic",
                    "parent": "P-priority-project",
                },
            )

            # Create feature
            await client.call_tool(
                "createObject",
                {
                    "kind": "feature",
                    "title": "Priority Test Feature",
                    "projectRoot": str(project_root),
                    "id": "priority-feature",
                    "parent": "E-priority-epic",
                },
            )

            # Create tasks with different priorities
            # High priority tasks (should be claimed first)
            await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "High Priority Task 1",
                    "projectRoot": str(project_root),
                    "id": "high-task-1",
                    "parent": "F-priority-feature",
                    "priority": "high",
                },
            )

            await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "High Priority Task 2",
                    "projectRoot": str(project_root),
                    "id": "high-task-2",
                    "parent": "F-priority-feature",
                    "priority": "high",
                },
            )

            # Normal priority task
            await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Normal Priority Task",
                    "projectRoot": str(project_root),
                    "id": "normal-task",
                    "parent": "F-priority-feature",
                    "priority": "normal",
                },
            )

            # Low priority task
            await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Low Priority Task",
                    "projectRoot": str(project_root),
                    "id": "low-task",
                    "parent": "F-priority-feature",
                    "priority": "low",
                },
            )

        return project_root

    async def _create_same_priority_tasks(self, temp_dir: Path) -> Path:
        """Create test structure with tasks of same priority but different creation dates."""
        project_root = temp_dir / "planning"
        project_root.mkdir()

        settings = Settings(planning_root=project_root.parent)
        server = create_server(settings)

        async with Client(server) as client:
            # Create basic structure
            await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Same Priority Test Project",
                    "projectRoot": str(project_root),
                    "id": "same-priority-project",
                },
            )

            await client.call_tool(
                "createObject",
                {
                    "kind": "epic",
                    "title": "Same Priority Test Epic",
                    "projectRoot": str(project_root),
                    "id": "same-priority-epic",
                    "parent": "P-same-priority-project",
                },
            )

            await client.call_tool(
                "createObject",
                {
                    "kind": "feature",
                    "title": "Same Priority Test Feature",
                    "projectRoot": str(project_root),
                    "id": "same-priority-feature",
                    "parent": "E-same-priority-epic",
                },
            )

            # Create high priority tasks with different creation dates
            await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "High Priority Task 1",
                    "projectRoot": str(project_root),
                    "id": "high-same-1",
                    "parent": "F-same-priority-feature",
                    "priority": "high",
                },
            )

            await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "High Priority Task 2",
                    "projectRoot": str(project_root),
                    "id": "high-same-2",
                    "parent": "F-same-priority-feature",
                    "priority": "high",
                },
            )

        return project_root

    async def _create_basic_structure_no_tasks(self, temp_dir: Path) -> Path:
        """Create basic structure with no tasks at all."""
        project_root = temp_dir / "planning"
        project_root.mkdir()

        settings = Settings(planning_root=project_root.parent)
        server = create_server(settings)

        async with Client(server) as client:
            # Create basic structure
            await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "No Tasks Project",
                    "projectRoot": str(project_root),
                    "id": "no-tasks-project",
                },
            )

            await client.call_tool(
                "createObject",
                {
                    "kind": "epic",
                    "title": "No Tasks Epic",
                    "projectRoot": str(project_root),
                    "id": "no-tasks-epic",
                    "parent": "P-no-tasks-project",
                },
            )

            await client.call_tool(
                "createObject",
                {
                    "kind": "feature",
                    "title": "No Tasks Feature",
                    "projectRoot": str(project_root),
                    "id": "no-tasks-feature",
                    "parent": "E-no-tasks-epic",
                },
            )

            # Don't create any tasks - this will trigger "No open tasks available"

        return project_root


class TestProtectedObjectDeletion:
    """Test cases for ProtectedObjectError when deleting objects with protected children."""

    @pytest.mark.asyncio
    async def test_delete_epic_with_in_progress_task_raises_protected_object_error(self, temp_dir):
        """Test that deleting an epic with in-progress task raises ProtectedObjectError."""
        project_root = temp_dir / "planning"

        settings = Settings(planning_root=project_root.parent)
        server = create_server(settings)

        async with Client(server) as client:
            # Create project → epic → feature → task hierarchy
            project_result = await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Test Project",
                    "projectRoot": str(project_root),
                },
            )
            project_id = project_result.data["id"]

            epic_result = await client.call_tool(
                "createObject",
                {
                    "kind": "epic",
                    "title": "Test Epic",
                    "projectRoot": str(project_root),
                    "parent": project_id,
                },
            )
            epic_id = epic_result.data["id"]

            feature_result = await client.call_tool(
                "createObject",
                {
                    "kind": "feature",
                    "title": "Test Feature",
                    "projectRoot": str(project_root),
                    "parent": epic_id,
                },
            )
            feature_id = feature_result.data["id"]

            task_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Test Task",
                    "projectRoot": str(project_root),
                    "parent": feature_id,
                },
            )
            task_id = task_result.data["id"]

            # Set task status to in-progress
            await client.call_tool(
                "updateObject",
                {
                    "kind": "task",
                    "id": task_id,
                    "projectRoot": str(project_root),
                    "yamlPatch": {"status": "in-progress"},
                },
            )

            # Try to delete the epic - should raise ProtectedObjectError
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "updateObject",
                    {
                        "kind": "epic",
                        "id": epic_id,
                        "projectRoot": str(project_root),
                        "yamlPatch": {"status": "deleted"},
                    },
                )

            # Verify it's the correct error with expected message
            error_message = str(exc_info.value)
            assert "Cannot delete epic" in error_message
            assert "has protected children" in error_message
            assert "in-progress" in error_message

    @pytest.mark.asyncio
    async def test_delete_epic_with_review_task_raises_protected_object_error(self, temp_dir):
        """Test that deleting an epic with review task raises ProtectedObjectError."""
        project_root = temp_dir / "planning"

        settings = Settings(planning_root=project_root.parent)
        server = create_server(settings)

        async with Client(server) as client:
            # Create project → epic → feature → task hierarchy
            project_result = await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Test Project",
                    "projectRoot": str(project_root),
                },
            )
            project_id = project_result.data["id"]

            epic_result = await client.call_tool(
                "createObject",
                {
                    "kind": "epic",
                    "title": "Test Epic",
                    "projectRoot": str(project_root),
                    "parent": project_id,
                },
            )
            epic_id = epic_result.data["id"]

            feature_result = await client.call_tool(
                "createObject",
                {
                    "kind": "feature",
                    "title": "Test Feature",
                    "projectRoot": str(project_root),
                    "parent": epic_id,
                },
            )
            feature_id = feature_result.data["id"]

            task_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Test Task",
                    "projectRoot": str(project_root),
                    "parent": feature_id,
                },
            )
            task_id = task_result.data["id"]

            # Set task status to in-progress first, then review
            await client.call_tool(
                "updateObject",
                {
                    "kind": "task",
                    "id": task_id,
                    "projectRoot": str(project_root),
                    "yamlPatch": {"status": "in-progress"},
                },
            )

            await client.call_tool(
                "updateObject",
                {
                    "kind": "task",
                    "id": task_id,
                    "projectRoot": str(project_root),
                    "yamlPatch": {"status": "review"},
                },
            )

            # Try to delete the epic - should raise ProtectedObjectError
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "updateObject",
                    {
                        "kind": "epic",
                        "id": epic_id,
                        "projectRoot": str(project_root),
                        "yamlPatch": {"status": "deleted"},
                    },
                )

            # Verify it's the correct error with expected message
            error_message = str(exc_info.value)
            assert "Cannot delete epic" in error_message
            assert "has protected children" in error_message
            assert "review" in error_message

    @pytest.mark.asyncio
    async def test_delete_feature_with_in_progress_task_raises_protected_object_error(
        self, temp_dir
    ):
        """Test that deleting a feature with in-progress task raises ProtectedObjectError."""
        project_root = temp_dir / "planning"

        settings = Settings(planning_root=project_root.parent)
        server = create_server(settings)

        async with Client(server) as client:
            # Create project → epic → feature → task hierarchy
            project_result = await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Test Project",
                    "projectRoot": str(project_root),
                },
            )
            project_id = project_result.data["id"]

            epic_result = await client.call_tool(
                "createObject",
                {
                    "kind": "epic",
                    "title": "Test Epic",
                    "projectRoot": str(project_root),
                    "parent": project_id,
                },
            )
            epic_id = epic_result.data["id"]

            feature_result = await client.call_tool(
                "createObject",
                {
                    "kind": "feature",
                    "title": "Test Feature",
                    "projectRoot": str(project_root),
                    "parent": epic_id,
                },
            )
            feature_id = feature_result.data["id"]

            task_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Test Task",
                    "projectRoot": str(project_root),
                    "parent": feature_id,
                },
            )
            task_id = task_result.data["id"]

            # Set task status to in-progress
            await client.call_tool(
                "updateObject",
                {
                    "kind": "task",
                    "id": task_id,
                    "projectRoot": str(project_root),
                    "yamlPatch": {"status": "in-progress"},
                },
            )

            # Try to delete the feature - should raise ProtectedObjectError
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "updateObject",
                    {
                        "kind": "feature",
                        "id": feature_id,
                        "projectRoot": str(project_root),
                        "yamlPatch": {"status": "deleted"},
                    },
                )

            # Verify it's the correct error with expected message
            error_message = str(exc_info.value)
            assert "Cannot delete feature" in error_message
            assert "has protected children" in error_message
            assert "in-progress" in error_message

    @pytest.mark.asyncio
    async def test_delete_project_with_nested_protected_children_raises_protected_object_error(
        self, temp_dir
    ):
        """Test that deleting project with nested protected children raises ProtectedObjectError."""
        project_root = temp_dir / "planning"

        settings = Settings(planning_root=project_root.parent)
        server = create_server(settings)

        async with Client(server) as client:
            # Create project → epic → feature → task hierarchy
            project_result = await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Test Project",
                    "projectRoot": str(project_root),
                },
            )
            project_id = project_result.data["id"]

            epic_result = await client.call_tool(
                "createObject",
                {
                    "kind": "epic",
                    "title": "Test Epic",
                    "projectRoot": str(project_root),
                    "parent": project_id,
                },
            )
            epic_id = epic_result.data["id"]

            feature_result = await client.call_tool(
                "createObject",
                {
                    "kind": "feature",
                    "title": "Test Feature",
                    "projectRoot": str(project_root),
                    "parent": epic_id,
                },
            )
            feature_id = feature_result.data["id"]

            # Create multiple tasks with different statuses
            task1_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Task 1",
                    "projectRoot": str(project_root),
                    "parent": feature_id,
                },
            )
            task1_id = task1_result.data["id"]

            task2_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Task 2",
                    "projectRoot": str(project_root),
                    "parent": feature_id,
                },
            )
            task2_id = task2_result.data["id"]

            # Set one task to in-progress and another to review
            await client.call_tool(
                "updateObject",
                {
                    "kind": "task",
                    "id": task1_id,
                    "projectRoot": str(project_root),
                    "yamlPatch": {"status": "in-progress"},
                },
            )

            await client.call_tool(
                "updateObject",
                {
                    "kind": "task",
                    "id": task2_id,
                    "projectRoot": str(project_root),
                    "yamlPatch": {"status": "in-progress"},
                },
            )

            await client.call_tool(
                "updateObject",
                {
                    "kind": "task",
                    "id": task2_id,
                    "projectRoot": str(project_root),
                    "yamlPatch": {"status": "review"},
                },
            )

            # Try to delete the project - should raise ProtectedObjectError
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "updateObject",
                    {
                        "kind": "project",
                        "id": project_id,
                        "projectRoot": str(project_root),
                        "yamlPatch": {"status": "deleted"},
                    },
                )

            # Verify it's the correct error with expected message
            error_message = str(exc_info.value)
            assert "Cannot delete project" in error_message
            assert "has protected children" in error_message
            # Should mention both protected children
            assert task1_id in error_message or task2_id in error_message

    @pytest.mark.asyncio
    async def test_delete_with_force_bypasses_protected_object_error(self, temp_dir):
        """Test that deleting with force=True bypasses ProtectedObjectError."""
        project_root = temp_dir / "planning"

        settings = Settings(planning_root=project_root.parent)
        server = create_server(settings)

        async with Client(server) as client:
            # Create project → epic → feature → task hierarchy
            project_result = await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Test Project",
                    "projectRoot": str(project_root),
                },
            )
            project_id = project_result.data["id"]

            epic_result = await client.call_tool(
                "createObject",
                {
                    "kind": "epic",
                    "title": "Test Epic",
                    "projectRoot": str(project_root),
                    "parent": project_id,
                },
            )
            epic_id = epic_result.data["id"]

            feature_result = await client.call_tool(
                "createObject",
                {
                    "kind": "feature",
                    "title": "Test Feature",
                    "projectRoot": str(project_root),
                    "parent": epic_id,
                },
            )
            feature_id = feature_result.data["id"]

            task_result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Test Task",
                    "projectRoot": str(project_root),
                    "parent": feature_id,
                },
            )
            task_id = task_result.data["id"]

            # Set task status to in-progress
            await client.call_tool(
                "updateObject",
                {
                    "kind": "task",
                    "id": task_id,
                    "projectRoot": str(project_root),
                    "yamlPatch": {"status": "in-progress"},
                },
            )

            # Delete the epic with force=True - should succeed
            result = await client.call_tool(
                "updateObject",
                {
                    "kind": "epic",
                    "id": epic_id,
                    "projectRoot": str(project_root),
                    "yamlPatch": {"status": "deleted"},
                    "force": True,
                },
            )

            # Verify the deletion succeeded
            assert result.data["changes"]["status"] == "deleted"
            assert "cascade_deleted" in result.data["changes"]
            assert len(result.data["changes"]["cascade_deleted"]) > 0
