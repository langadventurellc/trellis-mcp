"""Core validation functions for Trellis MCP objects.

This module provides the main validation orchestration functions that
coordinate all aspects of object validation.
"""

from pathlib import Path
from typing import Any

from pydantic import ValidationError

from ..models.common import Priority
from ..schema.kind_enum import KindEnum
from ..schema.status_enum import StatusEnum
from .context_utils import format_validation_error_with_context, generate_contextual_error_message
from .exceptions import TrellisValidationError
from .parent_validation import validate_parent_exists_for_object
from .security import validate_standalone_task_security
from .task_utils import is_standalone_task


def validate_object_data(data: dict[str, Any], project_root: str | Path) -> None:
    """Comprehensive validation of object data.

    This function now uses Pydantic schema model validation for field validation,
    enum validation, and status validation, while maintaining filesystem-based
    parent existence validation and security validation for standalone tasks.

    Args:
        data: The object data dictionary
        project_root: The root directory of the project

    Raises:
        TrellisValidationError: If validation fails
    """
    from ..schema import get_model_class_for_kind

    errors = []

    # Get object kind (still need to check manually for error handling)
    kind_value = data.get("kind")
    if not kind_value:
        errors.append("Missing 'kind' field")
        raise TrellisValidationError(errors)

    try:
        object_kind = KindEnum(kind_value)
    except ValueError:
        errors.append(f"Invalid kind '{kind_value}'")
        raise TrellisValidationError(errors)

    # Security validation for standalone tasks
    if object_kind == KindEnum.TASK:
        security_errors = validate_standalone_task_security(data)
        errors.extend(security_errors)

    # Use Pydantic model validation for required fields, enum validation, and status validation
    try:
        model_class = get_model_class_for_kind(object_kind)

        # Filter data to only include fields that are defined in the model
        model_fields = set(model_class.model_fields.keys())
        filtered_data = {k: v for k, v in data.items() if k in model_fields}

        # Attempt validation using Pydantic model
        model_class.model_validate(filtered_data)

    except ValidationError as e:
        # Parse Pydantic validation errors to maintain backward compatibility
        missing_fields = []

        for error in e.errors():
            field = error.get("loc", [""])[0] if error.get("loc") else ""
            error_type = error.get("type", "")
            input_value = error.get("input")
            msg = error.get("msg", "")

            # Handle missing field errors
            if error_type == "missing":
                missing_fields.append(str(field))
            elif (
                error_type == "value_error"
                and "parent" in str(field)
                and "must have a parent" in msg
            ):
                # Handle parent validation errors as missing fields (for backward compatibility)
                missing_fields.append("parent")
            elif error_type == "enum" and input_value is None and str(field) in ["status"]:
                # Handle None values for required enum fields as missing fields
                missing_fields.append(str(field))
            elif error_type == "enum" and input_value is not None:
                # Handle enum validation errors with contextual messages
                if "kind" in str(field):
                    valid_kinds = [k.value for k in KindEnum]
                    errors.append(f"Invalid kind '{input_value}'. Must be one of: {valid_kinds}")
                elif "status" in str(field):
                    valid_statuses = [s.value for s in StatusEnum]
                    contextual_msg = generate_contextual_error_message(
                        "invalid_enum",
                        data,
                        field="status",
                        value=input_value,
                        valid_values=valid_statuses,
                    )
                    errors.append(contextual_msg)
                elif "priority" in str(field):
                    valid_priorities = [str(p) for p in Priority]
                    contextual_msg = generate_contextual_error_message(
                        "invalid_enum",
                        data,
                        field="priority",
                        value=input_value,
                        valid_values=valid_priorities,
                    )
                    errors.append(contextual_msg)
            elif error_type == "value_error":
                # Handle custom validator errors (like status-for-kind validation)
                clean_msg = msg
                if "StatusEnum." in clean_msg:
                    # Clean up the error message format to match original
                    clean_msg = clean_msg.replace("StatusEnum.OPEN", "open")
                    clean_msg = clean_msg.replace("StatusEnum.IN_PROGRESS", "in-progress")
                    clean_msg = clean_msg.replace("StatusEnum.REVIEW", "review")
                    clean_msg = clean_msg.replace("StatusEnum.DONE", "done")
                    clean_msg = clean_msg.replace("StatusEnum.DRAFT", "draft")
                    # Remove "Value error, " prefix
                    if clean_msg.startswith("Value error, "):
                        clean_msg = clean_msg[13:]

                # Apply contextual formatting to status validation errors
                contextual_msg = format_validation_error_with_context(clean_msg, data)
                errors.append(contextual_msg)
            else:
                # Handle other validation errors
                if field:
                    errors.append(f"Invalid {field}: {msg}")
                else:
                    errors.append(msg)

        # Add missing fields error if any fields are missing
        if missing_fields:
            contextual_msg = generate_contextual_error_message(
                "missing_fields", data, fields=missing_fields
            )
            errors.append(contextual_msg)

    except ValueError as e:
        # Handle invalid kind from get_model_class_for_kind
        # (shouldn't happen since we validated kind above)
        errors.append(str(e))

    # Validate parent existence (still requires filesystem access)
    # Skip parent validation for standalone tasks - they don't need parent references
    if "parent" in data:
        # Early return: skip parent validation for standalone tasks
        if object_kind == KindEnum.TASK and is_standalone_task(data):
            pass  # Standalone tasks don't require parent validation
        else:
            try:
                validate_parent_exists_for_object(data["parent"], object_kind, project_root)
            except ValueError as e:
                # Apply contextual formatting to parent validation errors
                contextual_msg = format_validation_error_with_context(str(e), data)
                errors.append(contextual_msg)

    # Raise exception if any errors were found
    if errors:
        raise TrellisValidationError(errors)
