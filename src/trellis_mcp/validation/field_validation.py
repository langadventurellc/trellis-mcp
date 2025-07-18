"""Field validation functions for object data.

This module provides functions to validate individual fields and their
values in Trellis MCP objects.
"""

from datetime import datetime
from typing import Any

from pydantic import ValidationError

from ..models.common import Priority
from ..schema.kind_enum import KindEnum
from ..schema.status_enum import StatusEnum


def validate_required_fields_per_kind(data: dict[str, Any], object_kind: KindEnum) -> list[str]:
    """Validate that all required fields are present for a specific object kind.

    This function now uses Pydantic schema model validation to detect missing fields
    instead of manual validation logic.

    Args:
        data: The object data dictionary
        object_kind: The kind of object being validated

    Returns:
        List of missing required fields (empty if all fields are present)
    """
    from ..schema import get_model_class_for_kind

    try:
        # Get the appropriate Pydantic model class for this kind
        model_class = get_model_class_for_kind(object_kind)

        # Filter data to only include fields that are defined in the model
        model_fields = set(model_class.model_fields.keys())
        filtered_data = {k: v for k, v in data.items() if k in model_fields}

        # Attempt validation to detect missing fields
        model_class.model_validate(filtered_data)

        # If validation succeeds, check for fields that have defaults but should be
        # considered missing (for backward compatibility)
        missing_fields = []
        required_fields_with_defaults = {"schema_version"}
        for field in required_fields_with_defaults:
            if field not in data or data[field] is None:
                missing_fields.append(field)

        return missing_fields

    except ValidationError as e:
        # Extract missing field names from Pydantic validation errors
        missing_fields = []

        for error in e.errors():
            field = error.get("loc", [""])[0] if error.get("loc") else ""
            error_type = error.get("type", "")
            input_value = error.get("input")

            # Check for missing field errors
            if error_type == "missing":
                missing_fields.append(str(field))
            elif (
                error_type == "value_error"
                and "parent" in str(field)
                and "must have a parent" in error.get("msg", "")
            ):
                # Handle parent validation errors as missing fields (for backward compatibility)
                missing_fields.append("parent")
            elif error_type == "enum" and input_value is None and str(field) in ["status"]:
                # Handle None values for required enum fields as missing fields
                missing_fields.append(str(field))

        # Also check for fields that have defaults in Pydantic but were considered
        # required in original logic (for backward compatibility)
        required_fields_with_defaults = {"schema_version"}
        for field in required_fields_with_defaults:
            if field not in data or data[field] is None:
                missing_fields.append(field)

        return missing_fields

    except ValueError:
        # Handle invalid kind from get_model_class_for_kind
        # In this case, we can't validate so return empty list
        # (kind validation is handled elsewhere)
        return []


def validate_enum_membership(data: dict[str, Any]) -> list[str]:
    """Validate that enum fields have valid values.

    This function now uses Pydantic schema model validation to detect invalid enum values
    instead of manual validation logic. Note that this function requires a 'kind' field
    to determine which model to use for validation.

    Args:
        data: The object data dictionary

    Returns:
        List of validation errors (empty if all enums are valid)
    """
    from ..schema import get_model_class_for_kind

    # If no kind field, we can't determine which model to use, so fall back to manual validation
    if "kind" not in data:
        return _validate_enum_membership_manual(data)

    try:
        # Get the appropriate Pydantic model class for this kind
        kind_value = data["kind"]
        model_class = get_model_class_for_kind(kind_value)

        # Filter data to only include fields that are defined in the model
        model_fields = set(model_class.model_fields.keys())
        filtered_data = {k: v for k, v in data.items() if k in model_fields}

        # Attempt validation to detect enum errors
        model_class.model_validate(filtered_data)

        # If validation succeeds, no enum errors
        return []

    except ValidationError as e:
        # Extract enum validation errors from Pydantic validation errors
        errors = []

        for error in e.errors():
            field = error.get("loc", [""])[0] if error.get("loc") else ""
            error_type = error.get("type", "")
            input_value = error.get("input")

            # Check for enum validation errors (but skip missing field errors)
            if error_type == "enum" and input_value is not None:
                if "kind" in str(field):
                    valid_kinds = [k.value for k in KindEnum]
                    errors.append(f"Invalid kind '{input_value}'. Must be one of: {valid_kinds}")
                elif "status" in str(field):
                    valid_statuses = [s.value for s in StatusEnum]
                    errors.append(
                        f"Invalid status '{input_value}'. Must be one of: {valid_statuses}"
                    )
                elif "priority" in str(field):
                    valid_priorities = [str(p) for p in Priority]
                    errors.append(
                        f"Invalid priority '{input_value}'. Must be one of: {valid_priorities}"
                    )

        return errors

    except ValueError:
        # Handle invalid kind - fall back to manual validation
        return _validate_enum_membership_manual(data)


def _validate_enum_membership_manual(data: dict[str, Any]) -> list[str]:
    """Manual enum validation fallback when Pydantic validation cannot be used."""
    errors = []

    # Validate kind enum
    if "kind" in data:
        try:
            KindEnum(data["kind"])
        except ValueError:
            valid_kinds = [k.value for k in KindEnum]
            errors.append(f"Invalid kind '{data['kind']}'. Must be one of: {valid_kinds}")

    # Validate status enum
    if "status" in data:
        try:
            StatusEnum(data["status"])
        except ValueError:
            valid_statuses = [s.value for s in StatusEnum]
            errors.append(f"Invalid status '{data['status']}'. Must be one of: {valid_statuses}")

    # Validate priority enum
    if "priority" in data:
        try:
            Priority(data["priority"])
        except ValueError:
            valid_priorities = [str(p) for p in Priority]
            errors.append(
                f"Invalid priority '{data['priority']}'. Must be one of: {valid_priorities}"
            )

    return errors


def validate_priority_field(data: dict[str, Any]) -> list[str]:
    """Validate priority field and set default value if missing.

    This function explicitly validates the priority field in YAML data and
    ensures that the default value 'normal' is set if the field is missing.

    Args:
        data: The object data dictionary (will be modified in-place)

    Returns:
        List of validation errors (empty if valid)
    """
    errors = []

    # Set default priority if missing
    if "priority" not in data or data["priority"] is None:
        data["priority"] = str(Priority.NORMAL)

    # Validate priority field value
    priority_value = data["priority"]
    try:
        Priority(priority_value)
    except ValueError:
        valid_priorities = [str(p) for p in Priority]
        errors.append(f"Invalid priority '{priority_value}'. Must be one of: {valid_priorities}")

    return errors


def validate_status_for_kind(status: StatusEnum, object_kind: KindEnum) -> bool:
    """Validate that the status is allowed for the specific object kind.

    This function now uses Pydantic schema model validation to check status validity
    instead of hardcoded status sets.

    Args:
        status: The status to validate
        object_kind: The kind of object

    Returns:
        True if status is valid for the kind, False otherwise

    Raises:
        ValueError: If status is invalid for the kind
    """
    from ..schema import get_model_class_for_kind

    try:
        # Get the appropriate Pydantic model class for this kind
        model_class = get_model_class_for_kind(object_kind)

        # Create minimal validation data with all required fields
        validation_data = {
            "kind": object_kind.value,
            "status": status.value,
            "id": "temp-id",
            "title": "temp-title",
            "created": datetime.now(),
            "updated": datetime.now(),
            "schema_version": "1.1",
        }

        # Add parent field for kinds that require it
        if object_kind in [KindEnum.EPIC, KindEnum.FEATURE, KindEnum.TASK]:
            validation_data["parent"] = "temp-parent"

        # Attempt validation - if successful, status is valid
        model_class.model_validate(validation_data)
        return True

    except ValidationError as e:
        # Check if any error is specifically about status validation
        for error in e.errors():
            field = error.get("loc", [""])[0] if error.get("loc") else ""
            msg = error.get("msg", "")

            # If we find a status validation error, re-raise it with proper formatting
            if str(field) == "status" and "Invalid status" in msg:
                # Clean up the error message to match original format
                clean_msg = msg
                if "Value error, " in clean_msg:
                    clean_msg = clean_msg.replace("Value error, ", "")
                # Replace StatusEnum.VALUE with 'value' to match original format
                clean_msg = clean_msg.replace("'StatusEnum.DRAFT'", "'draft'")
                clean_msg = clean_msg.replace("'StatusEnum.OPEN'", "'open'")
                clean_msg = clean_msg.replace("'StatusEnum.IN_PROGRESS'", "'in-progress'")
                clean_msg = clean_msg.replace("'StatusEnum.REVIEW'", "'review'")
                clean_msg = clean_msg.replace("'StatusEnum.DONE'", "'done'")
                raise ValueError(clean_msg)

        # If no status validation errors, the status is valid (other errors are about other fields)
        return True

    except ValueError as e:
        # Handle invalid kind from get_model_class_for_kind or re-raised status validation errors
        raise e


def validate_front_matter(yaml_dict: dict[str, Any], kind: str | KindEnum) -> list[str]:
    """Validate front matter for required fields and enum values.

    This function validates YAML front matter using Pydantic schema models.
    It focuses on field presence and enum validation, not parent existence.

    Args:
        yaml_dict: Dictionary containing the parsed YAML front matter
        kind: The object kind (string or KindEnum)

    Returns:
        List of validation error messages (empty if valid)
    """
    from ..schema import get_model_class_for_kind

    # Validate priority field and set default value if missing
    priority_errors = validate_priority_field(yaml_dict)

    try:
        # Get the appropriate model class for this kind
        model_class = get_model_class_for_kind(kind)

        # Attempt to validate using Pydantic (filtering to only model fields)
        # Get the model's field names
        model_fields = set(model_class.model_fields.keys())

        # Filter yaml_dict to only include fields that are defined in the model
        filtered_dict = {k: v for k, v in yaml_dict.items() if k in model_fields}
        model_class.model_validate(filtered_dict)

        # If validation succeeds, return only priority errors (if any)
        return priority_errors

    except ValidationError as e:
        # Convert Pydantic validation errors to string list
        errors = []
        missing_fields = []

        for error in e.errors():
            field = error.get("loc", [""])[0] if error.get("loc") else ""
            error_type = error.get("type", "")
            input_value = error.get("input")
            msg = error.get("msg", "")

            # Format error messages to match existing format
            if error_type == "missing":
                # Collect missing fields to group them
                missing_fields.append(str(field))
            elif error_type == "enum":
                # Handle enum validation errors
                # Special case: None values for required enums should be treated as missing fields
                if input_value is None and str(field) in ["status"]:
                    missing_fields.append(str(field))
                elif "kind" in str(field):
                    valid_kinds = [k.value for k in KindEnum]
                    errors.append(f"Invalid kind '{input_value}'. Must be one of: {valid_kinds}")
                elif "status" in str(field):
                    valid_statuses = [s.value for s in StatusEnum]
                    errors.append(
                        f"Invalid status '{input_value}'. Must be one of: {valid_statuses}"
                    )
                elif "priority" in str(field):
                    # Skip priority errors if they were already handled by explicit validation
                    if not priority_errors:
                        valid_priorities = [str(p) for p in Priority]
                        errors.append(
                            f"Invalid priority '{input_value}'. Must be one of: {valid_priorities}"
                        )
                else:
                    errors.append(msg)
            elif error_type == "value_error":
                # Handle custom validator errors
                if "parent" in str(field) and ("must have a parent" in msg):
                    # Treat parent validation errors as missing required fields
                    # to match original behavior
                    missing_fields.append("parent")
                else:
                    # Other value errors (like status-for-kind validation)
                    # Clean up the error message format to match original
                    clean_msg = msg
                    if "StatusEnum." in clean_msg:
                        # Replace StatusEnum.VALUE with just VALUE
                        # (without quotes since they're already in the message)
                        clean_msg = clean_msg.replace("StatusEnum.OPEN", "open")
                        clean_msg = clean_msg.replace("StatusEnum.IN_PROGRESS", "in-progress")
                        clean_msg = clean_msg.replace("StatusEnum.REVIEW", "review")
                        clean_msg = clean_msg.replace("StatusEnum.DONE", "done")
                        clean_msg = clean_msg.replace("StatusEnum.DRAFT", "draft")
                        # Remove "Value error, " prefix
                        if clean_msg.startswith("Value error, "):
                            clean_msg = clean_msg[13:]
                    errors.append(clean_msg)
            else:
                # Handle other validation errors
                if field:
                    errors.append(f"Invalid {field}: {msg}")
                else:
                    errors.append(msg)

        # Add missing fields error if any fields are missing
        if missing_fields:
            errors.insert(0, f"Missing required fields: {', '.join(missing_fields)}")

        # Combine priority validation errors with Pydantic validation errors
        all_errors = priority_errors + errors
        return all_errors

    except ValueError as e:
        # Handle invalid kind from get_model_class_for_kind
        return [str(e)]
