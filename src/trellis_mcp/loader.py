"""Configuration loader for Trellis MCP Server.

Provides hierarchical configuration loading with support for YAML and TOML
files, environment variables, and CLI arguments. Maintains the precedence
chain: defaults → file → env → CLI.
"""

from __future__ import annotations

import tomllib
from pathlib import Path
from typing import Any, Dict, Type

import yaml
from pydantic.fields import FieldInfo
from pydantic_settings import BaseSettings, PydanticBaseSettingsSource

from .settings import Settings


class YamlConfigSettingsSource(PydanticBaseSettingsSource):
    """Pydantic settings source for YAML configuration files.

    Loads configuration from YAML files using safe_load for security.
    Gracefully handles missing files by returning empty configuration.
    """

    def __init__(self, settings_cls: Type[BaseSettings], yaml_file: str | Path):
        super().__init__(settings_cls)
        self.yaml_file = Path(yaml_file)

    def get_field_value(self, field: FieldInfo, field_name: str) -> tuple[Any, str, bool]:
        """Get field value from YAML file."""
        file_content = self._read_file()
        if file_content is None:
            return None, field_name, False

        # Handle nested field names (convert from env var format)
        yaml_field_name = field_name.lower()
        if yaml_field_name in file_content:
            return file_content[yaml_field_name], field_name, True

        return None, field_name, False

    def prepare_field_value(
        self,
        field_name: str,
        field: FieldInfo,
        value: Any,
        value_is_complex: bool,
    ) -> Any:
        """Prepare field value for settings."""
        return value

    def __call__(self) -> Dict[str, Any]:
        """Load entire YAML file configuration."""
        return self._read_file() or {}

    def _read_file(self) -> Dict[str, Any] | None:
        """Read and parse YAML file.

        Returns:
            Dictionary of configuration values or None if file doesn't exist.

        Raises:
            yaml.YAMLError: If YAML parsing fails.
            OSError: If file cannot be read.
        """
        if not self.yaml_file.exists():
            return None

        try:
            with open(self.yaml_file, "r", encoding="utf-8") as file:
                return yaml.safe_load(file) or {}
        except yaml.YAMLError as e:
            raise ValueError(f"Invalid YAML in {self.yaml_file}: {e}") from e
        except OSError as e:
            raise OSError(f"Cannot read config file {self.yaml_file}: {e}") from e

    def __repr__(self) -> str:
        return f"YamlConfigSettingsSource(yaml_file={self.yaml_file!r})"


class TomlConfigSettingsSource(PydanticBaseSettingsSource):
    """Pydantic settings source for TOML configuration files.

    Loads configuration from TOML files using built-in tomllib parser.
    Gracefully handles missing files by returning empty configuration.
    """

    def __init__(self, settings_cls: Type[BaseSettings], toml_file: str | Path):
        super().__init__(settings_cls)
        self.toml_file = Path(toml_file)

    def get_field_value(self, field: FieldInfo, field_name: str) -> tuple[Any, str, bool]:
        """Get field value from TOML file."""
        file_content = self._read_file()
        if file_content is None:
            return None, field_name, False

        # Handle nested field names (convert from env var format)
        toml_field_name = field_name.lower()
        if toml_field_name in file_content:
            return file_content[toml_field_name], field_name, True

        return None, field_name, False

    def prepare_field_value(
        self,
        field_name: str,
        field: FieldInfo,
        value: Any,
        value_is_complex: bool,
    ) -> Any:
        """Prepare field value for settings."""
        return value

    def __call__(self) -> Dict[str, Any]:
        """Load entire TOML file configuration."""
        return self._read_file() or {}

    def _read_file(self) -> Dict[str, Any] | None:
        """Read and parse TOML file.

        Returns:
            Dictionary of configuration values or None if file doesn't exist.

        Raises:
            tomllib.TOMLDecodeError: If TOML parsing fails.
            OSError: If file cannot be read.
        """
        if not self.toml_file.exists():
            return None

        try:
            with open(self.toml_file, "rb") as file:
                return tomllib.load(file)
        except tomllib.TOMLDecodeError as e:
            raise ValueError(f"Invalid TOML in {self.toml_file}: {e}") from e
        except OSError as e:
            raise OSError(f"Cannot read config file {self.toml_file}: {e}") from e

    def __repr__(self) -> str:
        return f"TomlConfigSettingsSource(toml_file={self.toml_file!r})"


class ConfigLoader:
    """Configuration loader for Trellis MCP Server.

    Provides hierarchical configuration loading with support for YAML/TOML
    files, environment variables, and CLI overrides. Follows the precedence
    chain: defaults → file → env → CLI (highest precedence).

    Example:
        loader = ConfigLoader()
        settings = loader.load_settings('config.yaml')

        # Or with TOML
        settings = loader.load_settings('config.toml')

        # Auto-detect format
        settings = loader.load_settings('config')  # tries .yaml, .toml
    """

    def load_settings(
        self,
        config_file: str | Path | None = None,
        **cli_overrides: Any,
    ) -> Settings:
        """Load settings with hierarchical configuration.

        Args:
            config_file: Path to YAML or TOML config file. If None, only uses
                environment variables and CLI overrides. If path without extension,
                tries .yaml then .toml.
            **cli_overrides: Direct CLI argument overrides (highest precedence).

        Returns:
            Settings instance with loaded configuration.

        Raises:
            ValueError: If config file format is unsupported or invalid.
            OSError: If config file cannot be read.
        """
        config_path = self._resolve_config_path(config_file)

        # Create custom settings class with file source
        class ConfigurableSettings(Settings):
            @classmethod
            def settings_customise_sources(
                cls,
                settings_cls: Type[BaseSettings],
                init_settings: PydanticBaseSettingsSource,
                env_settings: PydanticBaseSettingsSource,
                dotenv_settings: PydanticBaseSettingsSource,
                file_secret_settings: PydanticBaseSettingsSource,
            ) -> tuple[PydanticBaseSettingsSource, ...]:
                """Customize settings sources for hierarchical loading.

                Precedence order (highest to lowest):
                1. CLI overrides (init_settings)
                2. Environment variables
                3. Config file (YAML/TOML)
                4. Default values (implicit)
                """
                sources = [init_settings, env_settings]

                if config_path:
                    if config_path.suffix.lower() == ".yaml":
                        sources.append(YamlConfigSettingsSource(settings_cls, config_path))
                    elif config_path.suffix.lower() == ".toml":
                        sources.append(TomlConfigSettingsSource(settings_cls, config_path))

                return tuple(sources)

        return ConfigurableSettings(**cli_overrides)

    def _resolve_config_path(self, config_file: str | Path | None) -> Path | None:
        """Resolve configuration file path with auto-detection.

        Args:
            config_file: Path to config file or None.

        Returns:
            Resolved Path object or None if no config file.

        Raises:
            ValueError: If file format is unsupported.
        """
        if config_file is None:
            return None

        path = Path(config_file)

        # If no extension, try auto-detection
        if not path.suffix:
            yaml_path = path.with_suffix(".yaml")
            toml_path = path.with_suffix(".toml")

            if yaml_path.exists():
                return yaml_path
            elif toml_path.exists():
                return toml_path
            else:
                # Return YAML path for better error messages
                return yaml_path

        # Validate supported formats
        supported_formats = {".yaml", ".yml", ".toml"}
        if path.suffix.lower() not in supported_formats:
            raise ValueError(
                f"Unsupported config format '{path.suffix}'. "
                f"Supported formats: {', '.join(supported_formats)}"
            )

        return path
