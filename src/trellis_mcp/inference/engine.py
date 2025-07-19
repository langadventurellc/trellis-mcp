"""Kind Inference Engine API for Trellis MCP.

This module provides the main Kind Inference Engine API that integrates all
inference components (pattern matching, path resolution, validation, and caching)
into a cohesive, production-ready interface for simplified tool integration.
"""

import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from ..exceptions.validation_error import ValidationError, ValidationErrorCode
from ..utils.sanitization import sanitize_for_audit
from .cache import InferenceCache, InferenceResult
from .path_builder import PathBuilder
from .pattern_matcher import PatternMatcher
from .validator import FileSystemValidator, ValidationResult


@dataclass
class ExtendedInferenceResult:
    """Extended inference result with comprehensive validation details.

    Provides detailed information about inference operations including
    the inferred object type, validation status, performance metrics,
    and comprehensive error reporting for debugging and monitoring.
    """

    object_id: str
    inferred_kind: str
    is_valid: bool
    validation_result: ValidationResult | None = None
    inference_time_ms: float = 0.0
    cache_hit: bool = False

    def _sanitize_for_audit(self, text: str, max_length: int = 50) -> str:
        """Sanitize text for audit trail to prevent information disclosure.

        Args:
            text: The text to sanitize
            max_length: Maximum length of sanitized text

        Returns:
            Sanitized text safe for audit trails
        """
        return sanitize_for_audit(text, max_length)

    def __str__(self) -> str:
        """Return sanitized string representation for safe audit logging."""
        safe_object_id = self._sanitize_for_audit(self.object_id)

        # Sanitize validation result if present
        safe_validation_result = None
        if self.validation_result:
            safe_validation_result = self._sanitize_validation_result(self.validation_result)

        return (
            f"ExtendedInferenceResult(object_id='{safe_object_id}', "
            f"inferred_kind='{self.inferred_kind}', is_valid={self.is_valid}, "
            f"validation_result={safe_validation_result}, "
            f"inference_time_ms={self.inference_time_ms}, "
            f"cache_hit={self.cache_hit})"
        )

    def _sanitize_validation_result(self, validation_result: ValidationResult) -> str:
        """Sanitize validation result for safe audit logging."""
        if not validation_result:
            return "None"

        # Sanitize errors and warnings
        safe_errors = []
        for error in validation_result.errors:
            safe_error = self._sanitize_for_audit(error, max_length=100)
            safe_errors.append(safe_error)

        safe_warnings = []
        for warning in validation_result.warnings:
            safe_warning = self._sanitize_for_audit(warning, max_length=100)
            safe_warnings.append(safe_warning)

        return (
            f"ValidationResult(is_valid={validation_result.is_valid}, "
            f"object_exists={validation_result.object_exists}, "
            f"type_matches={validation_result.type_matches}, "
            f"metadata_valid={validation_result.metadata_valid}, "
            f"errors={safe_errors}, warnings={safe_warnings})"
        )


class KindInferenceEngine:
    """Main Kind Inference Engine API.

    Orchestrates all inference components (pattern matching, path resolution,
    validation, and caching) to provide a cohesive, high-performance API for
    automatic object type detection. Designed for integration with simplified
    tool interfaces.

    Performance targets:
    - Basic inference: < 10ms (including validation)
    - Cache hits: < 1ms
    - Thread-safe concurrent access
    - Memory efficient with bounded cache size

    Example:
        >>> engine = KindInferenceEngine("./planning")
        >>> kind = engine.infer_kind("T-implement-auth")
        >>> print(f"Detected: {kind}")  # "task"

        >>> result = engine.infer_with_validation("P-user-system")
        >>> if result.is_valid:
        ...     print(f"Valid {result.inferred_kind}")
    """

    def __init__(self, project_root: str | Path, cache_size: int = 1000):
        """Initialize KindInferenceEngine with all components.

        Initializes components in dependency order with proper error handling
        and validates project root accessibility.

        Args:
            project_root: Root directory for the planning structure
            cache_size: Maximum number of cache entries (default: 1000)

        Raises:
            ValidationError: If project root is invalid or inaccessible
            ValueError: If cache_size is not positive
        """
        if cache_size <= 0:
            raise ValueError("Cache size must be positive")

        self.project_root = Path(project_root)

        # Security validation: Check for path traversal attempts
        resolved_root = self.project_root.resolve()
        project_root_str = str(self.project_root)

        # Check for dangerous path patterns
        dangerous_patterns = ["..", "~", "%2e%2e", "%252e%252e"]
        for pattern in dangerous_patterns:
            if pattern in project_root_str:
                raise ValidationError(
                    errors=[f"Project root contains potentially dangerous path pattern: {pattern}"],
                    error_codes=[ValidationErrorCode.INVALID_FIELD],
                    context={"project_root": project_root_str, "pattern": pattern},
                )

        # Ensure the resolved path doesn't escape outside expected boundaries
        # This prevents symlink attacks and path traversal
        try:
            # Check that the path is absolute and doesn't contain relative components
            # after resolution
            if ".." in str(resolved_root):
                raise ValidationError(
                    errors=["Project root resolves to a path with parent directory references"],
                    error_codes=[ValidationErrorCode.INVALID_FIELD],
                    context={"project_root": project_root_str, "resolved": str(resolved_root)},
                )
        except (OSError, ValueError) as e:
            raise ValidationError(
                errors=[f"Project root path is invalid or inaccessible: {str(e)}"],
                error_codes=[ValidationErrorCode.INVALID_FIELD],
                context={"project_root": project_root_str, "error": str(e)},
            )

        # Validate project root accessibility
        if not self.project_root.exists():
            raise ValidationError(
                errors=[f"Project root does not exist: {self.project_root}"],
                error_codes=[ValidationErrorCode.INVALID_FIELD],
                context={"project_root": str(self.project_root)},
            )

        if not self.project_root.is_dir():
            raise ValidationError(
                errors=[f"Project root must be a directory, not a file: {self.project_root}"],
                error_codes=[ValidationErrorCode.INVALID_FIELD],
                context={"project_root": str(self.project_root)},
            )

        # Initialize components in dependency order
        self.pattern_matcher = PatternMatcher()
        self.path_builder = PathBuilder(self.project_root)
        self.validator = FileSystemValidator(self.path_builder)
        self.cache = InferenceCache(cache_size, self.path_builder)

    def infer_kind(self, object_id: str, validate: bool = True) -> str:
        """Infer object kind from ID prefix pattern.

        Main inference API that returns the KindEnum value for valid patterns.
        Integrates caching, pattern matching, and optional validation for
        optimal performance and reliability.

        Args:
            object_id: The object ID to analyze (e.g., "P-auth-system")
            validate: Whether to perform file system validation (default: True)

        Returns:
            The KindEnum value ("project", "epic", "feature", or "task")

        Raises:
            ValidationError: If object_id is invalid, doesn't match patterns,
                or validation fails when enabled

        Example:
            >>> engine.infer_kind("P-user-management")
            'project'
            >>> engine.infer_kind("T-create-login-form")
            'task'
        """
        # Validate input
        if not isinstance(object_id, str):
            if object_id is None:
                raise ValidationError(
                    errors=["Object ID cannot be empty"],
                    error_codes=[ValidationErrorCode.MISSING_REQUIRED_FIELD],
                    context={"object_id": object_id},
                )
            else:
                raise ValidationError(
                    errors=["Object ID must be a string"],
                    error_codes=[ValidationErrorCode.INVALID_FIELD],
                    context={"object_id": object_id, "type": type(object_id).__name__},
                )

        if not object_id.strip():
            raise ValidationError(
                errors=["Object ID cannot be empty"],
                error_codes=[ValidationErrorCode.MISSING_REQUIRED_FIELD],
                context={"object_id": object_id},
            )

        clean_id = object_id.strip()

        # 1. Check cache first
        cached_result = self.cache.get(clean_id)
        if cached_result and cached_result.is_valid:
            return cached_result.inferred_kind

        # 2. Pattern matching
        try:
            inferred_kind = self.pattern_matcher.infer_kind(clean_id)
        except ValidationError:
            # Re-raise pattern matching errors with additional context
            raise

        # 3. Optional validation
        if validate:
            validation_result = self.validator.validate_object_structure(inferred_kind, clean_id)
            if not validation_result.is_valid:
                # Sanitize error messages to prevent information disclosure
                sanitized_errors = self._sanitize_error_messages(validation_result.errors)
                raise ValidationError(
                    errors=sanitized_errors,
                    error_codes=[ValidationErrorCode.INVALID_FIELD],
                    context={
                        "object_id": clean_id,
                        "inferred_kind": inferred_kind,
                        "validation_step": "file_system_validation",
                    },
                )

        # 4. Cache result (only mark as valid if validation passed)
        # When validate=False, we don't know if the object is valid, so don't cache as valid
        is_valid = validate  # Only mark as valid if validation was performed and passed
        inference_result = InferenceResult.create(
            object_id=clean_id, inferred_kind=inferred_kind, is_valid=is_valid, file_mtime=None
        )
        if validate:  # Only cache validated results
            self.cache.put(clean_id, inference_result)

        return inferred_kind

    def infer_with_validation(self, object_id: str) -> ExtendedInferenceResult:
        """Extended inference API with comprehensive validation results.

        Provides detailed information about inference operations including
        validation results, performance metrics, and cache statistics.

        Args:
            object_id: The object ID to analyze

        Returns:
            ExtendedInferenceResult with detailed validation information

        Raises:
            ValidationError: If object_id format is invalid
        """
        start_time = time.time()

        # Validate input format
        if not isinstance(object_id, str) or not object_id.strip():
            raise ValidationError(
                errors=["Object ID must be a non-empty string"],
                error_codes=[ValidationErrorCode.INVALID_FIELD],
                context={"object_id": object_id},
            )

        clean_id = object_id.strip()
        cache_hit = False

        # Check cache first
        cached_result = self.cache.get(clean_id)
        if cached_result and cached_result.is_valid:
            cache_hit = True
            inference_time = (time.time() - start_time) * 1000
            return ExtendedInferenceResult(
                object_id=clean_id,
                inferred_kind=cached_result.inferred_kind,
                is_valid=True,
                validation_result=cached_result.validation_result,
                inference_time_ms=inference_time,
                cache_hit=True,
            )

        # Pattern matching with error capture
        try:
            inferred_kind = self.pattern_matcher.infer_kind(clean_id)
        except ValidationError as e:
            inference_time = (time.time() - start_time) * 1000
            return ExtendedInferenceResult(
                object_id=clean_id,
                inferred_kind="",
                is_valid=False,
                validation_result=ValidationResult.failure(errors=[str(e)]),
                inference_time_ms=inference_time,
                cache_hit=False,
            )

        # File system validation
        validation_result = self.validator.validate_object_structure(inferred_kind, clean_id)

        # Get file modification time for cache validation
        file_mtime = None
        if validation_result.is_valid:
            try:
                path = self.path_builder.for_object(inferred_kind, clean_id).build_path()
                if path.exists():
                    file_mtime = os.path.getmtime(path)
            except Exception:
                # If we can't get file mtime, cache will use time-based expiration
                pass

        # Cache result regardless of validation outcome
        inference_result = InferenceResult.create(
            object_id=clean_id,
            inferred_kind=inferred_kind,
            is_valid=validation_result.is_valid,
            validation_result=validation_result,
            file_mtime=file_mtime,
        )
        self.cache.put(clean_id, inference_result)

        inference_time = (time.time() - start_time) * 1000

        return ExtendedInferenceResult(
            object_id=clean_id,
            inferred_kind=inferred_kind,
            is_valid=validation_result.is_valid,
            validation_result=validation_result,
            inference_time_ms=inference_time,
            cache_hit=cache_hit,
        )

    def validate_object(self, object_id: str, expected_kind: str | None = None) -> ValidationResult:
        """Validation-only API for existing objects.

        Validates an object without caching the inference result.
        Useful for verification workflows and object consistency checking.

        Args:
            object_id: Object ID to validate
            expected_kind: Expected object type (inferred if not provided)

        Returns:
            ValidationResult with detailed validation information

        Raises:
            ValidationError: If object_id format is invalid
        """
        # Validate input
        if not isinstance(object_id, str) or not object_id.strip():
            raise ValidationError(
                errors=["Object ID must be a non-empty string"],
                error_codes=[ValidationErrorCode.INVALID_FIELD],
                context={"object_id": object_id},
            )

        clean_id = object_id.strip()

        # Determine kind to validate
        if expected_kind:
            kind = expected_kind
        else:
            try:
                kind = self.pattern_matcher.infer_kind(clean_id)
            except ValidationError as e:
                return ValidationResult.failure(errors=[f"Pattern inference failed: {str(e)}"])

        # Perform validation
        return self.validator.validate_object_structure(kind, clean_id)

    def get_cache_stats(self) -> dict[str, Any]:
        """Get cache performance statistics.

        Returns:
            Dictionary containing cache metrics for monitoring
        """
        return self.cache.get_stats()

    def clear_cache(self) -> None:
        """Clear the inference cache.

        Useful for testing or when project structure changes significantly.
        """
        self.cache.clear()

    def _sanitize_error_messages(self, errors: list[str]) -> list[str]:
        """Sanitize error messages to prevent information disclosure.

        Args:
            errors: List of error messages to sanitize

        Returns:
            List of sanitized error messages
        """
        sanitized = []
        for error in errors:
            # Check for Pydantic validation errors that might contain sensitive data
            if "input_value=" in error:
                # Remove the input_value part that could contain sensitive information
                parts = error.split("input_value=")
                if len(parts) > 1:
                    # Keep the part before input_value, remove the sensitive part
                    before_input = parts[0].strip()
                    if before_input.endswith(","):
                        before_input = before_input[:-1]
                    sanitized_error = before_input + " [input_value=REDACTED]"
                else:
                    sanitized_error = error
            else:
                # Apply general sanitization patterns
                sanitized_error = self._sanitize_for_general_errors(error)

            sanitized.append(sanitized_error)

        return sanitized

    def _sanitize_for_general_errors(self, text: str, max_length: int = 200) -> str:
        """Sanitize general error text for safe error reporting.

        Args:
            text: The text to sanitize
            max_length: Maximum length of sanitized text

        Returns:
            Sanitized text safe for error messages
        """
        return sanitize_for_audit(text, max_length)
