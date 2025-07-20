"""Tests for enhanced getObject tool with children array functionality.

Tests the getObject tool's ability to include immediate child objects in the response
while maintaining backward compatibility and proper error handling.
"""

from unittest.mock import patch

import pytest
from fastmcp import Client

from trellis_mcp.server import create_server
from trellis_mcp.settings import Settings


class TestGetObjectChildrenArray:
    """Test cases for getObject tool with children array enhancement."""

    @pytest.mark.asyncio
    async def test_get_project_with_epics(self, temp_dir):
        """Test retrieving a project object includes immediate epics in children array."""
        # Create project structure with epics
        project_root = temp_dir / "planning"
        project_dir = project_root / "projects" / "P-test-project"
        epics_dir = project_dir / "epics"

        # Create project
        project_dir.mkdir(parents=True)
        project_file = project_dir / "project.md"
        project_content = """---
kind: project
id: P-test-project
title: Test Project
status: draft
priority: normal
created: '2025-07-19T19:00:00Z'
updated: '2025-07-19T19:00:00Z'
schema_version: '1.1'
---
This is a test project.
"""
        project_file.write_text(project_content)

        # Create epic 1
        epic1_dir = epics_dir / "E-epic-one"
        epic1_dir.mkdir(parents=True)
        epic1_file = epic1_dir / "epic.md"
        epic1_content = """---
kind: epic
id: E-epic-one
parent: P-test-project
title: First Epic
status: open
priority: high
created: '2025-07-19T19:01:00Z'
updated: '2025-07-19T19:01:00Z'
schema_version: '1.1'
---
First epic description.
"""
        epic1_file.write_text(epic1_content)

        # Create epic 2
        epic2_dir = epics_dir / "E-epic-two"
        epic2_dir.mkdir(parents=True)
        epic2_file = epic2_dir / "epic.md"
        epic2_content = """---
kind: epic
id: E-epic-two
parent: P-test-project
title: Second Epic
status: in-progress
priority: normal
created: '2025-07-19T19:02:00Z'
updated: '2025-07-19T19:02:00Z'
schema_version: '1.1'
---
Second epic description.
"""
        epic2_file.write_text(epic2_content)

        # Create server and test getObject
        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            result = await client.call_tool(
                "getObject",
                {"id": "P-test-project", "projectRoot": str(project_root)},
            )

        # Verify basic response structure
        assert result.data["kind"] == "project"
        assert result.data["id"] == "test-project"
        assert result.data["yaml"]["title"] == "Test Project"

        # Verify children array is present and contains epics
        assert "children" in result.data
        children = result.data["children"]
        assert isinstance(children, list)
        assert len(children) == 2

        # Sort children by creation date for consistent testing
        children.sort(key=lambda x: x["created"])

        # Verify first epic
        epic1 = children[0]
        assert epic1["id"] == "epic-one"
        assert epic1["title"] == "First Epic"
        assert epic1["status"] == "open"
        assert epic1["kind"] == "epic"
        assert epic1["created"] == "2025-07-19T19:01:00Z"
        # file_path no longer included in response

        # Verify second epic
        epic2 = children[1]
        assert epic2["id"] == "epic-two"
        assert epic2["title"] == "Second Epic"
        assert epic2["status"] == "in-progress"
        assert epic2["kind"] == "epic"
        assert epic2["created"] == "2025-07-19T19:02:00Z"
        # file_path no longer included in response

    @pytest.mark.asyncio
    async def test_get_epic_with_features(self, temp_dir):
        """Test retrieving an epic object includes immediate features in children array."""
        # Create epic structure with features
        project_root = temp_dir / "planning"
        project_dir = project_root / "projects" / "P-test-project"
        epic_dir = project_dir / "epics" / "E-test-epic"
        features_dir = epic_dir / "features"

        # Create parent project first
        project_dir.mkdir(parents=True)
        project_file = project_dir / "project.md"
        project_content = """---
kind: project
id: P-test-project
title: Test Project
status: draft
priority: normal
created: '2025-07-19T18:59:00Z'
updated: '2025-07-19T18:59:00Z'
schema_version: '1.1'
---
Parent project for epic test.
"""
        project_file.write_text(project_content)

        # Create epic
        epic_dir.mkdir(parents=True)
        epic_file = epic_dir / "epic.md"
        epic_content = """---
kind: epic
id: E-test-epic
parent: P-test-project
title: Test Epic
status: in-progress
priority: normal
created: '2025-07-19T19:00:00Z'
updated: '2025-07-19T19:00:00Z'
schema_version: '1.1'
---
This is a test epic.
"""
        epic_file.write_text(epic_content)

        # Create feature
        feature_dir = features_dir / "F-test-feature"
        feature_dir.mkdir(parents=True)
        feature_file = feature_dir / "feature.md"
        feature_content = """---
kind: feature
id: F-test-feature
parent: E-test-epic
title: Test Feature
status: open
priority: high
created: '2025-07-19T19:01:00Z'
updated: '2025-07-19T19:01:00Z'
schema_version: '1.1'
---
Test feature description.
"""
        feature_file.write_text(feature_content)

        # Create server and test getObject
        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            result = await client.call_tool(
                "getObject",
                {"id": "E-test-epic", "projectRoot": str(project_root)},
            )

        # Verify children array contains feature
        assert "children" in result.data
        children = result.data["children"]
        assert len(children) == 1

        feature = children[0]
        assert feature["id"] == "test-feature"
        assert feature["title"] == "Test Feature"
        assert feature["status"] == "open"
        assert feature["kind"] == "feature"
        assert feature["created"] == "2025-07-19T19:01:00Z"
        # file_path no longer included in response

    @pytest.mark.asyncio
    async def test_get_feature_with_tasks(self, temp_dir):
        """Test retrieving a feature object includes immediate tasks in children array."""
        # Create feature structure with tasks
        project_root = temp_dir / "planning"
        project_dir = project_root / "projects" / "P-test-project"
        epic_dir = project_dir / "epics" / "E-test-epic"
        feature_dir = epic_dir / "features" / "F-test-feature"
        tasks_open_dir = feature_dir / "tasks-open"
        tasks_done_dir = feature_dir / "tasks-done"

        # Create parent project
        project_dir.mkdir(parents=True)
        project_file = project_dir / "project.md"
        project_content = """---
kind: project
id: P-test-project
title: Test Project
status: draft
priority: normal
created: '2025-07-19T18:58:00Z'
updated: '2025-07-19T18:58:00Z'
schema_version: '1.1'
---
Parent project for feature test.
"""
        project_file.write_text(project_content)

        # Create parent epic
        epic_dir.mkdir(parents=True)
        epic_file = epic_dir / "epic.md"
        epic_content = """---
kind: epic
id: E-test-epic
parent: P-test-project
title: Test Epic
status: in-progress
priority: normal
created: '2025-07-19T18:59:00Z'
updated: '2025-07-19T18:59:00Z'
schema_version: '1.1'
---
Parent epic for feature test.
"""
        epic_file.write_text(epic_content)

        # Create feature
        feature_dir.mkdir(parents=True)
        feature_file = feature_dir / "feature.md"
        feature_content = """---
kind: feature
id: F-test-feature
parent: E-test-epic
title: Test Feature
status: in-progress
priority: normal
created: '2025-07-19T19:00:00Z'
updated: '2025-07-19T19:00:00Z'
schema_version: '1.1'
---
This is a test feature.
"""
        feature_file.write_text(feature_content)

        # Create open task
        tasks_open_dir.mkdir(parents=True)
        open_task_file = tasks_open_dir / "T-open-task.md"
        open_task_content = """---
kind: task
id: T-open-task
parent: F-test-feature
title: Open Task
status: open
priority: high
created: '2025-07-19T19:01:00Z'
updated: '2025-07-19T19:01:00Z'
schema_version: '1.1'
---
Open task description.
"""
        open_task_file.write_text(open_task_content)

        # Create done task
        tasks_done_dir.mkdir(parents=True)
        done_task_file = tasks_done_dir / "20250719_190200-T-done-task.md"
        done_task_content = """---
kind: task
id: T-done-task
parent: F-test-feature
title: Done Task
status: done
priority: normal
created: '2025-07-19T19:02:00Z'
updated: '2025-07-19T19:02:00Z'
schema_version: '1.1'
---
Done task description.
"""
        done_task_file.write_text(done_task_content)

        # Create server and test getObject
        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            result = await client.call_tool(
                "getObject",
                {"id": "F-test-feature", "projectRoot": str(project_root)},
            )

        # Verify children array contains both tasks
        assert "children" in result.data
        children = result.data["children"]
        assert len(children) == 2

        # Sort children by creation date for consistent testing
        children.sort(key=lambda x: x["created"])

        # Verify open task
        open_task = children[0]
        assert open_task["id"] == "open-task"
        assert open_task["title"] == "Open Task"
        assert open_task["status"] == "open"
        assert open_task["kind"] == "task"
        assert open_task["created"] == "2025-07-19T19:01:00Z"
        # file_path no longer included in response

        # Verify done task
        done_task = children[1]
        assert done_task["id"] == "done-task"
        assert done_task["title"] == "Done Task"
        assert done_task["status"] == "done"
        assert done_task["kind"] == "task"
        assert done_task["created"] == "2025-07-19T19:02:00Z"
        # file_path no longer included in response

    @pytest.mark.asyncio
    async def test_get_task_empty_children(self, temp_dir):
        """Test retrieving a task object returns empty children array."""
        # Create task structure
        project_root = temp_dir / "planning"
        project_dir = project_root / "projects" / "P-test-project"
        epic_dir = project_dir / "epics" / "E-test-epic"
        feature_dir = epic_dir / "features" / "F-test-feature"
        tasks_open_dir = feature_dir / "tasks-open"

        # Create parent project
        project_dir.mkdir(parents=True)
        project_file = project_dir / "project.md"
        project_content = """---
kind: project
id: P-test-project
title: Test Project
status: draft
priority: normal
created: '2025-07-19T18:57:00Z'
updated: '2025-07-19T18:57:00Z'
schema_version: '1.1'
---
Parent project for task test.
"""
        project_file.write_text(project_content)

        # Create parent epic
        epic_dir.mkdir(parents=True)
        epic_file = epic_dir / "epic.md"
        epic_content = """---
kind: epic
id: E-test-epic
parent: P-test-project
title: Test Epic
status: in-progress
priority: normal
created: '2025-07-19T18:58:00Z'
updated: '2025-07-19T18:58:00Z'
schema_version: '1.1'
---
Parent epic for task test.
"""
        epic_file.write_text(epic_content)

        # Create parent feature
        feature_dir.mkdir(parents=True)
        feature_file = feature_dir / "feature.md"
        feature_content = """---
kind: feature
id: F-test-feature
parent: E-test-epic
title: Test Feature
status: in-progress
priority: normal
created: '2025-07-19T18:59:00Z'
updated: '2025-07-19T18:59:00Z'
schema_version: '1.1'
---
Parent feature for task test.
"""
        feature_file.write_text(feature_content)

        # Create task
        tasks_open_dir.mkdir(parents=True)
        task_file = tasks_open_dir / "T-test-task.md"
        task_content = """---
kind: task
id: T-test-task
parent: F-test-feature
title: Test Task
status: open
priority: normal
created: '2025-07-19T19:00:00Z'
updated: '2025-07-19T19:00:00Z'
schema_version: '1.1'
---
This is a test task.
"""
        task_file.write_text(task_content)

        # Create server and test getObject
        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            result = await client.call_tool(
                "getObject",
                {"id": "T-test-task", "projectRoot": str(project_root)},
            )

        # Verify children array is empty for tasks
        assert "children" in result.data
        children = result.data["children"]
        assert isinstance(children, list)
        assert len(children) == 0

    @pytest.mark.asyncio
    async def test_get_object_no_children_empty_array(self, temp_dir):
        """Test objects with no children return empty children array (not null)."""
        # Create project structure without any epics
        project_root = temp_dir / "planning"
        project_dir = project_root / "projects" / "P-empty-project"
        project_dir.mkdir(parents=True)
        project_file = project_dir / "project.md"
        project_content = """---
kind: project
id: P-empty-project
title: Empty Project
status: draft
priority: normal
created: '2025-07-19T19:00:00Z'
updated: '2025-07-19T19:00:00Z'
schema_version: '1.1'
---
This project has no epics.
"""
        project_file.write_text(project_content)

        # Create server and test getObject
        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            result = await client.call_tool(
                "getObject",
                {"id": "P-empty-project", "projectRoot": str(project_root)},
            )

        # Verify children array is empty list, not null
        assert "children" in result.data
        children = result.data["children"]
        assert isinstance(children, list)
        assert len(children) == 0

    @pytest.mark.asyncio
    async def test_children_discovery_error_independence(self, temp_dir):
        """Test that children discovery errors don't break getObject functionality."""
        # Create project structure
        project_root = temp_dir / "planning"
        project_dir = project_root / "projects" / "P-test-project"
        project_dir.mkdir(parents=True)
        project_file = project_dir / "project.md"
        project_content = """---
kind: project
id: P-test-project
title: Test Project
status: draft
priority: normal
created: '2025-07-19T19:00:00Z'
updated: '2025-07-19T19:00:00Z'
schema_version: '1.1'
---
This is a test project.
"""
        project_file.write_text(project_content)

        # Create server and test getObject with mocked children discovery failure
        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        # Mock discover_immediate_children to raise an exception
        with patch(
            "trellis_mcp.tools.get_object.discover_immediate_children",
            side_effect=Exception("Children discovery failed"),
        ):
            async with Client(server) as client:
                result = await client.call_tool(
                    "getObject",
                    {"id": "P-test-project", "projectRoot": str(project_root)},
                )

        # Verify getObject still works and returns empty children array
        assert result.data["kind"] == "project"
        assert result.data["id"] == "test-project"
        assert result.data["yaml"]["title"] == "Test Project"
        assert "children" in result.data
        assert result.data["children"] == []

    @pytest.mark.asyncio
    async def test_backward_compatibility_all_fields_present(self, temp_dir):
        """Test that all existing getObject response fields remain unchanged."""
        # Create project structure
        project_root = temp_dir / "planning"
        project_dir = project_root / "projects" / "P-test-project"
        project_dir.mkdir(parents=True)
        project_file = project_dir / "project.md"
        project_content = """---
kind: project
id: P-test-project
title: Test Project
status: draft
priority: normal
created: '2025-07-19T19:00:00Z'
updated: '2025-07-19T19:00:00Z'
schema_version: '1.1'
---
This is a test project body.

### Log

Project created.
"""
        project_file.write_text(project_content)

        # Create server and test getObject
        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            result = await client.call_tool(
                "getObject",
                {"id": "P-test-project", "projectRoot": str(project_root)},
            )

        # Verify all original fields are present and correct
        assert "yaml" in result.data
        assert "body" in result.data
        # file_path no longer included in response format
        assert "kind" in result.data
        assert "id" in result.data

        # Verify field values
        assert result.data["kind"] == "project"
        assert result.data["id"] == "test-project"
        # file_path no longer included in response format
        assert isinstance(result.data["yaml"], dict)
        assert result.data["yaml"]["title"] == "Test Project"
        assert "This is a test project body." in result.data["body"]

        # Verify new children field is also present
        assert "children" in result.data
        assert isinstance(result.data["children"], list)

    @pytest.mark.asyncio
    async def test_children_metadata_completeness(self, temp_dir):
        """Test that children objects contain all required metadata fields."""
        # Create epic structure with feature
        project_root = temp_dir / "planning"
        project_dir = project_root / "projects" / "P-test-project"
        epic_dir = project_dir / "epics" / "E-test-epic"
        features_dir = epic_dir / "features"

        # Create parent project
        project_dir.mkdir(parents=True)
        project_file = project_dir / "project.md"
        project_content = """---
kind: project
id: P-test-project
title: Test Project
status: draft
priority: normal
created: '2025-07-19T18:56:00Z'
updated: '2025-07-19T18:56:00Z'
schema_version: '1.1'
---
Parent project for metadata test.
"""
        project_file.write_text(project_content)

        # Create epic
        epic_dir.mkdir(parents=True)
        epic_file = epic_dir / "epic.md"
        epic_content = """---
kind: epic
id: E-test-epic
parent: P-test-project
title: Test Epic
status: in-progress
priority: normal
created: '2025-07-19T19:00:00Z'
updated: '2025-07-19T19:00:00Z'
schema_version: '1.1'
---
This is a test epic.
"""
        epic_file.write_text(epic_content)

        # Create feature with all metadata
        feature_dir = features_dir / "F-complete-feature"
        feature_dir.mkdir(parents=True)
        feature_file = feature_dir / "feature.md"
        feature_content = """---
kind: feature
id: F-complete-feature
parent: E-test-epic
title: Complete Feature
status: review
priority: high
created: '2025-07-19T19:01:00Z'
updated: '2025-07-19T19:01:30Z'
schema_version: '1.1'
---
Complete feature with all metadata.
"""
        feature_file.write_text(feature_content)

        # Create server and test getObject
        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            result = await client.call_tool(
                "getObject",
                {"id": "E-test-epic", "projectRoot": str(project_root)},
            )

        # Verify child metadata completeness
        children = result.data["children"]
        assert len(children) == 1

        child = children[0]
        required_fields = ["id", "title", "status", "kind", "created"]

        for field in required_fields:
            assert field in child, f"Missing required field: {field}"
            assert child[field] is not None, f"Field {field} should not be None"
            assert child[field] != "", f"Field {field} should not be empty"

        # Verify specific values
        assert child["id"] == "complete-feature"
        assert child["title"] == "Complete Feature"
        assert child["status"] == "review"
        assert child["kind"] == "feature"
        assert child["created"] == "2025-07-19T19:01:00Z"
        # file_path no longer included in child metadata
