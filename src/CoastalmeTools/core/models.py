"""Core data models for CoastalmeTools.

This module defines the fundamental data structures used throughout the toolkit,
including project paths, simulation metadata, and result containers.
"""

from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict
from enum import Enum


class ConfigFormat(Enum):
    """Configuration file format enumeration."""

    DAT = "dat"
    YAML = "yaml"


@dataclass
class ProjectPaths:
    """Paths for a CoastalME project.

    Attributes:
        ini_file: Path to the .ini file that points to the main config
        exec_path: Execution directory (where CoastalME runs)
        in_path: Input directory containing config and input files
        out_path: Output directory for simulation results
        config_file: Main configuration file (.dat or .yaml)
    """

    ini_file: Path
    exec_path: Path
    in_path: Path
    out_path: Path
    config_file: Path

    def __post_init__(self):
        """Convert all paths to Path objects."""
        self.ini_file = Path(self.ini_file)
        self.exec_path = Path(self.exec_path)
        self.in_path = Path(self.in_path)
        self.out_path = Path(self.out_path)
        self.config_file = Path(self.config_file)

    @property
    def exists(self) -> bool:
        """Check if required project files exist.

        Returns:
            True if both ini_file and config_file exist
        """
        return self.ini_file.exists() and self.config_file.exists()

    @property
    def is_valid(self) -> bool:
        """Validate that all paths are set and ini_file exists.

        Returns:
            True if project structure is valid
        """
        return (
            self.ini_file is not None
            and self.ini_file.exists()
            and self.config_file is not None
        )


@dataclass
class SimulationMetadata:
    """Metadata about a simulation run.

    Attributes:
        start_date: Simulation start datetime
        duration_seconds: Total simulation duration in seconds
        timestep_seconds: Timestep length in seconds
        save_times: List of datetime objects when outputs are saved
        config_format: Format of the configuration file (DAT or YAML)
    """

    start_date: datetime
    duration_seconds: float
    timestep_seconds: float
    save_times: List[datetime]
    config_format: ConfigFormat

    @property
    def num_timesteps(self) -> int:
        """Calculate number of timesteps.

        Returns:
            Number of timesteps in the simulation
        """
        if self.timestep_seconds > 0:
            return int(self.duration_seconds / self.timestep_seconds)
        return len(self.save_times)

    @property
    def num_saves(self) -> int:
        """Get number of save times.

        Returns:
            Number of times output is saved
        """
        return len(self.save_times)


@dataclass
class SimulationResult:
    """Result of a simulation execution.

    Attributes:
        success: True if simulation completed without errors
        return_code: Process return code from CoastalME executable
        log_file: Path to log file (if found)
        errors: Dictionary mapping line numbers to error messages
        warnings: Dictionary mapping line numbers to warning messages
        output_files: List of output file paths generated
        execution_time: Duration of simulation in seconds
    """

    success: bool
    return_code: int
    log_file: Optional[Path] = None
    errors: Dict[int, str] = field(default_factory=dict)
    warnings: Dict[int, str] = field(default_factory=dict)
    output_files: List[Path] = field(default_factory=list)
    execution_time: float = 0.0

    @property
    def crashed(self) -> bool:
        """Check if simulation crashed.

        Returns:
            True if simulation failed
        """
        return not self.success

    @property
    def has_errors(self) -> bool:
        """Check if errors were logged.

        Returns:
            True if any errors were found in log file
        """
        return len(self.errors) > 0

    @property
    def has_warnings(self) -> bool:
        """Check if warnings were logged.

        Returns:
            True if any warnings were found in log file
        """
        return len(self.warnings) > 0

    @property
    def num_outputs(self) -> int:
        """Count number of output files generated.

        Returns:
            Number of output files
        """
        return len(self.output_files)
