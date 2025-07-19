"""Tests for Trellis MCP server CRUD operation functionality.

Tests for getObject, createObject, and updateObject RPC handlers to ensure
proper object lifecycle management and data integrity.
"""

from pathlib import Path

import pytest
from fastmcp import Client

from trellis_mcp.server import create_server
from trellis_mcp.settings import Settings


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
            # Create project first
            create_result = await client.call_tool(
                "createObject",
                {
                    "kind": "project",
                    "title": "Test Project",
                    "projectRoot": str(project_root),
                    "id": "test-project",
                },
            )

            # Update project
            result = await client.call_tool(
                "updateObject",
                {
                    "kind": "project",
                    "id": "test-project",
                    "projectRoot": str(project_root),
                    "yamlPatch": {"priority": "high"},
                },
            )

        # Verify update results
        assert result.data["id"] == "test-project"
        assert "changes" in result.data

        # Verify file was updated
        file_path = Path(create_result.data["file_path"])
        content = file_path.read_text()
        assert "priority: high" in content

    @pytest.mark.asyncio
    async def test_update_task_status_transitions(self, temp_dir):
        """Test task status transitions."""
        project_root = temp_dir / "planning"

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            # Create task
            result = await client.call_tool(
                "createObject",
                {
                    "kind": "task",
                    "title": "Test Task",
                    "projectRoot": str(project_root),
                },
            )

            task_id = result.data["id"]

            # Update to in-progress
            await client.call_tool(
                "updateObject",
                {
                    "kind": "task",
                    "id": task_id,
                    "projectRoot": str(project_root),
                    "yamlPatch": {"status": "in-progress"},
                },
            )

            # Update to review
            await client.call_tool(
                "updateObject",
                {
                    "kind": "task",
                    "id": task_id,
                    "projectRoot": str(project_root),
                    "yamlPatch": {"status": "review"},
                },
            )

            # Complete the task using completeTask
            final_result = await client.call_tool(
                "completeTask",
                {
                    "taskId": task_id,
                    "projectRoot": str(project_root),
                },
            )

        # Verify final status
        assert final_result.data["task"]["status"] == "done"

        # Verify file was moved to tasks-done
        final_file = Path(final_result.data["file_path"])
        assert "tasks-done" in str(final_file)
        assert final_file.exists()

    @pytest.mark.asyncio
    async def test_update_object_not_found(self, temp_dir):
        """Test updateObject with non-existent object."""
        project_root = temp_dir / "planning"
        project_root.mkdir(parents=True)

        # Create server
        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        # Test updateObject call with non-existent ID
        async with Client(server) as client:
            with pytest.raises(Exception):  # Should raise an exception
                await client.call_tool(
                    "updateObject",
                    {
                        "kind": "project",
                        "id": "nonexistent",
                        "projectRoot": str(project_root),
                        "yamlPatch": {"priority": "high"},
                    },
                )
