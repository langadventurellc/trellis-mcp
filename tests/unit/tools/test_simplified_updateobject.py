"""Unit tests for simplified updateObject tool with automatic kind inference.

Tests the simplified updateObject tool that removes the kind parameter and uses
automatic kind inference while providing clean response formats without
internal implementation details like file_path.
"""

import pytest
from fastmcp import Client

from trellis_mcp.server import create_server
from trellis_mcp.settings import Settings


class TestSimplifiedUpdateObject:
    """Test cases for simplified updateObject tool functionality."""

    @pytest.mark.asyncio
    async def test_simplified_updateobject_basic_functionality(self, temp_dir):
        """Test basic updateObject functionality with simplified interface."""
        # Create project structure
        project_root = temp_dir / "planning"
        project_dir = project_root / "projects" / "P-update-test"
        project_dir.mkdir(parents=True)
        project_file = project_dir / "project.md"
        project_content = """---
kind: project
id: P-update-test
title: Update Test Project
status: draft
priority: normal
created: '2025-07-20T10:00:00Z'
updated: '2025-07-20T10:00:00Z'
schema_version: '1.1'
---
Original project content.
"""
        project_file.write_text(project_content)

        # Create server and test simplified updateObject
        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            result = await client.call_tool(
                "updateObject",
                {
                    "id": "P-update-test",
                    "projectRoot": str(project_root),
                    "yamlPatch": {"status": "in-progress", "priority": "high"},
                },
            )

        # Verify simplified response format
        assert result.data["kind"] == "project"
        assert result.data["id"] == "update-test"
        assert "updated" in result.data
        assert "changes" in result.data
        assert result.data["changes"]["yaml_fields"] == ["status", "priority"]

        # Verify file_path is NOT in response (simplified format)
        assert "file_path" not in result.data

    @pytest.mark.asyncio
    async def test_updateobject_all_object_types(self, temp_dir):
        """Test updateObject with all object type prefixes (P-, E-, F-, T-)."""
        # Create complete project structure
        project_root = temp_dir / "planning"

        # Create project
        project_dir = project_root / "projects" / "P-update-project"
        project_dir.mkdir(parents=True)
        project_file = project_dir / "project.md"
        project_content = """---
kind: project
id: P-update-project
title: Update Project
status: draft
priority: normal
created: '2025-07-20T09:00:00Z'
updated: '2025-07-20T09:00:00Z'
schema_version: '1.1'
---
Project for update testing.
"""
        project_file.write_text(project_content)

        # Create epic
        epic_dir = project_dir / "epics" / "E-update-epic"
        epic_dir.mkdir(parents=True)
        epic_file = epic_dir / "epic.md"
        epic_content = """---
kind: epic
id: E-update-epic
parent: P-update-project
title: Update Epic
status: draft
priority: normal
created: '2025-07-20T09:01:00Z'
updated: '2025-07-20T09:01:00Z'
schema_version: '1.1'
---
Epic for update testing.
"""
        epic_file.write_text(epic_content)

        # Create feature
        feature_dir = epic_dir / "features" / "F-update-feature"
        feature_dir.mkdir(parents=True)
        feature_file = feature_dir / "feature.md"
        feature_content = """---
kind: feature
id: F-update-feature
parent: E-update-epic
title: Update Feature
status: draft
priority: normal
created: '2025-07-20T09:02:00Z'
updated: '2025-07-20T09:02:00Z'
schema_version: '1.1'
---
Feature for update testing.
"""
        feature_file.write_text(feature_content)

        # Create task
        task_dir = feature_dir / "tasks-open"
        task_dir.mkdir(parents=True)
        task_file = task_dir / "T-update-task.md"
        task_content = """---
kind: task
id: T-update-task
parent: F-update-feature
title: Update Task
status: open
priority: normal
created: '2025-07-20T09:03:00Z'
updated: '2025-07-20T09:03:00Z'
schema_version: '1.1'
---
Task for update testing.
"""
        task_file.write_text(task_content)

        # Create server
        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        # Test all object types
        test_cases = [
            ("P-update-project", "project", "update-project", {"priority": "high"}),
            ("E-update-epic", "epic", "update-epic", {"status": "in-progress"}),
            ("F-update-feature", "feature", "update-feature", {"priority": "high"}),
            ("T-update-task", "task", "update-task", {"status": "in-progress"}),
        ]

        async with Client(server) as client:
            for object_id, expected_kind, expected_clean_id, yaml_patch in test_cases:
                result = await client.call_tool(
                    "updateObject",
                    {
                        "id": object_id,
                        "projectRoot": str(project_root),
                        "yamlPatch": yaml_patch,
                    },
                )

                # Verify kind inference worked
                assert result.data["kind"] == expected_kind, f"Failed for {object_id}"
                assert result.data["id"] == expected_clean_id, f"Failed for {object_id}"

                # Verify clean response format
                assert "file_path" not in result.data, f"file_path found in {object_id}"
                assert "updated" in result.data
                assert "changes" in result.data

    @pytest.mark.asyncio
    async def test_updateobject_invalid_id_patterns(self, temp_dir):
        """Test updateObject error handling for invalid ID patterns."""
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
                        "updateObject",
                        {
                            "id": invalid_id,
                            "projectRoot": str(project_root),
                            "yamlPatch": {"status": "in-progress"},
                        },
                    )

                # Verify it's a validation error
                assert "error" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_updateobject_clean_response_format(self, temp_dir):
        """Test that updateObject provides clean response format without file_path."""
        # Create task structure
        project_root = temp_dir / "planning"
        project_dir = project_root / "projects" / "P-response-test"
        epic_dir = project_dir / "epics" / "E-response-test"
        feature_dir = epic_dir / "features" / "F-response-test"
        task_dir = feature_dir / "tasks-open"

        # Create all parent objects
        project_dir.mkdir(parents=True)
        (project_dir / "project.md").write_text(
            """---
kind: project
id: P-response-test
title: Response Test Project
status: draft
priority: normal
created: '2025-07-20T08:00:00Z'
updated: '2025-07-20T08:00:00Z'
schema_version: '1.1'
---
Response test project."""
        )

        epic_dir.mkdir(parents=True)
        (epic_dir / "epic.md").write_text(
            """---
kind: epic
id: E-response-test
parent: P-response-test
title: Response Test Epic
status: draft
priority: normal
created: '2025-07-20T08:01:00Z'
updated: '2025-07-20T08:01:00Z'
schema_version: '1.1'
---
Response test epic."""
        )

        feature_dir.mkdir(parents=True)
        (feature_dir / "feature.md").write_text(
            """---
kind: feature
id: F-response-test
parent: E-response-test
title: Response Test Feature
status: draft
priority: normal
created: '2025-07-20T08:02:00Z'
updated: '2025-07-20T08:02:00Z'
schema_version: '1.1'
---
Response test feature."""
        )

        task_dir.mkdir(parents=True)
        (task_dir / "T-response-test.md").write_text(
            """---
kind: task
id: T-response-test
parent: F-response-test
title: Response Test Task
status: open
priority: normal
created: '2025-07-20T08:03:00Z'
updated: '2025-07-20T08:03:00Z'
schema_version: '1.1'
---
Response test task."""
        )

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            # Test all object types
            for object_id in [
                "P-response-test",
                "E-response-test",
                "F-response-test",
                "T-response-test",
            ]:
                result = await client.call_tool(
                    "updateObject",
                    {
                        "id": object_id,
                        "projectRoot": str(project_root),
                        "yamlPatch": {"priority": "high"},
                    },
                )

                # file_path should NOT be in simplified response
                assert (
                    "file_path" not in result.data
                ), f"file_path found in response for {object_id}"

                # But all other expected fields should be present
                expected_fields = ["id", "kind", "updated", "changes"]
                for field in expected_fields:
                    assert field in result.data, f"Missing field {field} for {object_id}"

    @pytest.mark.asyncio
    async def test_updateobject_with_inferred_kind(self, temp_dir):
        """Test that updateObject uses inferred kind correctly."""
        project_root = temp_dir / "planning"
        project_dir = project_root / "projects" / "P-kind-test"
        project_dir.mkdir(parents=True)

        project_file = project_dir / "project.md"
        project_content = """---
kind: project
id: P-kind-test
title: Kind Test Project
status: draft
priority: normal
created: '2025-07-20T07:00:00Z'
updated: '2025-07-20T07:00:00Z'
schema_version: '1.1'
---
Project for testing kind inference in updates.
"""
        project_file.write_text(project_content)

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            result = await client.call_tool(
                "updateObject",
                {
                    "id": "P-kind-test",  # Tool should infer kind=project from P- prefix
                    "projectRoot": str(project_root),
                    "yamlPatch": {"status": "in-progress"},
                },
            )

        # Verify inferred kind is included in response
        assert "kind" in result.data
        assert result.data["kind"] == "project"

        # Verify update was successful
        assert result.data["id"] == "kind-test"
        assert result.data["changes"]["yaml_fields"] == ["status"]

    @pytest.mark.asyncio
    async def test_updateobject_body_patch(self, temp_dir):
        """Test updateObject with body content updates."""
        project_root = temp_dir / "planning"
        project_dir = project_root / "projects" / "P-body-test"
        project_dir.mkdir(parents=True)

        project_file = project_dir / "project.md"
        project_content = """---
kind: project
id: P-body-test
title: Body Test Project
status: draft
priority: normal
created: '2025-07-20T06:00:00Z'
updated: '2025-07-20T06:00:00Z'
schema_version: '1.1'
---
Original body content.
"""
        project_file.write_text(project_content)

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        new_body = """Updated body content.

## New Section

This is the updated project description."""

        async with Client(server) as client:
            result = await client.call_tool(
                "updateObject",
                {
                    "id": "P-body-test",
                    "projectRoot": str(project_root),
                    "bodyPatch": new_body,
                },
            )

        # Verify body update was tracked
        assert "changes" in result.data
        assert result.data["changes"]["body_updated"] is True

        # Verify clean response format
        assert "file_path" not in result.data
        assert result.data["kind"] == "project"
        assert result.data["id"] == "body-test"

    @pytest.mark.asyncio
    async def test_updateobject_yaml_and_body_patch(self, temp_dir):
        """Test updateObject with both YAML and body updates."""
        project_root = temp_dir / "planning"
        project_dir = project_root / "projects" / "P-combined-test"
        project_dir.mkdir(parents=True)

        project_file = project_dir / "project.md"
        project_content = """---
kind: project
id: P-combined-test
title: Combined Test Project
status: draft
priority: normal
created: '2025-07-20T05:00:00Z'
updated: '2025-07-20T05:00:00Z'
schema_version: '1.1'
---
Original content.
"""
        project_file.write_text(project_content)

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        new_body = "Updated combined content."

        async with Client(server) as client:
            result = await client.call_tool(
                "updateObject",
                {
                    "id": "P-combined-test",
                    "projectRoot": str(project_root),
                    "yamlPatch": {"status": "in-progress", "priority": "high"},
                    "bodyPatch": new_body,
                },
            )

        # Verify both updates were tracked
        assert "changes" in result.data
        assert result.data["changes"]["yaml_fields"] == ["status", "priority"]
        assert result.data["changes"]["body_updated"] is True

        # Verify clean response format
        assert "file_path" not in result.data
        assert result.data["kind"] == "project"

    @pytest.mark.asyncio
    async def test_updateobject_missing_patches_error(self, temp_dir):
        """Test updateObject error when no patches are provided."""
        project_root = temp_dir / "planning"
        project_dir = project_root / "projects" / "P-error-test"
        project_dir.mkdir(parents=True)

        project_file = project_dir / "project.md"
        project_content = """---
kind: project
id: P-error-test
title: Error Test Project
status: draft
priority: normal
created: '2025-07-20T04:00:00Z'
updated: '2025-07-20T04:00:00Z'
schema_version: '1.1'
---
Error test content.
"""
        project_file.write_text(project_content)

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "updateObject",
                    {
                        "id": "P-error-test",
                        "projectRoot": str(project_root),
                        # No yamlPatch or bodyPatch provided
                    },
                )

            # Should fail with appropriate error about missing patches
            error_message = str(exc_info.value).lower()
            assert any(keyword in error_message for keyword in ["patch", "required", "missing"])

    @pytest.mark.asyncio
    async def test_updateobject_nonexistent_object_error(self, temp_dir):
        """Test updateObject error for non-existent objects."""
        project_root = temp_dir / "planning"
        project_root.mkdir(parents=True)

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "updateObject",
                    {
                        "id": "P-nonexistent",
                        "projectRoot": str(project_root),
                        "yamlPatch": {"status": "in-progress"},
                    },
                )

            # Should fail with file not found or similar
            error_message = str(exc_info.value).lower()
            assert any(keyword in error_message for keyword in ["not found", "missing", "exist"])

    @pytest.mark.asyncio
    async def test_updateobject_status_transition_validation(self, temp_dir):
        """Test updateObject status transition validation."""
        # Create task for status transition testing
        project_root = temp_dir / "planning"
        project_dir = project_root / "projects" / "P-status-test"
        epic_dir = project_dir / "epics" / "E-status-test"
        feature_dir = epic_dir / "features" / "F-status-test"
        task_dir = feature_dir / "tasks-open"

        # Create all parent objects
        project_dir.mkdir(parents=True)
        (project_dir / "project.md").write_text(
            """---
kind: project
id: P-status-test
title: Status Test Project
status: draft
priority: normal
created: '2025-07-20T03:00:00Z'
updated: '2025-07-20T03:00:00Z'
schema_version: '1.1'
---
Status test project."""
        )

        epic_dir.mkdir(parents=True)
        (epic_dir / "epic.md").write_text(
            """---
kind: epic
id: E-status-test
parent: P-status-test
title: Status Test Epic
status: draft
priority: normal
created: '2025-07-20T03:01:00Z'
updated: '2025-07-20T03:01:00Z'
schema_version: '1.1'
---
Status test epic."""
        )

        feature_dir.mkdir(parents=True)
        (feature_dir / "feature.md").write_text(
            """---
kind: feature
id: F-status-test
parent: E-status-test
title: Status Test Feature
status: draft
priority: normal
created: '2025-07-20T03:02:00Z'
updated: '2025-07-20T03:02:00Z'
schema_version: '1.1'
---
Status test feature."""
        )

        task_dir.mkdir(parents=True)
        (task_dir / "T-status-test.md").write_text(
            """---
kind: task
id: T-status-test
parent: F-status-test
title: Status Test Task
status: open
priority: normal
created: '2025-07-20T03:03:00Z'
updated: '2025-07-20T03:03:00Z'
schema_version: '1.1'
---
Status test task."""
        )

        settings = Settings(planning_root=project_root)
        server = create_server(settings)

        async with Client(server) as client:
            # Test valid status transition: open -> in-progress
            result = await client.call_tool(
                "updateObject",
                {
                    "id": "T-status-test",
                    "projectRoot": str(project_root),
                    "yamlPatch": {"status": "in-progress"},
                },
            )

            # Should succeed
            assert result.data["kind"] == "task"
            assert result.data["changes"]["yaml_fields"] == ["status"]

            # Test invalid status transition: trying to set task to 'done' via updateObject
            with pytest.raises(Exception) as exc_info:
                await client.call_tool(
                    "updateObject",
                    {
                        "id": "T-status-test",
                        "projectRoot": str(project_root),
                        "yamlPatch": {"status": "done"},
                    },
                )

            # Should fail with appropriate error about using completeTask
            error_message = str(exc_info.value).lower()
            assert any(
                keyword in error_message for keyword in ["completetask", "done", "transition"]
            )
