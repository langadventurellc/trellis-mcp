"""Update object tool for Trellis MCP server.

Updates existing Trellis MCP objects by applying patches to YAML front-matter and/or
body content. Handles cascade deletion, status transitions, and protected object validation.
"""

from datetime import datetime
from typing import Annotated, Any

from fastmcp import FastMCP
from pydantic import Field

from ..exceptions.cascade_error import CascadeError
from ..exceptions.protected_object_error import ProtectedObjectError
from ..exceptions.validation_error import ValidationError, ValidationErrorCode
from ..fs_utils import recursive_delete
from ..graph_utils import DependencyGraph
from ..inference import KindInferenceEngine
from ..io_utils import read_markdown, write_markdown
from ..path_resolver import children_of, id_to_path, resolve_project_roots
from ..settings import Settings
from ..validation import (
    TrellisValidationError,
    enforce_status_transition,
    validate_front_matter,
    validate_object_data,
)


def _deep_merge_dict(base: dict[str, Any], patch: dict[str, Any]) -> dict[str, Any]:
    """Deep merge two dictionaries, recursively merging nested dictionaries.

    This function performs a deep merge of two dictionaries, where nested dictionaries
    are merged recursively rather than replaced. This is essential for YAML patch
    operations to avoid losing nested fields.

    Args:
        base: The base dictionary to merge into
        patch: The patch dictionary containing updates

    Returns:
        A new dictionary with patch values merged into base

    Example:
        >>> base = {'meta': {'author': 'A'}, 'title': 'Old'}
        >>> patch = {'meta': {'reviewer': 'B'}, 'status': 'new'}
        >>> _deep_merge_dict(base, patch)
        {'meta': {'author': 'A', 'reviewer': 'B'}, 'title': 'Old', 'status': 'new'}
    """
    result = base.copy()

    for key, value in patch.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            # Recursively merge nested dictionaries
            result[key] = _deep_merge_dict(result[key], value)
        else:
            # Replace or add the value
            result[key] = value

    return result


def create_update_object_tool(settings: Settings):
    """Create an updateObject tool configured with the provided settings.

    Args:
        settings: Server configuration settings

    Returns:
        Configured updateObject tool function
    """
    mcp = FastMCP()

    @mcp.tool
    def updateObject(
        id: Annotated[
            str,
            Field(
                description="Object ID (P-, E-, F-, T- prefixed)",
                pattern=r"^(P-|E-|F-|T-).+",
                min_length=3,
            ),
        ],
        projectRoot: Annotated[
            str, Field(description="Root directory for planning structure", min_length=1)
        ],
        yamlPatch: Annotated[
            dict[str, str | list[str] | None],
            Field(
                description="YAML fields to update/merge",
                default={},
            ),
        ] = {},
        bodyPatch: Annotated[
            str,
            Field(
                description="New body content to replace existing body",
                default="",
            ),
        ] = "",
        force: Annotated[
            bool,
            Field(
                description="Bypass safeguards when deleting objects with protected children",
                default=False,
            ),
        ] = False,
    ) -> dict[str, str | dict[str, str | list[str] | bool]]:
        """Update a Trellis MCP object by applying patches to YAML front-matter and/or body content.

        Applies JSON merge patch-style updates to an existing object. The yamlPatch parameter
        allows updating individual YAML front-matter fields, while bodyPatch replaces the
        entire body content. The operation is atomic - either all changes succeed or none
        are applied.

        Supports cross-system prerequisite modifications, enabling updates to prerequisite
        lists that span both hierarchical and standalone task systems. All prerequisite
        changes are validated for existence across both systems and checked for circular
        dependencies to maintain graph integrity.

        Args:
            id: Object ID (with or without prefix)
            projectRoot: Root directory for the planning structure
            yamlPatch: Optional dictionary of YAML fields to update/merge. When updating
                prerequisites, supports cross-system references including hierarchical
                objects and standalone tasks. Example:
                {"prerequisites": ["T-auth-setup", "task-standalone-db", "F-validation"]}
                All prerequisite IDs are automatically cleaned and validated across both
                task systems before applying changes.
            bodyPatch: Optional new body content to replace existing body
            force: If True, bypass safeguards when deleting objects with protected children

        Returns:
            Dictionary containing the updated object information with structure:
            {
                "id": str,           # Clean object ID
                "kind": str,         # Object kind (automatically inferred)
                "updated": str,      # ISO timestamp of update
                "changes": dict      # Summary of changes made
            }

        Raises:
            ValidationError: If ID is invalid, inference fails, or validation fails
            FileNotFoundError: If object with the given ID cannot be found
            TrellisValidationError: If validation fails (front-matter, status transitions,
                or acyclic prerequisites)
            OSError: If file cannot be read or written due to permissions or disk space
        """
        # Basic parameter validation (Pydantic handles most validation automatically)
        if not id or not id.strip():
            raise ValidationError(
                errors=["Object ID cannot be empty"],
                error_codes=[ValidationErrorCode.MISSING_REQUIRED_FIELD],
                context={"field": "id"},
            )

        if not projectRoot or not projectRoot.strip():
            raise ValidationError(
                errors=["Project root cannot be empty"],
                error_codes=[ValidationErrorCode.MISSING_REQUIRED_FIELD],
                context={"field": "projectRoot"},
            )

        # At least one patch parameter must be provided
        if not yamlPatch and not bodyPatch:
            raise ValidationError(
                errors=["At least one of yamlPatch or bodyPatch must be provided"],
                error_codes=[ValidationErrorCode.MISSING_REQUIRED_FIELD],
                context={"field": "yamlPatch or bodyPatch"},
            )

        # Resolve project roots to get planning directory
        _, planning_root = resolve_project_roots(projectRoot)

        # Initialize kind inference engine and infer object type
        try:
            inference_engine = KindInferenceEngine(planning_root)
            kind = inference_engine.infer_kind(id.strip(), validate=False)
        except ValidationError as e:
            # Re-raise inference errors with additional context
            raise ValidationError(
                errors=[f"Kind inference failed: {'; '.join(e.errors)}"],
                error_codes=[ValidationErrorCode.INVALID_FIELD],
                context={
                    "object_id": id.strip(),
                    "inference_step": "kind_inference",
                    "original_errors": e.errors,
                },
            ) from e

        # Clean the ID (remove prefix if present)
        clean_id = id.strip()
        if clean_id.startswith(("P-", "E-", "F-", "T-")):
            clean_id = clean_id[2:]

        # Load existing object
        try:
            file_path = id_to_path(planning_root, kind, clean_id)
        except FileNotFoundError:
            raise
        except ValueError as e:
            raise ValidationError(
                errors=[f"Invalid kind or ID: {e}"],
                error_codes=[ValidationErrorCode.INVALID_FIELD],
                context={"validation_type": "id_resolution", "kind": kind},
                object_id=clean_id,
                object_kind=kind,
            )

        try:
            existing_yaml, existing_body = read_markdown(file_path)
        except FileNotFoundError:
            raise FileNotFoundError(f"Object not found: {file_path}")
        except OSError as e:
            raise OSError(f"Failed to read object file: {e}")

        # Store original status for transition validation
        original_status = existing_yaml.get("status")

        # Deep merge yamlPatch with existing YAML if provided
        updated_yaml = existing_yaml.copy()
        if yamlPatch:
            updated_yaml = _deep_merge_dict(updated_yaml, yamlPatch)

        # Update body if bodyPatch is provided
        updated_body = bodyPatch if bodyPatch else existing_body

        # Always update the timestamp
        updated_yaml["updated"] = datetime.now().isoformat()

        # Validate the updated front-matter
        try:
            front_matter_errors = validate_front_matter(updated_yaml, kind)
            if front_matter_errors:
                raise ValidationError(
                    errors=front_matter_errors,
                    error_codes=[ValidationErrorCode.INVALID_FIELD] * len(front_matter_errors),
                    context={"validation_type": "front_matter", "kind": kind},
                    object_id=clean_id,
                    object_kind=kind,
                )
        except ValidationError:
            raise
        except Exception as e:
            raise ValidationError(
                errors=[f"Front-matter validation failed: {str(e)}"],
                error_codes=[ValidationErrorCode.INVALID_FIELD],
                context={"validation_type": "front_matter", "kind": kind},
                object_id=clean_id,
                object_kind=kind,
            )

        # Comprehensive object validation (includes parent existence check)
        try:
            validate_object_data(updated_yaml, planning_root)
        except TrellisValidationError as e:
            # Convert legacy validation error to enhanced format
            raise ValidationError(
                errors=e.errors,
                error_codes=[ValidationErrorCode.INVALID_FIELD] * len(e.errors),
                context={"validation_type": "object_data", "kind": kind},
                object_id=clean_id,
                object_kind=kind,
            )
        except Exception as e:
            raise ValidationError(
                errors=[f"Object validation failed: {str(e)}"],
                error_codes=[ValidationErrorCode.INVALID_FIELD],
                context={"validation_type": "object_data", "kind": kind},
                object_id=clean_id,
                object_kind=kind,
            )

        # Validate status transitions if status was changed
        new_status = updated_yaml.get("status")
        if original_status and new_status and original_status != new_status:
            # Special validation: Tasks cannot be set to 'done' via updateObject
            if kind == "task" and new_status == "done":
                raise ValidationError(
                    errors=["updateObject cannot set a Task to 'done'; use completeTask instead."],
                    error_codes=[ValidationErrorCode.INVALID_STATUS_TRANSITION],
                    context={
                        "validation_type": "status_transition",
                        "kind": kind,
                        "original_status": original_status,
                        "new_status": new_status,
                    },
                    object_id=clean_id,
                    object_kind=kind,
                )

            try:
                enforce_status_transition(original_status, new_status, kind)
            except ValueError as e:
                raise ValidationError(
                    errors=[f"Status transition validation failed: {str(e)}"],
                    error_codes=[ValidationErrorCode.INVALID_STATUS_TRANSITION],
                    context={
                        "validation_type": "status_transition",
                        "kind": kind,
                        "original_status": original_status,
                        "new_status": new_status,
                    },
                    object_id=clean_id,
                    object_kind=kind,
                )

        # Handle cascade deletion when status is set to 'deleted'
        if new_status == "deleted":
            try:
                # Find all children of the object being deleted
                child_paths = children_of(kind, clean_id, planning_root)

                # Check for protected children (tasks with in-progress or review status)
                protected_children = []
                for child_path in child_paths:
                    try:
                        # Only check task files for protected status
                        if child_path.name.endswith(".md") and "/tasks-" in str(child_path):
                            child_yaml, _ = read_markdown(child_path)
                            child_status = child_yaml.get("status")
                            if child_status in ["in-progress", "review"]:
                                protected_children.append(
                                    {
                                        "path": str(child_path),
                                        "id": child_yaml.get("id", "unknown"),
                                        "status": child_status,
                                    }
                                )
                    except Exception:
                        # Skip files that can't be read/parsed
                        continue

                # If protected children exist, raise ProtectedObjectError unless force=True
                if protected_children and not force:
                    protected_ids = [child["id"] for child in protected_children]
                    raise ProtectedObjectError(
                        f"Cannot delete {kind} {clean_id}: has protected children {protected_ids} "
                        f"in 'in-progress' or 'review' status"
                    )

                # Perform cascade deletion
                # First, add the object's own file to the deletion list
                paths_to_delete = [file_path] + child_paths

                # Use recursive_delete to remove all paths
                deleted_paths = []
                for path in paths_to_delete:
                    if path.exists():
                        try:
                            # Use recursive_delete for each path
                            path_deleted = recursive_delete(path, dry_run=False)
                            deleted_paths.extend(path_deleted)
                        except Exception as e:
                            raise CascadeError(f"Failed to delete {path}: {str(e)}")

                # Return cascade deletion result
                return {
                    "id": clean_id,
                    "kind": kind,
                    "updated": updated_yaml["updated"],
                    "changes": {
                        "status": "deleted",
                        "cascade_deleted": [str(p) for p in deleted_paths],
                    },
                }

            except (CascadeError, ProtectedObjectError) as e:
                # Wrap cascade-specific errors in ValidationError
                raise ValidationError(
                    errors=[str(e)],
                    error_codes=[ValidationErrorCode.INVALID_STATUS_TRANSITION],
                    context={"validation_type": "cascade_deletion", "kind": kind},
                    object_id=clean_id,
                    object_kind=kind,
                )
            except Exception as e:
                # Wrap other errors in ValidationError
                raise ValidationError(
                    errors=[f"Cascade deletion failed: {str(e)}"],
                    error_codes=[ValidationErrorCode.INVALID_STATUS_TRANSITION],
                    context={"validation_type": "cascade_deletion", "kind": kind},
                    object_id=clean_id,
                    object_kind=kind,
                )

        # Write the updated file atomically
        try:
            write_markdown(file_path, updated_yaml, updated_body)
        except OSError as e:
            raise OSError(f"Failed to write updated object file: {e}")

        # Validate acyclic prerequisites after file update as fallback safety measure
        # This ensures the update doesn't introduce cycles (defense in depth)
        try:
            # Build dependency graph with the updated object included
            dependency_graph = DependencyGraph()
            dependency_graph.build(planning_root)

            # Check if the updated object created a cycle
            if dependency_graph.has_cycle():
                # If cycles are detected, restore the original file and raise error
                try:
                    write_markdown(file_path, existing_yaml, existing_body)
                except OSError:
                    pass  # Restoration failed, but we still need to report the cycle
                raise ValidationError(
                    errors=[
                        "Updating this object would introduce circular dependencies "
                        "in prerequisites"
                    ],
                    error_codes=[ValidationErrorCode.CIRCULAR_DEPENDENCY],
                    context={"validation_type": "dependency_graph", "kind": kind},
                    object_id=clean_id,
                    object_kind=kind,
                )
        except ValidationError:
            raise
        except Exception as e:
            # If cycle check fails for other reasons, restore the original file
            try:
                write_markdown(file_path, existing_yaml, existing_body)
            except OSError:
                pass
            raise ValidationError(
                errors=[f"Failed to validate prerequisites: {str(e)}"],
                error_codes=[ValidationErrorCode.INVALID_FIELD],
                context={"validation_type": "dependency_graph", "kind": kind},
                object_id=clean_id,
                object_kind=kind,
            )

        # Build change summary
        changes = {}
        if yamlPatch:
            changes["yaml_fields"] = list(yamlPatch.keys())
        if bodyPatch:
            changes["body_updated"] = True

        # Return success information
        return {
            "id": clean_id,
            "kind": kind,
            "updated": updated_yaml["updated"],
            "changes": changes,
        }

    return updateObject
