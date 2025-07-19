"""Field validation functions for object data.

This module provides functions to validate individual fields and their
values in Trellis MCP objects.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any

from pydantic import ValidationError

from ..models.common import Priority
from ..schema.kind_enum import KindEnum
from ..schema.status_enum import StatusEnum

if TYPE_CHECKING:
    from .error_collector import ValidationErrorCollector


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


def validate_standalone_task_path_parameters(task_id: str, status: str | None = None) -> list[str]:
    """Validate input parameters for standalone task path operations.

    Validates task IDs and status parameters used in standalone task path resolution
    to prevent security vulnerabilities and ensure data integrity.

    Args:
        task_id: The task ID to validate (with or without T- prefix)
        status: The status parameter to validate (optional)

    Returns:
        List of validation errors (empty if valid)

    Example:
        >>> validate_standalone_task_path_parameters("valid-task-id", "open")
        []
        >>> validate_standalone_task_path_parameters("../../../etc/passwd", "open")
        ['Task ID contains invalid characters for filesystem paths']
        >>> validate_standalone_task_path_parameters("valid-task", "invalid-status")
        ['Invalid status parameter for directory resolution']
    """
    from ..id_utils import validate_id_charset

    errors = []

    # Validate task_id parameter
    if not task_id or not task_id.strip():
        errors.append("Task ID cannot be empty")
        return errors

    # Clean the task ID (remove T- prefix if present)
    clean_id = task_id.strip()
    if clean_id.startswith("T-"):
        clean_id = clean_id[2:]

    # Validate character set for task ID
    if not validate_id_charset(clean_id):
        errors.append("Task ID contains invalid characters for filesystem paths")

    # Validate length constraints (use more permissive check for compatibility)
    # Focus on preventing excessively long IDs that could cause security issues
    # rather than enforcing the strict 32-character limit for existing IDs
    if len(clean_id) > 255:  # Filesystem limit, not the 32-char preference
        errors.append("Task ID exceeds filesystem name limits (255 characters)")

    # Additional security validation for task IDs
    task_security_errors = _validate_task_id_security(clean_id)
    errors.extend(task_security_errors)

    # Validate status parameter if provided
    if status is not None:
        status_errors = _validate_status_parameter_security(status)
        errors.extend(status_errors)

    return errors


def _validate_task_id_security(task_id: str) -> list[str]:
    """Validate task ID for security vulnerabilities.

    Checks for path traversal attempts, injection attacks, and other security issues.

    Args:
        task_id: The clean task ID to validate

    Returns:
        List of security validation errors
    """
    errors = []

    # Check for path traversal attempts
    if ".." in task_id:
        errors.append("Task ID contains path traversal sequences")

    # Check for absolute path attempts
    if task_id.startswith("/") or task_id.startswith("\\"):
        errors.append("Task ID cannot start with path separators")

    # Check for control characters
    if any(ord(c) < 32 for c in task_id if c not in ["\t", "\n", "\r"]):
        errors.append("Task ID contains control characters")

    # Check for reserved names that could cause filesystem issues
    reserved_names = {
        "con",
        "prn",
        "aux",
        "nul",
        "com1",
        "com2",
        "com3",
        "com4",
        "com5",
        "com6",
        "com7",
        "com8",
        "com9",
        "lpt1",
        "lpt2",
        "lpt3",
        "lpt4",
        "lpt5",
        "lpt6",
        "lpt7",
        "lpt8",
        "lpt9",
    }

    if task_id.lower() in reserved_names:
        errors.append("Task ID uses reserved system name")

    # Check for excessively long components (filesystem limits)
    # This is handled by the main validation function, so skip here to avoid duplicates
    # if len(task_id) > 255:
    #     errors.append("Task ID exceeds filesystem name limits")

    return errors


def _validate_status_parameter_security(status: str) -> list[str]:
    """Validate status parameter for security vulnerabilities.

    Ensures status parameters can be safely used in directory names.

    Args:
        status: The status parameter to validate

    Returns:
        List of security validation errors
    """
    errors = []

    # Check for valid status values
    valid_statuses = {"open", "in-progress", "review", "done"}
    if status not in valid_statuses:
        errors.append("Invalid status parameter for directory resolution")

    # Check for path traversal attempts in status
    if ".." in status:
        errors.append("Status parameter contains path traversal sequences")

    # Check for path separators
    if "/" in status or "\\" in status:
        errors.append("Status parameter contains path separators")

    # Check for control characters
    if any(ord(c) < 32 for c in status if c not in ["\t", "\n", "\r"]):
        errors.append("Status parameter contains control characters")

    return errors


def validate_prerequisite_existence(
    prerequisites: list[str],
    project_root: str,
    collector: "ValidationErrorCollector",
) -> None:
    """Validate prerequisite IDs exist across hierarchical and standalone task systems.

    This function verifies all prerequisite IDs exist in the project by building
    an efficient ID mapping using get_all_objects() and checking each prerequisite
    against both hierarchical and standalone task systems.

    Args:
        prerequisites: List of prerequisite IDs to validate (with or without prefixes)
        project_root: Root directory for the planning structure
        collector: ValidationErrorCollector instance for error aggregation

    Example:
        >>> from .error_collector import ValidationErrorCollector
        >>> collector = ValidationErrorCollector()
        >>> prerequisites = ["task-1", "T-task-2"]
        >>> validate_prerequisite_existence(prerequisites, "./planning", collector)
        >>> collector.has_errors()
        False
    """
    from ..exceptions.validation_error import ValidationErrorCode
    from ..id_utils import clean_prerequisite_id
    from .object_loader import get_all_objects

    if not prerequisites:
        return

    # Performance optimization: build object ID mapping once
    try:
        all_objects = get_all_objects(project_root)
    except Exception as e:
        collector.add_error(
            f"Failed to load project objects for prerequisite validation: {str(e)}",
            ValidationErrorCode.PARENT_NOT_EXIST,
            context={"validation_type": "prerequisite_existence", "project_root": project_root},
        )
        return

    # Validate each prerequisite
    for prereq_id in prerequisites:
        if not prereq_id or not prereq_id.strip():
            collector.add_error(
                "Empty prerequisite ID found",
                ValidationErrorCode.PARENT_NOT_EXIST,
                context={"validation_type": "prerequisite_existence", "prerequisite_id": ""},
            )
            continue

        # Clean the prerequisite ID for consistent lookup
        clean_id = clean_prerequisite_id(prereq_id.strip())

        # Security validation for prerequisite ID
        security_errors = _validate_prerequisite_id_security(clean_id)
        for error_msg in security_errors:
            collector.add_error(
                f"Prerequisite ID security validation failed: {error_msg}",
                ValidationErrorCode.INVALID_FIELD,
                context={
                    "validation_type": "prerequisite_security",
                    "prerequisite_id": prereq_id[:50],  # Truncate for safety
                },
            )
            continue  # Skip existence check if security validation fails

        # Check if prerequisite exists in the cross-system object mapping
        if clean_id not in all_objects:
            collector.add_error(
                f"Prerequisite '{prereq_id}' does not exist in project. "
                f"Checked both hierarchical and standalone task systems.",
                ValidationErrorCode.PARENT_NOT_EXIST,
                context={
                    "validation_type": "prerequisite_existence",
                    "prerequisite_id": prereq_id,
                    "clean_id": clean_id,
                    "cross_system_check": True,
                },
            )


def _validate_prerequisite_id_security(prereq_id: str) -> list[str]:
    """Validate prerequisite ID for security vulnerabilities.

    Uses existing security validation patterns to ensure prerequisite IDs
    are safe for filesystem operations and don't contain malicious content.

    Args:
        prereq_id: The clean prerequisite ID to validate

    Returns:
        List of security validation errors
    """
    from ..id_utils import validate_id_charset

    errors = []

    # Use existing character set validation
    if not validate_id_charset(prereq_id):
        errors.append("contains invalid characters for filesystem paths")

    # Check for path traversal attempts
    if ".." in prereq_id:
        errors.append("contains path traversal sequences")

    # Check for absolute path attempts
    if prereq_id.startswith("/") or prereq_id.startswith("\\"):
        errors.append("cannot start with path separators")

    # Check for control characters
    if any(ord(c) < 32 for c in prereq_id if c not in ["\t", "\n", "\r"]):
        errors.append("contains control characters")

    # Check length constraints to prevent filesystem issues
    if len(prereq_id) > 255:
        errors.append("exceeds filesystem name limits (255 characters)")

    return errors
