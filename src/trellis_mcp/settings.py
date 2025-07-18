"""Trellis MCP Server Settings.

Provides default configuration values for the Trellis MCP server with support
for hierarchical configuration loading (defaults → file → env → CLI).
"""

from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Trellis MCP Server configuration settings.

    Defines default values for server operation, transport configuration,
    and planning directory structure. Supports hierarchical configuration
    loading through environment variables with MCP_ prefix.
    """

    model_config = SettingsConfigDict(
        env_prefix="MCP_",
        case_sensitive=False,
        validate_default=True,
    )

    # Server Configuration
    host: str = Field(default="127.0.0.1", description="Server host address for HTTP transport")

    port: int = Field(default=8080, description="Server port for HTTP transport", ge=1024, le=65535)

    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = Field(
        default="INFO", description="Logging level for server operations"
    )

    log_dir: Path = Field(default=Path("./logs"), description="Directory for system log files")

    log_retention_days: int = Field(
        default=30, description="Number of days to retain log files before automatic cleanup", gt=0
    )

    # Transport Configuration
    default_transport: Literal["stdio", "http"] = Field(
        default="stdio", description="Default transport type for MCP server"
    )

    enable_http_transport: bool = Field(
        default=False, description="Enable HTTP transport in addition to STDIO"
    )

    # Planning Directory Configuration
    planning_root: Path = Field(
        default=Path("./planning"), description="Root directory for planning hierarchy"
    )

    projects_dir: str = Field(
        default="projects",
        description="Directory name for projects within planning root",
    )

    epics_dir: str = Field(
        default="epics",
        description="Directory name for epics within project directories",
    )

    features_dir: str = Field(
        default="features",
        description="Directory name for features within epic directories",
    )

    tasks_open_dir: str = Field(
        default="tasks-open",
        description="Directory name for open tasks within feature directories",
    )

    tasks_done_dir: str = Field(
        default="tasks-done",
        description="Directory name for completed tasks within feature dirs",
    )

    # File Configuration
    schema_version: str = Field(default="1.1", description="YAML schema version for object files")

    file_encoding: str = Field(
        default="utf-8", description="Text encoding for reading/writing files"
    )

    # Performance Configuration
    max_file_size_mb: int = Field(
        default=10, description="Maximum file size in MB for safety checks", gt=0
    )

    # CLI Configuration
    cli_prog_name: str = Field(
        default="trellis-mcp", description="Program name displayed in CLI help"
    )

    cli_description: str = Field(
        default=("Trellis MCP Server - File-backed project management " "for development agents"),
        description="Program description for CLI help",
    )

    # Development Configuration
    debug_mode: bool = Field(
        default=False,
        description="Enable debug mode with verbose logging and error details",
    )

    validate_schema: bool = Field(
        default=True, description="Enable YAML schema validation for object files"
    )

    auto_create_dirs: bool = Field(
        default=True, description="Automatically create missing directories"
    )
