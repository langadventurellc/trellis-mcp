"""Get object tool for Trellis MCP server.

Retrieves a Trellis MCP object by kind and ID, resolving the object path and
reading YAML front-matter and body content from the corresponding markdown file.
"""

from fastmcp import FastMCP

from ..exceptions.validation_error import ValidationError, ValidationErrorCode
from ..io_utils import read_markdown
from ..path_resolver import id_to_path, resolve_project_roots
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
        kind: str,
        id: str,
        projectRoot: str,
    ) -> dict[str, str | dict[str, str | list[str] | None]]:
        """Retrieve a Trellis MCP object by kind and ID.

        Resolves the object path and reads the YAML front-matter and body content
        from the corresponding markdown file.

        Args:
            kind: Object type ('project', 'epic', 'feature', or 'task')
            id: Object ID (with or without prefix)
            projectRoot: Root directory for the planning structure

        Returns:
            Dictionary containing the object data with structure:
            {
                "yaml": dict,  # YAML front-matter as dictionary
                "body": str,   # Markdown body content
                "file_path": str,  # Path to the object file
                "kind": str,   # Object kind
                "id": str      # Clean object ID
            }

        Raises:
            ValueError: If kind is invalid or required parameters are missing
            FileNotFoundError: If object with the given ID cannot be found
            OSError: If file cannot be read due to permissions or other IO errors
            yaml.YAMLError: If YAML front-matter is malformed
        """
        # Basic parameter validation
        if not kind or not kind.strip():
            raise ValidationError(
                errors=["Kind cannot be empty"],
                error_codes=[ValidationErrorCode.MISSING_REQUIRED_FIELD],
                context={"field": "kind"},
            )

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

        # Return the object data
        return {
            "yaml": yaml_dict,
            "body": body_str,
            "file_path": str(file_path),
            "kind": kind,
            "id": clean_id,
        }

    return getObject
