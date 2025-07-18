"""Enhanced validation functions using ValidationErrorCollector.

This module demonstrates how to use the ValidationErrorCollector
with the existing validation system for better error aggregation.
"""

from pathlib import Path
from typing import Any

from pydantic import ValidationError

from ..exceptions.validation_error import ValidationErrorCode
from ..models.common import Priority
from ..schema.kind_enum import KindEnum
from ..schema.status_enum import StatusEnum
from .context_utils import format_validation_error_with_context, generate_contextual_error_message
from .error_collector import ValidationErrorCollector
from .parent_validation import validate_parent_exists_for_object
from .security import validate_standalone_task_security
from .task_utils import is_hierarchy_task, is_standalone_task


def validate_object_data_with_collector(
    data: dict[str, Any], project_root: str | Path
) -> ValidationErrorCollector:
    """Enhanced object validation using ValidationErrorCollector.

    This function performs the same validation as validate_object_data
    but collects all errors using ValidationErrorCollector before
    raising an exception, enabling better error prioritization and
    presentation.

    Args:
        data: The object data dictionary
        project_root: The root directory of the project

    Returns:
        ValidationErrorCollector with all validation errors

    Raises:
        ValidationError: If validation fails (with prioritized errors)
    """
    from ..schema import get_model_class_for_kind

    # Initialize error collector with object context
    object_id = data.get("id", "unknown")
    kind_value = data.get("kind")

    collector = ValidationErrorCollector(object_id=object_id, object_kind=kind_value)

    # Validate kind first (required for other validations)
    if not kind_value:
        collector.add_error(
            "Missing 'kind' field",
            ValidationErrorCode.MISSING_REQUIRED_FIELD,
            context={"field": "kind"},
        )
        # Return collector early if no kind - can't continue validation
        return collector

    try:
        object_kind = KindEnum(kind_value)
    except ValueError:
        collector.add_error(
            f"Invalid kind '{kind_value}'",
            ValidationErrorCode.INVALID_ENUM_VALUE,
            context={
                "field": "kind",
                "value": kind_value,
                "valid_values": [k.value for k in KindEnum],
            },
        )
        # Return collector early if invalid kind - can't continue validation
        return collector

    # Security validation for standalone tasks
    if object_kind == KindEnum.TASK:
        security_errors = validate_standalone_task_security(data)
        for error_msg in security_errors:
            collector.add_error(
                error_msg,
                ValidationErrorCode.INVALID_FIELD,  # Security errors as field validation issues
                context={"security_check": True},
            )

    # Use Pydantic model validation for comprehensive field validation
    try:
        model_class = get_model_class_for_kind(object_kind)

        # Filter data to only include fields that are defined in the model
        model_fields = set(model_class.model_fields.keys())
        filtered_data = {k: v for k, v in data.items() if k in model_fields}

        # Attempt validation using Pydantic model
        model_class.model_validate(filtered_data)

    except ValidationError as e:
        # Parse Pydantic validation errors and add to collector
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
                # Handle parent validation errors as missing fields
                missing_fields.append("parent")
            elif error_type == "enum" and input_value is None and str(field) in ["status"]:
                # Handle None values for required enum fields as missing fields
                missing_fields.append(str(field))
            elif error_type == "enum" and input_value is not None:
                # Handle enum validation errors with proper error codes
                if "kind" in str(field):
                    valid_kinds = [k.value for k in KindEnum]
                    collector.add_error(
                        f"Invalid kind '{input_value}'. Must be one of: {valid_kinds}",
                        ValidationErrorCode.INVALID_ENUM_VALUE,
                        context={
                            "field": "kind",
                            "value": input_value,
                            "valid_values": valid_kinds,
                        },
                    )
                elif "status" in str(field):
                    valid_statuses = [s.value for s in StatusEnum]
                    contextual_msg = generate_contextual_error_message(
                        "invalid_enum",
                        data,
                        field="status",
                        value=input_value,
                        valid_values=valid_statuses,
                    )
                    collector.add_error(
                        contextual_msg,
                        ValidationErrorCode.INVALID_ENUM_VALUE,
                        context={
                            "field": "status",
                            "value": input_value,
                            "valid_values": valid_statuses,
                        },
                    )
                elif "priority" in str(field):
                    valid_priorities = [str(p) for p in Priority]
                    contextual_msg = generate_contextual_error_message(
                        "invalid_enum",
                        data,
                        field="priority",
                        value=input_value,
                        valid_values=valid_priorities,
                    )
                    collector.add_error(
                        contextual_msg,
                        ValidationErrorCode.INVALID_ENUM_VALUE,
                        context={
                            "field": "priority",
                            "value": input_value,
                            "valid_values": valid_priorities,
                        },
                    )
            elif error_type == "value_error":
                # Handle custom validator errors (like status-for-kind validation)
                clean_msg = msg
                if "StatusEnum." in clean_msg:
                    # Clean up the error message format
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
                collector.add_error(
                    contextual_msg,
                    ValidationErrorCode.INVALID_STATUS,
                    context={"field": "status", "validation_type": "status_for_kind"},
                )
            else:
                # Handle other validation errors
                error_msg = f"Invalid {field}: {msg}" if field else msg
                collector.add_error(
                    error_msg,
                    ValidationErrorCode.INVALID_FIELD,
                    context={"field": str(field), "error_type": error_type},
                )

        # Add missing fields error if any fields are missing
        if missing_fields:
            contextual_msg = generate_contextual_error_message(
                "missing_fields", data, fields=missing_fields
            )
            collector.add_error(
                contextual_msg,
                ValidationErrorCode.MISSING_REQUIRED_FIELD,
                context={"fields": missing_fields},
            )

    except ValueError as e:
        # Handle invalid kind from get_model_class_for_kind
        collector.add_error(
            str(e), ValidationErrorCode.INVALID_ENUM_VALUE, context={"schema_error": True}
        )

    # Validate parent existence (filesystem-based validation)
    # Skip parent validation for standalone tasks
    if "parent" in data:
        if object_kind == KindEnum.TASK and is_standalone_task(data):
            pass  # Standalone tasks don't require parent validation
        else:
            try:
                validate_parent_exists_for_object(data["parent"], object_kind, project_root)
            except ValueError as e:
                # Apply contextual formatting to parent validation errors
                contextual_msg = format_validation_error_with_context(str(e), data)
                collector.add_error(
                    contextual_msg,
                    ValidationErrorCode.PARENT_NOT_EXIST,
                    context={"parent_id": data["parent"], "parent_validation": True},
                )

    # Validate prerequisite existence across both hierarchical and standalone task systems
    # Only validate prerequisites for tasks (other object types don't use prerequisites in practice)
    if "prerequisites" in data and data["prerequisites"] and object_kind == KindEnum.TASK:
        from .field_validation import validate_prerequisite_existence

        validate_prerequisite_existence(data["prerequisites"], str(project_root), collector)

    return collector


def validate_object_data_enhanced(data: dict[str, Any], project_root: str | Path) -> None:
    """Enhanced validation function that uses ValidationErrorCollector.

    This function is a drop-in replacement for validate_object_data
    that uses ValidationErrorCollector for better error aggregation.

    Args:
        data: The object data dictionary
        project_root: The root directory of the project

    Raises:
        ValidationError: If validation fails (with prioritized errors)
    """
    collector = validate_object_data_with_collector(data, project_root)

    if collector.has_errors():
        # Create a proper ValidationError with prioritization
        task_type = (
            "standalone" if data.get("kind") == "task" and is_standalone_task(data) else "hierarchy"
        )
        raise collector.create_validation_error(task_type=task_type)


def validate_task_with_enhanced_errors(data: dict[str, Any], project_root: str | Path) -> None:
    """Enhanced validation for tasks using specific task type validation.

    This function determines the task type and delegates to the appropriate
    specialized validation function for better error handling and context.

    Args:
        data: The task data dictionary
        project_root: The root directory of the project

    Raises:
        ValueError: If the data is not a task
        StandaloneTaskValidationError: If standalone task validation fails
        HierarchyTaskValidationError: If hierarchy task validation fails
    """
    from .task_utils import (
        validate_hierarchy_task_with_enhanced_errors,
        validate_standalone_task_with_enhanced_errors,
    )

    # Validate that this is a task
    if data.get("kind") != "task":
        raise ValueError("validate_task_with_enhanced_errors can only be used with tasks")

    # Determine task type and delegate to appropriate validation
    if is_standalone_task(data):
        validate_standalone_task_with_enhanced_errors(data, project_root)
    elif is_hierarchy_task(data):
        validate_hierarchy_task_with_enhanced_errors(data, project_root)
    else:
        # Fallback for edge cases - use general enhanced validation
        validate_object_data_enhanced(data, project_root)
