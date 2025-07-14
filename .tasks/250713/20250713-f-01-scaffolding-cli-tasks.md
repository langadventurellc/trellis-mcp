# F-01 · Scaffolding & CLI — Task Checklist  (bootstrap scope)

## Checklist

**IMPORTANT**: When starting a new task, read @./20250713-f-01-scaffolding-cli-feature.md and @../../docs/task_mcp_spec_and_plan.md for context.

- [x] **S-01** (XS) Create `src/trellis_mcp/` package and `__init__.py`
  - Created `src/trellis_mcp/` directory structure
  - Added `__init__.py` with package metadata (version 0.1.0, description, author)
  - Verified package imports correctly
  - Files created: `src/trellis_mcp/__init__.py`
- [x] **S-02** (S) Add `pyproject.toml` with deps (click ≥ 8.1, fastmcp ≥ 0.7) & build-system
  - Created comprehensive pyproject.toml with project metadata and build system configuration
  - Added required dependencies: click>=8.1, fastmcp>=0.7  
  - Configured setuptools build-backend with proper package discovery
  - Added CLI entry point: trellis-mcp = "trellis_mcp.cli:cli"
  - Included development dependencies and project URLs
  - Validated configuration with pip dry-run (all dependencies resolve correctly)
  - Files created: `pyproject.toml`
- [x] **S-03** (XS) Add `.gitignore` and bootstrap `README.md`
  - Created comprehensive `.gitignore` using official GitHub Python template with 2024 best practices
  - Added MCP/FastMCP specific patterns (.mcp/, *.mcp.log, mcp_server_logs/)
  - Added Click CLI specific patterns (.click_completion/, cli_logs/)
  - Expanded `README.md` with project description, installation instructions, quick start guide
  - Included development setup instructions and repository links
  - Verified .gitignore patterns work correctly with git check-ignore
  - Files created: `.gitignore`
  - Files updated: `README.md`
- [x] **S-04** (XS) Configure **uv** lock file; verify `uv pip install -e .` works
  - Created uv.lock file with 70 resolved packages using `uv lock`
  - Set up virtual environment with `uv venv` (.venv/ directory created)
  - Successfully installed package in editable mode using `uv pip install -e .`
  - Verified package imports correctly: `import trellis_mcp` works
  - Confirmed CLI entry point installed correctly at .venv/bin/trellis-mcp
  - Installation included all dependencies: click>=8.1, fastmcp>=0.7, and 43 transitive dependencies
  - Python syntax validation passed on all package files
  - Files created: `uv.lock`, `.venv/` (virtual environment)
- [x] **S-05** (S) Add **pre-commit** config (black, flake8, pyright, pytest)
  - Created comprehensive `.pre-commit-config.yaml` with local hooks for all required tools
  - Configured black for code formatting using `uv run black`
  - Added flake8 linting with proper src/ directory targeting
  - Included pyright type checking for src/ directory  
  - Set up pytest with conditional execution (skips when no tests exist)
  - Successfully installed pre-commit hooks with `uv run pre-commit install`
  - Fixed line length issue in src/trellis_mcp/__init__.py to comply with flake8
  - Verified `uv run pre-commit run --all-files` executes successfully
  - Files created: `.pre-commit-config.yaml`
- [x] **S-06** (XS) Set up pytest skeleton (`tests/conftest.py`)
  - Created `tests/` directory structure for pytest test suite
  - Implemented comprehensive `tests/conftest.py` with essential fixtures:
    - `temp_dir`: Temporary directory for file operations testing
    - `clean_working_dir`: Clean working directory context manager  
    - `sample_planning_structure`: Sample project hierarchy for testing
  - Follows pytest best practices with proper type hints and documentation
  - Provides foundation for future test development across the test suite
  - Files created: `tests/conftest.py`
- [x] **S-07** (XS) Implement `settings.py` with default config values
  - Created comprehensive `src/trellis_mcp/settings.py` with Pydantic BaseSettings class
  - Defined default values for server configuration (host, port, log level)
  - Added transport settings (stdio/http), planning directory structure
  - Included CLI configuration, file settings, and development options
  - Configured MCP_ environment variable prefix for hierarchical config loading
  - Follows one-export-per-file rule (exports only Settings class)
  - Ready for future config loader implementation (S-08) and CLI integration (S-09+)
  - Files created: `src/trellis_mcp/settings.py`
- [x] **S-08** (S) Implement `loader.py` — load YAML/TOML, apply env overrides
  - Implemented comprehensive `src/trellis_mcp/loader.py` with `ConfigLoader` class (one export per file)
  - Added custom Pydantic settings sources for YAML (`YamlConfigSettingsSource`) and TOML (`TomlConfigSettingsSource`)
  - Supports hierarchical configuration loading: defaults → file → env → CLI (highest precedence)
  - Added PyYAML and pydantic-settings>=2.0.0 dependencies to pyproject.toml
  - Security-first: uses `yaml.safe_load()` for YAML parsing, proper error handling
  - Auto-detection of config file formats (.yaml/.yml/.toml) when extension omitted
  - Graceful fallback when config files don't exist (returns empty config)
  - Includes config file discovery in common locations (`find_config_file` method)
  - Comprehensive test suite covers YAML/TOML loading, precedence chain, error cases, integration scenarios
  - Updated tooling: added flake8-pyproject for proper pyproject.toml configuration support
  - Files created: `src/trellis_mcp/loader.py`, `tests/test_loader.py`
  - Files updated: `pyproject.toml` (added dependencies), `.pre-commit-config.yaml` (improved config)
- [x] **S-09** (XS) Create `trellis_mcp.cli:cli` Click command group
  - Created `src/trellis_mcp/cli.py` with main Click command group
  - Implemented CLI foundation with proper help text and configuration integration
  - Added command-line options for config file path, debug mode, and log level
  - Integrated with existing Settings and ConfigLoader for hierarchical configuration loading
  - Follows one-export-per-file rule (exports only `cli` group)
  - CLI accessible via `trellis-mcp` entry point as configured in pyproject.toml
  - Supports MCP_ environment variable prefix for configuration overrides
  - Files created: `src/trellis_mcp/cli.py`
- [x] **S-10** (S) Implement `serve` sub-command — start FastMCP server (STDIO)
  - Created FastMCP server factory function in `src/trellis_mcp/server.py` following one-export-per-file rule
  - Implemented `create_server()` function that returns configured FastMCP instance with health check tool and server info resource
  - Added `serve` subcommand to CLI that starts FastMCP server with STDIO transport (default)
  - Server displays startup information including transport type, planning root, and log level
  - Integrated with existing Settings class for server configuration
  - Added comprehensive test suite covering server creation and basic functionality
  - All quality checks pass: formatting (black), linting (flake8), type checking (pyright), and tests (pytest)
  - Successfully tested: `trellis-mcp serve` command starts FastMCP server with proper configuration
  - Files created: `src/trellis_mcp/server.py`, `tests/test_server.py`
  - Files updated: `src/trellis_mcp/cli.py`, `pyproject.toml` (added pytest-asyncio dependency)
- [x] **S-11** (S) Add `--http HOST:PORT` flag — attach HTTP transport
  - Added `--http HOST:PORT` option to the `serve` command in CLI
  - Implemented HOST:PORT parsing with validation (host non-empty, port 1024-65535)
  - Updated server startup logic to use HTTP transport when flag provided
  - Added comprehensive error handling for invalid HOST:PORT formats
  - Created extensive test suite covering validation scenarios and edge cases
  - Updated help text and command documentation
  - All quality checks pass: formatting (black), linting (flake8), type checking (pyright), tests (pytest)
  - Files modified: `src/trellis_mcp/cli.py`, `tests/test_server.py`
- [x] **S-12** (S) Implement `init` sub-command — create minimal `planning/` tree
  - Added `init` subcommand to CLI that creates minimal planning directory structure (planning/projects/)
  - Accepts optional PATH argument (defaults to current working directory)
  - Uses pathlib.Path for cross-platform compatibility and settings configuration for directory names
  - Handles existing directories gracefully with exist_ok=True
  - Provides clear user feedback with ✓ success indicators and created directory paths
  - Includes comprehensive error handling for permission errors and invalid paths
  - Added debug mode output showing full paths when debug is enabled
  - All quality checks pass: formatting (black), linting (flake8), type checking (pyright), tests (pytest)
  - Successfully tested: `trellis-mcp init` and `trellis-mcp init PATH` work correctly
  - Follows one-export-per-file rule (CLI still exports only the cli group)
  - Files modified: `src/trellis_mcp/cli.py`
- [x] **S-13** (XS) Unit tests for settings loader & precedence chain
  - Created comprehensive `tests/test_settings.py` with 26 unit tests covering Settings class functionality
  - Added Settings class validation tests: default values, field types, constraint validation (port range, log levels)
  - Implemented environment variable testing with MCP_ prefix, case insensitivity, type conversion
  - Created focused precedence chain tests: defaults → env → CLI override testing in isolation
  - Added integration tests for Settings class with ConfigLoader, serialization, and model configuration
  - All quality checks pass: formatting (black), linting (flake8), type checking (pyright), tests (pytest)
  - Files created: `tests/test_settings.py`
- [x] **S-14** (M) Integration test: start `trellis-mcp serve` and hit with FastMCP test client
  - Created comprehensive integration test suite in `tests/test_integration.py` using FastMCP in-memory transport
  - Implemented 6 integration tests covering server startup, connectivity, health checks, and concurrent connections
  - Tests verify server responds correctly to `ping()`, `health_check` tool, and `info://server` resource
  - Added concurrent client connection testing to verify server handles multiple simultaneous clients
  - Used in-memory FastMCP transport (recommended approach) for efficient testing without network overhead
  - All quality checks pass: formatting (black), linting (flake8), type checking (pyright), tests (pytest)
  - Integration tests validate end-to-end server functionality and MCP protocol compliance
  - Files created: `tests/test_integration.py`

### Quality Gates
* **Black, flake8, pyright** all pass.
* **pytest** coverage ≥ 90 % on new code.
* `trellis-mcp serve` prints active transport(s) at startup.
* CLI commands work on macOS, Linux, Windows (CI matrix).

### Relevant Files
* `src/trellis_mcp/__init__.py` - Package initialization with metadata
* `src/trellis_mcp/settings.py` - Pydantic BaseSettings class with default configuration values
* `src/trellis_mcp/loader.py` - ConfigLoader class with YAML/TOML support and hierarchical config loading
* `src/trellis_mcp/cli.py` - Main Click command group for CLI interface with configuration integration and serve command
* `src/trellis_mcp/server.py` - FastMCP server factory function with health check tool and server info resource
* `pyproject.toml` - Project configuration, dependencies, and build system (includes PyYAML, pydantic-settings, pytest-asyncio)
* `.gitignore` - Git ignore patterns for Python, MCP, and development files
* `README.md` - Project documentation with installation and usage instructions
* `uv.lock` - UV lock file with exact dependency versions (69 packages resolved)
* `.venv/` - Virtual environment directory for isolated package installation
* `.pre-commit-config.yaml` - Pre-commit hooks configuration for code quality (black, flake8, pyright, pytest)
* `tests/conftest.py` - Pytest configuration with shared fixtures for testing
* `tests/test_loader.py` - Comprehensive test suite for configuration loader functionality
* `tests/test_server.py` - Test suite for FastMCP server creation and functionality
* `tests/test_settings.py` - Unit tests for Settings class validation and precedence chain testing
* `tests/test_integration.py` - Integration tests for FastMCP server end-to-end functionality with client testing
