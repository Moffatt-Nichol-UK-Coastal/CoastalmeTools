"""Abstract base class for configuration adapters.

This module defines the ConfigAdapter interface that all configuration
format handlers must implement, enabling format-agnostic configuration
management throughout the toolkit.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional

from ..core.models import ConfigFormat
from ..core.exceptions import ConfigError


class ConfigAdapter(ABC):
    """Abstract base for configuration file adapters.

    This class defines the interface for all configuration adapters,
    ensuring consistent behavior across different file formats (.dat, .yaml, etc.).

    Attributes:
        file_path: Path to the configuration file
        _data: Internal dictionary storing configuration key-value pairs
        _modified: Dictionary tracking which keys have been modified
    """

    def __init__(self, file_path: Path):
        """Initialize the configuration adapter.

        Args:
            file_path: Path to configuration file
        """
        self.file_path = Path(file_path)
        self._data: Dict[str, Any] = {}
        self._modified: Dict[str, bool] = {}

    @abstractmethod
    def load(self) -> None:
        """Load configuration from file.

        Reads the configuration file and populates internal data structures.

        Raises:
            ConfigNotFoundError: If file doesn't exist
            ConfigParseError: If file cannot be parsed
        """
        pass

    @abstractmethod
    def save(self) -> None:
        """Save configuration to file.

        Writes the current configuration state back to the file,
        preserving format-specific features like comments.

        Raises:
            ConfigError: If file cannot be written
        """
        pass

    @abstractmethod
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get configuration value by exact key match.

        Args:
            key: Configuration key (exact match)
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        pass

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Set configuration value for key.

        Args:
            key: Configuration key
            value: Value to set

        Raises:
            KeyError: If key doesn't exist in configuration
        """
        pass

    @abstractmethod
    def find(self, query: str, case_sensitive: bool = False) -> Any:
        """Find configuration value by partial key match.

        Supports space-separated queries for progressive narrowing.
        Compatible with legacy tools.find_var() behavior.

        Args:
            query: Search query (space-separated for multiple terms)
            case_sensitive: Whether to perform case-sensitive search

        Returns:
            Configuration value

        Raises:
            KeyError: If no matches or multiple matches found
        """
        pass

    @property
    @abstractmethod
    def format(self) -> ConfigFormat:
        """Return configuration format.

        Returns:
            ConfigFormat enum value (DAT or YAML)
        """
        pass

    @property
    def is_modified(self) -> bool:
        """Check if configuration has been modified.

        Returns:
            True if any values have been modified since load
        """
        return any(self._modified.values())

    @property
    def exists(self) -> bool:
        """Check if configuration file exists.

        Returns:
            True if file exists on filesystem
        """
        return self.file_path.exists()

    def __getitem__(self, key: str) -> Any:
        """Dictionary-style access for reading values.

        Args:
            key: Configuration key

        Returns:
            Configuration value
        """
        return self.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        """Dictionary-style access for setting values.

        Args:
            key: Configuration key
            value: Value to set
        """
        self.set(key, value)

    def __contains__(self, key: str) -> bool:
        """Check if key exists in configuration.

        Args:
            key: Configuration key

        Returns:
            True if key exists
        """
        return key in self._data

    def keys(self) -> list:
        """Get all configuration keys.

        Returns:
            List of configuration keys
        """
        return list(self._data.keys())

    def values(self) -> list:
        """Get all configuration values.

        Returns:
            List of configuration values
        """
        return list(self._data.values())

    def items(self) -> list:
        """Get all configuration key-value pairs.

        Returns:
            List of (key, value) tuples
        """
        return list(self._data.items())
