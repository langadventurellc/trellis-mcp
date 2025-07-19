"""Default message templates for validation errors.

This module provides the default set of message templates for all
validation scenarios in the Trellis MCP system.
"""

from .core import MessageTemplate


def get_default_templates() -> dict[str, MessageTemplate]:
    """Get the default set of message templates.

    Returns:
        Dictionary of template keys to MessageTemplate instances
    """
    return {
        # Status validation templates
        "status.invalid": MessageTemplate(
            template="Invalid status '{value}' for {task_context}",
            category="status",
            description="Invalid status value for object type",
            required_params=["value", "task_context"],
        ),
        "status.invalid_with_options": MessageTemplate(
            template=(
                "Invalid status '{value}' for {task_context}. " "Must be one of: {valid_values}"
            ),
            category="status",
            description="Invalid status with list of valid options",
            required_params=["value", "task_context", "valid_values"],
        ),
        "status.transition_invalid": MessageTemplate(
            template=(
                "Invalid status transition for {object_kind}: '{old_status}' "
                "cannot transition to '{new_status}'"
            ),
            category="status",
            description="Invalid status transition",
            required_params=["object_kind", "old_status", "new_status"],
        ),
        "status.transition_invalid_with_options": MessageTemplate(
            template=(
                "Invalid status transition for {object_kind}: '{old_status}' "
                "cannot transition to '{new_status}'. Valid transitions: {valid_transitions}"
            ),
            category="status",
            description="Invalid status transition with valid options",
            required_params=["object_kind", "old_status", "new_status", "valid_transitions"],
        ),
        "status.terminal": MessageTemplate(
            template=(
                "Invalid status transition for {object_kind}: '{old_status}' is a terminal "
                "status with no valid transitions"
            ),
            category="status",
            description="Attempt to transition from terminal status",
            required_params=["object_kind", "old_status"],
        ),
        # Parent validation templates
        "parent.missing": MessageTemplate(
            template="Missing required fields for {task_context}: parent",
            category="parent",
            description="Missing required parent field",
            required_params=["task_context"],
        ),
        "parent.missing_with_note": MessageTemplate(
            template="Missing required fields for {task_context}: parent (Note: {note})",
            category="parent",
            description="Missing parent with explanatory note",
            required_params=["task_context", "note"],
        ),
        "parent.not_found": MessageTemplate(
            template="Parent {parent_kind} with ID '{parent_id}' does not exist",
            category="parent",
            description="Parent object not found",
            required_params=["parent_kind", "parent_id"],
        ),
        "parent.not_found_with_context": MessageTemplate(
            template=(
                "Parent {parent_kind} with ID '{parent_id}' does not exist "
                "({task_context} validation)"
            ),
            category="parent",
            description="Parent not found with task context",
            required_params=["parent_kind", "parent_id", "task_context"],
        ),
        "parent.not_allowed": MessageTemplate(
            template="{object_kind}s cannot have a parent",
            category="parent",
            description="Parent not allowed for object type",
            required_params=["object_kind"],
        ),
        "parent.required": MessageTemplate(
            template="{object_kind}s must have a parent {parent_kind} ID",
            category="parent",
            description="Parent required for object type",
            required_params=["object_kind", "parent_kind"],
        ),
        "parent.standalone_task_cannot_have": MessageTemplate(
            template=("Standalone task cannot have a parent (parent '{parent_id}' specified)"),
            category="parent",
            description="Standalone task with parent specified",
            required_params=["parent_id"],
        ),
        # Field validation templates
        "fields.missing": MessageTemplate(
            template="Missing required fields: {fields}",
            category="fields",
            description="Missing required fields",
            required_params=["fields"],
        ),
        "fields.missing_with_context": MessageTemplate(
            template="Missing required fields for {task_context}: {fields}",
            category="fields",
            description="Missing fields with task context",
            required_params=["task_context", "fields"],
        ),
        "fields.invalid_enum": MessageTemplate(
            template=(
                "Invalid {field} '{value}' for {task_context}. " "Must be one of: {valid_values}"
            ),
            category="fields",
            description="Invalid enum field value",
            required_params=["field", "value", "task_context", "valid_values"],
        ),
        "fields.invalid_type": MessageTemplate(
            template=(
                "Invalid {field} type for {task_context}: "
                "expected {expected_type}, got {actual_type}"
            ),
            category="fields",
            description="Invalid field type",
            required_params=["field", "task_context", "expected_type", "actual_type"],
        ),
        # Security validation templates
        "security.suspicious_pattern": MessageTemplate(
            template=(
                "Security validation failed: {field} field contains "
                "suspicious pattern '{pattern}'"
            ),
            category="security",
            description="Suspicious pattern detected in field",
            required_params=["field", "pattern"],
        ),
        "security.privileged_field": MessageTemplate(
            template=("Security validation failed: privileged field '{field}' is not allowed"),
            category="security",
            description="Privileged field not allowed",
            required_params=["field"],
        ),
        "security.whitespace_only": MessageTemplate(
            template=("Security validation failed: {field} field contains only whitespace"),
            category="security",
            description="Field contains only whitespace",
            required_params=["field"],
        ),
        "security.control_characters": MessageTemplate(
            template=("Security validation failed: {field} field contains control characters"),
            category="security",
            description="Field contains control characters",
            required_params=["field"],
        ),
        "security.max_length_exceeded": MessageTemplate(
            template=(
                "Security validation failed: {field} field exceeds maximum length "
                "({max_length} characters)"
            ),
            category="security",
            description="Field exceeds maximum length",
            required_params=["field", "max_length"],
        ),
        # Hierarchy validation templates
        "hierarchy.circular_dependency": MessageTemplate(
            template="Circular dependency detected: {cycle_path}",
            category="hierarchy",
            description="Circular dependency in prerequisites",
            required_params=["cycle_path"],
        ),
        "hierarchy.invalid_level": MessageTemplate(
            template=("Invalid hierarchy level: {object_kind} cannot be child of {parent_kind}"),
            category="hierarchy",
            description="Invalid hierarchy relationship",
            required_params=["object_kind", "parent_kind"],
        ),
        # Schema validation templates
        "schema.version_mismatch": MessageTemplate(
            template=(
                "Schema version mismatch: {object_kind} requires schema version "
                "{required_version}, got {actual_version}"
            ),
            category="schema",
            description="Schema version mismatch",
            required_params=["object_kind", "required_version", "actual_version"],
        ),
        "schema.version_constraint": MessageTemplate(
            template="{constraint_description} in schema version {schema_version}",
            category="schema",
            description="Schema version constraint violation",
            required_params=["constraint_description", "schema_version"],
        ),
        # Generic validation templates
        "generic.validation_error": MessageTemplate(
            template="Validation error for {task_context}",
            category="generic",
            description="Generic validation error",
            required_params=["task_context"],
        ),
        "generic.validation_failed": MessageTemplate(
            template="Validation failed: {error_message}",
            category="generic",
            description="Generic validation failure",
            required_params=["error_message"],
        ),
        # Prerequisite validation templates
        "prerequisites.not_found": MessageTemplate(
            template=(
                "Prerequisite {prerequisite_kind} with ID '{prerequisite_id}' does not exist"
            ),
            category="prerequisites",
            description="Prerequisite object not found",
            required_params=["prerequisite_kind", "prerequisite_id"],
        ),
        "prerequisites.incomplete": MessageTemplate(
            template=(
                "Prerequisite {prerequisite_id} is not complete " "(status: {prerequisite_status})"
            ),
            category="prerequisites",
            description="Prerequisite not complete",
            required_params=["prerequisite_id", "prerequisite_status"],
        ),
        # File system validation templates
        "filesystem.not_found": MessageTemplate(
            template="{object_kind} file not found: {file_path}",
            category="filesystem",
            description="Object file not found",
            required_params=["object_kind", "file_path"],
        ),
        "filesystem.access_denied": MessageTemplate(
            template="Access denied to {object_kind} file: {file_path}",
            category="filesystem",
            description="File access denied",
            required_params=["object_kind", "file_path"],
        ),
        # Cross-system validation templates
        "cross_system.reference_conflict": MessageTemplate(
            template=(
                "Cannot reference {target_task_type} task '{target_task_id}' from "
                "{source_task_type} task '{source_task_id}'"
            ),
            category="cross_system",
            description="Cross-system task reference conflict",
            required_params=[
                "source_task_type",
                "target_task_type",
                "source_task_id",
                "target_task_id",
            ],
        ),
        "cross_system.prerequisite_invalid": MessageTemplate(
            template=(
                "Prerequisite validation failed: {source_task_type} task '{source_task_id}' "
                "requires {target_task_type} task '{target_task_id}' which does not exist"
            ),
            category="cross_system",
            description="Cross-system prerequisite validation failure",
            required_params=[
                "source_task_type",
                "target_task_type",
                "source_task_id",
                "target_task_id",
            ],
        ),
        "cross_system.hierarchy_to_standalone": MessageTemplate(
            template=(
                "Cannot reference standalone task '{target_task_id}' from "
                "hierarchical task '{source_task_id}'"
            ),
            category="cross_system",
            description="Hierarchical task referencing standalone task",
            required_params=["source_task_id", "target_task_id"],
        ),
        "cross_system.standalone_to_hierarchy": MessageTemplate(
            template=(
                "Cannot reference hierarchical task '{target_task_id}' from "
                "standalone task '{source_task_id}'"
            ),
            category="cross_system",
            description="Standalone task referencing hierarchical task",
            required_params=["source_task_id", "target_task_id"],
        ),
        "cross_system.prerequisite_context": MessageTemplate(
            template=(
                "Prerequisite validation failed: {source_task_context} requires "
                "{target_task_context} '{target_task_id}' which does not exist"
            ),
            category="cross_system",
            description="Cross-system prerequisite with task context",
            required_params=["source_task_context", "target_task_context", "target_task_id"],
        ),
    }
