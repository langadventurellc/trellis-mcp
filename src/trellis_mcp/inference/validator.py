"""File system validation for Trellis MCP object inference.

This module provides file system validation that verifies inferred object types
match actual objects on disk, including YAML metadata consistency checking.
Integrates with the existing validation framework for comprehensive error handling.
"""

from dataclasses import dataclass

from ..exceptions.validation_error import ValidationError, ValidationErrorCode
from ..object_parser import parse_object
from ..validation.error_collector import ValidationErrorCollector
from .path_builder import PathBuilder


@dataclass
class ValidationResult:
    """Comprehensive validation result structure.

    Provides detailed information about file system validation operations,
    including object existence, type consistency, metadata validity, and
    comprehensive error reporting.
    """

    is_valid: bool
    object_exists: bool
    type_matches: bool
    metadata_valid: bool
    errors: list[str]
    warnings: list[str]

    @classmethod
    def success(cls) -> "ValidationResult":
        """Create a successful validation result."""
        return cls(
            is_valid=True,
            object_exists=True,
            type_matches=True,
            metadata_valid=True,
            errors=[],
            warnings=[],
        )

    @classmethod
    def failure(
        cls,
        object_exists: bool = False,
        type_matches: bool = False,
        metadata_valid: bool = False,
        errors: list[str] | None = None,
        warnings: list[str] | None = None,
    ) -> "ValidationResult":
        """Create a failed validation result with specific failure details."""
        return cls(
            is_valid=False,
            object_exists=object_exists,
            type_matches=type_matches,
            metadata_valid=metadata_valid,
            errors=errors or [],
            warnings=warnings or [],
        )


class FileSystemValidator:
    """File system validation for inferred object types.

    Verifies that inferred object types match actual objects on disk,
    including comprehensive YAML metadata consistency checking.
    Integrates with existing PathBuilder and validation infrastructure
    for security and error handling.

    Example:
        >>> path_builder = PathBuilder("./planning")
        >>> validator = FileSystemValidator(path_builder)
        >>> result = validator.validate_object_structure("task", "T-implement-auth")
        >>> if result.is_valid:
        ...     print("Validation passed")
        ... else:
        ...     print(f"Validation failed: {result.errors}")
    """

    def __init__(self, path_builder: PathBuilder):
        """Initialize FileSystemValidator with PathBuilder.

        Args:
            path_builder: PathBuilder instance for secure path construction

        Raises:
            ValueError: If path_builder is None
        """
        if path_builder is None:
            raise ValueError("PathBuilder cannot be None")

        self.path_builder = path_builder

    def validate_object_exists(self, kind: str, object_id: str, status: str = "open") -> bool:
        """Check if object file exists at inferred path.

        Uses PathBuilder to construct the appropriate file path based on
        object kind and ID, then verifies the file exists on disk.

        Args:
            kind: Object type ("project", "epic", "feature", or "task")
            object_id: Object ID (with or without prefix)
            status: Object status for task path resolution (default: "open")

        Returns:
            True if object file exists, False otherwise

        Raises:
            ValueError: If kind is invalid or object_id is empty
            ValidationError: If path construction fails due to security validation
        """
        try:
            # Use PathBuilder to construct secure path
            # For tasks, we need to specify status to build correct path
            builder = self.path_builder.for_object(kind, object_id)
            if kind == "task":
                builder = builder.with_status(status)
            path = builder.build_path()
            return path.exists() and path.is_file()
        except (ValueError, ValidationError):
            # Path construction failed - object doesn't exist or is invalid
            return False

    def validate_type_consistency(self, kind: str, object_id: str, status: str = "open") -> bool:
        """Verify YAML metadata kind field matches inferred type.

        Parses the object's YAML front-matter and verifies that the
        'kind' field matches the inferred object type.

        Args:
            kind: Inferred object type
            object_id: Object ID (with or without prefix)
            status: Object status for task path resolution (default: "open")

        Returns:
            True if types match, False otherwise
        """
        try:
            # First check if object exists
            if not self.validate_object_exists(kind, object_id, status):
                return False

            # Construct path and parse object
            builder = self.path_builder.for_object(kind, object_id)
            if kind == "task":
                builder = builder.with_status(status)
            path = builder.build_path()
            obj = parse_object(path)

            # Compare inferred kind with actual kind
            return obj.kind == kind

        except Exception:
            # Any parsing or validation error means types don't match
            return False

    def validate_object_structure(
        self, kind: str, object_id: str, status: str = "open"
    ) -> ValidationResult:
        """Complete validation with detailed results.

        Performs comprehensive validation including file existence,
        type consistency, and metadata validation using existing
        validation infrastructure.

        Args:
            kind: Object type to validate
            object_id: Object ID to validate
            status: Object status for task path resolution (default: "open")

        Returns:
            ValidationResult with detailed validation information
        """
        # Initialize error collector for comprehensive error handling
        collector = ValidationErrorCollector(object_id=object_id, object_kind=kind)

        # Track validation state
        object_exists = False
        type_matches = False
        metadata_valid = False

        try:
            # Step 1: Check file existence
            object_exists = self.validate_object_exists(kind, object_id, status)
            if not object_exists:
                collector.add_error(
                    f"Object file not found for {kind} '{object_id}'",
                    ValidationErrorCode.INVALID_FIELD,
                    context={
                        "validation_step": "file_existence",
                        "kind": kind,
                        "object_id": object_id,
                    },
                )
                return ValidationResult.failure(
                    object_exists=False,
                    errors=[msg for msg, _, _ in collector.get_prioritized_errors()],
                )

            # Step 2: Parse object metadata
            try:
                builder = self.path_builder.for_object(kind, object_id)
                if kind == "task":
                    builder = builder.with_status(status)
                path = builder.build_path()
                obj = parse_object(path)
                metadata_valid = True

            except Exception as e:
                metadata_valid = False
                collector.add_error(
                    f"Failed to parse object metadata: {str(e)}",
                    ValidationErrorCode.INVALID_FIELD,
                    context={"validation_step": "metadata_parsing", "parse_error": str(e)},
                )
                return ValidationResult.failure(
                    object_exists=True,
                    metadata_valid=False,
                    errors=[msg for msg, _, _ in collector.get_prioritized_errors()],
                )

            # Step 3: Verify type consistency
            type_matches = obj.kind == kind
            if not type_matches:
                collector.add_error(
                    f"Type mismatch: inferred '{kind}' but actual object is '{obj.kind}'",
                    ValidationErrorCode.INVALID_FIELD,
                    context={
                        "validation_step": "type_consistency",
                        "inferred_kind": kind,
                        "actual_kind": obj.kind,
                    },
                )
                return ValidationResult.failure(
                    object_exists=True,
                    metadata_valid=True,
                    type_matches=False,
                    errors=[msg for msg, _, _ in collector.get_prioritized_errors()],
                )

            # Step 4: Validate schema compliance using existing validation
            try:
                from ..validation.enhanced_validation import validate_object_data_with_collector

                # Convert Pydantic model to dict for validation
                obj_data = obj.model_dump()

                # Use existing enhanced validation for schema compliance
                schema_collector = validate_object_data_with_collector(
                    obj_data, self.path_builder._project_root
                )

                if schema_collector.has_errors():
                    # Add schema validation errors to our collector
                    for msg, code, ctx in schema_collector.get_prioritized_errors():
                        collector.add_error(
                            f"Schema validation failed: {msg}",
                            code,
                            context={**ctx, "validation_step": "schema_compliance"},
                        )

                    return ValidationResult.failure(
                        object_exists=True,
                        metadata_valid=True,
                        type_matches=True,
                        errors=[msg for msg, _, _ in collector.get_prioritized_errors()],
                    )

            except Exception as e:
                collector.add_error(
                    f"Schema validation error: {str(e)}",
                    ValidationErrorCode.INVALID_FIELD,
                    context={"validation_step": "schema_compliance", "schema_error": str(e)},
                )
                return ValidationResult.failure(
                    object_exists=True,
                    metadata_valid=True,
                    type_matches=True,
                    errors=[msg for msg, _, _ in collector.get_prioritized_errors()],
                )

            # All validation passed
            return ValidationResult.success()

        except Exception as e:
            # Unexpected error during validation
            collector.add_error(
                f"Unexpected validation error: {str(e)}",
                ValidationErrorCode.INVALID_FIELD,
                context={"validation_step": "unexpected_error", "error": str(e)},
            )
            return ValidationResult.failure(
                object_exists=object_exists,
                type_matches=type_matches,
                metadata_valid=metadata_valid,
                errors=[msg for msg, _, _ in collector.get_prioritized_errors()],
            )
