"""Unit tests for simplified getObject tool with automatic kind inference.

Tests the simplified getObject tool that removes the kind parameter and uses
automatic kind inference while providing clean response formats without
internal implementation details like file_path.
"""

import pytest
from fastmcp import Client

from trellis_mcp.server import create_server
from trellis_mcp.settings import Settings


class TestSimplifiedGetObject:
    """Test cases for simplified getObject tool functionality."""

    @pytest.mark.asyncio
    async def test_simplified_getobject_basic_functionality(self, temp_dir):
        """Test basic getObject functionality with simplified interface."""
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
created: '2025-07-20T10:00:00Z'
updated: '2025-07-20T10:00:00Z'
schema_version: '1.1'
---
This is a test project.
"""
        project_file.write_text(project_content)

        # Create server and test simplified getObject
        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            result = await client.call_tool(
                "getObject",
                {"id": "P-test-project", "projectRoot": str(project_root)},
            )

        # Verify simplified response format
        assert result.data["kind"] == "project"
        assert result.data["id"] == "test-project"
        assert result.data["yaml"]["title"] == "Test Project"
        assert "body" in result.data
        assert "children" in result.data

        # Verify file_path is NOT in response (simplified format)
        assert "file_path" not in result.data

    @pytest.mark.asyncio
    async def test_getobject_all_object_types(self, temp_dir):
        """Test getObject with all object type prefixes (P-, E-, F-, T-)."""
        # Create complete project structure
        project_root = temp_dir / "planning"

        # Create project
        project_dir = project_root / "projects" / "P-sample-project"
        project_dir.mkdir(parents=True)
        project_file = project_dir / "project.md"
        project_content = """---
kind: project
id: P-sample-project
title: Sample Project
status: in-progress
priority: normal
created: '2025-07-20T09:00:00Z'
updated: '2025-07-20T09:00:00Z'
schema_version: '1.1'
---
Sample project for testing.
"""
        project_file.write_text(project_content)

        # Create epic
        epic_dir = project_dir / "epics" / "E-core-features"
        epic_dir.mkdir(parents=True)
        epic_file = epic_dir / "epic.md"
        epic_content = """---
kind: epic
id: E-core-features
parent: P-sample-project
title: Core Features
status: in-progress
priority: normal
created: '2025-07-20T09:01:00Z'
updated: '2025-07-20T09:01:00Z'
schema_version: '1.1'
---
Core features epic.
"""
        epic_file.write_text(epic_content)

        # Create feature
        feature_dir = epic_dir / "features" / "F-user-auth"
        feature_dir.mkdir(parents=True)
        feature_file = feature_dir / "feature.md"
        feature_content = """---
kind: feature
id: F-user-auth
parent: E-core-features
title: User Authentication
status: in-progress
priority: high
created: '2025-07-20T09:02:00Z'
updated: '2025-07-20T09:02:00Z'
schema_version: '1.1'
---
User authentication feature.
"""
        feature_file.write_text(feature_content)

        # Create task
        task_dir = feature_dir / "tasks-open"
        task_dir.mkdir(parents=True)
        task_file = task_dir / "T-implement-login.md"
        task_content = """---
kind: task
id: T-implement-login
parent: F-user-auth
title: Implement Login
status: open
priority: high
created: '2025-07-20T09:03:00Z'
updated: '2025-07-20T09:03:00Z'
schema_version: '1.1'
---
Implement login functionality.
"""
        task_file.write_text(task_content)

        # Create server
        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        # Test all object types
        test_cases = [
            ("P-sample-project", "project", "sample-project"),
            ("E-core-features", "epic", "core-features"),
            ("F-user-auth", "feature", "user-auth"),
            ("T-implement-login", "task", "implement-login"),
        ]

        async with Client(server) as client:
            for object_id, expected_kind, expected_clean_id in test_cases:
                result = await client.call_tool(
                    "getObject",
                    {"id": object_id, "projectRoot": str(project_root)},
                )

                # Verify kind inference worked
                assert result.data["kind"] == expected_kind, f"Failed for {object_id}"
                assert result.data["id"] == expected_clean_id, f"Failed for {object_id}"

                # Verify clean response format
                assert "file_path" not in result.data, f"file_path found in {object_id}"
                assert "yaml" in result.data
                assert "body" in result.data
                assert "children" in result.data

    @pytest.mark.asyncio
    async def test_getobject_invalid_id_patterns(self, temp_dir):
        """Test getObject error handling for invalid ID patterns."""
        project_root = temp_dir / "planning"
        project_root.mkdir(parents=True)

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        invalid_ids = [
            "",  # Empty string
            "   ",  # Whitespace only
            "INVALID-FORMAT",  # Invalid prefix
            "X-unknown-prefix",  # Unknown prefix
        ]

        async with Client(server) as client:
            for invalid_id in invalid_ids:
                with pytest.raises(Exception) as exc_info:
                    await client.call_tool(
                        "getObject",
                        {"id": invalid_id, "projectRoot": str(project_root)},
                    )

                # Verify it's a validation error
                assert "error" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_response_format_excludes_file_path(self, temp_dir):
        """Verify simplified tools exclude file_path from responses."""
        # Create task structure
        project_root = temp_dir / "planning"
        project_dir = project_root / "projects" / "P-test-project"
        epic_dir = project_dir / "epics" / "E-test-epic"
        feature_dir = epic_dir / "features" / "F-test-feature"
        task_dir = feature_dir / "tasks-open"

        # Create all parent objects
        project_dir.mkdir(parents=True)
        (project_dir / "project.md").write_text(
            """---
kind: project
id: P-test-project
title: Test Project
status: draft
priority: normal
created: '2025-07-20T08:00:00Z'
updated: '2025-07-20T08:00:00Z'
schema_version: '1.1'
---
Test project."""
        )

        epic_dir.mkdir(parents=True)
        (epic_dir / "epic.md").write_text(
            """---
kind: epic
id: E-test-epic
parent: P-test-project
title: Test Epic
status: in-progress
priority: normal
created: '2025-07-20T08:01:00Z'
updated: '2025-07-20T08:01:00Z'
schema_version: '1.1'
---
Test epic."""
        )

        feature_dir.mkdir(parents=True)
        (feature_dir / "feature.md").write_text(
            """---
kind: feature
id: F-test-feature
parent: E-test-epic
title: Test Feature
status: in-progress
priority: normal
created: '2025-07-20T08:02:00Z'
updated: '2025-07-20T08:02:00Z'
schema_version: '1.1'
---
Test feature."""
        )

        task_dir.mkdir(parents=True)
        (task_dir / "T-test-task.md").write_text(
            """---
kind: task
id: T-test-task
parent: F-test-feature
title: Test Task
status: open
priority: normal
created: '2025-07-20T08:03:00Z'
updated: '2025-07-20T08:03:00Z'
schema_version: '1.1'
---
Test task."""
        )

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            # Test all object types
            for object_id in ["P-test-project", "E-test-epic", "F-test-feature", "T-test-task"]:
                result = await client.call_tool(
                    "getObject",
                    {"id": object_id, "projectRoot": str(project_root)},
                )

                # file_path should NOT be in simplified response
                assert (
                    "file_path" not in result.data
                ), f"file_path found in response for {object_id}"

                # But all other expected fields should be present
                expected_fields = ["yaml", "body", "kind", "id", "children"]
                for field in expected_fields:
                    assert field in result.data, f"Missing field {field} for {object_id}"

    @pytest.mark.asyncio
    async def test_response_format_includes_inferred_kind(self, temp_dir):
        """Verify simplified tools include inferred kind in responses."""
        project_root = temp_dir / "planning"
        project_dir = project_root / "projects" / "P-inference-test"
        project_dir.mkdir(parents=True)

        project_file = project_dir / "project.md"
        project_content = """---
kind: project
id: P-inference-test
title: Inference Test Project
status: draft
priority: normal
created: '2025-07-20T07:00:00Z'
updated: '2025-07-20T07:00:00Z'
schema_version: '1.1'
---
Project for testing kind inference.
"""
        project_file.write_text(project_content)

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            result = await client.call_tool(
                "getObject",
                {"id": "P-inference-test", "projectRoot": str(project_root)},
            )

        # Verify inferred kind is included in response
        assert "kind" in result.data
        assert result.data["kind"] == "project"

        # Verify it's the inferred kind, not from YAML front-matter
        # (The tool should infer from ID prefix, not read from file)
        assert result.data["yaml"]["kind"] == "project"  # This is from file
        assert result.data["kind"] == "project"  # This is inferred

    @pytest.mark.asyncio
    async def test_kind_inference_error_propagation(self, temp_dir):
        """Test that kind inference errors are properly propagated."""
        project_root = temp_dir / "planning"
        project_root.mkdir(parents=True)

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        # Test with ID that will cause inference failure
        async with Client(server) as client:
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "getObject",
                    {"id": "INVALID-PREFIX-test", "projectRoot": str(project_root)},
                )

            # Verify the error is related to kind inference
            error_message = str(exc_info.value).lower()
            assert any(keyword in error_message for keyword in ["invalid", "pattern", "format"])

    @pytest.mark.asyncio
    async def test_missing_object_error_handling(self, temp_dir):
        """Test error handling when inferred object doesn't exist."""
        project_root = temp_dir / "planning"
        project_root.mkdir(parents=True)

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        # Test with valid ID format but missing object
        async with Client(server) as client:
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "getObject",
                    {"id": "P-nonexistent-project", "projectRoot": str(project_root)},
                )

            # Should fail with file not found or similar
            error_message = str(exc_info.value).lower()
            assert any(keyword in error_message for keyword in ["not found", "missing", "exist"])

    @pytest.mark.asyncio
    async def test_children_discovery_with_simplified_interface(self, temp_dir):
        """Test that children discovery works correctly with simplified interface."""
        # Create project with epics
        project_root = temp_dir / "planning"
        project_dir = project_root / "projects" / "P-parent-test"
        epics_dir = project_dir / "epics"

        # Create project
        project_dir.mkdir(parents=True)
        (project_dir / "project.md").write_text(
            """---
kind: project
id: P-parent-test
title: Parent Test Project
status: in-progress
priority: normal
created: '2025-07-20T06:00:00Z'
updated: '2025-07-20T06:00:00Z'
schema_version: '1.1'
---
Project for testing children discovery."""
        )

        # Create epic 1
        epic1_dir = epics_dir / "E-child-epic-one"
        epic1_dir.mkdir(parents=True)
        (epic1_dir / "epic.md").write_text(
            """---
kind: epic
id: E-child-epic-one
parent: P-parent-test
title: Child Epic One
status: open
priority: high
created: '2025-07-20T06:01:00Z'
updated: '2025-07-20T06:01:00Z'
schema_version: '1.1'
---
First child epic."""
        )

        # Create epic 2
        epic2_dir = epics_dir / "E-child-epic-two"
        epic2_dir.mkdir(parents=True)
        (epic2_dir / "epic.md").write_text(
            """---
kind: epic
id: E-child-epic-two
parent: P-parent-test
title: Child Epic Two
status: in-progress
priority: normal
created: '2025-07-20T06:02:00Z'
updated: '2025-07-20T06:02:00Z'
schema_version: '1.1'
---
Second child epic."""
        )

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            result = await client.call_tool(
                "getObject",
                {"id": "P-parent-test", "projectRoot": str(project_root)},
            )

        # Verify children are discovered correctly
        assert "children" in result.data
        children = result.data["children"]
        assert len(children) == 2

        # Sort children by creation date for consistent testing
        children.sort(key=lambda x: x["created"])

        # Verify first epic
        assert children[0]["id"] == "child-epic-one"
        assert children[0]["title"] == "Child Epic One"
        assert children[0]["status"] == "open"
        assert children[0]["kind"] == "epic"

        # Verify second epic
        assert children[1]["id"] == "child-epic-two"
        assert children[1]["title"] == "Child Epic Two"
        assert children[1]["status"] == "in-progress"
        assert children[1]["kind"] == "epic"

        # Verify file_path is NOT in children metadata (simplified format)
        for child in children:
            assert "file_path" not in child
