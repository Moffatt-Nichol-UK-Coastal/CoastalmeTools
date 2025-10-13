"""Configuration adapter for CoastalME YAML files.

This module handles the modern YAML format for CoastalME configuration,
supporting nested structures and improved readability.
"""

import yaml
import pandas as pd
from pathlib import Path
from typing import Any, Optional, Dict
import re

from .base import ConfigAdapter
from ..core.models import ConfigFormat
from ..core.exceptions import ConfigParseError, ConfigNotFoundError, ConfigError


class YamlConfig(ConfigAdapter):
    """Configuration adapter for YAML files.

    The YAML format supports nested structures with sections:

    Example:
        simulation:
          start_date: "00-00-00 01/01/2020"
          duration: "1 year"
        output:
          folder: "out"

    Keys are flattened for compatibility with DAT format queries.
    Nested keys are joined with underscores (e.g., "median_sizes_fine").

    Attributes:
        _raw_yaml: Original YAML structure as loaded from file
        _df: Internal DataFrame for compatibility with update operations
    """

    def __init__(self, file_path: Path):
        """Initialize YAML configuration adapter.

        Args:
            file_path: Path to .yaml or .yml file
        """
        super().__init__(file_path)
        self._raw_yaml: Optional[Dict] = None
        self._df: Optional[pd.DataFrame] = None

    @property
    def format(self) -> ConfigFormat:
        """Return configuration format.

        Returns:
            ConfigFormat.YAML
        """
        return ConfigFormat.YAML

    def load(self) -> None:
        """Load YAML configuration file.

        Parses the YAML file and flattens nested structures into a DataFrame
        for compatibility with the query interface.

        Raises:
            ConfigNotFoundError: If file doesn't exist
            ConfigParseError: If file cannot be parsed
        """
        if not self.file_path.exists():
            raise ConfigNotFoundError(f"Config file not found: {self.file_path}")

        try:
            with open(self.file_path, "r") as f:
                self._raw_yaml = yaml.safe_load(f)

            # Flatten YAML into DataFrame structure
            data = {"section": [], "key": [], "value": []}
            self._flatten_yaml(self._raw_yaml, data)

            self._df = pd.DataFrame(data)
            self._df["type"] = "setting"
            self._df["modified"] = False

            # Build data dictionary from flattened structure
            self._data = dict(zip(self._df["key"], self._df["value"]))

        except yaml.YAMLError as e:
            raise ConfigParseError(f"Error parsing YAML file: {e}")
        except Exception as e:
            raise ConfigParseError(f"Error loading YAML: {e}")

    def save(self) -> None:
        """Save YAML configuration file.

        Reconstructs the nested YAML structure from the flattened DataFrame
        and writes it back to file with proper formatting.

        Raises:
            ConfigError: If no configuration loaded
        """
        if self._df is None:
            raise ConfigError("No configuration loaded")

        # Reconstruct nested YAML from flat DataFrame
        config = self._reconstruct_yaml(self._df)

        # Write with nice formatting
        with open(self.file_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(
                config,
                f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
                width=120,
                indent=2,
            )

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get value by exact key match.

        Args:
            key: Configuration key (exact match)
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set value for key.

        Args:
            key: Configuration key
            value: Value to set

        Raises:
            KeyError: If key doesn't exist in configuration
        """
        if self._df is None:
            raise ConfigError("No configuration loaded")

        # Find the key in DataFrame
        mask = self._df["key"] == key
        if not mask.any():
            raise KeyError(f"Key not found: {key}")

        # Update DataFrame and internal dict
        self._df.loc[mask, "value"] = value
        self._df.loc[mask, "modified"] = True
        self._data[key] = value
        self._modified[key] = True

    def find(self, query: str, case_sensitive: bool = False) -> Any:
        """Find value by partial key match.

        Uses the same progressive narrowing algorithm as DatConfig for
        compatibility with legacy code.

        Args:
            query: Search query (space-separated for multiple terms)
            case_sensitive: Whether to perform case-sensitive search

        Returns:
            Configuration value (with trailing comments stripped)

        Raises:
            KeyError: If no matches or multiple matches found
        """
        # Split query into individual terms
        queries = query.split() if isinstance(query, str) else query

        # Start with all keys
        results = self._data.copy()

        # Progressive narrowing: each term must match
        for q in queries:
            flags = 0 if case_sensitive else re.I
            results = {k: v for k, v in results.items() if re.search(q, k, flags)}

            # If we're down to one match, return it
            if len(results) == 1:
                value = next(iter(results.values()))
                # Strip trailing comments (after ';')
                if isinstance(value, str) and ";" in value:
                    value = value.partition(";")[0].strip()
                return value

        # Check results
        if len(results) == 0:
            raise KeyError(f"No matches for: {query}")
        if len(results) > 1:
            raise KeyError(f"Multiple matches for '{query}': {list(results.keys())}")

        # Return single match
        value = next(iter(results.values()))
        if isinstance(value, str) and ";" in value:
            value = value.partition(";")[0].strip()
        return value

    def _flatten_yaml(self, data: Dict, output: Dict, section: str = "") -> None:
        """Recursively flatten nested YAML structure.

        Converts nested dictionaries into flat key-value pairs with section
        information. Handles up to 3 levels of nesting.

        Args:
            data: Dictionary to flatten
            output: Output dictionary to populate (modified in-place)
            section: Current section name (for recursion)
        """
        for key, value in data.items():
            if isinstance(value, dict):
                # Nested structure - check depth
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, dict):
                        # 3-level nesting: section -> parent_key -> child_key
                        for sub_sub_key, sub_sub_value in sub_value.items():
                            output["section"].append(key)
                            output["key"].append(f"{sub_key}_{sub_sub_key}")
                            output["value"].append(sub_sub_value)
                    else:
                        # 2-level nesting: section -> key
                        output["section"].append(key)
                        output["key"].append(sub_key)
                        output["value"].append(sub_value)
            else:
                # Flat structure - top-level key
                output["section"].append(section)
                output["key"].append(key)
                output["value"].append(value)

    def _reconstruct_yaml(self, df: pd.DataFrame) -> Dict:
        """Reconstruct nested YAML from flat DataFrame.

        Intelligently detects compound keys (e.g., "median_sizes_fine") and
        rebuilds nested dictionary structures.

        Args:
            df: DataFrame with section, key, value columns

        Returns:
            Nested dictionary ready for YAML serialization
        """
        config = {}

        # First pass: identify which keys should be nested
        nested_keys = {}  # {(section, parent_key): [child_keys]}

        for section in df["section"].unique():
            section_rows = df[df["section"] == section]

            # Look for keys that could be nested (contain underscore)
            for _, row in section_rows.iterrows():
                key = row["key"]
                if pd.isna(key) or key == "":
                    continue

                if "_" in key:
                    # Split on first underscore to get potential parent
                    parts = key.split("_", 1)
                    parent_key = parts[0]
                    child_key = parts[1]

                    # Count how many keys share this parent prefix
                    same_parent = section_rows[
                        section_rows["key"].str.startswith(parent_key + "_", na=False)
                    ]

                    # If multiple keys share prefix, treat as nested
                    if len(same_parent) > 1:
                        key_tuple = (section, parent_key)
                        if key_tuple not in nested_keys:
                            nested_keys[key_tuple] = []
                        nested_keys[key_tuple].append(child_key)

        # Second pass: build the config dictionary
        for _, row in df.iterrows():
            section = row["section"]
            key = row["key"]
            value = row["value"]

            # Skip invalid rows
            if pd.isna(key) or key == "":
                continue

            # Handle flat structure (no section - top level)
            if section == "" or pd.isna(section):
                config[key] = value
                continue

            # Ensure section exists
            if section not in config:
                config[section] = {}

            # Check if this key should be nested
            is_nested = False
            if "_" in key:
                parent_key = key.split("_", 1)[0]
                child_key = key.split("_", 1)[1]

                if (section, parent_key) in nested_keys:
                    # This is a nested key
                    is_nested = True
                    if parent_key not in config[section]:
                        config[section][parent_key] = {}
                    config[section][parent_key][child_key] = value

            if not is_nested:
                # Simple key under section
                config[section][key] = value

        return config
