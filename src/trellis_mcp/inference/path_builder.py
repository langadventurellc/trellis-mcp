"""Path builder for Trellis MCP object path construction.

This module provides a unified PathBuilder class that constructs appropriate file
paths based on inferred object types, supporting both hierarchical and standalone
object structures while integrating with existing security validation.
"""

from pathlib import Path
from typing import Final

from ..exceptions.validation_error import ValidationError, ValidationErrorCode
from ..fs_utils import ensure_parent_dirs
from ..path_resolver import resolve_project_roots


class PathBuilder:
    """Unified path builder for all Trellis MCP object types.

    Provides a fluent interface for constructing filesystem paths for projects,
    epics, features, and tasks while integrating with existing path resolution
    utilities and security validation.

    The builder pattern allows for flexible path construction workflows:
    1. Initialize with project root
    2. Configure object type, ID, and optional parameters
    3. Build and validate the final path
    4. Optionally ensure parent directories exist

    Supports both hierarchical objects (within project/epic/feature structure)
    and standalone tasks with comprehensive security validation.

    Example:
        >>> builder = PathBuilder("./planning")
        >>> path = builder.for_object("task", "T-implement-auth", "F-login").build_path()
        >>> builder.ensure_directories()

    Security Features:
        - Input validation using existing validation functions
        - Path boundary validation to prevent traversal attacks
        - Integration with existing security validation patterns
        - Safe directory creation using existing fs_utils
    """

    # Valid object kinds supported by the builder
    _VALID_KINDS: Final[set[str]] = {"project", "epic", "feature", "task"}

    def __init__(self, project_root: str | Path):
        """Initialize PathBuilder with project root.

        Args:
            project_root: Root directory for the planning structure

        Raises:
            ValueError: If project_root is empty or invalid
            ValidationError: If project_root contains invalid path components
        """
        if not project_root:
            raise ValueError("Project root cannot be empty")

        # Convert to Path and resolve project roots using existing utility
        self._project_root = Path(project_root)
        try:
            self._scanning_root, self._resolution_root = resolve_project_roots(self._project_root)
        except Exception as e:
            raise ValidationError(
                errors=[f"Invalid project root: {e}"],
                error_codes=[ValidationErrorCode.INVALID_FIELD],
                context={"project_root": str(project_root)},
            )

        # Builder state
        self._kind: str | None = None
        self._object_id: str | None = None
        self._parent_id: str | None = None
        self._status: str | None = None
        self._constructed_path: Path | None = None

    def for_object(self, kind: str, object_id: str, parent_id: str | None = None) -> "PathBuilder":
        """Configure object type, ID, and optional parent for path construction.

        Args:
            kind: Object type ("project", "epic", "feature", or "task")
            object_id: Object ID (with or without prefix, e.g., "T-auth" or "auth")
            parent_id: Parent object ID (required for epics/features, optional for tasks)

        Returns:
            Self for method chaining

        Raises:
            ValueError: If kind is invalid or object_id is empty
        """
        # Validate kind
        if not kind or kind not in self._VALID_KINDS:
            raise ValueError(f"Invalid kind '{kind}'. Must be one of: {self._VALID_KINDS}")

        # Validate object_id
        if not object_id or not object_id.strip():
            raise ValueError("Object ID cannot be empty")

        self._kind = kind
        self._object_id = object_id.strip()
        self._parent_id = parent_id.strip() if parent_id else None
        return self

    def with_status(self, status: str | None) -> "PathBuilder":
        """Configure object status for path construction (affects task paths).

        Args:
            status: Object status (e.g., "open", "done", "in-progress")

        Returns:
            Self for method chaining
        """
        self._status = status
        return self

    def build_path(self) -> Path:
        """Construct the filesystem path based on configured parameters.

        Uses existing path resolution utilities and applies comprehensive
        security validation to ensure safe path construction.

        Returns:
            Path object pointing to the target file location

        Raises:
            ValueError: If required configuration is missing or invalid
            ValidationError: If security validation fails
        """
        if not self._kind or not self._object_id:
            raise ValueError("Must configure object kind and ID before building path")

        # Apply existing security validation for tasks
        if self._kind == "task":
            self._validate_task_security()

        # Clean the object ID using existing patterns
        clean_id = self._clean_object_id(self._object_id)

        # Construct path based on object type
        if self._kind == "project":
            path = self._build_project_path(clean_id)
        elif self._kind == "epic":
            path = self._build_epic_path(clean_id)
        elif self._kind == "feature":
            path = self._build_feature_path(clean_id)
        elif self._kind == "task":
            path = self._build_task_path(clean_id)
        else:
            raise ValueError(f"Unsupported kind: {self._kind}")

        # Final security validation using existing utilities
        self._validate_path_security(path)

        self._constructed_path = path
        return path

    def ensure_directories(self) -> Path:
        """Ensure all parent directories for the constructed path exist.

        Uses existing fs_utils.ensure_parent_dirs() for safe directory creation.

        Returns:
            The constructed path after ensuring directories exist

        Raises:
            ValueError: If path hasn't been constructed yet
            OSError: If directory creation fails
        """
        if not self._constructed_path:
            raise ValueError("Must build path before ensuring directories")

        # Use existing utility for safe directory creation
        ensure_parent_dirs(self._constructed_path)
        return self._constructed_path

    def validate_security(self) -> None:
        """Perform comprehensive security validation on the constructed path.

        Validates path boundaries and security constraints using existing
        validation utilities.

        Raises:
            ValueError: If path hasn't been constructed yet
            ValidationError: If security validation fails
        """
        if not self._constructed_path:
            raise ValueError("Must build path before validating security")

        self._validate_path_security(self._constructed_path)

    def _clean_object_id(self, object_id: str) -> str:
        """Clean object ID by removing prefixes using existing patterns.

        Args:
            object_id: Raw object ID (may have prefix)

        Returns:
            Clean ID without prefix
        """
        clean_id = object_id.strip()
        if clean_id.startswith(("P-", "E-", "F-", "T-")):
            clean_id = clean_id[2:]
        return clean_id

    def _build_project_path(self, clean_id: str) -> Path:
        """Build path for project objects."""
        return self._resolution_root / "projects" / f"P-{clean_id}" / "project.md"

    def _build_epic_path(self, clean_id: str) -> Path:
        """Build path for epic objects."""
        if not self._parent_id:
            raise ValueError("Parent project ID is required for epic objects")

        parent_clean = self._clean_object_id(self._parent_id)
        return (
            self._resolution_root
            / "projects"
            / f"P-{parent_clean}"
            / "epics"
            / f"E-{clean_id}"
            / "epic.md"
        )

    def _build_feature_path(self, clean_id: str) -> Path:
        """Build path for feature objects."""
        if not self._parent_id:
            raise ValueError("Parent epic ID is required for feature objects")

        # Use existing utility to find parent epic path
        from ..path_resolver import id_to_path

        parent_clean = self._clean_object_id(self._parent_id)
        try:
            epic_path = id_to_path(self._resolution_root, "epic", parent_clean)
            # Extract project directory from epic path
            project_dir = epic_path.parts[epic_path.parts.index("projects") + 1]
            return (
                self._resolution_root
                / "projects"
                / project_dir
                / "epics"
                / f"E-{parent_clean}"
                / "features"
                / f"F-{clean_id}"
                / "feature.md"
            )
        except FileNotFoundError:
            raise ValueError(f"Parent epic '{self._parent_id}' not found")

    def _build_task_path(self, clean_id: str) -> Path:
        """Build path for task objects (both hierarchical and standalone)."""
        if not self._parent_id:
            # Standalone task
            return self._build_standalone_task_path(clean_id)
        else:
            # Hierarchical task
            return self._build_hierarchical_task_path(clean_id)

    def _build_standalone_task_path(self, clean_id: str) -> Path:
        """Build path for standalone task objects."""
        from ..path_resolver import get_standalone_task_filename

        task_dir = "tasks-done" if self._status == "done" else "tasks-open"
        filename = get_standalone_task_filename(clean_id, self._status)
        return self._resolution_root / task_dir / filename

    def _build_hierarchical_task_path(self, clean_id: str) -> Path:
        """Build path for hierarchical task objects."""
        if not self._parent_id:
            raise ValueError("Parent feature ID is required for hierarchical task objects")

        # Use existing utility to find parent feature path
        from ..path_resolver import get_standalone_task_filename, id_to_path

        parent_clean = self._clean_object_id(self._parent_id)
        try:
            feature_path = id_to_path(self._resolution_root, "feature", parent_clean)
            # Extract project and epic directories from feature path
            project_dir = feature_path.parts[feature_path.parts.index("projects") + 1]
            epic_dir = feature_path.parts[feature_path.parts.index("epics") + 1]

            task_dir = "tasks-done" if self._status == "done" else "tasks-open"
            filename = get_standalone_task_filename(clean_id, self._status)

            return (
                self._resolution_root
                / "projects"
                / project_dir
                / "epics"
                / epic_dir
                / "features"
                / f"F-{parent_clean}"
                / task_dir
                / filename
            )
        except FileNotFoundError:
            raise ValueError(f"Parent feature '{self._parent_id}' not found")

    def _validate_task_security(self) -> None:
        """Apply security validation for task objects using existing utilities."""
        from ..validation.field_validation import validate_standalone_task_path_parameters
        from ..validation.security import validate_standalone_task_path_security

        # Field validation - ensure object_id is not None
        object_id_str = self._object_id or ""
        validation_errors = validate_standalone_task_path_parameters(object_id_str, self._status)
        if validation_errors:
            raise ValidationError(
                errors=validation_errors,
                error_codes=[ValidationErrorCode.INVALID_FIELD],
                context={"object_id": self._object_id, "status": self._status},
            )

        # Security validation - ensure object_id is not None
        security_errors = validate_standalone_task_path_security(
            object_id_str, str(self._project_root)
        )
        if security_errors:
            raise ValidationError(
                errors=security_errors,
                error_codes=[ValidationErrorCode.INVALID_FIELD],
                context={"object_id": self._object_id, "project_root": str(self._project_root)},
            )

    def _validate_path_security(self, path: Path) -> None:
        """Validate path security using existing boundary validation utilities."""
        if self._kind == "task":
            from ..validation.security import validate_path_boundaries

            boundary_errors = validate_path_boundaries(str(path), str(self._resolution_root))
            if boundary_errors:
                raise ValidationError(
                    errors=boundary_errors,
                    error_codes=[ValidationErrorCode.INVALID_FIELD],
                    context={"path": str(path), "resolution_root": str(self._resolution_root)},
                )
