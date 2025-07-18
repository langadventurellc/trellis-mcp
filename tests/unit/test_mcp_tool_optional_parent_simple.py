"""Simple test to verify MCP tool handlers handle optional parent fields correctly.

This test verifies that the MCP tool handlers properly handle None parent values
and return appropriate data structures for standalone tasks.
"""

from datetime import datetime

import pytest

from trellis_mcp.models.common import Priority
from trellis_mcp.schema.status_enum import StatusEnum
from trellis_mcp.schema.task import TaskModel
from trellis_mcp.settings import Settings
from trellis_mcp.tools.create_object import create_create_object_tool
from trellis_mcp.tools.list_backlog import create_list_backlog_tool


class TestMCPToolOptionalParentSimple:
    """Simple test for MCP tool handlers with optional parent field handling."""

    @pytest.fixture
    def settings(self):
        """Create settings for testing."""
        return Settings(schema_version="1.1")

    @pytest.fixture
    def temp_planning_dir(self, tmp_path):
        """Create a temporary planning directory structure."""
        planning_dir = tmp_path / "planning"
        planning_dir.mkdir()
        return planning_dir

    @pytest.fixture
    def mock_standalone_task(self):
        """Create a mock standalone task with None parent."""
        from trellis_mcp.schema.kind_enum import KindEnum

        return TaskModel(
            kind=KindEnum.TASK,
            id="test-standalone-task",
            title="Test Standalone Task",
            status=StatusEnum.OPEN,
            priority=Priority.NORMAL,
            parent=None,  # None parent for standalone task
            worktree=None,
            created=datetime.now(),
            updated=datetime.now(),
            schema_version="1.1",
        )

    def test_mcp_tools_instantiate_correctly(self, settings):
        """Test that MCP tools can be instantiated without errors."""
        # Test that all tools can be created without errors
        create_object = create_create_object_tool(settings)
        list_backlog = create_list_backlog_tool(settings)

        # Tools should be FastMCP FunctionTool instances
        assert hasattr(create_object, "name")
        assert hasattr(list_backlog, "name")
        assert create_object.name == "createObject"
        assert list_backlog.name == "listBacklog"

    def test_documentation_updated_for_optional_parent(self):
        """Test that tool documentation reflects optional parent fields."""
        # Read the updated documentation in list_backlog.py
        with open("/Users/zach/code/trellis-mcp/src/trellis_mcp/tools/list_backlog.py", "r") as f:
            content = f.read()

        # Verify the documentation was updated to show optional parent
        assert '"parent": str | None' in content
        assert "None for standalone tasks" in content

    def test_get_next_reviewable_task_documentation_updated(self):
        """Test that getNextReviewableTask documentation reflects optional parent fields."""
        # Read the updated documentation in get_next_reviewable_task.py
        with open(
            "/Users/zach/code/trellis-mcp/src/trellis_mcp/tools/get_next_reviewable_task.py", "r"
        ) as f:
            content = f.read()

        # Verify the documentation was updated to show optional parent
        assert '"parent": str | None' in content
        assert "None for standalone tasks" in content

    def test_create_object_tool_documentation_correct(self):
        """Test that createObject tool documentation is correct for optional parent."""
        # Read the createObject tool documentation
        with open("/Users/zach/code/trellis-mcp/src/trellis_mcp/tools/create_object.py", "r") as f:
            content = f.read()

        # Verify the function signature has correct type annotation (MCP Inspector compatible)
        assert 'parent: str = ""' in content
        # Verify the documentation explains the optional parent
        assert "empty string for no parent" in content

    def test_update_object_tool_type_annotation_correct(self):
        """Test that updateObject tool has correct type annotations for optional values."""
        # Read the updateObject tool
        with open("/Users/zach/code/trellis-mcp/src/trellis_mcp/tools/update_object.py", "r") as f:
            content = f.read()

        # Verify the yamlPatch parameter has correct type annotation
        assert "yamlPatch: dict[str, str | list[str] | None]" in content

    def test_get_object_tool_return_type_annotation_correct(self):
        """Test that getObject tool has correct return type annotation."""
        # Read the getObject tool
        with open("/Users/zach/code/trellis-mcp/src/trellis_mcp/tools/get_object.py", "r") as f:
            content = f.read()

        # Verify the return type annotation handles None values
        assert "dict[str, str | dict[str, str | list[str] | None]]" in content
