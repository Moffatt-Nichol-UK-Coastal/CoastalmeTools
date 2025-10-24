# CoastalmeTools

## What is it?
Python tools to work with [CoastalME](https://github.com/coastalme/coastalme)

>CoastalME (Coastal Modelling Environment) is a Free and Open Source software for geospatial modelling to simulate decadal and longer coastal morphological changes.
>
>It is an engineering tool for advanced modellers seeking to simulate the interaction of multiple coastal landforms and different types of human interventions.

## Features

CoastalmeTools provides a complete Python workflow for CoastalME simulations:

### Core Functionality
- **Configuration Management**: Unified API for both `.dat` (legacy) and `.yaml` (modern) formats
- **Simulation Execution**: Run CoastalME with real-time monitoring and error detection
- **Result Collation**: Aggregate time-series outputs into NetCDF and GeoPackage formats
- **Pre-run Checks**: Validate inputs, generate tide/wave plots, quick-start model generation

### Project Manipulation
- **Cropping**: Extract spatial subsets from existing projects
- **Resampling**: Change grid resolution (upsampling/downsampling)
- **Basement Generation**: Create base elevations from TIN (LandXML) or raster data

### Visualization Support
- **NetCDF Output**: Time-series raster data optimized for QGIS
- **GeoPackage**: Multi-layer vector outputs in single file
- **Profile Plots**: Automated cross-shore profile visualization

## Requirements

- **Python**: 3.9 or higher
- **CoastalME executable**: Required for running simulations (not included)
- **Operating System**: Linux, macOS, or Windows (via WSL for CoastalME)

## Installation

### Option 1: Install from Source (Recommended for Development)

```bash
# Clone the repository
git clone https://github.com/wilfchun/CoastalmeTools.git
cd CoastalmeTools

# Create virtual environment with uv (fast) or venv
uv venv                    # Using uv (recommended)
# python -m venv .venv     # Or using standard venv

# Activate virtual environment
source .venv/bin/activate  # Linux/macOS
# .venv\Scripts\activate   # Windows

# Install in editable mode with all dependencies
uv pip install -e .        # Using uv
# pip install -e .         # Or using pip

# Optional: Install development dependencies (includes pytest)
uv pip install -e ".[dev]"
```

### Option 2: Install from Wheel

Binary distributions (wheels) are available from the [releases](https://github.com/wilfchun/CoastalmeTools/releases) tab.

```bash
pip install CoastalmeTools-0.1.0-py3-none-any.whl
```

### Verify Installation

```bash
python -c "from CoastalmeTools import Cme; print('CoastalmeTools installed successfully!')"
```

## Quick Start

### Basic Workflow

The simplest way to run a complete CoastalME workflow:

```python
from pathlib import Path
from CoastalmeTools import Cme

# 1. Define paths
ini_file = Path("path/to/your/project/cme.ini")
run_path = Path("path/to/your/project/")
cme_executable = Path("path/to/coastalme/cme")

# 2. Setup simulation
cme = Cme(ini_file, run_path)

# 3. Optional: Pre-run checks and model initialization
cme.preflight_checks()  # Interactive checks (quick-start, wave roses, etc.)
cme.build_model()       # Build initial state (t=0)

# 4. Run simulation
cme.run(cme_executable)

# 5. Collate results into NetCDF and GeoPackage
raster_vars = ['wave_height', 'top_elevation', 'total_actual_beach_erosion']
vector_vars = ['coast', 'normals', 'cliff_notch']

cme.collate_results(vars=raster_vars, vars_v=vector_vars)

# Results saved to:
#   - run_path/out/all_vars.nc (NetCDF)
#   - run_path/out/all_vars.gpkg (GeoPackage)
```

### Using the Modern Configuration API (New in v0.1.0)

The refactored configuration system provides type-safe, format-agnostic access:

```python
from pathlib import Path
from CoastalmeTools.config import load_config

# Load configuration (auto-detects .dat or .yaml format)
config = load_config(Path("scenario.yaml"))

# Query values - three methods available:

# Method 1: Flexible search (backward compatible)
basement = config.find("basement")  # Partial match: "basement", "Basement DEM", etc.

# Method 2: Exact key lookup
duration = config.get("Duration simulation", default=10.0)

# Method 3: Dictionary-style access
if "output folder" in config:
    output = config["output folder"]

# Modify and save (preserves format and comments)
config.set("output folder", "new_output")
config.save()  # Writes back to original file

# Check configuration format
print(f"Format: {config.format}")  # ConfigFormat.YAML or ConfigFormat.DAT
```

### Complete Example with Error Handling

```python
import logging
from pathlib import Path
from CoastalmeTools import Cme

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Define paths
ini_file = Path("my_project/cme.ini")
run_path = Path("my_project/")
cme_path = Path("/usr/local/bin/cme")

# Verify paths exist
if not ini_file.exists():
    logger.error(f"Configuration not found: {ini_file}")
    exit(1)

if not cme_path.exists():
    logger.error(f"CoastalME executable not found: {cme_path}")
    exit(1)

# Setup and run
cme = Cme(ini_file, run_path)
logger.info(f"Running simulation from: {cme.in_path}")

# Build initial conditions
cme.build_model()

# Execute simulation
return_code = cme.run(cme_path)

# Check for errors
if cme.crashed:
    logger.error("Simulation crashed!")
    cme.return_rescue()  # Print colored error summary
    exit(1)

# Collate all available outputs
raster_vars = [
    'landform_class',
    'top_elevation',
    'wave_height',
    'total_actual_beach_erosion',
    'total_actual_platform_erosion',
]

vector_vars = [
    'coast',
    'normals',
    'cliff_notch',
    'breaking_wave_height',
]

try:
    cme.collate_results(vars=raster_vars, vars_v=vector_vars)
    logger.info(f"Results saved to: {cme.out_path}")
except Exception as e:
    logger.error(f"Result collation failed: {e}")
    exit(1)

logger.info("Workflow complete!")
```

### Advanced: Project Manipulation

Copy, crop, and resample projects programmatically:

```python
from pathlib import Path
from CoastalmeTools.project_tools import copy_project, get_project_extent

# Get source project extent
source_ini = Path("original_project/cme.ini")
extent = get_project_extent(str(source_ini))
print(f"Original extent: {extent}")

# Copy project with cropping and resampling
dest = Path("cropped_project/")
cme = copy_project(
    source_ini_path=source_ini,
    dest_project_path=dest,
    crop_bbox=(653696, 289701, 656062, 297949),  # (xmin, ymin, xmax, ymax)
    target_cell_size=5.0,                        # Resample to 5m resolution
    resampling_method="bilinear",                # or "nearest", "cubic", etc.
    verbose=True
)

# Run the cropped/resampled project
cme.run(Path("/usr/local/bin/cme"))
```

## Running Tests

```bash
# Run all tests
pytest

# Run with coverage report
pytest --cov=src/CoastalmeTools --cov-report=html

# Run specific test module
pytest tests/unit/test_config.py
```

## Example Scripts

Complete workflow examples are available in the `scripts/` directory:

- **`template_full_modern.py`**: Full workflow using both legacy and new APIs
- **`config_example.py`**: Comprehensive configuration system demonstrations
- **`template_full.py`**: Legacy API workflow (still fully supported)

Run an example:

```bash
# Edit paths in the script first, then:
python scripts/template_full_modern.py
```

## Documentation

- **[GitHub Repository](https://github.com/wilfchun/CoastalmeTools)**: Source code and issues
- **[CoastalME Wiki](https://earthwise.bgs.ac.uk/index.php/Category:Coastal_Modeling_Environment)**: Core model documentation
- **[Refactoring Plan](REFACTORING_PLAN.md)**: Architecture roadmap (for contributors)
- **In-code documentation**: See `CLAUDE.md` for development guidance

## Getting Help

- **Issues**: Report bugs at https://github.com/wilfchun/CoastalmeTools/issues
- **CoastalME Core**: https://github.com/coastalme/coastalme/issues

## What's New in v0.1.0

This version introduces a major refactoring with:

- ✅ **Modern Configuration API**: Format-agnostic handling of `.dat` and `.yaml` files
- ✅ **Type-Safe Models**: Dataclasses for `ProjectPaths`, `SimulationResult`, etc.
- ✅ **Custom Exceptions**: Structured error hierarchy for better debugging
- ✅ **Comprehensive Tests**: 61 unit tests with pytest framework
- ✅ **Backward Compatibility**: All legacy code continues to work

See [PR_DESCRIPTION.md](PR_DESCRIPTION.md) for detailed changes.

## Development Status

**Active Development** - This package is under active development. APIs may change between minor versions until v1.0.0.

Current architecture phase: **Phase 2 Complete** (Configuration System)
Next up: **Phase 3** (Execution Module Refactoring)

## License

See [LICENSE](LICENSE) file for details.
