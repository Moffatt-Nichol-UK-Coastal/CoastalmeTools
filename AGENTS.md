# CoastalmeTools Context & Guidelines

This file provides context, architectural guidance, and coding standards for agents (like Claude Code) working on the **CoastalmeTools** repository.

## 1. Project Purpose
CoastalmeTools is the Python companion toolkit for **CoastalME** (Coastal Modelling Environment). It handles:
*   **Automation:** Pre-processing inputs and post-processing results.
*   **Orchestration:** Running simulations and managing workflows.
*   **Analysis:** Aggregating complex model outputs (rasters/vectors) into standardized formats (NetCDF/GeoPackage).
*   **Visualization:** Real-time monitoring (Bokeh) and static plotting.

## 2. Directives & Philosophy
**⚠️ CRITICAL:** All code changes must adhere to these principles.

### Functional Style & Design
*   **Immutability:** Prefer immutable data structures. **Never** mutate function arguments unless explicitly designed for in-place modification.
*   **Pure Functions:** Separate logic from I/O. Calculation functions should take data in and return data out, without side effects.
*   **Composition:** Prefer small, composable functions over deep inheritance or "God Classes".

### Levels of Abstraction
*   **Separation of Concerns:** Workflow logic $\neq$ Implementation details. Keep them separate.
*   **Top-Down Reading:** Public methods at the top; helpers/privates below. Code should read like a narrative.
*   **Single Responsibility:** One function = One clear purpose.

### Input/Output Contracts
*   **Type Hinting:** **MANDATORY** for all new code (`typing` module).
*   **Explicit Returns:** Return results; do not modify state implicitly.
*   **Validation:** Fail fast at boundaries (public API entry points).

### Modern Python Practices
*   **Pathlib:** Use `pathlib.Path` exclusively. No `os.path`.
*   **String Formatting:** Use f-strings (`f"{var}"`).
*   **Context Managers:** Use `with` for all resources (files, locks, plots).
*   **Iterables:** List comprehensions/generators > explicit loops.

## 3. Architecture

### High-Level Mental Model
1.  **Config:** User provides parameters (`.dat` or `.yaml`).
2.  **Orchestration:** `Cme` class prepares the environment (`preflight_checks`), handling file paths and inputs.
3.  **Execution:** CoastalME C++ executable is run as a subprocess.
4.  **Collation:** Outputs (`.tif`, `.shp`) are discovered and aggregated into efficient storage formats (`.nc`, `.gpkg`).

### File Structure & Modules
```
src/CoastalmeTools/
├── Cme.py              # 🚧 MONOLITH: Main workflow orchestrator & legacy config logic.
├── config/             # ✅ NEW: Modular configuration system (DatConfig/YamlConfig).
├── core/               # ✅ NEW: Shared models and exceptions.
├── execution/          # ✅ NEW: Execution logic (Runner, Log Parsing).
├── files.py            # Result processing (NetCDF/GeoPackage aggregation).
├── xml2raster.py       # TIN -> Raster conversion (LandXML).
├── hydro.py            # Wave data handling (GRIB/hindcast).
└── monitor.py          # Bokeh dashboard for real-time monitoring.
```

## 4. Workflows & Development

### Setup & Environment
```bash
# 0. if in NixOS enable devenv if not already active
devenv shell

# 1. Create venv & install
uv venv && source .venv/bin/activate
uv pip install -e ".[dev]"

# 2. Build distribution
uv build
```

### Common Tasks
*   **Run Tests:** `uv run pytest` (Unit tests) or `uv run scripts/template_full_modern.py` (Integration).
*   **Debug:** Use VSCode launch config "Python Debugger: test all".

## 5. Technical Reference

### Configuration System
*   **Status:** *Transitional*. We are moving from `Cme.py`'s internal logic to the `config/` module.
*   **Legacy (`Cme.py`):** Uses dataframe-based parsing. `write_ini()` is DAT-only.
*   **Modern (`config/`):** Object-oriented `DatConfig` and `YamlConfig`. Supports nested YAML structures.

### Result Processing
*   **`collect_files()`**: Pattern matching for outputs.
*   **`rasters()`**: Time-series aggregation into NetCDF (using `xarray`/`rioxarray`).
*   **`vectors()`**: Aggregation into GeoPackages (`geopandas`).
*   **HDF5 Locking:** `files.py` disables file locking (`HDF5_USE_FILE_LOCKING=FALSE`) to prevent concurrency issues.

## 6. Constraints & Gotchas

### 🔴 Critical Constraints
*   **Numpy Version:** `pyproject.toml` requires **`numpy>=2.0.0`**. (Previously `<2.0.0`). *Verify migration status.*
*   **Projections:** Hardcoded to **EPSG:27700** (British National Grid) in `xml2raster.py` and `genBase()`.
*   **YAML writes:** In `Cme.py`, `write_yaml` supports nested structures via flattened DataFrame reconstruction.

### 🟠 Known Issues
*   **Transitional Code:** `Cme.py` is currently a mix of new and old patterns. Refactoring should prioritize extracting logic into `core/` and `execution/`.
*   **Empty Files:** `src/CoastalmeTools/execution/runner.py` is currently empty.
