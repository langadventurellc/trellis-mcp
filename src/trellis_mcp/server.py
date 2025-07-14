"""Trellis MCP Server Factory.

Creates and configures the FastMCP server instance for the Trellis MCP application.
Provides server setup with basic tools and resources for project management.
"""

from __future__ import annotations

import yaml
from datetime import datetime
from pathlib import Path

from fastmcp import FastMCP

from .settings import Settings
from .id_utils import generate_id
from .fs_utils import ensure_parent_dirs
from .path_resolver import id_to_path


def create_server(settings: Settings) -> FastMCP:
    """Create and configure a FastMCP server instance.

    Creates a Trellis MCP server with basic tools and resources for hierarchical
    project management. Server is configured using the provided settings.

    Args:
        settings: Configuration settings for server setup

    Returns:
        Configured FastMCP server instance ready to run
    """
    # Create server with descriptive name and instructions
    server = FastMCP(
        name="Trellis MCP Server",
        instructions="""
        This is the Trellis MCP Server implementing the Trellis MCP v1.0 specification.
        It provides file-backed hierarchical project management with the structure:
        Projects → Epics → Features → Tasks

        The server manages planning data stored as Markdown files with YAML front-matter
        in a nested directory structure under the planning root directory.
        """,
    )

    @server.tool
    def health_check() -> dict[str, str]:
        """Check server health and return status information.

        Returns basic server health information including server name,
        schema version, and planning root directory.
        """
        return {
            "status": "healthy",
            "server": "Trellis MCP Server",
            "schema_version": settings.schema_version,
            "planning_root": str(settings.planning_root),
        }

    @server.resource("info://server")
    def server_info() -> dict[str, str | int | bool]:
        """Provide server configuration and runtime information.

        Returns current server configuration including transport settings,
        directory structure, and operational parameters.
        """
        return {
            "name": "Trellis MCP Server",
            "version": settings.schema_version,
            "host": settings.host,
            "port": settings.port,
            "log_level": settings.log_level,
            "planning_root": str(settings.planning_root),
            "debug_mode": settings.debug_mode,
            "auto_create_dirs": settings.auto_create_dirs,
        }

    @server.tool
    def createObject(
        kind: str,
        title: str,
        projectRoot: str,
        id: str | None = None,
        parent: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        prerequisites: list[str] | None = None,
        description: str | None = None,
    ) -> dict[str, str]:
        """Create a new Trellis MCP object (Project, Epic, Feature, or Task).

        Creates a new object file with proper YAML front-matter and Markdown structure.
        When no ID is provided, automatically generates a unique ID based on the title.

        Args:
            kind: Object type ('project', 'epic', 'feature', or 'task')
            title: Human-readable title for the object
            projectRoot: Root directory for the planning structure
            id: Optional custom ID (auto-generated if not provided)
            parent: Parent object ID (required for epics, features, tasks)
            status: Object status (defaults based on kind)
            priority: Priority level ('high', 'normal', 'low' - defaults to 'normal')
            prerequisites: List of prerequisite object IDs (defaults to empty list)
            description: Optional description for the object body

        Returns:
            Dictionary containing the created object information including id, file_path, and status

        Raises:
            ValueError: If kind is invalid or required parameters are missing
            FileExistsError: If object with the same ID already exists
            OSError: If file cannot be created due to permissions or disk space
        """
        # Validate kind
        valid_kinds = {"project", "epic", "feature", "task"}
        if kind not in valid_kinds:
            raise ValueError(f"Invalid kind '{kind}'. Must be one of: {valid_kinds}")

        # Validate required parameters
        if not title or not title.strip():
            raise ValueError("Title cannot be empty")

        if not projectRoot or not projectRoot.strip():
            raise ValueError("Project root cannot be empty")

        # Validate parent requirements
        if kind in {"epic", "feature", "task"} and not parent:
            raise ValueError(f"Parent is required for {kind} objects")

        if kind == "project" and parent:
            raise ValueError("Projects cannot have parent objects")

        # Convert projectRoot to Path object
        project_root_path = Path(projectRoot)

        # Generate ID if not provided
        if not id:
            id = generate_id(kind, title, project_root_path)

        # Set default status based on kind
        if not status:
            status = "draft" if kind in {"project", "epic", "feature"} else "open"

        # Set default priority
        if not priority:
            priority = "normal"

        # Set default prerequisites
        if prerequisites is None:
            prerequisites = []

        # Generate timestamps
        now = datetime.now().isoformat()

        # Create YAML front-matter
        front_matter = {
            "kind": kind,
            "id": f"{kind[0].upper()}-{id}",
            "title": title,
            "status": status,
            "priority": priority,
            "prerequisites": prerequisites,
            "created": now,
            "updated": now,
            "schema": settings.schema_version,
        }

        # Add parent if provided
        if parent:
            front_matter["parent"] = parent

        # Determine file path based on kind
        if kind == "project":
            file_path = project_root_path / "projects" / f"P-{id}" / "project.md"
        elif kind == "epic":
            # For epics, the parent should be a project
            if parent is None:
                raise ValueError("Parent is required for epic objects")
            # Remove prefix if present to get clean parent ID
            parent_clean = parent.replace("P-", "") if parent.startswith("P-") else parent
            file_path = (
                project_root_path
                / "projects"
                / f"P-{parent_clean}"
                / "epics"
                / f"E-{id}"
                / "epic.md"
            )
        elif kind == "feature":
            # For features, we need to find the parent epic and its project
            if parent is None:
                raise ValueError("Parent is required for feature objects")
            # Remove prefix if present to get clean parent ID
            parent_clean = parent.replace("E-", "") if parent.startswith("E-") else parent

            # Find the parent epic's path to determine the project
            try:
                epic_path = id_to_path(project_root_path, "epic", parent_clean)
                # Extract project directory from epic path
                project_dir = epic_path.parts[epic_path.parts.index("projects") + 1]
                file_path = (
                    project_root_path
                    / "projects"
                    / project_dir
                    / "epics"
                    / f"E-{parent_clean}"
                    / "features"
                    / f"F-{id}"
                    / "feature.md"
                )
            except FileNotFoundError:
                raise ValueError(f"Parent epic '{parent}' not found")
        elif kind == "task":
            # For tasks, we need to find the parent feature and its path
            if parent is None:
                raise ValueError("Parent is required for task objects")
            # Remove prefix if present to get clean parent ID
            parent_clean = parent.replace("F-", "") if parent.startswith("F-") else parent

            # Find the parent feature's path to determine the project and epic
            try:
                feature_path = id_to_path(project_root_path, "feature", parent_clean)
                # Extract project and epic directories from feature path
                project_dir = feature_path.parts[feature_path.parts.index("projects") + 1]
                epic_dir = feature_path.parts[feature_path.parts.index("epics") + 1]
                file_path = (
                    project_root_path
                    / "projects"
                    / project_dir
                    / "epics"
                    / epic_dir
                    / "features"
                    / f"F-{parent_clean}"
                    / "tasks-open"
                    / f"T-{id}.md"
                )
            except FileNotFoundError:
                raise ValueError(f"Parent feature '{parent}' not found")
        else:
            raise ValueError(f"Invalid kind: {kind}")

        # Check if file already exists
        if file_path.exists():
            raise FileExistsError(f"Object with ID '{id}' already exists at {file_path}")

        # Ensure parent directories exist
        ensure_parent_dirs(file_path)

        # Create markdown content
        yaml_content = yaml.dump(front_matter, default_flow_style=False, sort_keys=False)
        markdown_content = f"---\n{yaml_content}---\n\n"

        # Add description if provided
        if description:
            markdown_content += f"{description}\n\n"

        # Add log section
        markdown_content += "### Log\n\n"

        # Write file
        try:
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(markdown_content)
        except OSError as e:
            raise OSError(f"Failed to create object file: {e}") from e

        # Return success information
        return {
            "id": front_matter["id"],
            "kind": kind,
            "title": title,
            "status": status,
            "file_path": str(file_path),
            "created": now,
        }

    return server
