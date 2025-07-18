"""Context utilities for validation error messages.

This module provides utility functions for generating contextual error
messages based on task type and object context.
"""

from typing import Any

from .task_utils import is_hierarchy_task, is_standalone_task


def get_task_type_context(data: dict[str, Any]) -> str:
    """Get task type context for error messages.

    Args:
        data: The object data dictionary

    Returns:
        String describing the task type context, empty string if not a task
    """
    if data.get("kind") != "task":
        return ""

    if is_standalone_task(data):
        return "standalone task"
    elif is_hierarchy_task(data):
        return "hierarchy task"
    else:
        return "task"


def format_validation_error_with_context(error_message: str, data: dict[str, Any]) -> str:
    """Format validation error message with task type context.

    Args:
        error_message: The base error message
        data: The object data dictionary

    Returns:
        Enhanced error message with context
    """
    task_context = get_task_type_context(data)

    if not task_context:
        return error_message

    # Add context to specific error patterns
    if "Invalid status" in error_message and "for task" in error_message:
        return error_message.replace("for task", f"for {task_context}")
    elif "does not exist" in error_message and "task" in data.get("kind", ""):
        return f"{error_message} ({task_context} validation)"
    elif "must have a parent" in error_message and task_context == "standalone task":
        return f"{error_message} (Note: standalone tasks don't require parent)"

    return error_message


def generate_contextual_error_message(error_type: str, data: dict[str, Any], **kwargs) -> str:
    """Generate contextual error messages based on task type.

    This function provides backward compatibility while integrating with
    the new template system. New code should use the template system directly.

    Args:
        error_type: Type of error (e.g., 'invalid_status', 'missing_parent')
        data: The object data dictionary
        **kwargs: Additional context for error message

    Returns:
        Contextual error message string
    """
    # Try to use template system first
    try:
        from .message_templates import generate_template_message

        # Map error types to template keys
        template_mapping = {
            "invalid_status": (
                "status.invalid_with_options" if "valid_values" in kwargs else "status.invalid"
            ),
            "missing_parent": (
                "parent.missing_with_note"
                if get_task_type_context(data) == "standalone task"
                else "parent.missing"
            ),
            "parent_not_exist": (
                "parent.not_found_with_context"
                if get_task_type_context(data)
                else "parent.not_found"
            ),
            "missing_fields": "fields.missing_with_context",
            "invalid_enum": "fields.invalid_enum",
        }

        template_key = template_mapping.get(error_type)
        if template_key:
            # Prepare parameters for template
            params = kwargs.copy()

            # Handle special parameter mappings
            if error_type == "invalid_status":
                params["value"] = kwargs.get("status", "unknown")
            elif error_type == "missing_parent":
                if get_task_type_context(data) == "standalone task":
                    params["note"] = "standalone tasks don't require parent"
            elif error_type == "parent_not_exist":
                params["parent_kind"] = kwargs.get("parent_kind", "parent")
                params["parent_id"] = kwargs.get("parent_id", "unknown")
            elif error_type == "missing_fields":
                params["fields"] = kwargs.get("fields", [])
            elif error_type == "invalid_enum":
                params["field"] = kwargs.get("field", "field")
                params["value"] = kwargs.get("value", "unknown")
                params["valid_values"] = kwargs.get("valid_values", [])

            return generate_template_message(template_key, data, **params)

    except (ImportError, KeyError):
        # Fall back to original implementation if template system fails
        pass

    # Original implementation as fallback
    task_context = get_task_type_context(data)
    object_kind = data.get("kind", "object")

    if error_type == "invalid_status":
        status = kwargs.get("status", "unknown")
        if task_context:
            return f"Invalid status '{status}' for {task_context}"
        else:
            return f"Invalid status '{status}' for {object_kind}"

    elif error_type == "missing_parent":
        if task_context == "standalone task":
            return (
                f"Missing required fields for {task_context}: parent "
                "(Note: standalone tasks don't require parent)"
            )
        elif task_context == "hierarchy task":
            return f"Missing required fields for {task_context}: parent"
        else:
            return f"{object_kind} objects must have a parent"

    elif error_type == "parent_not_exist":
        parent_kind = kwargs.get("parent_kind", "parent")
        parent_id = kwargs.get("parent_id", "unknown")
        if task_context:
            return (
                f"Parent {parent_kind} with ID '{parent_id}' does not exist "
                f"({task_context} validation)"
            )
        else:
            return f"Parent {parent_kind} with ID '{parent_id}' does not exist"

    elif error_type == "missing_fields":
        fields = kwargs.get("fields", [])
        if task_context == "standalone task":
            return f"Missing required fields for {task_context}: {', '.join(fields)}"
        elif task_context == "hierarchy task":
            return f"Missing required fields for {task_context}: {', '.join(fields)}"
        else:
            return f"Missing required fields: {', '.join(fields)}"

    elif error_type == "invalid_enum":
        field = kwargs.get("field", "field")
        value = kwargs.get("value", "unknown")
        valid_values = kwargs.get("valid_values", [])
        if task_context:
            return f"Invalid {field} '{value}' for {task_context}. Must be one of: {valid_values}"
        else:
            return f"Invalid {field} '{value}' for {object_kind}. Must be one of: {valid_values}"

    # Default fallback
    return f"Validation error for {task_context or object_kind}"
