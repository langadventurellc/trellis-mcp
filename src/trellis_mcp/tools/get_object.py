"""Get object tool for Trellis MCP server.

Retrieves a Trellis MCP object by ID with automatic kind inference, resolving the
object path and reading YAML front-matter and body content from the corresponding
markdown file.
"""

from typing import Annotated

from fastmcp import FastMCP
from pydantic import Field

from ..exceptions.validation_error import ValidationError, ValidationErrorCode
from ..inference import KindInferenceEngine
from ..io_utils import read_markdown
from ..path_resolver import discover_immediate_children, id_to_path, resolve_project_roots
from ..settings import Settings


def create_get_object_tool(settings: Settings):
    """Create a getObject tool configured with the provided settings.

    Args:
        settings: Server configuration settings

    Returns:
        Configured getObject tool function
    """
    mcp = FastMCP()

    @mcp.tool
    def getObject(
        id: Annotated[
            str,
            Field(
                description="Object ID (with or without P-, E-, F-, T- prefix)",
                min_length=1,
            ),
        ],
        projectRoot: Annotated[
            str, Field(description="Root directory for planning structure", min_length=1)
        ],
    ):
        """Retrieve a Trellis MCP object by ID with automatic kind inference.

        Uses the kind inference engine to automatically determine object type from
        ID prefix, then resolves the object path and reads YAML front-matter and
        body content from the corresponding markdown file.

        Args:
            id: Object ID (P-, E-, F-, T- prefixed)
            projectRoot: Root directory for the planning structure

        Returns:
            Dictionary containing the object data with structure:
            {
                "yaml": dict,  # YAML front-matter as dictionary
                "body": str,   # Markdown body content
                "kind": str,   # Inferred object kind
                "id": str,     # Clean object ID
                "children": list[dict[str, str]]  # Immediate child objects
            }

            The children array contains immediate child objects only:
            - Projects: immediate epics
            - Epics: immediate features
            - Features: immediate tasks
            - Tasks: empty array (no children)

            Each child object contains: {id, title, status, kind, created}

        Raises:
            ValidationError: If ID is invalid, inference fails, or validation fails
            FileNotFoundError: If object with the given ID cannot be found
            OSError: If file cannot be read due to permissions or other IO errors
            yaml.YAMLError: If YAML front-matter is malformed
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

        # Resolve the file path using path_resolver
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

        # Read the markdown file
        try:
            yaml_dict, body_str = read_markdown(file_path)
        except FileNotFoundError:
            raise FileNotFoundError(f"Object file not found: {file_path}")
        except OSError as e:
            raise OSError(f"Failed to read object file: {e}")

        # Discover immediate children
        children_list = []
        try:
            raw_children = discover_immediate_children(kind, clean_id, planning_root)
            # Filter out file_path for clean response format
            children_list = [
                {k: v for k, v in child.items() if k != "file_path"} for child in raw_children
            ]
        except Exception:
            # Log warning but continue with empty children array
            # Don't let children discovery errors break getObject functionality
            children_list = []

        # Return the object data with clean response format
        return {
            "yaml": yaml_dict,
            "body": body_str,
            "kind": kind,  # Now inferred automatically
            "id": clean_id,
            "children": children_list,
        }

    return getObject
