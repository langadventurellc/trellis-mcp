"""Trellis MCP Server Factory.

Creates and configures the FastMCP server instance for the Trellis MCP application.
Provides server setup with basic tools and resources for project management.
"""

from datetime import datetime
from pathlib import Path
from typing import Any

from fastmcp import FastMCP

from .claim_next_task import claim_next_task
from .complete_task import complete_task
from .exceptions.cascade_error import CascadeError
from .exceptions.invalid_status_for_completion import InvalidStatusForCompletion
from .exceptions.no_available_task import NoAvailableTask
from .exceptions.protected_object_error import ProtectedObjectError
from .filters import apply_filters, filter_by_scope
from .fs_utils import ensure_parent_dirs, recursive_delete
from .graph_utils import DependencyGraph
from .id_utils import generate_id
from .io_utils import read_markdown, write_markdown
from .json_rpc_logging_middleware import JsonRpcLoggingMiddleware
from .logger import write_event
from .models.filter_params import FilterParams
from .models.task_sort_key import task_sort_key
from .path_resolver import (
    children_of,
    id_to_path,
    resolve_path_for_new_object,
    resolve_project_roots,
)
from .prune_logs import prune_logs
from .query import get_oldest_review
from .scanner import scan_tasks
from .settings import Settings
from .validation import (
    TrellisValidationError,
    enforce_status_transition,
    validate_front_matter,
    validate_object_data,
)


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
        Uses comprehensive validation to ensure object consistency and acyclic prerequisites.

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
            TrellisValidationError: If validation fails (front-matter, object data,
                or acyclic prerequisites)
            FileExistsError: If object with the same ID already exists
            OSError: If file cannot be created due to permissions or disk space
        """
        # Basic parameter validation
        if not title or not title.strip():
            raise ValueError("Title cannot be empty")

        if not projectRoot or not projectRoot.strip():
            raise ValueError("Project root cannot be empty")

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
            "schema_version": settings.schema_version,
        }

        # Add parent if provided
        if parent:
            front_matter["parent"] = parent

        # Validate front-matter using validation utilities
        try:
            front_matter_errors = validate_front_matter(front_matter, kind)
            if front_matter_errors:
                raise TrellisValidationError(front_matter_errors)
        except TrellisValidationError:
            raise
        except Exception as e:
            raise TrellisValidationError([f"Front-matter validation failed: {str(e)}"])

        # Comprehensive object validation (includes parent existence check)
        try:
            validate_object_data(front_matter, project_root_path)
        except TrellisValidationError:
            raise
        except Exception as e:
            raise TrellisValidationError([f"Object validation failed: {str(e)}"])

        # Determine file path using centralized path logic
        try:
            file_path = resolve_path_for_new_object(kind, id, parent, project_root_path, status)
        except ValueError as e:
            raise ValueError(str(e))
        except FileNotFoundError as e:
            raise ValueError(str(e))

        # Check if file already exists
        if file_path.exists():
            raise FileExistsError(f"Object with ID '{id}' already exists at {file_path}")

        # Ensure parent directories exist
        ensure_parent_dirs(file_path)

        # Create markdown body content
        body_content = ""
        if description:
            body_content += f"{description}\n\n"
        body_content += "### Log\n\n"

        # Write file using io_utils
        try:
            write_markdown(file_path, front_matter, body_content)
        except OSError as e:
            raise OSError(f"Failed to create object file: {e}") from e

        # Validate acyclic prerequisites after file creation as fallback safety measure
        # This ensures the newly created object doesn't introduce cycles (defense in depth)
        try:
            # Build dependency graph with the new object included
            dependency_graph = DependencyGraph()
            dependency_graph.build(project_root_path)

            # Check if the new object created a cycle
            if dependency_graph.has_cycle():
                # If cycles are detected, remove the created file and raise error
                try:
                    file_path.unlink()
                except OSError:
                    pass  # File removal failed, but we still need to report the cycle
                raise TrellisValidationError(
                    ["Creating this object would introduce circular dependencies in prerequisites"]
                )
        except TrellisValidationError:
            raise
        except Exception as e:
            # If cycle check fails for other reasons, remove the created file
            try:
                file_path.unlink()
            except OSError:
                pass
            raise TrellisValidationError([f"Failed to validate prerequisites: {str(e)}"])

        # Return success information
        return {
            "id": front_matter["id"],
            "kind": kind,
            "title": title,
            "status": status,
            "file_path": str(file_path),
            "created": now,
        }

    @server.tool
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
            raise ValueError("Kind cannot be empty")

        if not id or not id.strip():
            raise ValueError("Object ID cannot be empty")

        if not projectRoot or not projectRoot.strip():
            raise ValueError("Project root cannot be empty")

        # Convert projectRoot to Path object
        project_root_path = Path(projectRoot)

        # Clean the ID (remove prefix if present)
        clean_id = id.strip()
        if clean_id.startswith(("P-", "E-", "F-", "T-")):
            clean_id = clean_id[2:]

        # Resolve the file path using path_resolver
        try:
            file_path = id_to_path(project_root_path, kind, clean_id)
        except FileNotFoundError:
            raise
        except ValueError as e:
            raise ValueError(f"Invalid kind or ID: {e}")

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

    @server.tool
    def updateObject(
        kind: str,
        id: str,
        projectRoot: str,
        yamlPatch: dict[str, str | list[str] | None] | None = None,
        bodyPatch: str | None = None,
        force: bool = False,
    ) -> dict[str, str | dict[str, str | list[str] | bool]]:
        """Update a Trellis MCP object by applying patches to YAML front-matter and/or body content.

        Applies JSON merge patch-style updates to an existing object. The yamlPatch parameter
        allows updating individual YAML front-matter fields, while bodyPatch replaces the
        entire body content. The operation is atomic - either all changes succeed or none
        are applied.

        Args:
            kind: Object type ('project', 'epic', 'feature', or 'task')
            id: Object ID (with or without prefix)
            projectRoot: Root directory for the planning structure
            yamlPatch: Optional dictionary of YAML fields to update/merge
            bodyPatch: Optional new body content to replace existing body
            force: If True, bypass safeguards when deleting objects with protected children

        Returns:
            Dictionary containing the updated object information with structure:
            {
                "id": str,           # Clean object ID
                "kind": str,         # Object kind
                "file_path": str,    # Path to the updated file
                "updated": str,      # ISO timestamp of update
                "changes": dict      # Summary of changes made
            }

        Raises:
            ValueError: If kind is invalid or required parameters are missing
            FileNotFoundError: If object with the given ID cannot be found
            TrellisValidationError: If validation fails (front-matter, status transitions,
                or acyclic prerequisites)
            OSError: If file cannot be read or written due to permissions or disk space
        """
        # Basic parameter validation
        if not kind or not kind.strip():
            raise ValueError("Kind cannot be empty")

        if not id or not id.strip():
            raise ValueError("Object ID cannot be empty")

        if not projectRoot or not projectRoot.strip():
            raise ValueError("Project root cannot be empty")

        # At least one patch parameter must be provided
        if yamlPatch is None and bodyPatch is None:
            raise ValueError("At least one of yamlPatch or bodyPatch must be provided")

        # Convert projectRoot to Path object
        project_root_path = Path(projectRoot)

        # Clean the ID (remove prefix if present)
        clean_id = id.strip()
        if clean_id.startswith(("P-", "E-", "F-", "T-")):
            clean_id = clean_id[2:]

        # Load existing object
        try:
            file_path = id_to_path(project_root_path, kind, clean_id)
        except FileNotFoundError:
            raise
        except ValueError as e:
            raise ValueError(f"Invalid kind or ID: {e}")

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
        updated_body = bodyPatch if bodyPatch is not None else existing_body

        # Always update the timestamp
        updated_yaml["updated"] = datetime.now().isoformat()

        # Validate the updated front-matter
        try:
            front_matter_errors = validate_front_matter(updated_yaml, kind)
            if front_matter_errors:
                raise TrellisValidationError(front_matter_errors)
        except TrellisValidationError:
            raise
        except Exception as e:
            raise TrellisValidationError([f"Front-matter validation failed: {str(e)}"])

        # Comprehensive object validation (includes parent existence check)
        try:
            validate_object_data(updated_yaml, project_root_path)
        except TrellisValidationError:
            raise
        except Exception as e:
            raise TrellisValidationError([f"Object validation failed: {str(e)}"])

        # Validate status transitions if status was changed
        new_status = updated_yaml.get("status")
        if original_status and new_status and original_status != new_status:
            # Special validation: Tasks cannot be set to 'done' via updateObject
            if kind == "task" and new_status == "done":
                raise TrellisValidationError(
                    ["updateObject cannot set a Task to 'done'; use completeTask instead."]
                )

            try:
                enforce_status_transition(original_status, new_status, kind)
            except ValueError as e:
                raise TrellisValidationError([f"Status transition validation failed: {str(e)}"])

        # Handle cascade deletion when status is set to 'deleted'
        if new_status == "deleted":
            try:
                # Find all children of the object being deleted
                child_paths = children_of(kind, clean_id, project_root_path)

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
                    "file_path": str(file_path),
                    "updated": updated_yaml["updated"],
                    "changes": {
                        "status": "deleted",
                        "cascade_deleted": [str(p) for p in deleted_paths],
                    },
                }

            except (CascadeError, ProtectedObjectError) as e:
                # Wrap cascade-specific errors in TrellisValidationError
                raise TrellisValidationError([str(e)])
            except Exception as e:
                # Wrap other errors in TrellisValidationError
                raise TrellisValidationError([f"Cascade deletion failed: {str(e)}"])

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
            dependency_graph.build(project_root_path)

            # Check if the updated object created a cycle
            if dependency_graph.has_cycle():
                # If cycles are detected, restore the original file and raise error
                try:
                    write_markdown(file_path, existing_yaml, existing_body)
                except OSError:
                    pass  # Restoration failed, but we still need to report the cycle
                raise TrellisValidationError(
                    ["Updating this object would introduce circular dependencies in prerequisites"]
                )
        except TrellisValidationError:
            raise
        except Exception as e:
            # If cycle check fails for other reasons, restore the original file
            try:
                write_markdown(file_path, existing_yaml, existing_body)
            except OSError:
                pass
            raise TrellisValidationError([f"Failed to validate prerequisites: {str(e)}"])

        # Build change summary
        changes = {}
        if yamlPatch:
            changes["yaml_fields"] = list(yamlPatch.keys())
        if bodyPatch is not None:
            changes["body_updated"] = True

        # Return success information
        return {
            "id": clean_id,
            "kind": kind,
            "file_path": str(file_path),
            "updated": updated_yaml["updated"],
            "changes": changes,
        }

    @server.tool
    def listBacklog(
        projectRoot: str,
        scope: str | None = None,
        status: str | None = None,
        priority: str | None = None,
        sortByPriority: bool = True,
    ):
        """List tasks filtered by scope, status, and priority.

        Uses the modular task scanner, filters, and sorting components to efficiently
        find and filter tasks across the entire project hierarchy.

        Args:
            projectRoot: Root directory for the planning structure
            scope: Optional scope ID to filter tasks by parent (project/epic/feature ID)
            status: Optional status filter ('open', 'in-progress', 'review', 'done')
            priority: Optional priority filter ('high', 'normal', 'low')
            sortByPriority: Whether to sort tasks by priority and creation date (default: True)

        Returns:
            Dictionary with structure:
            {
                "tasks": [
                    {
                        "id": str,           # Clean task ID
                        "title": str,        # Task title
                        "status": str,       # Task status
                        "priority": str,     # Task priority
                        "parent": str,       # Parent feature ID
                        "file_path": str,    # Path to task file
                        "created": str,      # Creation timestamp
                        "updated": str,      # Last update timestamp
                    },
                    ...
                ]
            }

        Raises:
            ValueError: If projectRoot is empty or invalid
            OSError: If there are file system access issues
        """
        # Basic parameter validation
        if not projectRoot or not projectRoot.strip():
            raise ValueError("Project root cannot be empty")

        # Resolve project roots using centralized utility
        scanning_root, path_resolution_root = resolve_project_roots(projectRoot)

        # Create FilterParams from individual parameters, handling validation gracefully
        try:
            filter_status = [status] if status else []
            filter_priority = [priority] if priority else []
            filter_params = FilterParams(status=filter_status, priority=filter_priority)
        except Exception:
            # If validation fails (e.g., invalid status/priority), return empty results
            return {"tasks": []}

        # Get tasks using modular components
        if scope:
            # Use scope filtering if provided
            tasks_iterator = filter_by_scope(scanning_root, scope)
        else:
            # Use scanner to get all tasks
            tasks_iterator = scan_tasks(scanning_root)

        # Apply status and priority filters
        filtered_tasks = apply_filters(tasks_iterator, filter_params)

        # Convert to list and sort if requested
        tasks_list = list(filtered_tasks)
        if sortByPriority:
            tasks_list.sort(key=task_sort_key)

        # Convert TaskModel objects to JSON-serializable format
        result_tasks = []
        for task in tasks_list:
            try:
                # Resolve file path - use path_resolution_root for path resolution
                task_file_path = id_to_path(path_resolution_root, "task", task.id)

                task_data = {
                    "id": f"T-{task.id}" if not task.id.startswith("T-") else task.id,
                    "title": task.title,
                    "status": task.status.value,
                    "priority": str(task.priority),
                    "parent": task.parent or "",
                    "file_path": str(task_file_path),
                    "created": task.created.isoformat(),
                    "updated": task.updated.isoformat(),
                }
                result_tasks.append(task_data)
            except Exception:
                # Skip tasks that can't be processed
                continue

        return {"tasks": result_tasks}

    @server.tool
    def claimNextTask(
        projectRoot: str,
        worktree: str | None = None,
    ) -> dict[str, str | dict[str, str]]:
        """Claim the next highest-priority open task with all prerequisites completed.

        Atomically selects the highest-priority open task (where all prerequisites
        have status='done'), sets its status to 'in-progress', and optionally
        stamps the worktree field.

        Tasks are sorted by priority (high=1, normal=2, low=3) then by creation date.
        Only tasks with status='open' and completed prerequisites are eligible.

        Args:
            projectRoot: Root directory for the planning structure
            worktree: Optional worktree identifier to stamp on the claimed task

        Returns:
            Dictionary containing the claimed task data and file path, or error info

        Raises:
            TrellisValidationError: If no eligible tasks are available
            OSError: If file operations fail
        """
        # Basic parameter validation
        if not projectRoot or not projectRoot.strip():
            raise ValueError("Project root cannot be empty")

        # Call the core claim_next_task function
        try:
            claimed_task = claim_next_task(projectRoot, worktree)
        except NoAvailableTask as e:
            raise TrellisValidationError([str(e)])
        except Exception as e:
            raise TrellisValidationError([f"Failed to claim task: {str(e)}"])

        # Convert TaskModel to the expected dictionary format
        project_root_path = Path(projectRoot)
        task_file_path = id_to_path(project_root_path, "task", claimed_task.id)

        # Build task dictionary in the format expected by the API
        task_dict = {
            "id": claimed_task.id,
            "title": claimed_task.title,
            "status": claimed_task.status.value,
            "priority": str(claimed_task.priority),
            "parent": claimed_task.parent or "",
            "file_path": str(task_file_path),
            "created": claimed_task.created.isoformat(),
            "updated": claimed_task.updated.isoformat(),
        }

        # Return the claimed task info in the expected format
        return {
            "task": task_dict,
            "claimed_status": "in-progress",
            "worktree": worktree if worktree is not None else "",
            "file_path": str(task_file_path),
        }

    @server.tool
    def completeTask(
        projectRoot: str,
        taskId: str,
        summary: str | None = None,
        filesChanged: list[str] | None = None,
    ) -> dict[str, str | dict[str, str]]:
        """Complete a task that is in in-progress or review status.

        Validates that the specified task is in a valid status for completion
        (in-progress or review) and optionally appends a log entry with summary
        and list of changed files. This is part of the task completion workflow.

        Args:
            projectRoot: Root directory for the planning structure
            taskId: ID of the task to complete (with or without T- prefix)
            summary: Optional summary text for the log entry
            filesChanged: Optional list of relative file paths that were changed

        Returns:
            Dictionary containing the validated task data and file path

        Raises:
            TrellisValidationError: If task is not in valid status for completion
            FileNotFoundError: If task with the given ID cannot be found
            OSError: If file operations fail

        Example:
            >>> result = completeTask("./planning", "T-implement-auth")
            >>> result["task"]["status"]
            'in-progress'
        """
        # Basic parameter validation
        if not projectRoot or not projectRoot.strip():
            raise ValueError("Project root cannot be empty")

        if not taskId or not taskId.strip():
            raise ValueError("Task ID cannot be empty")

        # Call the core complete_task function
        try:
            validated_task = complete_task(projectRoot, taskId, summary, filesChanged)
        except InvalidStatusForCompletion as e:
            raise TrellisValidationError([str(e)])
        except FileNotFoundError as e:
            raise TrellisValidationError([f"Task not found: {str(e)}"])
        except Exception as e:
            raise TrellisValidationError([f"Failed to validate task for completion: {str(e)}"])

        # Resolve the task file path for response
        project_root_path = Path(projectRoot)
        task_file_path = id_to_path(project_root_path, "task", validated_task.id)

        # Build task dictionary in the format expected by the API
        task_dict = {
            "id": validated_task.id,
            "title": validated_task.title,
            "status": validated_task.status.value,
            "priority": str(validated_task.priority),
            "parent": validated_task.parent or "",
            "file_path": str(task_file_path),
            "created": validated_task.created.isoformat(),
            "updated": validated_task.updated.isoformat(),
        }

        # Return the validated task info in the expected format
        return {
            "task": task_dict,
            "validation_status": "ready_for_completion",
            "file_path": str(task_file_path),
        }

    @server.tool
    def getNextReviewableTask(
        projectRoot: str,
    ) -> dict[str, str | dict[str, str] | None]:
        """Get the next task that needs review, ordered by oldest updated timestamp.

        Finds the task in 'review' status with the oldest 'updated' timestamp across
        the entire project hierarchy. If multiple tasks have the same timestamp,
        priority is used as a tiebreaker (high > normal > low).

        Args:
            projectRoot: Root directory for the planning structure

        Returns:
            Dictionary containing the reviewable task data, or None if no reviewable tasks exist.
            Structure when task found:
            {
                "task": {
                    "id": str,           # Clean task ID (e.g., "implement-auth")
                    "title": str,        # Task title
                    "status": str,       # Task status ("review")
                    "priority": str,     # Task priority ("high", "normal", "low")
                    "parent": str,       # Parent feature ID
                    "file_path": str,    # Path to task file
                    "created": str,      # Creation timestamp
                    "updated": str,      # Last update timestamp
                }
            }

            When no reviewable tasks exist:
            {
                "task": None
            }

        Raises:
            ValueError: If projectRoot is empty or invalid
            TrellisValidationError: If there are issues accessing the project structure
        """
        # Basic parameter validation
        if not projectRoot or not projectRoot.strip():
            raise ValueError("Project root cannot be empty")

        # Convert projectRoot to Path object
        project_root_path = Path(projectRoot)

        # Call the query function to get the oldest reviewable task
        try:
            reviewable_task = get_oldest_review(project_root_path)
        except Exception as e:
            raise TrellisValidationError([f"Failed to query reviewable tasks: {str(e)}"])

        # Handle case where no reviewable tasks exist
        if reviewable_task is None:
            return {"task": None}

        # Convert TaskModel to dictionary format
        try:
            task_file_path = id_to_path(project_root_path, "task", reviewable_task.id)
        except Exception as e:
            raise TrellisValidationError([f"Failed to resolve task file path: {str(e)}"])

        # Build task dictionary in the format expected by the API
        task_dict = {
            "id": reviewable_task.id,
            "title": reviewable_task.title,
            "status": reviewable_task.status.value,
            "priority": str(reviewable_task.priority),
            "parent": reviewable_task.parent or "",
            "file_path": str(task_file_path),
            "created": reviewable_task.created.isoformat(),
            "updated": reviewable_task.updated.isoformat(),
        }

        # Return the reviewable task info
        return {"task": task_dict}

    # Register JSON-RPC logging middleware
    server.add_middleware(JsonRpcLoggingMiddleware(settings))

    # Prune old log files at startup if retention is configured
    if settings.log_retention_days > 0:
        try:
            prune_logs(settings)
        except Exception as e:
            # Log the error but don't prevent server startup
            write_event(
                "ERROR", "Log pruning failed during startup", settings=settings, error=str(e)
            )

    return server
