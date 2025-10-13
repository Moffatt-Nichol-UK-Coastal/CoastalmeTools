"""Configuration management for CoastalmeTools.

This module provides a unified interface for working with different configuration
file formats (.dat and .yaml) through the ConfigAdapter abstraction.

Example:
    >>> from CoastalmeTools.config import load_config
    >>> config = load_config(Path("cme.dat"))
    >>> basement = config.find("basement")
    >>> config.set("output folder", "new_out")
    >>> config.save()
"""

from .base import ConfigAdapter
from .dat_config import DatConfig
from .yaml_config import YamlConfig
from ..core.models import ConfigFormat
from ..core.exceptions import ConfigError
from pathlib import Path


def load_config(file_path: Path) -> ConfigAdapter:
    """Factory function to load configuration file.

    Automatically detects the file format based on extension and returns
    the appropriate ConfigAdapter implementation.

    Args:
        file_path: Path to configuration file (.dat, .yaml, or .yml)

    Returns:
        ConfigAdapter instance (DatConfig or YamlConfig) with loaded configuration

    Raises:
        ConfigError: If file format is not supported
        ConfigNotFoundError: If file doesn't exist
        ConfigParseError: If file cannot be parsed

    Example:
        >>> config = load_config(Path("scenario.dat"))
        >>> print(config.format)  # ConfigFormat.DAT
        >>> value = config.get("basement")
        >>> print(value)  # "in/basement.tif"
    """
    file_path = Path(file_path)
    suffix = file_path.suffix.lower()

    # Select appropriate adapter based on file extension
    if suffix == ".dat":
        config = DatConfig(file_path)
    elif suffix in [".yaml", ".yml"]:
        config = YamlConfig(file_path)
    else:
        raise ConfigError(
            f"Unsupported config format: {suffix}. "
            f"Supported formats: .dat, .yaml, .yml"
        )

    # Load the configuration
    config.load()
    return config


__all__ = [
    "ConfigAdapter",
    "DatConfig",
    "YamlConfig",
    "load_config",
]
