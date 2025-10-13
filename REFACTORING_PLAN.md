# CoastalmeTools Refactoring Plan

**Date:** 2025-10-13
**Status:** Planning Phase
**Preferences:** Modular architecture (A), Best practices for config/error/testing, Breaking changes OK (C), Modern Python (A)

---

## 🎯 Goals

1. **Modular architecture** with clear separation of concerns
2. **Modern Python** (3.9+) with type hints, dataclasses, and pathlib
3. **Testable code** with both unit and integration tests
4. **Clean slate** - breaking changes are acceptable for better design
5. **Best practices** for config handling, error management, and data processing

---

## 📐 Proposed Architecture

### New Structure

```
CoastalmeTools/
├── src/CoastalmeTools/
│   ├── __init__.py              # Public API exports
│   ├── core/                    # Core domain models
│   │   ├── __init__.py
│   │   ├── simulation.py        # Simulation orchestrator (new Cme)
│   │   ├── config.py            # Configuration abstractions
│   │   ├── models.py            # Data models (dataclasses)
│   │   └── exceptions.py        # Custom exceptions
│   ├── config/                  # Configuration management
│   │   ├── __init__.py
│   │   ├── base.py              # ConfigAdapter ABC
│   │   ├── dat_config.py        # .dat file handler
│   │   ├── yaml_config.py       # .yaml file handler
│   │   └── validators.py        # Config validation
│   ├── execution/               # Simulation execution
│   │   ├── __init__.py
│   │   ├── runner.py            # Subprocess management
│   │   ├── monitor.py           # Real-time monitoring (moved)
│   │   └── log_parser.py        # Log file parsing
│   ├── results/                 # Result processing
│   │   ├── __init__.py
│   │   ├── collector.py         # File collection
│   │   ├── raster_processor.py  # NetCDF generation
│   │   ├── vector_processor.py  # GeoPackage generation
│   │   └── profile_processor.py # Profile plots
│   ├── preprocessing/           # Input preparation
│   │   ├── __init__.py
│   │   ├── basement_generator.py # Quick-start model (from xml2raster)
│   │   ├── wave_preprocessor.py  # Wave data handling (from hydro)
│   │   └── tide_preprocessor.py  # Tide data handling
│   ├── project/                 # Project manipulation (already good!)
│   │   ├── __init__.py
│   │   └── tools.py             # Existing project_tools.py
│   ├── interactive/             # Interactive features
│   │   ├── __init__.py
│   │   ├── preflight.py         # Preflight checks UI
│   │   └── prompts.py           # User prompt utilities
│   ├── utils/                   # Shared utilities
│   │   ├── __init__.py
│   │   ├── files.py             # File search utilities
│   │   ├── geospatial.py        # CRS/transform helpers
│   │   └── logging.py           # Logging configuration
│   └── legacy/                  # Deprecated code (for migration)
│       ├── __init__.py
│       └── Cme.py               # Original Cme class (with deprecation warnings)
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # Pytest fixtures
│   ├── unit/                    # Unit tests
│   │   ├── test_config.py
│   │   ├── test_models.py
│   │   ├── test_raster_processor.py
│   │   └── ...
│   ├── integration/             # Integration tests
│   │   ├── test_full_workflow.py
│   │   └── test_project_copy.py
│   └── fixtures/                # Test data
│       ├── configs/
│       └── small_project/
├── scripts/                     # Example scripts (updated)
└── pyproject.toml               # Updated with dev dependencies
```

---

## 🔧 Phase-by-Phase Implementation

### **Phase 1: Foundation (Weeks 1-2)**

**Insight:** Starting with models and exceptions creates a stable foundation. These are the most reusable components and have minimal dependencies, making them perfect for test-driven development from the start.

#### 1.1 Core Models & Exceptions

**New: `core/models.py`**
```python
from dataclasses import dataclass, field
from pathlib import Path
from datetime import datetime
from typing import Optional, List, Dict
from enum import Enum

class ConfigFormat(Enum):
    DAT = "dat"
    YAML = "yaml"

@dataclass
class ProjectPaths:
    """Paths for a CoastalME project."""
    ini_file: Path
    exec_path: Path
    in_path: Path
    out_path: Path
    config_file: Path

    @property
    def exists(self) -> bool:
        return self.ini_file.exists() and self.config_file.exists()

@dataclass
class SimulationMetadata:
    """Metadata about a simulation run."""
    start_date: datetime
    duration_seconds: float
    timestep_seconds: float
    save_times: List[datetime]
    config_format: ConfigFormat

@dataclass
class SimulationResult:
    """Result of a simulation execution."""
    success: bool
    return_code: int
    log_file: Optional[Path] = None
    errors: Dict[int, str] = field(default_factory=dict)
    warnings: Dict[int, str] = field(default_factory=dict)
    output_files: List[Path] = field(default_factory=list)

    @property
    def crashed(self) -> bool:
        return not self.success
```

**New: `core/exceptions.py`**
```python
class CoastalmeToolsError(Exception):
    """Base exception for all CoastalmeTools errors."""
    pass

class ConfigError(CoastalmeToolsError):
    """Configuration file errors."""
    pass

class ConfigNotFoundError(ConfigError):
    """Configuration file not found."""
    pass

class ConfigParseError(ConfigError):
    """Error parsing configuration file."""
    pass

class ConfigValidationError(ConfigError):
    """Configuration validation failed."""
    pass

class ExecutionError(CoastalmeToolsError):
    """Simulation execution errors."""
    pass

class PreprocessingError(CoastalmeToolsError):
    """Input preprocessing errors."""
    pass

class ResultProcessingError(CoastalmeToolsError):
    """Output processing errors."""
    pass
```

#### 1.2 Testing Infrastructure

**New: `pyproject.toml` additions**
```toml
[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "pytest-mock>=3.11.1",
    "black>=23.7.0",
    "ruff>=0.0.285",
    "mypy>=1.5.0",
    "types-PyYAML>=6.0.12",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = "--cov=src/CoastalmeTools --cov-report=html --cov-report=term"

[tool.black]
line-length = 100
target-version = ["py39"]

[tool.ruff]
line-length = 100
select = ["E", "F", "I", "N", "W", "UP"]

[tool.mypy]
python_version = "3.9"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

**New: `tests/conftest.py`**
```python
import pytest
from pathlib import Path
import tempfile
import shutil

@pytest.fixture
def temp_project_dir():
    """Create temporary project directory."""
    temp_dir = Path(tempfile.mkdtemp())
    yield temp_dir
    shutil.rmtree(temp_dir)

@pytest.fixture
def sample_dat_config():
    """Sample .dat configuration content."""
    return """
; CoastalME configuration
output folder          : out
basement               : in/basement.tif
start date             : 00-00-00 01/01/2020
Duration of simulation : 1 year
""".strip()

@pytest.fixture
def sample_yaml_config():
    """Sample YAML configuration."""
    return {
        "output": {"folder": "out"},
        "input": {"basement": "in/basement.tif"},
        "simulation": {
            "start_date": "00-00-00 01/01/2020",
            "duration": "1 year"
        }
    }
```

---

### **Phase 2: Configuration System (Weeks 3-4)**

**Insight:** The configuration system uses the Strategy pattern - each format has its own implementation, but they all conform to the same interface. This makes adding new formats trivial and allows the rest of the system to be format-agnostic.

#### 2.1 Configuration Abstraction

**New: `config/base.py`**
```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Any, Optional
from ..core.models import ConfigFormat
from ..core.exceptions import ConfigError

class ConfigAdapter(ABC):
    """Abstract base for configuration file adapters."""

    def __init__(self, file_path: Path):
        self.file_path = file_path
        self._data: Dict[str, Any] = {}
        self._modified: Dict[str, bool] = {}

    @abstractmethod
    def load(self) -> None:
        """Load configuration from file."""
        pass

    @abstractmethod
    def save(self) -> None:
        """Save configuration to file."""
        pass

    @abstractmethod
    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get configuration value."""
        pass

    @abstractmethod
    def set(self, key: str, value: Any) -> None:
        """Set configuration value."""
        pass

    @abstractmethod
    def find(self, query: str, case_sensitive: bool = False) -> Any:
        """Find configuration value by partial key match."""
        pass

    @property
    @abstractmethod
    def format(self) -> ConfigFormat:
        """Return configuration format."""
        pass

    @property
    def is_modified(self) -> bool:
        """Check if configuration has been modified."""
        return any(self._modified.values())

    def __getitem__(self, key: str) -> Any:
        return self.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        self.set(key, value)
```

**New: `config/dat_config.py`**
```python
import re
import pandas as pd
from pathlib import Path
from typing import Any, Optional
from .base import ConfigAdapter
from ..core.models import ConfigFormat
from ..core.exceptions import ConfigParseError, ConfigNotFoundError

class DatConfig(ConfigAdapter):
    """Configuration adapter for .dat files."""

    def __init__(self, file_path: Path):
        super().__init__(file_path)
        self._df: Optional[pd.DataFrame] = None

    @property
    def format(self) -> ConfigFormat:
        return ConfigFormat.DAT

    def load(self) -> None:
        """Load .dat configuration file."""
        if not self.file_path.exists():
            raise ConfigNotFoundError(f"Config file not found: {self.file_path}")

        try:
            with open(self.file_path, 'r') as f:
                lines = f.read().splitlines()

            # Parse into DataFrame (similar to existing read_ini)
            self._df = pd.DataFrame({
                'string': lines,
                'type': ['setting'] * len(lines)
            })

            # Categorize lines
            mask = (self._df.string.str.startswith(';')) | \
                   (self._df.string.str.startswith('#'))
            self._df.loc[mask, 'type'] = 'comment'
            self._df.loc[self._df.string == '', 'type'] = 'blank'

            # Parse settings
            mask = self._df.type == 'setting'
            self._df['key'] = None
            self._df['value'] = None
            self._df['modified'] = False

            self._df.loc[mask, 'key'] = \
                self._df.string.map(lambda x: self._parse_line(x)[0])
            self._df.loc[mask, 'value'] = \
                self._df.string.map(lambda x: self._parse_line(x)[1])

            # Build data dictionary
            settings_mask = self._df.type == 'setting'
            self._data = dict(zip(
                self._df.loc[settings_mask, 'key'],
                self._df.loc[settings_mask, 'value']
            ))

        except Exception as e:
            raise ConfigParseError(f"Error parsing .dat file: {e}")

    def save(self) -> None:
        """Save .dat configuration file."""
        if self._df is None:
            raise ConfigError("No configuration loaded")

        # Update strings with modified values
        changed = ~self._df.key.isnull()
        max_key_len = max(len(x) for x in self._df['key'] if x)

        self._df.loc[changed, 'string'] = self._df[changed].apply(
            lambda row: f"{row['key']:{max_key_len}} : {row['value']}",
            axis=1
        )

        # Write back to file
        with open(self.file_path, 'w', encoding='utf-8') as f:
            f.write('\n'.join(self._df['string'].to_list()))

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get value by exact key match."""
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set value for key."""
        if self._df is None:
            raise ConfigError("No configuration loaded")

        mask = self._df['key'] == key
        if not mask.any():
            raise KeyError(f"Key not found: {key}")

        self._df.loc[mask, 'value'] = str(value)
        self._df.loc[mask, 'modified'] = True
        self._data[key] = value
        self._modified[key] = True

    def find(self, query: str, case_sensitive: bool = False) -> Any:
        """Find value by partial key match (compatible with tools.find_var)."""
        queries = query.split() if isinstance(query, str) else query

        results = self._data.copy()
        for q in queries:
            flags = 0 if case_sensitive else re.I
            results = {k: v for k, v in results.items() if re.search(q, k, flags)}

            if len(results) == 1:
                value = next(iter(results.values()))
                # Strip trailing comments
                if isinstance(value, str) and ';' in value:
                    value = value.partition(';')[0].strip()
                return value

        if len(results) == 0:
            raise KeyError(f"No matches for: {query}")
        raise KeyError(f"Multiple matches: {list(results.keys())}")

    @staticmethod
    def _parse_line(line: str) -> tuple[str, str]:
        """Parse key:value line."""
        parts = line.partition(':')
        parts = [x.strip() for x in parts if x != ':']
        parts = [re.sub(r' +', ' ', x) for x in parts]
        return tuple(parts) if len(parts) == 2 else ('', '')
```

**New: `config/yaml_config.py`**
```python
import yaml
import pandas as pd
from pathlib import Path
from typing import Any, Optional, Dict
from .base import ConfigAdapter
from ..core.models import ConfigFormat
from ..core.exceptions import ConfigParseError, ConfigNotFoundError

class YamlConfig(ConfigAdapter):
    """Configuration adapter for YAML files."""

    def __init__(self, file_path: Path):
        super().__init__(file_path)
        self._raw_yaml: Optional[Dict] = None
        self._df: Optional[pd.DataFrame] = None

    @property
    def format(self) -> ConfigFormat:
        return ConfigFormat.YAML

    def load(self) -> None:
        """Load YAML configuration file."""
        if not self.file_path.exists():
            raise ConfigNotFoundError(f"Config file not found: {self.file_path}")

        try:
            with open(self.file_path, 'r') as f:
                self._raw_yaml = yaml.safe_load(f)

            # Flatten YAML into DataFrame (similar to existing read_yaml)
            data = {'section': [], 'key': [], 'value': []}
            self._flatten_yaml(self._raw_yaml, data)

            self._df = pd.DataFrame(data)
            self._df['type'] = 'setting'
            self._df['modified'] = False

            # Build data dictionary
            self._data = dict(zip(self._df['key'], self._df['value']))

        except yaml.YAMLError as e:
            raise ConfigParseError(f"Error parsing YAML file: {e}")
        except Exception as e:
            raise ConfigParseError(f"Error loading YAML: {e}")

    def save(self) -> None:
        """Save YAML configuration file."""
        if self._df is None:
            raise ConfigError("No configuration loaded")

        # Reconstruct nested YAML from flat DataFrame
        config = self._reconstruct_yaml(self._df)

        with open(self.file_path, 'w', encoding='utf-8') as f:
            yaml.safe_dump(
                config, f,
                default_flow_style=False,
                sort_keys=False,
                allow_unicode=True,
                width=120,
                indent=2
            )

    def get(self, key: str, default: Optional[Any] = None) -> Any:
        """Get value by exact key match."""
        return self._data.get(key, default)

    def set(self, key: str, value: Any) -> None:
        """Set value for key."""
        if self._df is None:
            raise ConfigError("No configuration loaded")

        mask = self._df['key'] == key
        if not mask.any():
            raise KeyError(f"Key not found: {key}")

        self._df.loc[mask, 'value'] = value
        self._df.loc[mask, 'modified'] = True
        self._data[key] = value
        self._modified[key] = True

    def find(self, query: str, case_sensitive: bool = False) -> Any:
        """Find value by partial key match."""
        # Reuse same logic as DatConfig
        import re
        queries = query.split() if isinstance(query, str) else query

        results = self._data.copy()
        for q in queries:
            flags = 0 if case_sensitive else re.I
            results = {k: v for k, v in results.items() if re.search(q, k, flags)}

            if len(results) == 1:
                value = next(iter(results.values()))
                # Strip trailing comments
                if isinstance(value, str) and ';' in value:
                    value = value.partition(';')[0].strip()
                return value

        if len(results) == 0:
            raise KeyError(f"No matches for: {query}")
        raise KeyError(f"Multiple matches: {list(results.keys())}")

    def _flatten_yaml(self, data: Dict, output: Dict,
                      section: str = '') -> None:
        """Recursively flatten nested YAML."""
        for key, value in data.items():
            if isinstance(value, dict):
                # Check if this should be nested
                for sub_key, sub_value in value.items():
                    if isinstance(sub_value, dict):
                        # 3-level nesting
                        for sub_sub_key, sub_sub_value in sub_value.items():
                            output['section'].append(key)
                            output['key'].append(f"{sub_key}_{sub_sub_key}")
                            output['value'].append(sub_sub_value)
                    else:
                        # 2-level nesting
                        output['section'].append(key)
                        output['key'].append(sub_key)
                        output['value'].append(sub_value)
            else:
                # Flat structure
                output['section'].append(section)
                output['key'].append(key)
                output['value'].append(value)

    def _reconstruct_yaml(self, df: pd.DataFrame) -> Dict:
        """Reconstruct nested YAML from flat DataFrame."""
        # Use existing write_yaml logic from Cme.py
        config = {}

        # First pass: identify which keys should be nested
        nested_keys = {}  # {(section, parent_key): [child_keys]}

        for section in df["section"].unique():
            section_rows = df[df["section"] == section]

            for _, row in section_rows.iterrows():
                key = row["key"]
                if pd.isna(key) or key == "":
                    continue

                if "_" in key:
                    parts = key.split("_", 1)
                    parent_key = parts[0]
                    child_key = parts[1]

                    same_parent = section_rows[
                        section_rows["key"].str.startswith(parent_key + "_", na=False)
                    ]

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

            if pd.isna(key) or key == "":
                continue

            if section == "" or pd.isna(section):
                config[key] = value
                continue

            if section not in config:
                config[section] = {}

            is_nested = False
            if "_" in key:
                parent_key = key.split("_", 1)[0]
                child_key = key.split("_", 1)[1]

                if (section, parent_key) in nested_keys:
                    is_nested = True
                    if parent_key not in config[section]:
                        config[section][parent_key] = {}
                    config[section][parent_key][child_key] = value

            if not is_nested:
                config[section][key] = value

        return config
```

**New: `config/__init__.py`**
```python
from .base import ConfigAdapter
from .dat_config import DatConfig
from .yaml_config import YamlConfig
from ..core.models import ConfigFormat
from ..core.exceptions import ConfigError
from pathlib import Path

def load_config(file_path: Path) -> ConfigAdapter:
    """
    Factory function to load configuration file.

    Args:
        file_path: Path to configuration file

    Returns:
        Appropriate ConfigAdapter instance

    Raises:
        ConfigError: If file format is not supported
    """
    suffix = file_path.suffix.lower()

    if suffix == '.dat':
        config = DatConfig(file_path)
    elif suffix in ['.yaml', '.yml']:
        config = YamlConfig(file_path)
    else:
        raise ConfigError(f"Unsupported config format: {suffix}")

    config.load()
    return config

__all__ = [
    'ConfigAdapter',
    'DatConfig',
    'YamlConfig',
    'load_config'
]
```

#### 2.2 Tests for Configuration

**New: `tests/unit/test_config.py`**
```python
import pytest
from pathlib import Path
from CoastalmeTools.config import load_config, DatConfig, YamlConfig
from CoastalmeTools.core.exceptions import ConfigNotFoundError, ConfigParseError

def test_dat_config_load(temp_project_dir, sample_dat_config):
    """Test loading .dat configuration."""
    config_file = temp_project_dir / "test.dat"
    config_file.write_text(sample_dat_config)

    config = DatConfig(config_file)
    config.load()

    assert config.get("output folder") == "out"
    assert config.find("basement") == "in/basement.tif"

def test_dat_config_modify_and_save(temp_project_dir, sample_dat_config):
    """Test modifying and saving .dat config."""
    config_file = temp_project_dir / "test.dat"
    config_file.write_text(sample_dat_config)

    config = load_config(config_file)
    config.set("output folder", "new_out")
    config.save()

    # Reload and verify
    config2 = load_config(config_file)
    assert config2.get("output folder") == "new_out"

def test_yaml_config_load(temp_project_dir, sample_yaml_config):
    """Test loading YAML configuration."""
    # Implementation...
    pass

def test_config_factory(temp_project_dir, sample_dat_config):
    """Test config factory function."""
    dat_file = temp_project_dir / "test.dat"
    dat_file.write_text(sample_dat_config)

    config = load_config(dat_file)
    assert isinstance(config, DatConfig)

def test_config_not_found():
    """Test error handling for missing config."""
    with pytest.raises(ConfigNotFoundError):
        config = DatConfig(Path("nonexistent.dat"))
        config.load()
```

---

### **Phase 3: Execution & Results (Weeks 5-6)**

#### 3.1 Execution Management

**New: `execution/runner.py`**
```python
from pathlib import Path
from typing import Optional
import subprocess
import logging
from contextlib import chdir

from ..core.models import SimulationResult
from ..core.exceptions import ExecutionError
from .log_parser import LogParser

logger = logging.getLogger(__name__)

class SimulationRunner:
    """Manages CoastalME simulation execution."""

    def __init__(self, executable_path: Path, working_dir: Path):
        self.executable_path = Path(executable_path)
        self.working_dir = Path(working_dir)

        if not self.executable_path.exists():
            raise ExecutionError(f"Executable not found: {self.executable_path}")

    def run(
        self,
        clear_output: bool = True,
        output_dir: Optional[Path] = None,
        enable_monitoring: bool = True
    ) -> SimulationResult:
        """
        Execute CoastalME simulation.

        Args:
            clear_output: Clear output directory before run
            output_dir: Output directory to clear
            enable_monitoring: Launch Bokeh monitoring dashboard

        Returns:
            SimulationResult with execution details
        """
        # Prepare output directory
        if clear_output and output_dir:
            self._prepare_output_dir(output_dir)

        # Start monitoring if enabled
        monitor_process = None
        if enable_monitoring and output_dir:
            monitor_process = self._start_monitor(output_dir)

        try:
            # Run CoastalME
            with chdir(self.working_dir):
                process = subprocess.Popen(
                    [str(self.executable_path)],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE
                )

                stdout, stderr = process.communicate()
                return_code = process.returncode

            # Parse log file
            log_parser = LogParser()
            log_file, errors, warnings = log_parser.parse(output_dir)

            result = SimulationResult(
                success=(return_code == 0),
                return_code=return_code,
                log_file=log_file,
                errors=errors,
                warnings=warnings
            )

            return result

        except KeyboardInterrupt:
            process.kill()
            raise ExecutionError("Simulation interrupted by user")

        finally:
            if monitor_process:
                monitor_process.kill()

    def _prepare_output_dir(self, output_dir: Path) -> None:
        """Clear and recreate output directory."""
        import shutil

        if output_dir.exists():
            shutil.rmtree(output_dir)
        output_dir.mkdir(parents=True)

    def _start_monitor(self, output_dir: Path) -> subprocess.Popen:
        """Start Bokeh monitoring dashboard."""
        from ..utils.files import get_model_start_time

        monitor_script = Path(__file__).parent / "monitor.py"
        start_timestamp = get_model_start_time(output_dir).timestamp()

        return subprocess.Popen([
            "bokeh", "serve", "--show",
            str(monitor_script),
            "--args", str(output_dir), str(start_timestamp)
        ])
```

**New: `execution/log_parser.py`**
```python
from pathlib import Path
from typing import Dict, Tuple, Optional, List
import glob
import logging

logger = logging.getLogger(__name__)

class LogParser:
    """Parser for CoastalME log files."""

    def parse(
        self,
        output_dir: Path,
        log_level: int = 1
    ) -> Tuple[Optional[Path], Dict[int, str], Dict[int, str]]:
        """
        Parse CoastalME log file.

        Args:
            output_dir: Directory containing log file
            log_level: Log detail level from config

        Returns:
            Tuple of (log_file_path, errors_dict, warnings_dict)
        """
        log_file = self._find_log_file(output_dir)

        if not log_file:
            logger.warning("Log file not found")
            return None, {}, {}

        with open(log_file, 'r') as f:
            lines = f.readlines()

        errors = {
            idx: line.strip()
            for idx, line in enumerate(lines)
            if 'ERROR' in line
        }

        warnings = {
            idx: line.strip()
            for idx, line in enumerate(lines)
            if 'WARNING' in line
        }

        logger.info(
            f"Log parsed: {len(errors)} errors, {len(warnings)} warnings"
        )

        return log_file, errors, warnings

    def _find_log_file(self, output_dir: Path) -> Optional[Path]:
        """Find log file in output directory."""
        log_files = list(output_dir.glob("*.log"))

        if not log_files:
            return None

        if len(log_files) > 1:
            logger.warning(f"Multiple log files found, using first: {log_files[0]}")

        return log_files[0]

    def format_errors(
        self,
        errors: Dict[int, str],
        warnings: Dict[int, str],
        use_color: bool = True
    ) -> str:
        """Format errors and warnings for display."""
        from ..legacy.Cme import bcolors  # Reuse existing color codes

        if not errors and not warnings:
            return "✓ No errors or warnings"

        output = []

        if errors:
            if use_color:
                output.append(bcolors.FAIL + "ERRORS:" + bcolors.ENDC)
            else:
                output.append("ERRORS:")

            for line_no, msg in errors.items():
                output.append(f"  Line {line_no}: {msg}")

        if warnings:
            if use_color:
                output.append(bcolors.WARNING + "WARNINGS:" + bcolors.ENDC)
            else:
                output.append("WARNINGS:")

            for line_no, msg in warnings.items():
                output.append(f"  Line {line_no}: {msg}")

        return '\n'.join(output)
```

#### 3.2 Result Processing

**New: `results/raster_processor.py`**
```python
from pathlib import Path
from typing import List, Optional
from datetime import datetime
import logging

import xarray as xr
import numpy as np
import rasterio
from netCDF4 import Dataset
from cftime import date2num

from ..core.exceptions import ResultProcessingError

logger = logging.getLogger(__name__)

class RasterProcessor:
    """Process CoastalME raster outputs into NetCDF."""

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.netcdf_path = output_dir / "all_vars.nc"

    def process(
        self,
        timestamps: List[datetime],
        variables: List[str],
        basement_path: Path,
        compression_level: int = 9
    ) -> Path:
        """
        Collate raster outputs into NetCDF file.

        Args:
            timestamps: List of simulation save times
            variables: List of variable names to include
            basement_path: Path to basement DEM (for grid definition)
            compression_level: NetCDF compression level (1-9)

        Returns:
            Path to created NetCDF file
        """
        logger.info(f"Processing {len(variables)} variables over {len(timestamps)} timesteps")

        # Get grid parameters from basement
        with rasterio.open(basement_path) as src:
            transform = src.transform
            height, width = src.shape
            bounds = src.bounds

        # Create NetCDF file
        self._create_netcdf_structure(
            timestamps, width, height, bounds, transform, compression_level
        )

        # Process each variable
        with Dataset(self.netcdf_path, 'a') as ds:
            for var_name in variables:
                self._add_variable(ds, var_name, timestamps, height, width)

        logger.info(f"NetCDF created: {self.netcdf_path}")
        return self.netcdf_path

    def _create_netcdf_structure(
        self,
        timestamps: List[datetime],
        width: int,
        height: int,
        bounds: rasterio.coords.BoundingBox,
        transform: rasterio.Affine,
        compression: int
    ) -> None:
        """Create NetCDF file with dimensions and coordinates."""
        with Dataset(self.netcdf_path, 'w', format='NETCDF4') as ds:
            # Dimensions
            ds.createDimension('time', None)
            ds.createDimension('x', width)
            ds.createDimension('y', height)

            # Coordinates
            x_var = ds.createVariable(
                'x', 'f8', ('x',),
                compression='zlib', shuffle=True, complevel=compression,
                fill_value=-9999.0
            )
            y_var = ds.createVariable(
                'y', 'f8', ('y',),
                compression='zlib', shuffle=True, complevel=compression,
                fill_value=-9999.0
            )
            time_var = ds.createVariable(
                'time', 'f8', ('time',),
                compression='zlib', shuffle=True, complevel=compression
            )

            # Coordinate values
            x_var[:] = np.linspace(bounds.left, bounds.right, width)
            y_var[:] = np.linspace(bounds.bottom, bounds.top, height)

            # Time values
            time_var.units = f"hours since {timestamps[0]}"
            time_var.calendar = "gregorian"
            time_var.standard_name = "time"
            time_var[:] = date2num(timestamps, units=time_var.units, calendar=time_var.calendar)

            # Global attributes
            ds.description = "CoastalME Output"
            ds.source = "CoastalME Simulation"
            ds.history = f"Created {datetime.now()}"

            # Store transform
            crs_var = ds.createVariable('GeoTransform', 'i4')
            # Store transform as attributes...

    def _add_variable(
        self,
        dataset: Dataset,
        var_name: str,
        timestamps: List[datetime],
        height: int,
        width: int
    ) -> None:
        """Add a variable to the NetCDF dataset."""
        # Find raster files for this variable
        file_pattern = self.output_dir / f"{var_name}_*.tif"
        raster_files = sorted(file_pattern.parent.glob(file_pattern.name))

        if not raster_files:
            logger.warning(f"No raster files found for {var_name}")
            return

        # Calculate optimal chunking
        chunk_time = min(10, len(timestamps))
        chunk_y = min(100, height)
        chunk_x = min(100, width)

        # Create variable
        var = dataset.createVariable(
            var_name, 'f4', ('time', 'y', 'x'),
            compression='zlib', shuffle=True, complevel=9,
            chunksizes=(chunk_time, chunk_y, chunk_x),
            fill_value=-9999.0
        )

        # Load data for each timestep
        for idx, raster_file in enumerate(raster_files):
            with rasterio.open(raster_file) as src:
                arr = src.read(1)
                arr_flipped = np.flip(arr, 0)
                arr_flipped = np.where(np.isfinite(arr_flipped), arr_flipped, -9999.0)
                var[idx] = arr_flipped

        logger.info(f"  ✓ {var_name}")
```

---

### **Phase 4: Core Simulation Orchestrator (Week 7)**

**Insight:** The new Simulation class is a facade that composes smaller, focused components. This dramatically simplifies testing - you can mock the ConfigAdapter, SimulationRunner, and ResultProcessor independently. The original 933-line monolith becomes a ~200-line orchestrator.

**New: `core/simulation.py`**
```python
from pathlib import Path
from typing import List, Optional
from datetime import datetime, timedelta
import logging

from .models import ProjectPaths, SimulationMetadata, SimulationResult
from .exceptions import ConfigError, ExecutionError
from ..config import load_config, ConfigAdapter
from ..execution.runner import SimulationRunner
from ..execution.log_parser import LogParser
from ..results.collector import ResultCollector
from ..results.raster_processor import RasterProcessor
from ..results.vector_processor import VectorProcessor
from ..results.profile_processor import ProfileProcessor

logger = logging.getLogger(__name__)

class Simulation:
    """
    Main orchestrator for CoastalME simulations.

    This is the modern replacement for the legacy Cme class.
    """

    def __init__(self, ini_file: Path, run_path: Optional[Path] = None):
        """
        Initialize simulation from ini file.

        Args:
            ini_file: Path to .ini file
            run_path: Execution directory (defaults to ini_file parent)
        """
        self.paths = self._initialize_paths(ini_file, run_path)
        self.config = load_config(self.paths.config_file)
        self.metadata = self._load_metadata()

        self.result: Optional[SimulationResult] = None

    def run(
        self,
        executable_path: Path,
        clear_output: bool = True,
        enable_monitoring: bool = True
    ) -> SimulationResult:
        """
        Execute the simulation.

        Args:
            executable_path: Path to CoastalME executable
            clear_output: Clear output directory before running
            enable_monitoring: Launch real-time monitoring dashboard

        Returns:
            SimulationResult with execution details
        """
        logger.info(f"Starting simulation: {self.paths.ini_file}")

        runner = SimulationRunner(executable_path, self.paths.exec_path)

        self.result = runner.run(
            clear_output=clear_output,
            output_dir=self.paths.out_path,
            enable_monitoring=enable_monitoring
        )

        if self.result.crashed:
            logger.error(f"Simulation crashed with code {self.result.return_code}")
            self._print_errors()
        else:
            logger.info("Simulation completed successfully")

        return self.result

    def collate_results(
        self,
        raster_vars: List[str] = None,
        vector_vars: List[str] = None
    ) -> None:
        """
        Collate simulation outputs into NetCDF and GeoPackage.

        Args:
            raster_vars: List of raster variables to include (None = all)
            vector_vars: List of vector variables to include (None = all)
        """
        if not self.result:
            raise ExecutionError("Simulation not run yet")

        logger.info("Collating results...")

        # Collect output files
        collector = ResultCollector(self.paths.out_path)
        raster_files, vector_files = collector.collect(
            self.metadata.save_times
        )

        # Process rasters
        if raster_vars is None or 'all' in raster_vars:
            raster_vars = raster_files['variables'].tolist()

        raster_proc = RasterProcessor(self.paths.out_path)
        basement_path = self.paths.in_path.parent / self.config.find('basement')

        raster_proc.process(
            timestamps=self.metadata.save_times,
            variables=raster_vars,
            basement_path=basement_path
        )

        # Process vectors
        if vector_vars is None or 'all' in vector_vars:
            vector_vars = vector_files['variables'].tolist()

        vector_proc = VectorProcessor(self.paths.out_path)
        vector_proc.process(
            timestamps=self.metadata.save_times,
            variables=vector_vars
        )

        # Process profiles
        profile_proc = ProfileProcessor(self.paths.out_path)
        profile_proc.process(self.metadata.save_times)

        logger.info("Results collated successfully")

    def _initialize_paths(
        self,
        ini_file: Path,
        run_path: Optional[Path]
    ) -> ProjectPaths:
        """Initialize project paths."""
        ini_file = Path(ini_file).resolve()
        exec_path = Path(run_path) if run_path else ini_file.parent

        # Read ini to get input/output paths
        ini_config = load_config(ini_file)
        in_path = exec_path / ini_config.find('input')
        out_path = exec_path / ini_config.find('output')

        return ProjectPaths(
            ini_file=ini_file,
            exec_path=exec_path,
            in_path=in_path,
            out_path=out_path,
            config_file=in_path
        )

    def _load_metadata(self) -> SimulationMetadata:
        """Load simulation metadata from config."""
        from pytimeparse2 import parse as timeparse

        start_str = self.config.find('start date')
        start_date = datetime.strptime(start_str, "%H-%M-%S %m/%d/%Y")

        duration_str = self.config.find('Duration of simulation')
        duration = timedelta(seconds=timeparse(duration_str))

        # Parse save times
        save_times = self._parse_save_times(start_date, duration)

        return SimulationMetadata(
            start_date=start_date,
            duration_seconds=duration.total_seconds(),
            timestep_seconds=0,  # Parse from config if needed
            save_times=save_times,
            config_format=self.config.format
        )

    def _parse_save_times(
        self,
        start: datetime,
        duration: timedelta
    ) -> List[datetime]:
        """Parse save times from config."""
        # Reuse logic from legacy Cme.out_times()
        # ... (implementation)
        pass

    def _print_errors(self) -> None:
        """Print colored error summary."""
        if not self.result:
            return

        parser = LogParser()
        formatted = parser.format_errors(
            self.result.errors,
            self.result.warnings,
            use_color=True
        )
        print(formatted)
```

---

### **Phase 5: Interactive & Preprocessing (Week 8)**

#### 5.1 Interactive Preflight

**New: `interactive/preflight.py`**
```python
from pathlib import Path
from typing import Optional, Callable
import logging

from ..core.simulation import Simulation
from ..preprocessing.basement_generator import BasementGenerator
from ..preprocessing.wave_preprocessor import WavePreprocessor
from .prompts import Prompter

logger = logging.getLogger(__name__)

class PreflightChecker:
    """Interactive preflight checks for simulation setup."""

    def __init__(
        self,
        simulation: Simulation,
        prompter: Optional[Prompter] = None
    ):
        self.simulation = simulation
        self.prompter = prompter or Prompter()

    def run_checks(self, interactive: bool = True) -> bool:
        """
        Run preflight checks.

        Args:
            interactive: Enable interactive prompts

        Returns:
            True if all checks pass
        """
        logger.info("Running preflight checks...")

        # Check if output exists
        if self.simulation.paths.out_path.exists():
            if interactive:
                overwrite = self.prompter.confirm(
                    "Output directory exists. Overwrite?"
                )
                if not overwrite:
                    return False

        # Offer quick-start model generation
        if interactive and not self._basement_exists():
            generate = self.prompter.confirm(
                "Basement DEM not found. Generate quick-start model?"
            )
            if generate:
                self._generate_quick_start()

        # Offer wave rose generation
        if interactive:
            wave_rose = self.prompter.confirm(
                "Generate wave rose plot?"
            )
            if wave_rose:
                self._generate_wave_rose()

        logger.info("Preflight checks complete")
        return True

    def _basement_exists(self) -> bool:
        """Check if basement DEM exists."""
        basement_rel = self.simulation.config.find('basement')
        basement_path = self.simulation.paths.in_path.parent / basement_rel
        return basement_path.exists()

    def _generate_quick_start(self) -> None:
        """Generate quick-start model."""
        generator = BasementGenerator(
            self.simulation.paths.in_path.parent,
            self.prompter
        )
        generator.generate_interactive()

    def _generate_wave_rose(self) -> None:
        """Generate wave rose plot."""
        preprocessor = WavePreprocessor(
            self.simulation.paths.in_path.parent
        )
        preprocessor.plot_wave_rose()
```

**New: `interactive/prompts.py`**
```python
from typing import Optional, Dict, Any
import sys

class Prompter:
    """User interaction utilities."""

    def __init__(self, interactive: bool = True):
        self.interactive = interactive

    def confirm(self, message: str, default: bool = False) -> bool:
        """
        Ask yes/no question.

        Args:
            message: Question to ask
            default: Default answer if non-interactive

        Returns:
            User's response (or default)
        """
        if not self.interactive:
            return default

        try:
            response = input(f"{message} (Y/N): ").strip().lower()
            return response in ['y', 'yes']
        except (EOFError, KeyboardInterrupt):
            return default

    def select(
        self,
        message: str,
        options: Dict[int, str],
        default: Optional[int] = None
    ) -> int:
        """
        Select from numbered options.

        Args:
            message: Prompt message
            options: Dictionary of {index: description}
            default: Default selection

        Returns:
            Selected index
        """
        if not self.interactive and default is not None:
            return default

        options_str = '\n'.join(f"  {k}: {v}" for k, v in options.items())
        prompt = f"{message}\n{options_str}\nSelect: "

        try:
            selection = int(input(prompt))
            if selection not in options:
                raise ValueError("Invalid selection")
            return selection
        except (EOFError, KeyboardInterrupt, ValueError):
            if default is not None:
                return default
            raise

    def input_text(
        self,
        message: str,
        default: Optional[str] = None
    ) -> str:
        """
        Get text input.

        Args:
            message: Prompt message
            default: Default value

        Returns:
            User's input (or default)
        """
        if not self.interactive and default:
            return default

        try:
            prompt = f"{message}" + (f" [{default}]" if default else "") + ": "
            response = input(prompt).strip()
            return response if response else (default or "")
        except (EOFError, KeyboardInterrupt):
            return default or ""
```

---

## 🧪 Testing Strategy

### Unit Tests Priority
1. **Configuration system** (Phases 2) - Critical foundation
2. **Data models** (Phase 1) - Simple dataclasses
3. **Result processors** (Phase 3) - Pure functions, mockable I/O
4. **Utilities** - File search, path manipulation

### Integration Tests Priority
1. **Full workflow** - Load config → Run simulation → Collate results
2. **Project copy** - Already well-tested in project_tools.py
3. **Configuration round-trip** - Load → Modify → Save → Reload

### Test Coverage Goals
- **80%+ for new code** - All new modules should have comprehensive tests
- **Existing code unchanged** - Don't require tests for legacy code initially
- **CI/CD integration** - Run tests on every commit (GitHub Actions)

---

## 📦 Migration Strategy

### Backwards Compatibility Layer

**Updated: `__init__.py`**
```python
# New API (primary)
from .core.simulation import Simulation
from .config import load_config
from .project.tools import copy_project, get_project_extent

# Legacy API (deprecated)
from .legacy.Cme import Cme
import warnings

def __getattr__(name):
    """Intercept legacy imports and warn."""
    if name == 'Cme':
        warnings.warn(
            "CoastalmeTools.Cme is deprecated. Use CoastalmeTools.Simulation instead.",
            DeprecationWarning,
            stacklevel=2
        )
        return Cme
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = [
    # New API
    'Simulation',
    'load_config',
    'copy_project',
    'get_project_extent',
    # Legacy (deprecated)
    'Cme',
]
```

### Migration Path for Users

**Create migration guide: `docs/MIGRATION.md`**
```markdown
# Migration Guide: Cme → Simulation

## Old API (Deprecated)
```python
from CoastalmeTools import Cme

cme = Cme(ini='cme.ini', run_path='.')
cme.preflight_checks()
cme.run(ex_p='./coastalme', ready=True, clear=True)
cme.collate_results(vars=['all'], vars_v=['all'])
```

## New API
```python
from CoastalmeTools import Simulation
from CoastalmeTools.interactive import PreflightChecker

sim = Simulation(ini_file='cme.ini', run_path='.')
preflight = PreflightChecker(sim)
preflight.run_checks(interactive=True)

result = sim.run(executable_path='./coastalme', clear_output=True)
sim.collate_results(raster_vars=None, vector_vars=None)
```

## Key Changes
- `Cme` → `Simulation`
- Separate `PreflightChecker` for interactive workflows
- Explicit result objects instead of instance attributes
- Type hints throughout
```

---

## 📋 Implementation Timeline

| Phase | Duration | Deliverables | Tests |
|-------|----------|--------------|-------|
| 1. Foundation | 2 weeks | Models, exceptions, test infrastructure | Unit tests for models |
| 2. Configuration | 2 weeks | ConfigAdapter, DatConfig, YamlConfig | Unit + integration tests |
| 3. Execution & Results | 2 weeks | Runner, LogParser, result processors | Unit tests with mocks |
| 4. Simulation Core | 1 week | Simulation class (orchestrator) | Integration tests |
| 5. Interactive/Preprocessing | 1 week | Preflight, prompts, generators | Unit tests |
| 6. Migration & Docs | 1 week | Deprecation layer, migration guide | Legacy compatibility tests |
| **Total** | **9 weeks** | Full refactored codebase | 80%+ coverage |

---

## 🎁 Benefits Summary

### For Maintainability
- **Modular design**: Each module has a single responsibility
- **Testable**: Small, focused functions with dependency injection
- **Type safety**: Full type hints enable IDE support and early error detection
- **Clear interfaces**: ABCs define contracts between components

### For Features
- **Easy to extend**: Add new config formats by implementing ConfigAdapter
- **Pluggable**: Swap out result processors, monitoring, etc.
- **Composable**: Mix and match components for custom workflows
- **Reusable**: Utilities can be used independently

### For Users
- **Cleaner API**: Explicit, discoverable methods
- **Better errors**: Custom exceptions with helpful messages
- **Backwards compatible**: Legacy Cme class still works (with warnings)
- **Well-documented**: Type hints + docstrings + migration guide

---

## 📝 Next Steps

To begin implementation:
1. Create the new directory structure
2. Implement Phase 1 (Foundation) - models and exceptions
3. Set up testing infrastructure with pytest
4. Implement Phase 2 (Configuration system)
5. Write comprehensive tests as we go

Each phase can be implemented incrementally without breaking existing functionality, since the legacy Cme class remains untouched until Phase 6.
