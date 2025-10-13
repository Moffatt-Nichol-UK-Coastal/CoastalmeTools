# Project Copy Feature Implementation Plan

**Date:** 2025-01-13
**Purpose:** Add functionality to CoastalmeTools for creating modified copies of CoastalME projects with cropping and resampling capabilities

## Overview

This feature allows users to create modified copies of existing CoastalME projects with:
1. **Cropping** - Focus on a smaller geographic area
2. **Resampling** - Change cell size/resolution for faster prototyping or detailed analysis

## User Requirements

### High Priority
1. **Cropping method:** Bounding box coordinates `(minx, miny, maxx, maxy)` in model CRS (EPSG:27700)
2. **Interface:** Python API only (no CLI tool needed initially)
3. **Configuration format:** Implement YAML writing capability to handle both `.dat` and `.yaml` files

### Implementation Decisions
- **Water level adjustment:** NOT needed when cropping (only if elevations are modified)
- **Wave station validation:** YES - check if wave stations fall outside new domain and warn
- **Sediment resampling:** Use "average" method (concentration conserved)
- **Dry-run mode:** Not needed for initial implementation

## Architecture

### Phase 1: YAML Writing Capability

**Location:** `src/CoastalmeTools/Cme.py`

**New Function:**
```python
def write_yaml(path, df):
    """
    Write coastalme configuration to YAML file

    Reverses the flattening process from read_yaml() to reconstruct
    nested YAML structure from DataFrame.

    Args:
        path: Output file path
        df: DataFrame with 'section', 'key', 'value' columns
    """
```

**Key Technical Details:**
- Reconstruct nested structure from flattened DataFrame
- Handle 2-tier (`section: {key: value}`) and 3-tier (`section: {parent: {child: value}}`) nesting
- Detect nested patterns by analyzing key prefixes (e.g., `median_sizes_fine` → `median_sizes: {fine: value}`)
- Use `yaml.safe_dump()` with formatting options for readability
- Add validation to ensure written YAML can be re-read

**Updates Required:**
- Modify `update_config()` to support saving YAML files (currently only supports `.dat`)
- Update `preflight_checks()` to use new YAML writer

---

### Phase 2: Project Tools Module

**Location:** `src/CoastalmeTools/project_tools.py` (new file)

#### Core Function

```python
def copy_project(
    source_ini_path: str,
    dest_project_path: str,
    crop_bbox: tuple[float, float, float, float] | None = None,  # (minx, miny, maxx, maxy)
    target_cell_size: float | None = None,  # meters
    resampling_method: str = "bilinear",  # for DEM
    sediment_resampling: str = "average",  # average for sediment concentration
    validate: bool = True,  # run preflight checks on new project
    verbose: bool = True
) -> Cme:
    """
    Create a modified copy of a CoastalME project.

    Args:
        source_ini_path: Path to source .ini file
        dest_project_path: Destination directory for new project
        crop_bbox: Bounding box (minx, miny, maxx, maxy) in EPSG:27700
        target_cell_size: New cell size in meters (None = keep original)
        resampling_method: Method for DEM ('bilinear', 'cubic', 'nearest')
        sediment_resampling: Method for sediment layers ('average', 'sum')
        validate: Run preflight checks after creation
        verbose: Print progress messages

    Returns:
        Cme object initialized with the new project

    Raises:
        ValueError: If crop_bbox is outside source extent or invalid parameters
        FileNotFoundError: If source files are missing
    """
```

#### Processing Steps

1. **Initialize and Validate Source**
   - Load source `Cme` object
   - Extract grid parameters from basement DEM (nx, ny, dx, dy, origin, transform)
   - Validate crop_bbox against source extent

2. **Calculate New Grid Parameters**
   ```python
   def calculate_grid_parameters(
       source_bbox: tuple,
       source_transform: Affine,
       crop_bbox: tuple | None,
       target_cell_size: float | None
   ) -> dict:
       """
       Calculate new grid dimensions and transform
       Returns: {nx, ny, dx, dy, origin_x, origin_y, transform}
       """
   ```

3. **Create Destination Directory Structure**
   - Replicate source tree (in/, out/ if exists)
   - Copy non-raster files as-is (wave data, tide data, text files)

4. **Process Raster Inputs**
   ```python
   def process_raster(
       src_path: Path,
       dest_path: Path,
       crop_window: rasterio.windows.Window | None,
       target_transform: Affine | None,
       target_shape: tuple[int, int] | None,
       resampling_method: Resampling
   ):
       """Crop and/or resample a raster file"""
   ```

   **Resampling Strategy by File Type:**
   - **Basement DEM:** Use specified `resampling_method` (bilinear, cubic, nearest)
   - **Sediment layers:** Use "average" to preserve concentration
   - **Intervention rasters:** Use "nearest" to preserve discrete class values

5. **Process Vector Inputs**
   ```python
   def process_vector(
       src_path: Path,
       dest_path: Path,
       crop_bbox: tuple | None
   ):
       """Clip vector files to new extent using geopandas"""
   ```
   - Clip shapefiles (intervention polygons, initial coastlines)
   - **Wave station check:** Validate wave station locations fall within new domain, warn if outside

6. **Update Configuration Files**
   - Copy `.ini` file, update paths if needed
   - Update main config (`.dat` or `.yaml`):
     - Grid parameters: nx, ny based on new dimensions
     - Cell size: dx, dy if resolution changed
     - Origin coordinates: if cropped
     - File paths: Keep relative (should work automatically)
   - Use `write_yaml()` for YAML files, `write_ini()` for DAT files

7. **Generate Summary Report**
   ```python
   class ProjectCopyReport:
       """Summary of changes made during project copy"""
       old_extent: tuple
       new_extent: tuple
       old_cell_size: float
       new_cell_size: float
       old_grid_dims: tuple[int, int]
       new_grid_dims: tuple[int, int]
       runtime_ratio: float  # estimated computation time change
       files_processed: dict  # {file_type: count}
       warnings: list[str]
   ```

8. **Validate New Project**
   - Initialize `Cme` object with new `.ini`
   - Optionally run `preflight_checks()` (if validate=True, non-interactive)
   - Return configured `Cme` object

#### Utility Functions

```python
def get_project_extent(ini_path: str) -> tuple:
    """Extract bounding box from project's basement DEM"""

def estimate_runtime_change(old_cells: int, new_cells: int) -> float:
    """Estimate computational time multiplier based on cell count"""

def validate_crop_bbox(
    source_extent: tuple,
    crop_bbox: tuple,
    buffer_cells: int = 10
) -> tuple[bool, list[str]]:
    """
    Validate crop area and return (is_valid, warnings)

    Checks:
    - Crop is within source bounds
    - Sufficient buffer from edges for boundary conditions
    - Minimum domain size for model stability
    - Returns warnings for potential issues
    """

def get_raster_files_in_project(cme: Cme) -> dict:
    """
    Discover all raster files referenced in config

    Returns:
        {
            'basement': path,
            'sediment_layers': [(layer_num, sediment_type, path), ...],
            'interventions': [path, ...],
            'other': [path, ...]
        }
    """

def check_wave_stations_in_domain(
    wave_shapefile: Path,
    domain_bbox: tuple
) -> tuple[bool, list[str]]:
    """
    Check if wave station locations fall within new domain

    Returns:
        (all_inside, warnings) where warnings list station IDs outside domain
    """
```

---

### Phase 3: Example Script

**Location:** `scripts/copy_project_example.py`

```python
#!/usr/bin/env python3
"""
Example script showing how to create modified copies of CoastalME projects.

Demonstrates:
1. Cropping a project to focus on a smaller area
2. Changing resolution for faster prototyping
3. Combined cropping and resampling
"""

from CoastalmeTools import Cme
from CoastalmeTools.project_tools import copy_project
from pathlib import Path

# Example 1: Crop to focus area
print("Example 1: Cropping Thorpness project")
source = Path("/home/wilfchun/CoastalME/CoastalME_data_local/CSE/Thorpness/cme.ini")
dest = Path("/home/wilfchun/CoastalME/CoastalME_data_local/CSE/Thorpness_cropped")

# Define crop area in EPSG:27700 coordinates
crop_bbox = (640000, 263000, 642000, 265000)  # Example - adjust to actual data

cme = copy_project(
    source_ini_path=source,
    dest_project_path=dest,
    crop_bbox=crop_bbox,
    verbose=True
)

print(f"Cropped project created at: {dest}")
print(f"New grid dimensions: {cme.config_df}")

# Example 2: Coarsen resolution for rapid prototyping
print("\nExample 2: Coarsening resolution for rapid testing")
dest_coarse = Path("/home/wilfchun/CoastalME/CoastalME_data_local/CSE/Thorpness_10m")

cme_coarse = copy_project(
    source_ini_path=source,
    dest_project_path=dest_coarse,
    target_cell_size=10.0,  # Change to 10m cells
    resampling_method="bilinear",
    verbose=True
)

# Example 3: Both crop AND resample
print("\nExample 3: Crop and resample together")
dest_both = Path("/home/wilfchun/CoastalME/CoastalME_data_local/CSE/Thorpness_small")

cme_both = copy_project(
    source_ini_path=source,
    dest_project_path=dest_both,
    crop_bbox=crop_bbox,
    target_cell_size=5.0,
    verbose=True
)

print("\nAll examples completed!")
```

---

## Technical Considerations

### Coordinate Reference System
- **Current:** Hardcoded to EPSG:27700 (British National Grid) matching existing codebase
- **Documentation:** Clearly state in docstrings that bbox must be in EPSG:27700
- **Future enhancement:** Auto-detect CRS from input rasters

### Resampling Strategy

| File Type | Resampling Method | Rationale |
|-----------|-------------------|-----------|
| Basement DEM | bilinear/cubic/nearest (user choice) | Smooth elevation changes |
| Sediment layers | average | Preserve sediment concentration |
| Intervention rasters | nearest | Preserve discrete class values |

### Memory Management
- Process rasters one at a time (avoid loading all into memory)
- Use rasterio windowed reading for very large rasters
- Clean up temporary arrays explicitly

### Error Handling
- Validate all inputs before processing
- Provide clear error messages with actionable suggestions
- Consider rollback (delete partial output) if critical error occurs mid-process

### Wave Station Validation
```python
# Pseudocode for wave station check
wave_shp = cme.find_config("wave_height_shape_file")
if wave_shp:
    stations_ok, warnings = check_wave_stations_in_domain(
        wave_shapefile=in_path / wave_shp,
        domain_bbox=new_bbox
    )
    if not stations_ok:
        logger.warning(f"Wave stations outside domain: {warnings}")
        print(f"⚠️  Warning: {len(warnings)} wave station(s) fall outside new domain")
```

### Grid Parameter Updates

**Parameters that MUST be updated in config:**
- `nx`, `ny` or equivalent (grid cell counts) - if cropping or resampling
- `dx`, `dy` or cell size - if resampling only
- Grid origin coordinates - if cropping only
- Extent bounds (minx, miny, maxx, maxy) - if either operation

**Parameters that should NOT change:**
- `initial_water_level` - per user requirement
- Timestep, duration, save times - temporal parameters unchanged
- Material properties - physical parameters unchanged
- Wave/tide data files - copied as-is (validated separately)

---

## Testing Strategy

### Test Cases

1. **Test 1: Crop only**
   - Source: Thorpness project
   - Operation: Crop to 50% of original extent
   - Validate: Grid dimensions reduced, cell size unchanged

2. **Test 2: Resample only**
   - Source: Thorpness project
   - Operation: Change from 1m to 5m cells
   - Validate: Grid dimensions reduced ~5x, extent unchanged

3. **Test 3: Crop and resample**
   - Source: Thorpness project
   - Operation: Crop to 50% extent AND 2m cells
   - Validate: Both operations applied correctly

4. **Test 4: YAML configuration**
   - Source: Project with `.yaml` config
   - Operation: Any modification
   - Validate: New YAML file is valid and re-readable

5. **Test 5: Wave station validation**
   - Source: Project with wave stations shapefile
   - Operation: Crop that excludes some stations
   - Validate: Warning issued for excluded stations

### Validation Checklist

After creating copied project:
- [ ] New project directory structure matches source
- [ ] All raster files present and correct dimensions
- [ ] Configuration file updated with correct parameters
- [ ] `Cme` object initializes without errors
- [ ] Config values can be queried correctly
- [ ] Raster extents align correctly (check with QGIS)
- [ ] No elevation shifts (unless resampling introduced them)
- [ ] Sediment layer totals roughly preserved (for average resampling)

---

## Implementation Order

1. **Phase 1: YAML writing** - Foundational capability needed for config updates
   - Implement `write_yaml()` function
   - Update `update_config()` to support YAML
   - Test YAML round-trip (read → modify → write → read)

2. **Phase 2: Utility functions** - Building blocks for main function
   - `get_project_extent()`
   - `calculate_grid_parameters()`
   - `validate_crop_bbox()`
   - `get_raster_files_in_project()`
   - `check_wave_stations_in_domain()`

3. **Phase 3: Core functionality** - Main copy_project implementation
   - Directory structure creation
   - Raster processing loop
   - Vector processing
   - Configuration updates
   - Report generation

4. **Phase 4: Testing and examples** - Validation and documentation
   - Create example script
   - Test with Thorpness project
   - Document any gotchas or limitations

---

## Future Enhancements

### Not in Initial Implementation
- Command-line interface (CLI tool)
- Interactive bbox selection (QGIS plugin integration)
- Dry-run mode
- Auto-detection of CRS from input data
- Polygon-based cropping (vs bbox only)
- Multiple resampling strategies for sediment (mass-conservative algorithms)
- Undo/rollback functionality
- Progress bars for large operations
- Multi-processing for parallel raster processing

### Potential Follow-ups
- Integration with coastalme-viewer QGIS plugin for visual bbox selection
- Batch processing (crop multiple projects at once)
- Template-based project creation
- Automatic sensitivity studies (run same scenario at multiple resolutions)

---

## Key Insights for Implementation

### From Codebase Analysis

1. **YAML structure is nested but flattened internally**
   - `read_yaml()` creates compound keys like `section_key` or `section_subsection_key`
   - Writing requires reconstructing this hierarchy intelligently
   - Must detect nested patterns from key naming conventions

2. **Raster processing patterns already exist**
   - `xml2raster.py` has `genBase()` showing rasterio usage
   - Uses EPSG:27700 hardcoded throughout
   - Already handles resampling with `transform.scale()` pattern

3. **Configuration paradigm**
   - DataFrame-based manipulation in memory
   - Modifications tracked with `modified` column
   - Saving is separate operation (user must explicitly call write function)

4. **Existing file discovery patterns**
   - `file_search()` in files.py finds files by pattern
   - `collect_files()` discovers outputs by timestep pattern
   - Can adapt these patterns for input file discovery

---

## Open Questions / Notes

1. **Multi-layer sediment projects:** Current plan assumes most projects have 1 layer. Need to test with multi-layer configs (layer_0, layer_1, etc.)

2. **Intervention height files:** If these are rasters, should they be resampled? Probably nearest neighbor to preserve discrete values.

3. **Profile output locations:** If user has specified specific profile numbers to save, do these need updating after crop? (Profile numbering might change)

4. **Existing output directory:** Should we warn if source project has an `out/` directory? (We won't copy it, but user should know)

5. **Relative vs absolute paths:** Config files use relative paths - need to ensure they stay relative and work from new location

---

## Documentation Updates Needed

After implementation:
- Add docstring examples to `project_tools.py`
- Update `CoastalmeTools/CLAUDE.md` with new functionality
- Add section to main repo `CLAUDE.md` about project copying workflow
- Create notebook tutorial showing common use cases
- Update `pyproject.toml` if any new dependencies added

---

## Dependencies

### Existing (already in CoastalmeTools)
- `rasterio` - raster I/O and processing
- `geopandas` - vector operations
- `numpy` - numerical operations
- `pandas` - dataframe operations
- `yaml` - YAML parsing/writing
- `pathlib` - path handling

### No new dependencies required ✓

---

## Success Criteria

Implementation is complete when:
1. ✅ `write_yaml()` can write valid YAML files that can be re-read
2. ✅ `copy_project()` successfully creates working project copies
3. ✅ Example script runs without errors on Thorpness test data
4. ✅ Copied projects can be loaded by `Cme` class
5. ✅ Wave station validation warns when stations outside domain
6. ✅ All test cases pass validation checklist
7. ✅ Code follows project standards (type hints, docstrings, logging)

---

**End of Implementation Plan**
