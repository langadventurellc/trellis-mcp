"""Tests for graph_utils module."""

from pathlib import Path
from unittest.mock import patch

import pytest

from trellis_mcp.graph_utils import DependencyGraph


class TestDependencyGraph:
    """Test cases for DependencyGraph class."""

    def test_init_creates_empty_graph(self):
        """Test that __init__ creates an empty graph."""
        graph = DependencyGraph()
        assert graph._graph == {}
        assert graph._objects == {}

    def test_graph_property_returns_copy(self):
        """Test that graph property returns a copy, not the original."""
        graph = DependencyGraph()
        graph._graph = {"a": ["b"], "b": []}

        graph_copy = graph.graph
        graph_copy["a"].append("c")

        # Original should be unchanged
        assert graph._graph == {"a": ["b"], "b": []}

    def test_objects_property_returns_copy(self):
        """Test that objects property returns a copy, not the original."""
        graph = DependencyGraph()
        graph._objects = {"a": {"id": "a"}, "b": {"id": "b"}}

        objects_copy = graph.objects
        objects_copy["a"]["modified"] = True

        # Original should be unchanged
        assert graph._objects == {"a": {"id": "a"}, "b": {"id": "b"}}

    @patch("trellis_mcp.graph_utils.get_all_objects")
    @patch("trellis_mcp.graph_utils.build_prerequisites_graph")
    def test_build_success(self, mock_build_graph, mock_get_objects):
        """Test successful graph building."""
        # Mock the dependencies
        mock_objects = {
            "task-a": {"id": "task-a", "prerequisites": ["task-b"]},
            "task-b": {"id": "task-b", "prerequisites": []},
        }
        mock_graph = {"task-a": ["task-b"], "task-b": []}

        mock_get_objects.return_value = mock_objects
        mock_build_graph.return_value = mock_graph

        # Build the graph
        graph = DependencyGraph()
        graph.build("/fake/project/root")

        # Verify calls
        mock_get_objects.assert_called_once_with("/fake/project/root")
        mock_build_graph.assert_called_once_with(mock_objects)

        # Verify state
        assert graph._objects == mock_objects
        assert graph._graph == mock_graph

    @patch("trellis_mcp.graph_utils.get_all_objects")
    def test_build_file_not_found_error(self, mock_get_objects):
        """Test that build raises FileNotFoundError when project root doesn't exist."""
        mock_get_objects.side_effect = FileNotFoundError("Project root not found")

        graph = DependencyGraph()
        with pytest.raises(FileNotFoundError, match="Project root not found"):
            graph.build("/nonexistent/path")

    @patch("trellis_mcp.graph_utils.get_all_objects")
    def test_build_value_error(self, mock_get_objects):
        """Test that build raises ValueError when object parsing fails."""
        mock_get_objects.side_effect = ValueError("Object parsing failed")

        graph = DependencyGraph()
        with pytest.raises(ValueError, match="Object parsing failed"):
            graph.build("/fake/project/root")

    def test_has_cycle_true(self):
        """Test has_cycle returns True when cycle is detected."""
        graph = DependencyGraph()
        graph._graph = {"task-a": ["task-b"], "task-b": ["task-a"]}

        assert graph.has_cycle() is True

    def test_has_cycle_false(self):
        """Test has_cycle returns False when no cycle is detected."""
        graph = DependencyGraph()
        graph._graph = {"task-a": ["task-b"], "task-b": []}

        assert graph.has_cycle() is False

    def test_has_cycle_empty_graph(self):
        """Test has_cycle with empty graph."""
        graph = DependencyGraph()
        assert graph.has_cycle() is False

    def test_build_accepts_path_object(self):
        """Test that build method accepts Path objects."""
        with patch("trellis_mcp.graph_utils.get_all_objects") as mock_get_objects:
            with patch("trellis_mcp.graph_utils.build_prerequisites_graph") as mock_build_graph:
                mock_get_objects.return_value = {}
                mock_build_graph.return_value = {}

                graph = DependencyGraph()
                path_obj = Path("/fake/project/root")
                graph.build(path_obj)

                mock_get_objects.assert_called_once_with(path_obj)

    def test_build_accepts_string_path(self):
        """Test that build method accepts string paths."""
        with patch("trellis_mcp.graph_utils.get_all_objects") as mock_get_objects:
            with patch("trellis_mcp.graph_utils.build_prerequisites_graph") as mock_build_graph:
                mock_get_objects.return_value = {}
                mock_build_graph.return_value = {}

                graph = DependencyGraph()
                graph.build("/fake/project/root")

                mock_get_objects.assert_called_once_with("/fake/project/root")

    def test_has_cycle_three_node_cycle(self):
        """Test has_cycle with 3-node cycle A->B->C->A."""
        graph = DependencyGraph()
        graph._graph = {"task-a": ["task-b"], "task-b": ["task-c"], "task-c": ["task-a"]}

        assert graph.has_cycle() is True

    def test_has_cycle_self_loop(self):
        """Test has_cycle with self-referencing node A->A."""
        graph = DependencyGraph()
        graph._graph = {"task-a": ["task-a"]}

        assert graph.has_cycle() is True

    def test_has_cycle_complex_no_cycle(self):
        """Test has_cycle with complex graph but no cycles."""
        graph = DependencyGraph()
        graph._graph = {
            "task-a": ["task-b", "task-c"],
            "task-b": ["task-d"],
            "task-c": ["task-d"],
            "task-d": [],
        }

        assert graph.has_cycle() is False

    def test_has_cycle_orphaned_nodes(self):
        """Test has_cycle with orphaned nodes (referenced but not in graph)."""
        graph = DependencyGraph()
        graph._graph = {"task-a": ["task-b", "task-orphan"], "task-b": []}

        assert graph.has_cycle() is False

    def test_has_cycle_no_cycle_chain(self):
        """Test has_cycle with no-cycle chain A→B→C."""
        graph = DependencyGraph()
        graph._graph = {"task-a": ["task-b"], "task-b": ["task-c"], "task-c": []}

        assert graph.has_cycle() is False
