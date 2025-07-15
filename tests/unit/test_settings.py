"""Tests for Settings class and precedence chain functionality."""

import os
from pathlib import Path

import pytest
from pydantic import ValidationError

from trellis_mcp.loader import ConfigLoader
from trellis_mcp.settings import Settings


class TestSettingsDefaults:
    """Test Settings class default values and basic functionality."""

    def test_default_values(self) -> None:
        """Test that Settings class provides correct default values."""
        settings = Settings()

        # Server configuration defaults
        assert settings.host == "127.0.0.1"
        assert settings.port == 8080
        assert settings.log_level == "INFO"

        # Transport configuration defaults
        assert settings.default_transport == "stdio"
        assert settings.enable_http_transport is False

        # Planning directory defaults
        assert settings.planning_root == Path("./planning")
        assert settings.projects_dir == "projects"
        assert settings.epics_dir == "epics"
        assert settings.features_dir == "features"
        assert settings.tasks_open_dir == "tasks-open"
        assert settings.tasks_done_dir == "tasks-done"

        # File configuration defaults
        assert settings.schema_version == "1.0"
        assert settings.file_encoding == "utf-8"

        # Performance configuration defaults
        assert settings.max_file_size_mb == 10

        # CLI configuration defaults
        assert settings.cli_prog_name == "trellis-mcp"
        assert "Trellis MCP Server" in settings.cli_description

        # Development configuration defaults
        assert settings.debug_mode is False
        assert settings.validate_schema is True
        assert settings.auto_create_dirs is True

    def test_field_types(self) -> None:
        """Test that Settings fields have correct types."""
        settings = Settings()

        assert isinstance(settings.host, str)
        assert isinstance(settings.port, int)
        assert isinstance(settings.log_level, str)
        assert isinstance(settings.default_transport, str)
        assert isinstance(settings.enable_http_transport, bool)
        assert isinstance(settings.planning_root, Path)
        assert isinstance(settings.projects_dir, str)
        assert isinstance(settings.epics_dir, str)
        assert isinstance(settings.features_dir, str)
        assert isinstance(settings.tasks_open_dir, str)
        assert isinstance(settings.tasks_done_dir, str)
        assert isinstance(settings.schema_version, str)
        assert isinstance(settings.file_encoding, str)
        assert isinstance(settings.max_file_size_mb, int)
        assert isinstance(settings.cli_prog_name, str)
        assert isinstance(settings.cli_description, str)
        assert isinstance(settings.debug_mode, bool)
        assert isinstance(settings.validate_schema, bool)
        assert isinstance(settings.auto_create_dirs, bool)


class TestSettingsValidation:
    """Test Settings field validation and constraints."""

    def test_port_validation_valid_range(self) -> None:
        """Test that port accepts valid range values."""
        settings = Settings(port=1024)
        assert settings.port == 1024

        settings = Settings(port=65535)
        assert settings.port == 65535

        settings = Settings(port=8080)
        assert settings.port == 8080

    def test_port_validation_invalid_low(self) -> None:
        """Test that port rejects values below 1024."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(port=80)

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "greater_than_equal"
        assert errors[0]["loc"] == ("port",)

    def test_port_validation_invalid_high(self) -> None:
        """Test that port rejects values above 65535."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(port=70000)

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "less_than_equal"
        assert errors[0]["loc"] == ("port",)

    def test_log_level_validation_valid(self) -> None:
        """Test that log_level accepts valid values."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        for level in valid_levels:
            settings = Settings(log_level=level)  # type: ignore[arg-type]
            assert settings.log_level == level

    def test_log_level_validation_invalid(self) -> None:
        """Test that log_level rejects invalid values."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(log_level="INVALID")  # type: ignore[arg-type]

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "literal_error"
        assert errors[0]["loc"] == ("log_level",)

    def test_default_transport_validation_valid(self) -> None:
        """Test that default_transport accepts valid values."""
        settings = Settings(default_transport="stdio")
        assert settings.default_transport == "stdio"

        settings = Settings(default_transport="http")
        assert settings.default_transport == "http"

    def test_default_transport_validation_invalid(self) -> None:
        """Test that default_transport rejects invalid values."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(default_transport="invalid")  # type: ignore[arg-type]

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "literal_error"
        assert errors[0]["loc"] == ("default_transport",)

    def test_max_file_size_mb_validation_valid(self) -> None:
        """Test that max_file_size_mb accepts positive values."""
        settings = Settings(max_file_size_mb=1)
        assert settings.max_file_size_mb == 1

        settings = Settings(max_file_size_mb=100)
        assert settings.max_file_size_mb == 100

    def test_max_file_size_mb_validation_invalid(self) -> None:
        """Test that max_file_size_mb rejects non-positive values."""
        with pytest.raises(ValidationError) as exc_info:
            Settings(max_file_size_mb=0)

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "greater_than"
        assert errors[0]["loc"] == ("max_file_size_mb",)

        with pytest.raises(ValidationError) as exc_info:
            Settings(max_file_size_mb=-1)

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "greater_than"
        assert errors[0]["loc"] == ("max_file_size_mb",)

    def test_path_field_conversion(self) -> None:
        """Test that Path fields accept strings and convert properly."""
        settings = Settings(planning_root="./custom-planning")  # type: ignore[arg-type]
        assert isinstance(settings.planning_root, Path)
        assert settings.planning_root == Path("./custom-planning")

        settings = Settings(planning_root=Path("/absolute/path"))
        assert isinstance(settings.planning_root, Path)
        assert settings.planning_root == Path("/absolute/path")


class TestSettingsEnvironmentVariables:
    """Test Settings environment variable handling with MCP_ prefix."""

    def test_env_var_prefix_basic(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test basic environment variable mapping with MCP_ prefix."""
        monkeypatch.setenv("MCP_HOST", "env-host")
        monkeypatch.setenv("MCP_PORT", "9999")
        monkeypatch.setenv("MCP_DEBUG_MODE", "true")

        settings = Settings()

        assert settings.host == "env-host"
        assert settings.port == 9999
        assert settings.debug_mode is True

    def test_env_var_case_insensitive(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that environment variables are case insensitive."""
        monkeypatch.setenv("mcp_host", "lowercase-host")
        monkeypatch.setenv("MCP_PORT", "8888")
        monkeypatch.setenv("Mcp_Debug_Mode", "true")

        settings = Settings()

        assert settings.host == "lowercase-host"
        assert settings.port == 8888
        assert settings.debug_mode is True

    def test_env_var_type_conversion(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test type conversion from environment variables."""
        monkeypatch.setenv("MCP_PORT", "7777")
        monkeypatch.setenv("MCP_DEBUG_MODE", "false")
        monkeypatch.setenv("MCP_MAX_FILE_SIZE_MB", "25")
        monkeypatch.setenv("MCP_ENABLE_HTTP_TRANSPORT", "true")

        settings = Settings()

        assert isinstance(settings.port, int)
        assert settings.port == 7777
        assert isinstance(settings.debug_mode, bool)
        assert settings.debug_mode is False
        assert isinstance(settings.max_file_size_mb, int)
        assert settings.max_file_size_mb == 25
        assert isinstance(settings.enable_http_transport, bool)
        assert settings.enable_http_transport is True

    def test_env_var_validation_errors(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that environment variables still trigger validation errors."""
        monkeypatch.setenv("MCP_PORT", "80")  # Below minimum

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "greater_than_equal"
        assert errors[0]["loc"] == ("port",)

    def test_env_var_invalid_values(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test environment variables with invalid values."""
        monkeypatch.setenv("MCP_LOG_LEVEL", "INVALID_LEVEL")

        with pytest.raises(ValidationError) as exc_info:
            Settings()

        errors = exc_info.value.errors()
        assert len(errors) == 1
        assert errors[0]["type"] == "literal_error"
        assert errors[0]["loc"] == ("log_level",)

    def test_env_var_path_conversion(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test Path field conversion from environment variables."""
        monkeypatch.setenv("MCP_PLANNING_ROOT", "/custom/planning")

        settings = Settings()

        assert isinstance(settings.planning_root, Path)
        assert settings.planning_root == Path("/custom/planning")


class TestPrecedenceChainFocused:
    """Test focused precedence chain behavior in isolation."""

    def test_defaults_only(self) -> None:
        """Test settings with only default values (no other sources)."""
        # Clear any existing env vars
        for key in os.environ.keys():
            if key.startswith("MCP_"):
                del os.environ[key]

        settings = Settings()

        # Should use all default values
        assert settings.host == "127.0.0.1"
        assert settings.port == 8080
        assert settings.log_level == "INFO"
        assert settings.debug_mode is False

    def test_env_overrides_defaults(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that environment variables override defaults."""
        monkeypatch.setenv("MCP_HOST", "env-host")
        monkeypatch.setenv("MCP_PORT", "9000")

        settings = Settings()

        # Env vars should override defaults
        assert settings.host == "env-host"
        assert settings.port == 9000
        # Unset values should use defaults
        assert settings.log_level == "INFO"
        assert settings.debug_mode is False

    def test_cli_overrides_env(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test that CLI arguments override environment variables."""
        monkeypatch.setenv("MCP_HOST", "env-host")
        monkeypatch.setenv("MCP_PORT", "9000")

        # Simulate CLI overrides by passing to Settings constructor
        settings = Settings(host="cli-host", port=7777)

        # CLI should override env
        assert settings.host == "cli-host"
        assert settings.port == 7777

    def test_config_loader_precedence_chain(
        self, temp_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test complete precedence chain through ConfigLoader."""
        # 1. Set up config file (lowest precedence for non-defaults)
        config_file = temp_dir / "config.yaml"
        config_content = """
host: "file-host"
port: 8000
log_level: "DEBUG"
debug_mode: true
"""
        config_file.write_text(config_content)

        # 2. Set environment variable (middle precedence)
        monkeypatch.setenv("MCP_HOST", "env-host")
        monkeypatch.setenv("MCP_LOG_LEVEL", "WARNING")

        # 3. Use ConfigLoader with CLI overrides (highest precedence)
        loader = ConfigLoader()
        settings = loader.load_settings(config_file, host="cli-host", port=9999)

        # Verify complete precedence chain
        assert settings.host == "cli-host"  # CLI override (highest)
        assert settings.port == 9999  # CLI override (highest)
        assert settings.log_level == "WARNING"  # Env var (middle)
        assert settings.debug_mode is True  # Config file (lower)
        assert settings.default_transport == "stdio"  # Default (lowest)

    def test_missing_config_file_precedence(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test precedence when config file is missing."""
        monkeypatch.setenv("MCP_HOST", "env-host")
        monkeypatch.setenv("MCP_DEBUG_MODE", "true")

        loader = ConfigLoader()
        settings = loader.load_settings("nonexistent.yaml", port=8888)

        # Should work without config file
        assert settings.host == "env-host"  # From env
        assert settings.port == 8888  # From CLI
        assert settings.debug_mode is True  # From env
        assert settings.log_level == "INFO"  # Default


class TestSettingsIntegration:
    """Test Settings class integration with other components."""

    def test_settings_with_config_loader_integration(self, temp_dir: Path) -> None:
        """Test Settings integration with ConfigLoader."""
        config_file = temp_dir / "integration.yaml"
        config_content = """
host: "integration-host"
port: 8888
planning_root: "./custom-planning"
debug_mode: true
"""
        config_file.write_text(config_content)

        loader = ConfigLoader()
        settings = loader.load_settings(config_file)

        # Verify all values loaded correctly
        assert settings.host == "integration-host"
        assert settings.port == 8888
        assert settings.planning_root == Path("./custom-planning")
        assert settings.debug_mode is True
        # Non-specified values should use defaults
        assert settings.log_level == "INFO"
        assert settings.schema_version == "1.0"

    def test_settings_serialization(self) -> None:
        """Test that Settings can be serialized/deserialized properly."""
        original = Settings(
            host="test-host",
            port=9999,
            debug_mode=True,
            planning_root=Path("/test/path"),
        )

        # Convert to dict
        settings_dict = original.model_dump()

        # Verify dict structure
        assert settings_dict["host"] == "test-host"
        assert settings_dict["port"] == 9999
        assert settings_dict["debug_mode"] is True
        assert settings_dict["planning_root"] == Path("/test/path")

        # Recreate from dict
        restored = Settings(**settings_dict)

        # Verify restoration
        assert restored.host == original.host
        assert restored.port == original.port
        assert restored.debug_mode == original.debug_mode
        assert restored.planning_root == original.planning_root

    def test_settings_model_config(self) -> None:
        """Test Settings model configuration behavior."""
        settings = Settings()

        # Verify environment prefix is configured
        assert settings.model_config.get("env_prefix") == "MCP_"
        assert settings.model_config.get("case_sensitive") is False
        assert settings.model_config.get("validate_default") is True
