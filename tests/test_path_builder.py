"""Comprehensive test suite for PathBuilder class.

Tests path construction logic for all object types, security validation,
cross-system compatibility, and integration with existing utilities.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from src.trellis_mcp.exceptions.validation_error import ValidationError
from src.trellis_mcp.inference.path_builder import PathBuilder


class TestPathBuilderInitialization:
    """Test PathBuilder initialization and configuration."""

    def test_init_with_valid_project_root(self, temp_planning_dir):
        """Test initialization with valid project root."""
        builder = PathBuilder(temp_planning_dir)
        assert builder._project_root == Path(temp_planning_dir)
        assert builder._resolution_root is not None
        assert builder._scanning_root is not None

    def test_init_with_empty_project_root(self):
        """Test initialization with empty project root raises ValueError."""
        with pytest.raises(ValueError, match="Project root cannot be empty"):
            PathBuilder("")

    def test_init_with_none_project_root(self):
        """Test initialization with None project root raises ValueError."""
        with pytest.raises(ValueError, match="Project root cannot be empty"):
            PathBuilder(None)  # type: ignore


class TestPathBuilderConfiguration:
    """Test PathBuilder fluent configuration methods."""

    def test_for_object_valid_parameters(self, temp_planning_dir):
        """Test for_object with valid parameters."""
        builder = PathBuilder(temp_planning_dir)
        result = builder.for_object("project", "P-test-project")

        assert result is builder  # Returns self for chaining
        assert builder._kind == "project"
        assert builder._object_id == "P-test-project"
        assert builder._parent_id is None

    def test_for_object_with_parent(self, temp_planning_dir):
        """Test for_object with parent ID."""
        builder = PathBuilder(temp_planning_dir)
        builder.for_object("epic", "E-test-epic", "P-test-project")

        assert builder._kind == "epic"
        assert builder._object_id == "E-test-epic"
        assert builder._parent_id == "P-test-project"

    def test_for_object_invalid_kind(self, temp_planning_dir):
        """Test for_object with invalid kind raises ValueError."""
        builder = PathBuilder(temp_planning_dir)
        with pytest.raises(ValueError, match="Invalid kind 'invalid'"):
            builder.for_object("invalid", "test-id")

    def test_for_object_empty_object_id(self, temp_planning_dir):
        """Test for_object with empty object ID raises ValueError."""
        builder = PathBuilder(temp_planning_dir)
        with pytest.raises(ValueError, match="Object ID cannot be empty"):
            builder.for_object("project", "")

    def test_with_status(self, temp_planning_dir):
        """Test with_status configuration."""
        builder = PathBuilder(temp_planning_dir)
        result = builder.with_status("done")

        assert result is builder  # Returns self for chaining
        assert builder._status == "done"


class TestProjectPathConstruction:
    """Test project path construction."""

    def test_build_project_path_with_prefix(self, temp_planning_dir):
        """Test building project path with P- prefix."""
        builder = PathBuilder(temp_planning_dir)
        path = builder.for_object("project", "P-user-auth").build_path()

        expected = Path(temp_planning_dir) / "projects" / "P-user-auth" / "project.md"
        assert path == expected

    def test_build_project_path_without_prefix(self, temp_planning_dir):
        """Test building project path without P- prefix."""
        builder = PathBuilder(temp_planning_dir)
        path = builder.for_object("project", "user-auth").build_path()

        expected = Path(temp_planning_dir) / "projects" / "P-user-auth" / "project.md"
        assert path == expected

    def test_build_project_path_existing_planning(self, temp_planning_dir):
        """Test building project path when planning directory exists."""
        planning_dir = Path(temp_planning_dir) / "planning"
        planning_dir.mkdir()

        builder = PathBuilder(planning_dir)
        path = builder.for_object("project", "test-project").build_path()

        expected = planning_dir / "projects" / "P-test-project" / "project.md"
        assert path == expected


class TestEpicPathConstruction:
    """Test epic path construction."""

    def test_build_epic_path_valid_parent(self, temp_planning_dir):
        """Test building epic path with valid parent project."""
        builder = PathBuilder(temp_planning_dir)
        path = builder.for_object("epic", "E-authentication", "P-user-system").build_path()

        expected = (
            Path(temp_planning_dir)
            / "projects"
            / "P-user-system"
            / "epics"
            / "E-authentication"
            / "epic.md"
        )
        assert path == expected

    def test_build_epic_path_parent_without_prefix(self, temp_planning_dir):
        """Test building epic path with parent without prefix."""
        builder = PathBuilder(temp_planning_dir)
        path = builder.for_object("epic", "authentication", "user-system").build_path()

        expected = (
            Path(temp_planning_dir)
            / "projects"
            / "P-user-system"
            / "epics"
            / "E-authentication"
            / "epic.md"
        )
        assert path == expected

    def test_build_epic_path_missing_parent(self, temp_planning_dir):
        """Test building epic path without parent raises ValueError."""
        builder = PathBuilder(temp_planning_dir)
        with pytest.raises(ValueError, match="Parent project ID is required"):
            builder.for_object("epic", "authentication").build_path()


class TestFeaturePathConstruction:
    """Test feature path construction."""

    @patch("src.trellis_mcp.path_resolver.id_to_path")
    def test_build_feature_path_valid_parent(self, mock_id_to_path, temp_planning_dir):
        """Test building feature path with valid parent epic."""
        # Mock the epic path lookup
        mock_epic_path = (
            Path(temp_planning_dir) / "projects" / "P-user-system" / "epics" / "E-auth" / "epic.md"
        )
        mock_id_to_path.return_value = mock_epic_path

        builder = PathBuilder(temp_planning_dir)
        path = builder.for_object("feature", "F-login", "E-auth").build_path()

        expected = (
            Path(temp_planning_dir)
            / "projects"
            / "P-user-system"
            / "epics"
            / "E-auth"
            / "features"
            / "F-login"
            / "feature.md"
        )
        assert path == expected
        mock_id_to_path.assert_called_once()

    @patch("src.trellis_mcp.path_resolver.id_to_path")
    def test_build_feature_path_parent_not_found(self, mock_id_to_path, temp_planning_dir):
        """Test building feature path with non-existent parent epic."""
        mock_id_to_path.side_effect = FileNotFoundError("Epic not found")

        builder = PathBuilder(temp_planning_dir)
        with pytest.raises(ValueError, match="Parent epic 'E-nonexistent' not found"):
            builder.for_object("feature", "login", "E-nonexistent").build_path()

    def test_build_feature_path_missing_parent(self, temp_planning_dir):
        """Test building feature path without parent raises ValueError."""
        builder = PathBuilder(temp_planning_dir)
        with pytest.raises(ValueError, match="Parent epic ID is required"):
            builder.for_object("feature", "login").build_path()


class TestStandaloneTaskPathConstruction:
    """Test standalone task path construction."""

    @patch("src.trellis_mcp.path_resolver.get_standalone_task_filename")
    @patch("src.trellis_mcp.validation.field_validation.validate_standalone_task_path_parameters")
    @patch("src.trellis_mcp.validation.security.validate_standalone_task_path_security")
    def test_build_standalone_task_open(
        self, mock_security, mock_params, mock_filename, temp_planning_dir
    ):
        """Test building standalone task path for open task."""
        mock_params.return_value = []  # No validation errors
        mock_security.return_value = []  # No security errors
        mock_filename.return_value = "T-implement-auth.md"

        builder = PathBuilder(temp_planning_dir)
        path = builder.for_object("task", "T-implement-auth").with_status("open").build_path()

        expected = Path(temp_planning_dir) / "tasks-open" / "T-implement-auth.md"
        assert path == expected

    @patch("src.trellis_mcp.path_resolver.get_standalone_task_filename")
    @patch("src.trellis_mcp.validation.field_validation.validate_standalone_task_path_parameters")
    @patch("src.trellis_mcp.validation.security.validate_standalone_task_path_security")
    def test_build_standalone_task_done(
        self, mock_security, mock_params, mock_filename, temp_planning_dir
    ):
        """Test building standalone task path for done task."""
        mock_params.return_value = []  # No validation errors
        mock_security.return_value = []  # No security errors
        mock_filename.return_value = "20250718_143000-T-implement-auth.md"

        builder = PathBuilder(temp_planning_dir)
        path = builder.for_object("task", "implement-auth").with_status("done").build_path()

        expected = Path(temp_planning_dir) / "tasks-done" / "20250718_143000-T-implement-auth.md"
        assert path == expected


class TestHierarchicalTaskPathConstruction:
    """Test hierarchical task path construction."""

    @patch("src.trellis_mcp.path_resolver.id_to_path")
    @patch("src.trellis_mcp.path_resolver.get_standalone_task_filename")
    @patch("src.trellis_mcp.validation.field_validation.validate_standalone_task_path_parameters")
    @patch("src.trellis_mcp.validation.security.validate_standalone_task_path_security")
    def test_build_hierarchical_task_open(
        self, mock_security, mock_params, mock_filename, mock_id_to_path, temp_planning_dir
    ):
        """Test building hierarchical task path for open task."""
        mock_params.return_value = []  # No validation errors
        mock_security.return_value = []  # No security errors
        mock_filename.return_value = "T-implement-login.md"

        # Mock the feature path lookup
        mock_feature_path = (
            Path(temp_planning_dir)
            / "projects"
            / "P-user-system"
            / "epics"
            / "E-auth"
            / "features"
            / "F-login"
            / "feature.md"
        )
        mock_id_to_path.return_value = mock_feature_path

        builder = PathBuilder(temp_planning_dir)
        path = (
            builder.for_object("task", "T-implement-login", "F-login")
            .with_status("open")
            .build_path()
        )

        expected = (
            Path(temp_planning_dir)
            / "projects"
            / "P-user-system"
            / "epics"
            / "E-auth"
            / "features"
            / "F-login"
            / "tasks-open"
            / "T-implement-login.md"
        )
        assert path == expected

    @patch("src.trellis_mcp.path_resolver.id_to_path")
    def test_build_hierarchical_task_parent_not_found(self, mock_id_to_path, temp_planning_dir):
        """Test building hierarchical task path with non-existent parent feature."""
        mock_id_to_path.side_effect = FileNotFoundError("Feature not found")

        with patch(
            "src.trellis_mcp.validation.field_validation.validate_standalone_task_path_parameters",
            return_value=[],
        ):
            with patch(
                "src.trellis_mcp.validation.security.validate_standalone_task_path_security",
                return_value=[],
            ):
                builder = PathBuilder(temp_planning_dir)
                with pytest.raises(ValueError, match="Parent feature 'F-nonexistent' not found"):
                    builder.for_object("task", "implement-login", "F-nonexistent").build_path()


class TestSecurityValidation:
    """Test security validation integration."""

    @patch("src.trellis_mcp.validation.field_validation.validate_standalone_task_path_parameters")
    def test_task_validation_errors(self, mock_params, temp_planning_dir):
        """Test task validation errors are properly raised."""
        mock_params.return_value = ["Invalid task ID format"]

        builder = PathBuilder(temp_planning_dir)
        with pytest.raises(ValidationError) as exc_info:
            builder.for_object("task", "invalid..task").build_path()

        assert "Invalid task ID format" in str(exc_info.value)

    @patch("src.trellis_mcp.validation.security.validate_standalone_task_path_security")
    @patch("src.trellis_mcp.validation.field_validation.validate_standalone_task_path_parameters")
    def test_task_security_errors(self, mock_params, mock_security, temp_planning_dir):
        """Test task security errors are properly raised."""
        mock_params.return_value = []  # No validation errors
        mock_security.return_value = ["Path traversal attempt detected"]

        builder = PathBuilder(temp_planning_dir)
        with pytest.raises(ValidationError) as exc_info:
            builder.for_object("task", "malicious-task").build_path()

        assert "Path traversal attempt detected" in str(exc_info.value)

    @patch("src.trellis_mcp.validation.security.validate_path_boundaries")
    @patch("src.trellis_mcp.validation.field_validation.validate_standalone_task_path_parameters")
    @patch("src.trellis_mcp.validation.security.validate_standalone_task_path_security")
    def test_path_boundary_validation(
        self, mock_task_security, mock_params, mock_boundaries, temp_planning_dir
    ):
        """Test path boundary validation for tasks."""
        mock_params.return_value = []  # No validation errors
        mock_task_security.return_value = []  # No task security errors
        mock_boundaries.return_value = ["Path exceeds project boundaries"]

        builder = PathBuilder(temp_planning_dir)
        with pytest.raises(ValidationError) as exc_info:
            builder.for_object("task", "boundary-test").build_path()

        assert "Path exceeds project boundaries" in str(exc_info.value)


class TestDirectoryCreation:
    """Test directory creation functionality."""

    @patch("src.trellis_mcp.inference.path_builder.ensure_parent_dirs")
    def test_ensure_directories_success(self, mock_ensure, temp_planning_dir):
        """Test successful directory creation."""
        builder = PathBuilder(temp_planning_dir)
        path = builder.for_object("project", "test-project").build_path()

        result = builder.ensure_directories()

        assert result == path
        mock_ensure.assert_called_once_with(path)

    def test_ensure_directories_without_build(self, temp_planning_dir):
        """Test ensure_directories without building path first raises ValueError."""
        builder = PathBuilder(temp_planning_dir)

        with pytest.raises(ValueError, match="Must build path before ensuring directories"):
            builder.ensure_directories()


class TestValidationMethods:
    """Test standalone validation methods."""

    @patch("src.trellis_mcp.validation.security.validate_path_boundaries")
    @patch("src.trellis_mcp.validation.field_validation.validate_standalone_task_path_parameters")
    @patch("src.trellis_mcp.validation.security.validate_standalone_task_path_security")
    def test_validate_security_success(
        self, mock_task_security, mock_params, mock_boundaries, temp_planning_dir
    ):
        """Test successful security validation."""
        mock_params.return_value = []
        mock_task_security.return_value = []
        mock_boundaries.return_value = []

        builder = PathBuilder(temp_planning_dir)
        builder.for_object("task", "test-task").build_path()

        # Should not raise any exceptions
        builder.validate_security()

    def test_validate_security_without_build(self, temp_planning_dir):
        """Test validate_security without building path first raises ValueError."""
        builder = PathBuilder(temp_planning_dir)

        with pytest.raises(ValueError, match="Must build path before validating security"):
            builder.validate_security()


class TestErrorConditions:
    """Test various error conditions and edge cases."""

    def test_build_path_without_configuration(self, temp_planning_dir):
        """Test building path without configuring object raises ValueError."""
        builder = PathBuilder(temp_planning_dir)

        with pytest.raises(ValueError, match="Must configure object kind and ID"):
            builder.build_path()

    def test_build_path_missing_object_id(self, temp_planning_dir):
        """Test building path with missing object ID raises ValueError."""
        builder = PathBuilder(temp_planning_dir)
        builder._kind = "project"  # Set kind but not object_id

        with pytest.raises(ValueError, match="Must configure object kind and ID"):
            builder.build_path()


class TestMethodChaining:
    """Test fluent interface method chaining."""

    @patch("src.trellis_mcp.validation.field_validation.validate_standalone_task_path_parameters")
    @patch("src.trellis_mcp.validation.security.validate_standalone_task_path_security")
    @patch("src.trellis_mcp.validation.security.validate_path_boundaries")
    @patch("src.trellis_mcp.inference.path_builder.ensure_parent_dirs")
    def test_complete_fluent_workflow(
        self, mock_ensure, mock_boundaries, mock_task_security, mock_params, temp_planning_dir
    ):
        """Test complete fluent workflow with method chaining."""
        mock_params.return_value = []
        mock_task_security.return_value = []
        mock_boundaries.return_value = []

        builder = PathBuilder(temp_planning_dir)
        path = builder.for_object("task", "T-test-task").with_status("open").build_path()

        final_path = builder.ensure_directories()

        assert path == final_path
        mock_ensure.assert_called_once_with(path)


# Fixtures for testing


@pytest.fixture
def temp_planning_dir():
    """Create a temporary directory for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield temp_dir


# Integration tests with real filesystem


class TestIntegrationWithFilesystem:
    """Integration tests with actual filesystem operations."""

    def test_project_path_construction_integration(self, temp_planning_dir):
        """Integration test for project path construction."""
        planning_dir = Path(temp_planning_dir) / "planning"
        planning_dir.mkdir()

        builder = PathBuilder(temp_planning_dir)
        path = builder.for_object("project", "integration-test").build_path()

        expected = planning_dir / "projects" / "P-integration-test" / "project.md"
        assert path == expected
        assert path.is_absolute()

    def test_directory_creation_integration(self, temp_planning_dir):
        """Integration test for directory creation."""
        builder = PathBuilder(temp_planning_dir)
        path = builder.for_object("project", "dir-test").build_path()

        # Directory shouldn't exist yet
        assert not path.parent.exists()

        # Create directories
        builder.ensure_directories()

        # Directory should now exist
        assert path.parent.exists()
        assert path.parent.is_dir()


class TestPerformanceRequirements:
    """Test performance requirements for path construction."""

    @patch("src.trellis_mcp.validation.field_validation.validate_standalone_task_path_parameters")
    @patch("src.trellis_mcp.validation.security.validate_standalone_task_path_security")
    def test_path_construction_speed(self, mock_security, mock_params, temp_planning_dir):
        """Test that path construction completes in < 5ms."""
        import time

        mock_params.return_value = []
        mock_security.return_value = []

        builder = PathBuilder(temp_planning_dir)

        start_time = time.time()
        path = builder.for_object("project", "speed-test").build_path()
        end_time = time.time()

        construction_time = (end_time - start_time) * 1000  # Convert to milliseconds
        assert (
            construction_time < 5.0
        ), f"Path construction took {construction_time:.2f}ms, should be < 5ms"
        assert path is not None
