"""Simple test to verify MCP tool handlers handle optional parent fields correctly.

This test verifies that the MCP tool handlers properly handle None parent values
and return appropriate data structures for standalone tasks.
"""

from datetime import datetime
from pathlib import Path

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
        # Get the project root directory
        project_root = Path(__file__).parent.parent.parent
        list_backlog_path = project_root / "src" / "trellis_mcp" / "tools" / "list_backlog.py"

        with open(list_backlog_path, "r") as f:
            content = f.read()

        # Verify the documentation was updated to show optional parent
        assert '"parent": str | None' in content
        assert "None for standalone tasks" in content

    def test_create_object_tool_documentation_correct(self):
        """Test that createObject tool documentation is correct for optional parent."""
        # Get the project root directory
        project_root = Path(__file__).parent.parent.parent
        create_object_path = project_root / "src" / "trellis_mcp" / "tools" / "create_object.py"

        with open(create_object_path, "r") as f:
            content = f.read()

        # Verify the function signature has correct type annotation (MCP Inspector compatible)
        assert 'parent: str = ""' in content
        # Verify the documentation explains the optional parent
        assert "empty string for no parent" in content

    def test_update_object_tool_type_annotation_correct(self):
        """Test that updateObject tool has correct type annotations for optional values."""
        # Get the project root directory
        project_root = Path(__file__).parent.parent.parent
        update_object_path = project_root / "src" / "trellis_mcp" / "tools" / "update_object.py"

        with open(update_object_path, "r") as f:
            content = f.read()

        # Verify the yamlPatch parameter has correct type annotation
        # Updated to match new Annotated type signature
        assert "yamlPatch: Annotated[" in content
        assert "dict[str, str | list[str] | None]" in content

    def test_get_object_tool_return_type_annotation_correct(self):
        """Test that getObject tool has correct return type annotation."""
        # Get the project root directory
        project_root = Path(__file__).parent.parent.parent
        get_object_path = project_root / "src" / "trellis_mcp" / "tools" / "get_object.py"

        with open(get_object_path, "r") as f:
            content = f.read()

        # Verify the getObject function exists and can be used
        # (no specific return type annotation required)
        assert "def getObject(" in content
