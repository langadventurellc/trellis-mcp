"""Tests for configuration loader functionality."""

from __future__ import annotations

from pathlib import Path
from typing import cast

import pytest
import yaml
from pydantic.fields import FieldInfo

from trellis_mcp.loader import (
    ConfigLoader,
    TomlConfigSettingsSource,
    YamlConfigSettingsSource,
)
from trellis_mcp.settings import Settings


class TestYamlConfigSettingsSource:
    """Test YAML configuration settings source."""

    def test_load_valid_yaml(self, temp_dir: Path) -> None:
        """Test loading valid YAML configuration."""
        config_file = temp_dir / "config.yaml"
        config_data = {
            "host": "0.0.0.0",
            "port": 9000,
            "log_level": "DEBUG",
            "debug_mode": True,
        }

        with open(config_file, "w") as f:
            yaml.safe_dump(config_data, f)

        source = YamlConfigSettingsSource(Settings, config_file)
        result = source()

        assert result == config_data

    def test_load_missing_file(self, temp_dir: Path) -> None:
        """Test graceful handling of missing YAML file."""
        config_file = temp_dir / "missing.yaml"
        source = YamlConfigSettingsSource(Settings, config_file)
        result = source()

        assert result == {}

    def test_load_empty_yaml(self, temp_dir: Path) -> None:
        """Test loading empty YAML file."""
        config_file = temp_dir / "empty.yaml"
        config_file.write_text("")

        source = YamlConfigSettingsSource(Settings, config_file)
        result = source()

        assert result == {}

    def test_load_invalid_yaml(self, temp_dir: Path) -> None:
        """Test error handling for invalid YAML."""
        config_file = temp_dir / "invalid.yaml"
        config_file.write_text("invalid: yaml: content: [")

        source = YamlConfigSettingsSource(Settings, config_file)

        with pytest.raises(ValueError, match="Invalid YAML"):
            source()

    def test_get_field_value(self, temp_dir: Path) -> None:
        """Test getting specific field values."""
        config_file = temp_dir / "config.yaml"
        config_data = {"host": "0.0.0.0", "port": 9000}

        with open(config_file, "w") as f:
            yaml.safe_dump(config_data, f)

        source = YamlConfigSettingsSource(Settings, config_file)

        # Test existing field
        value, field_name, found = source.get_field_value(cast(FieldInfo, None), "host")
        assert value == "0.0.0.0"
        assert field_name == "host"
        assert found is True

        # Test missing field
        value, field_name, found = source.get_field_value(cast(FieldInfo, None), "missing")
        assert value is None
        assert field_name == "missing"
        assert found is False


class TestTomlConfigSettingsSource:
    """Test TOML configuration settings source."""

    def test_load_valid_toml(self, temp_dir: Path) -> None:
        """Test loading valid TOML configuration."""
        config_file = temp_dir / "config.toml"
        config_content = """
host = "0.0.0.0"
port = 9000
log_level = "DEBUG"
debug_mode = true
"""
        config_file.write_text(config_content)

        source = TomlConfigSettingsSource(Settings, config_file)
        result = source()

        expected = {
            "host": "0.0.0.0",
            "port": 9000,
            "log_level": "DEBUG",
            "debug_mode": True,
        }
        assert result == expected

    def test_load_missing_file(self, temp_dir: Path) -> None:
        """Test graceful handling of missing TOML file."""
        config_file = temp_dir / "missing.toml"
        source = TomlConfigSettingsSource(Settings, config_file)
        result = source()

        assert result == {}

    def test_load_invalid_toml(self, temp_dir: Path) -> None:
        """Test error handling for invalid TOML."""
        config_file = temp_dir / "invalid.toml"
        config_file.write_text("invalid toml [content")

        source = TomlConfigSettingsSource(Settings, config_file)

        with pytest.raises(ValueError, match="Invalid TOML"):
            source()

    def test_get_field_value(self, temp_dir: Path) -> None:
        """Test getting specific field values."""
        config_file = temp_dir / "config.toml"
        config_content = """
host = "0.0.0.0"
port = 9000
"""
        config_file.write_text(config_content)

        source = TomlConfigSettingsSource(Settings, config_file)

        # Test existing field
        value, field_name, found = source.get_field_value(cast(FieldInfo, None), "host")
        assert value == "0.0.0.0"
        assert field_name == "host"
        assert found is True

        # Test missing field
        value, field_name, found = source.get_field_value(cast(FieldInfo, None), "missing")
        assert value is None
        assert field_name == "missing"
        assert found is False


class TestConfigLoader:
    """Test configuration loader main functionality."""

    def test_load_settings_yaml(self, temp_dir: Path) -> None:
        """Test loading settings from YAML file."""
        config_file = temp_dir / "config.yaml"
        config_data = {"host": "0.0.0.0", "port": 9000, "log_level": "DEBUG"}

        with open(config_file, "w") as f:
            yaml.safe_dump(config_data, f)

        loader = ConfigLoader()
        settings = loader.load_settings(config_file)

        assert settings.host == "0.0.0.0"
        assert settings.port == 9000
        assert settings.log_level == "DEBUG"

    def test_load_settings_toml(self, temp_dir: Path) -> None:
        """Test loading settings from TOML file."""
        config_file = temp_dir / "config.toml"
        config_content = """
host = "0.0.0.0"
port = 9000
log_level = "DEBUG"
"""
        config_file.write_text(config_content)

        loader = ConfigLoader()
        settings = loader.load_settings(config_file)

        assert settings.host == "0.0.0.0"
        assert settings.port == 9000
        assert settings.log_level == "DEBUG"

    def test_load_settings_no_file(self) -> None:
        """Test loading settings without config file (env vars only)."""
        loader = ConfigLoader()
        settings = loader.load_settings()

        # Should use default values
        assert settings.host == "127.0.0.1"
        assert settings.port == 8080
        assert settings.log_level == "INFO"

    def test_cli_overrides(self, temp_dir: Path) -> None:
        """Test CLI argument overrides (highest precedence)."""
        config_file = temp_dir / "config.yaml"
        config_data = {"host": "0.0.0.0", "port": 9000}

        with open(config_file, "w") as f:
            yaml.safe_dump(config_data, f)

        loader = ConfigLoader()
        settings = loader.load_settings(config_file, host="10.0.0.1", port=8888)

        # CLI overrides should take precedence
        assert settings.host == "10.0.0.1"
        assert settings.port == 8888

    def test_env_var_precedence(self, temp_dir: Path, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test environment variable precedence over config file."""
        config_file = temp_dir / "config.yaml"
        config_data = {"host": "0.0.0.0", "port": 9000}

        with open(config_file, "w") as f:
            yaml.safe_dump(config_data, f)

        # Set environment variable
        monkeypatch.setenv("MCP_HOST", "192.168.1.1")

        loader = ConfigLoader()
        settings = loader.load_settings(config_file)

        # Env var should override config file
        assert settings.host == "192.168.1.1"
        assert settings.port == 9000  # From config file

    def test_auto_detect_yaml(self, temp_dir: Path) -> None:
        """Test auto-detection of YAML file."""
        config_file = temp_dir / "config.yaml"
        config_data = {"host": "0.0.0.0"}

        with open(config_file, "w") as f:
            yaml.safe_dump(config_data, f)

        loader = ConfigLoader()
        # Use base name without extension
        settings = loader.load_settings(temp_dir / "config")

        assert settings.host == "0.0.0.0"

    def test_auto_detect_toml(self, temp_dir: Path) -> None:
        """Test auto-detection of TOML file."""
        config_file = temp_dir / "config.toml"
        config_content = 'host = "0.0.0.0"'
        config_file.write_text(config_content)

        loader = ConfigLoader()
        # Use base name without extension
        settings = loader.load_settings(temp_dir / "config")

        assert settings.host == "0.0.0.0"

    def test_auto_detect_yaml_preference(self, temp_dir: Path) -> None:
        """Test that YAML is preferred when both YAML and TOML exist."""
        yaml_file = temp_dir / "config.yaml"
        toml_file = temp_dir / "config.toml"

        yaml_data = {"host": "yaml-host"}
        with open(yaml_file, "w") as f:
            yaml.safe_dump(yaml_data, f)

        toml_content = 'host = "toml-host"'
        toml_file.write_text(toml_content)

        loader = ConfigLoader()
        settings = loader.load_settings(temp_dir / "config")

        # YAML should be preferred
        assert settings.host == "yaml-host"

    def test_unsupported_format(self) -> None:
        """Test error for unsupported config file format."""
        loader = ConfigLoader()

        with pytest.raises(ValueError, match="Unsupported config format"):
            loader.load_settings("config.json")

    def test_find_config_file(self, temp_dir: Path) -> None:
        """Test finding configuration files in search directories."""
        config_dir = temp_dir / "subdir"
        config_dir.mkdir()
        config_file = config_dir / "trellis-mcp.yaml"
        config_file.write_text("host: test")

        loader = ConfigLoader()
        found_file = loader.find_config_file(search_dirs=[temp_dir, config_dir])

        # Resolve paths to handle symlinks (macOS temp dirs)
        assert found_file is not None
        assert found_file.resolve() == config_file.resolve()

    def test_find_config_file_not_found(self, temp_dir: Path) -> None:
        """Test finding configuration files when none exist."""
        loader = ConfigLoader()
        found_file = loader.find_config_file(search_dirs=[temp_dir])

        assert found_file is None

    def test_find_config_file_precedence(self, temp_dir: Path) -> None:
        """Test config file name precedence."""
        config_dir = temp_dir

        # Create files in order of precedence
        config1 = config_dir / "trellis-mcp.yaml"
        config2 = config_dir / "config.yaml"

        config2.write_text("host: config")
        config1.write_text("host: trellis-mcp")

        loader = ConfigLoader()
        found_file = loader.find_config_file(search_dirs=[config_dir])

        # trellis-mcp should be found first (resolve paths for symlinks)
        assert found_file is not None
        assert found_file.resolve() == config1.resolve()

    def test_path_types(self, temp_dir: Path) -> None:
        """Test that both string and Path objects work."""
        config_file = temp_dir / "config.yaml"
        config_data = {"host": "0.0.0.0"}

        with open(config_file, "w") as f:
            yaml.safe_dump(config_data, f)

        loader = ConfigLoader()

        # Test with Path object
        settings1 = loader.load_settings(config_file)
        assert settings1.host == "0.0.0.0"

        # Test with string
        settings2 = loader.load_settings(str(config_file))
        assert settings2.host == "0.0.0.0"


class TestIntegrationScenarios:
    """Test real-world integration scenarios."""

    def test_complete_hierarchical_loading(
        self, temp_dir: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test complete hierarchical configuration loading scenario."""
        # 1. Create config file
        config_file = temp_dir / "config.yaml"
        config_data = {
            "host": "config-host",
            "port": 9000,
            "log_level": "DEBUG",
            "debug_mode": True,
        }

        with open(config_file, "w") as f:
            yaml.safe_dump(config_data, f)

        # 2. Set environment variables (should override config file)
        monkeypatch.setenv("MCP_HOST", "env-host")
        monkeypatch.setenv("MCP_LOG_LEVEL", "WARNING")

        # 3. Provide CLI overrides (should override everything)
        loader = ConfigLoader()
        settings = loader.load_settings(config_file, host="cli-host", port=7777)

        # Verify precedence: CLI > Env > Config > Defaults
        assert settings.host == "cli-host"  # CLI override
        assert settings.port == 7777  # CLI override
        assert settings.log_level == "WARNING"  # Env var override
        assert settings.debug_mode is True  # From config file
        assert settings.default_transport == "stdio"  # Default value

    def test_missing_config_with_env_vars(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test configuration when file is missing but env vars exist."""
        monkeypatch.setenv("MCP_HOST", "env-host")
        monkeypatch.setenv("MCP_PORT", "9999")
        monkeypatch.setenv("MCP_DEBUG_MODE", "true")

        loader = ConfigLoader()
        settings = loader.load_settings("nonexistent.yaml")

        # Should use env vars and defaults
        assert settings.host == "env-host"
        assert settings.port == 9999
        assert settings.debug_mode is True
        assert settings.log_level == "INFO"  # Default

    def test_type_conversion(self, temp_dir: Path) -> None:
        """Test that types are properly converted from config files."""
        config_file = temp_dir / "config.yaml"
        config_data = {
            "port": "8888",  # String that should become int
            "debug_mode": "true",  # String that should become bool
            "max_file_size_mb": "20",  # String that should become int
        }

        with open(config_file, "w") as f:
            yaml.safe_dump(config_data, f)

        loader = ConfigLoader()
        settings = loader.load_settings(config_file)

        # Pydantic should handle type conversion
        assert isinstance(settings.port, int)
        assert settings.port == 8888
        assert isinstance(settings.debug_mode, bool)
        assert settings.debug_mode is True
        assert isinstance(settings.max_file_size_mb, int)
        assert settings.max_file_size_mb == 20
