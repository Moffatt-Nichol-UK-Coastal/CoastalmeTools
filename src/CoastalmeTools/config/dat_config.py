"""Configuration adapter for CoastalME .dat files.

This module handles the legacy .dat format used by CoastalME, which uses
a simple key:value syntax with semicolon comments.
"""

import re
import pandas as pd
from pathlib import Path
from typing import Any, Optional

from .base import ConfigAdapter
from ..core.models import ConfigFormat
from ..core.exceptions import ConfigParseError, ConfigNotFoundError


class DatConfig(ConfigAdapter):
    """Configuration adapter for .dat files.

    The .dat format uses a simple structure:
    - Lines starting with ';' or '#' are comments
    - Empty lines are preserved
    - Settings use 'key : value' format
    - Comments can appear after values (separated by ';')

    Attributes:
        _df: Internal DataFrame storing parsed file structure
    """

    def __init__(self, file_path: Path):
        """Initialize DAT configuration adapter.

        Args:
            file_path: Path to .dat file
        """
        super().__init__(file_path)
        self._df: Optional[pd.DataFrame] = None

    @property
    def format(self) -> ConfigFormat:
        """Return configuration format.

        Returns:
            ConfigFormat.DAT
        """
        return ConfigFormat.DAT

    def load(self) -> None:
        """Load .dat configuration file.

        Parses the .dat file into an internal DataFrame structure that
        preserves comments, blank lines, and formatting for write-back.

        Raises:
            ConfigNotFoundError: If file doesn't exist
            ConfigParseError: If file cannot be parsed
        """
        if not self.file_path.exists():
            raise ConfigNotFoundError(f"Config file not found: {self.file_path}")

        try:
            with open(self.file_path, "r") as f:
                lines = f.read().splitlines()

            # Create DataFrame from lines
            line_numbers = range(len(lines))
            self._df = pd.DataFrame(
                {"string": lines}, index=line_numbers
            )

            # Categorize lines
            self._df["type"] = "setting"

            # Identify comments (lines starting with ; or #)
            mask = (
                self._df.string.str.startswith(";") |
                self._df.string.str.startswith("#")
            )
            self._df.loc[mask, "type"] = "comment"

            # Identify blank lines
            self._df.loc[self._df.string == "", "type"] = "blank"

            # Initialize key, value, modified columns
            self._df["key"] = None
            self._df["value"] = None
            self._df["modified"] = False

            # Parse settings (non-comment, non-blank lines)
            mask = self._df.type == "setting"
            if mask.any():
                self._df.loc[mask, "key"] = self._df.loc[mask, "string"].map(
                    lambda x: self._parse_line(x)[0]
                )
                self._df.loc[mask, "value"] = self._df.loc[mask, "string"].map(
                    lambda x: self._parse_line(x)[1]
                )

            # Build data dictionary from settings
            settings_mask = self._df.type == "setting"
            keys = self._df.loc[settings_mask, "key"].values
            values = self._df.loc[settings_mask, "value"].values
            self._data = dict(zip(keys, values))

        except Exception as e:
            raise ConfigParseError(f"Error parsing .dat file: {e}")

    def save(self) -> None:
        """Save .dat configuration file.

        Writes the configuration back to file, preserving comments and
        formatting. Modified keys are regenerated with aligned spacing.

        Raises:
            ConfigError: If no configuration loaded
        """
        if self._df is None:
            from ..core.exceptions import ConfigError
            raise ConfigError("No configuration loaded")

        # Update strings for modified values with aligned formatting
        changed_mask = ~self._df.key.isnull()

        if changed_mask.any():
            # Calculate max key length for alignment
            valid_keys = [k for k in self._df["key"] if k is not None]
            if valid_keys:
                max_key_len = max(len(k) for k in valid_keys)

                # Regenerate string representation for all settings
                def format_row(row):
                    if pd.isna(row["key"]) or row["key"] is None:
                        return row["string"]
                    return f"{row['key']:{max_key_len}} : {row['value']}"

                self._df.loc[changed_mask, "string"] = self._df[changed_mask].apply(
                    format_row, axis=1
                )

        # Write to file
        out_lines = self._df["string"].to_list()
        with open(self.file_path, mode="wt", encoding="utf-8") as f:
            f.write("\n".join(out_lines))

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
            from ..core.exceptions import ConfigError
            raise ConfigError("No configuration loaded")

        # Find the key in DataFrame
        mask = self._df["key"] == key
        if not mask.any():
            raise KeyError(f"Key not found: {key}")

        # Update DataFrame and internal dict
        self._df.loc[mask, "value"] = str(value)
        self._df.loc[mask, "modified"] = True
        self._data[key] = str(value)
        self._modified[key] = True

    def find(self, query: str, case_sensitive: bool = False) -> Any:
        """Find value by partial key match.

        Supports space-separated queries for progressive narrowing, matching
        the behavior of the legacy tools.find_var() function.

        Args:
            query: Search query (space-separated for multiple terms)
            case_sensitive: Whether to perform case-sensitive search

        Returns:
            Configuration value (with trailing comments stripped)

        Raises:
            KeyError: If no matches or multiple matches found

        Examples:
            >>> config.find("basement")  # Matches "basement"
            'in/basement.tif'
            >>> config.find("start date")  # Matches "start date"
            '00-00-00 01/01/2020'
            >>> config.find("duration simulation")  # Progressive match
            '1 year'
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

        # Return single match (shouldn't reach here due to early return above)
        value = next(iter(results.values()))
        if isinstance(value, str) and ";" in value:
            value = value.partition(";")[0].strip()
        return value

    @staticmethod
    def _parse_line(line: str) -> tuple:
        """Parse key:value line.

        Args:
            line: Line string in 'key : value' format

        Returns:
            Tuple of (key, value). Empty strings if parsing fails.

        Examples:
            >>> DatConfig._parse_line("basement : in/basement.tif")
            ('basement', 'in/basement.tif')
            >>> DatConfig._parse_line("output folder  :  out")
            ('output folder', 'out')
        """
        # Split on colon
        parts = line.partition(":")
        # Remove the delimiter and strip whitespace
        parts = [x.strip() for x in parts if x != ":"]
        # Normalize multiple spaces to single space
        parts = [re.sub(r" +", " ", x) for x in parts]

        # Return tuple or empty strings
        if len(parts) == 2:
            return tuple(parts)
        return ("", "")
