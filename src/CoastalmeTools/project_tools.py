"""
Project manipulation tools for CoastalME.

This module provides utilities for creating modified copies of CoastalME projects,
including cropping to smaller geographic areas and resampling to different resolutions.

Author: CoastalME Development Team
Date: 2025-01-13
"""

import logging
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Union
import shutil
import numpy as np
import rasterio
from rasterio.windows import Window, from_bounds
from rasterio.transform import Affine
from rasterio.enums import Resampling
import geopandas as gpd
from shapely.geometry import box

# Get module logger
logger = logging.getLogger(__name__)


def copy_project(
    source_ini_path: Union[str, Path],
    dest_project_path: Union[str, Path],
    crop_bbox: Optional[Tuple[float, float, float, float]] = None,
    target_cell_size: Optional[float] = None,
    resampling_method: str = "bilinear",
    sediment_resampling: str = "average",
    validate: bool = True,
    verbose: bool = True
):
    """
    Create a modified copy of a CoastalME project with optional cropping and resampling.

    Args:
        source_ini_path: Path to source project .ini file
        dest_project_path: Destination directory for new project
        crop_bbox: Bounding box (minx, miny, maxx, maxy) in EPSG:27700, or None
        target_cell_size: New cell size in meters, or None to keep original
        resampling_method: Method for DEM resampling ('bilinear', 'cubic', 'nearest')
        sediment_resampling: Method for sediment layers ('average', 'sum')
        validate: Run validation checks (not full preflight)
        verbose: Print progress messages

    Returns:
        Cme object initialized with the new project

    Raises:
        ValueError: If crop_bbox is invalid or parameters are incompatible
        FileNotFoundError: If source files are missing
        IOError: If destination cannot be created

    Example:
        >>> from CoastalmeTools.project_tools import copy_project
        >>> cme = copy_project(
        ...     source_ini_path="/path/to/project/cme.ini",
        ...     dest_project_path="/path/to/new_project",
        ...     crop_bbox=(640000, 263000, 642000, 265000),
        ...     target_cell_size=5.0,
        ...     verbose=True
        ... )
        >>> print(f"New project has {cme.find_config('timestep')} timestep")
    """
    from .Cme import Cme, write_ini, write_yaml

    # Convert paths
    source_ini_path = Path(source_ini_path)
    dest_project_path = Path(dest_project_path)

    if verbose:
        print("\n" + "=" * 70)
        print("CoastalME Project Copy")
        print("=" * 70)
        print(f"Source: {source_ini_path}")
        print(f"Destination: {dest_project_path}")

    # Initialize report
    report = ProjectCopyReport()

    # ========== Step 1: Load and validate source project ==========
    if verbose:
        print("\n[1/8] Loading source project...")

    if not source_ini_path.exists():
        raise FileNotFoundError(f"Source ini file not found: {source_ini_path}")

    source_cme = Cme(ini=source_ini_path, run_path=source_ini_path.parent)

    # Get basement DEM info
    basement_rel_path = source_cme.find_config("basement")
    basement_path = source_cme.in_path.parent / basement_rel_path

    if not basement_path.exists():
        raise FileNotFoundError(f"Basement DEM not found: {basement_path}")

    with rasterio.open(basement_path) as src:
        source_transform = src.transform
        source_shape = src.shape
        source_bounds = src.bounds
        source_crs = src.crs

    source_extent = (source_bounds.left, source_bounds.bottom,
                     source_bounds.right, source_bounds.top)
    source_cell_size = (abs(source_transform.a), abs(source_transform.e))

    report.old_extent = source_extent
    report.old_cell_size = source_cell_size
    report.old_grid_dims = (source_shape[1], source_shape[0])  # (nx, ny)

    if verbose:
        print(f"  ✓ Source grid: {source_shape[1]} x {source_shape[0]} cells")
        print(f"  ✓ Source cell size: {source_cell_size[0]:.2f} x {source_cell_size[1]:.2f} m")

    # ========== Step 2: Validate crop bbox if provided ==========
    if crop_bbox is not None:
        if verbose:
            print("\n[2/8] Validating crop area...")

        is_valid, warnings = validate_crop_bbox(source_extent, crop_bbox)

        if not is_valid:
            raise ValueError(f"Invalid crop bbox: {warnings}")

        if warnings:
            report.warnings.extend(warnings)
            if verbose:
                for warning in warnings:
                    print(f"  ⚠️  {warning}")
    else:
        if verbose:
            print("\n[2/8] No cropping (using full extent)")

    # ========== Step 3: Calculate new grid parameters ==========
    if verbose:
        print("\n[3/8] Calculating new grid parameters...")

    new_params = calculate_grid_parameters(
        source_transform=source_transform,
        source_shape=source_shape,
        crop_bbox=crop_bbox,
        target_cell_size=target_cell_size
    )

    report.new_extent = new_params['extent']
    report.new_cell_size = (new_params['dx'], new_params['dy'])
    report.new_grid_dims = (new_params['nx'], new_params['ny'])

    old_cells = report.old_grid_dims[0] * report.old_grid_dims[1]
    new_cells = report.new_grid_dims[0] * report.new_grid_dims[1]
    report.runtime_ratio = estimate_runtime_change(old_cells, new_cells)

    if verbose:
        print(f"  ✓ New grid: {new_params['nx']} x {new_params['ny']} cells")
        print(f"  ✓ New cell size: {new_params['dx']:.2f} x {new_params['dy']:.2f} m")
        print(f"  ✓ Estimated runtime: {report.runtime_ratio:.1%} of original")

    # ========== Step 4: Create destination directory structure ==========
    if verbose:
        print("\n[4/8] Creating destination directory...")

    if dest_project_path.exists():
        if verbose:
            print(f"  ⚠️  Destination exists, will overwrite")
        shutil.rmtree(dest_project_path)

    dest_project_path.mkdir(parents=True)
    dest_in_path = dest_project_path / "in"
    dest_in_path.mkdir()
    dest_out_path = dest_project_path / "out"
    dest_out_path.mkdir()

    if verbose:
        print(f"  ✓ Created: {dest_project_path}")

    # ========== Step 5: Process raster files ==========
    if verbose:
        print("\n[5/8] Processing raster files...")

    raster_files = get_raster_files_in_project(source_cme)
    report.files_processed['rasters'] = 0

    # Map resampling method names to rasterio enums
    resampling_map = {
        'nearest': Resampling.nearest,
        'bilinear': Resampling.bilinear,
        'cubic': Resampling.cubic,
        'average': Resampling.average,
        'sum': Resampling.sum,
    }

    dem_resampling = resampling_map.get(resampling_method, Resampling.bilinear)
    sed_resampling = resampling_map.get(sediment_resampling, Resampling.average)

    # Process basement DEM
    if raster_files['basement']:
        if verbose:
            print(f"  Processing basement DEM...")

        _process_single_raster(
            src_path=raster_files['basement'],
            dest_path=dest_in_path / raster_files['basement'].name,
            new_transform=new_params['transform'],
            new_shape=(new_params['ny'], new_params['nx']),
            resampling_method=dem_resampling,
            crop_bbox=crop_bbox,
            verbose=verbose
        )
        report.files_processed['rasters'] += 1

    # Process top/initial surface elevation (if exists)
    if raster_files['top']:
        if verbose:
            print(f"  Processing top/initial surface elevation...")

        _process_single_raster(
            src_path=raster_files['top'],
            dest_path=dest_in_path / raster_files['top'].name,
            new_transform=new_params['transform'],
            new_shape=(new_params['ny'], new_params['nx']),
            resampling_method=dem_resampling,
            crop_bbox=crop_bbox,
            verbose=verbose
        )
        report.files_processed['rasters'] += 1

    # Process sediment layers
    if raster_files['sediment_layers']:
        if verbose:
            print(f"  Processing {len(raster_files['sediment_layers'])} sediment layers...")

        for layer_num, sed_type, src_path in raster_files['sediment_layers']:
            _process_single_raster(
                src_path=src_path,
                dest_path=dest_in_path / src_path.name,
                new_transform=new_params['transform'],
                new_shape=(new_params['ny'], new_params['nx']),
                resampling_method=sed_resampling,
                crop_bbox=crop_bbox,
                verbose=False  # Don't print each one
            )
            report.files_processed['rasters'] += 1

        if verbose:
            print(f"  ✓ Processed {len(raster_files['sediment_layers'])} sediment layers")

    # Process intervention rasters (use nearest neighbor to preserve classes)
    if raster_files['interventions']:
        if verbose:
            print(f"  Processing {len(raster_files['interventions'])} intervention rasters...")

        for src_path in raster_files['interventions']:
            if src_path.exists():  # May be optional
                _process_single_raster(
                    src_path=src_path,
                    dest_path=dest_in_path / src_path.name,
                    new_transform=new_params['transform'],
                    new_shape=(new_params['ny'], new_params['nx']),
                    resampling_method=Resampling.nearest,  # Preserve discrete values
                    crop_bbox=crop_bbox,
                    verbose=False
                )
                report.files_processed['rasters'] += 1

        if verbose:
            print(f"  ✓ Processed {len(raster_files['interventions'])} intervention files")

    if verbose:
        print(f"  ✓ Total rasters processed: {report.files_processed['rasters']}")

    # ========== Step 6: Copy and process non-raster files ==========
    if verbose:
        print("\n[6/8] Copying non-raster input files...")

    # Copy wave data, tide data, and other text files
    source_in_path = source_cme.in_path.parent
    non_raster_count = 0

    for file_path in source_in_path.iterdir():
        if file_path.is_file():
            # Skip raster files (already processed)
            if file_path.suffix.lower() in ['.tif', '.tiff', '.asc', '.grd']:
                continue

            # Copy text files, shapefiles, etc.
            dest_file = dest_in_path / file_path.name
            shutil.copy2(file_path, dest_file)
            non_raster_count += 1

    # Process vector files (clip to new extent if cropping)
    report.files_processed['vectors'] = 0
    if crop_bbox is not None:
        for file_path in dest_in_path.iterdir():
            if file_path.suffix.lower() == '.shp':
                try:
                    _clip_vector_file(file_path, crop_bbox)
                    report.files_processed['vectors'] += 1
                except Exception as e:
                    logger.warning(f"Could not clip vector file {file_path.name}: {e}")

    if verbose:
        print(f"  ✓ Copied {non_raster_count} non-raster files")
        if report.files_processed['vectors'] > 0:
            print(f"  ✓ Clipped {report.files_processed['vectors']} vector files")

    # ========== Step 7: Update configuration files ==========
    if verbose:
        print("\n[7/8] Updating configuration files...")

    # Copy and update .ini file
    dest_ini = dest_project_path / source_ini_path.name
    shutil.copy2(source_ini_path, dest_ini)

    # Update main configuration file
    dest_config_path = dest_in_path / source_cme.in_path.name

    # Copy configuration
    if source_cme.conf_type == "dat":
        # Copy and update .dat file
        config_df = source_cme.config_df.copy()

        # No updates needed for .dat files - grid is read from rasters
        # Just copy it
        write_ini(dest_config_path, config_df)

        if verbose:
            print(f"  ✓ Copied .dat configuration")

    elif source_cme.conf_type == "yaml":
        # Copy and update .yaml file
        config_df = source_cme.config_df.copy()

        # No updates needed - CoastalME reads grid from rasters
        # But we can optionally update comments/metadata
        write_yaml(dest_config_path, config_df)

        if verbose:
            print(f"  ✓ Copied .yaml configuration")

    # ========== Step 8: Validate wave stations ==========
    if verbose:
        print("\n[8/8] Validating wave stations...")

    try:
        wave_shp_name = source_cme.find_config("wave_height_shape")
        if wave_shp_name and wave_shp_name.strip():
            wave_shp = dest_in_path / wave_shp_name

            if wave_shp.exists():
                all_inside, outside_stations = check_wave_stations_in_domain(
                    wave_shp, new_params['extent']
                )

                if not all_inside:
                    warning_msg = (
                        f"{len(outside_stations)} wave station(s) fall outside new domain: "
                        f"{', '.join(outside_stations)}"
                    )
                    report.warnings.append(warning_msg)
                    if verbose:
                        print(f"  ⚠️  {warning_msg}")
                else:
                    if verbose:
                        print(f"  ✓ All wave stations within new domain")
            else:
                if verbose:
                    print(f"  ⚠️  Wave station shapefile not found (may be okay)")
    except (KeyError, ValueError):
        if verbose:
            print(f"  • No wave station shapefile configured")

    # ========== Finalize ==========
    if verbose:
        print("\n" + "=" * 70)
        print("✅ Project copy complete!")
        report.print_summary()

    # Initialize and return new Cme object
    new_cme = Cme(ini=dest_ini, run_path=dest_project_path)

    return new_cme


def _process_single_raster(
    src_path: Path,
    dest_path: Path,
    new_transform: Affine,
    new_shape: Tuple[int, int],
    resampling_method: Resampling,
    crop_bbox: Optional[Tuple[float, float, float, float]] = None,
    verbose: bool = False
):
    """
    Process a single raster file (crop and/or resample).

    Args:
        src_path: Source raster path
        dest_path: Destination raster path
        new_transform: Target transform
        new_shape: Target shape (height, width)
        resampling_method: Resampling method from rasterio.enums.Resampling
        crop_bbox: Optional crop bounds (minx, miny, maxx, maxy)
        verbose: Print progress
    """
    if verbose:
        print(f"    Processing {src_path.name}...")

    with rasterio.open(src_path) as src:
        # Read metadata
        profile = src.profile.copy()

        # Update profile for output
        profile.update({
            'transform': new_transform,
            'width': new_shape[1],
            'height': new_shape[0],
        })

        # Determine window if cropping
        if crop_bbox is not None:
            window = from_bounds(*crop_bbox, transform=src.transform)
        else:
            window = None

        # Read and resample data
        data = src.read(
            1,
            out_shape=new_shape,
            resampling=resampling_method,
            window=window,
            masked=True
        )

        # Write output
        with rasterio.open(dest_path, 'w', **profile) as dst:
            dst.write(data, 1)


def _clip_vector_file(vector_path: Path, clip_bbox: Tuple[float, float, float, float]):
    """
    Clip a vector file to a bounding box.

    Args:
        vector_path: Path to shapefile (will be modified in place)
        clip_bbox: (minx, miny, maxx, maxy) to clip to
    """
    # Read shapefile
    gdf = gpd.read_file(vector_path)

    # Create clip polygon
    clip_poly = box(*clip_bbox)

    # Clip geometries
    gdf_clipped = gdf[gdf.intersects(clip_poly)].copy()
    gdf_clipped['geometry'] = gdf_clipped.intersection(clip_poly)

    # Remove empty geometries
    gdf_clipped = gdf_clipped[~gdf_clipped.is_empty]

    # Write back
    if len(gdf_clipped) > 0:
        gdf_clipped.to_file(vector_path)
    else:
        logger.warning(f"Vector file {vector_path.name} has no features after clipping")


def get_project_extent(ini_path: str) -> Tuple[float, float, float, float]:
    """
    Extract bounding box from a project's basement DEM file.

    Args:
        ini_path: Path to project .ini file

    Returns:
        Tuple of (minx, miny, maxx, maxy) in the raster's CRS (typically EPSG:27700)

    Raises:
        FileNotFoundError: If ini file or basement DEM not found
        ValueError: If basement DEM cannot be read

    Example:
        >>> extent = get_project_extent("/path/to/project/cme.ini")
        >>> print(f"Project extent: {extent}")
        Project extent: (640000.0, 263000.0, 642000.0, 265000.0)
    """
    from .Cme import Cme

    ini_path = Path(ini_path)
    if not ini_path.exists():
        raise FileNotFoundError(f"INI file not found: {ini_path}")

    # Load project to get basement DEM path
    cme = Cme(ini=ini_path, run_path=ini_path.parent)
    basement_path = cme.in_path.parent / cme.find_config("basement")

    if not basement_path.exists():
        raise FileNotFoundError(f"Basement DEM not found: {basement_path}")

    # Read extent from raster
    with rasterio.open(basement_path) as src:
        bounds = src.bounds
        return (bounds.left, bounds.bottom, bounds.right, bounds.top)


def calculate_grid_parameters(
    source_transform: Affine,
    source_shape: Tuple[int, int],
    crop_bbox: Optional[Tuple[float, float, float, float]] = None,
    target_cell_size: Optional[float] = None
) -> Dict:
    """
    Calculate new grid parameters after cropping and/or resampling.

    Args:
        source_transform: Affine transform from source raster
        source_shape: (height, width) of source raster
        crop_bbox: (minx, miny, maxx, maxy) to crop to, or None for no cropping
        target_cell_size: Target cell size in map units, or None to keep original

    Returns:
        Dictionary with keys:
            - 'nx': number of columns
            - 'ny': number of rows
            - 'dx': cell width
            - 'dy': cell height (positive value)
            - 'origin_x': x-coordinate of origin (top-left corner)
            - 'origin_y': y-coordinate of origin (top-left corner)
            - 'transform': new Affine transform
            - 'extent': (minx, miny, maxx, maxy)

    Example:
        >>> params = calculate_grid_parameters(
        ...     source_transform=src.transform,
        ...     source_shape=src.shape,
        ...     crop_bbox=(640000, 263000, 641000, 264000),
        ...     target_cell_size=5.0
        ... )
        >>> print(f"New grid: {params['nx']} x {params['ny']} cells")
    """
    # Extract source parameters
    source_cell_x = abs(source_transform.a)  # cell width
    source_cell_y = abs(source_transform.e)  # cell height

    # Determine final cell size
    if target_cell_size is not None:
        final_cell_x = target_cell_size
        final_cell_y = target_cell_size
    else:
        final_cell_x = source_cell_x
        final_cell_y = source_cell_y

    # Determine extent
    if crop_bbox is not None:
        minx, miny, maxx, maxy = crop_bbox
    else:
        # Use full source extent
        minx = source_transform.c
        maxy = source_transform.f
        maxx = minx + source_shape[1] * source_cell_x
        miny = maxy - source_shape[0] * source_cell_y

    # Calculate new dimensions
    width = maxx - minx
    height = maxy - miny
    nx = int(np.round(width / final_cell_x))
    ny = int(np.round(height / final_cell_y))

    # Create new transform
    new_transform = Affine.translation(minx, maxy) * Affine.scale(final_cell_x, -final_cell_y)

    return {
        'nx': nx,
        'ny': ny,
        'dx': final_cell_x,
        'dy': final_cell_y,
        'origin_x': minx,
        'origin_y': maxy,
        'transform': new_transform,
        'extent': (minx, miny, maxx, maxy)
    }


def validate_crop_bbox(
    source_extent: Tuple[float, float, float, float],
    crop_bbox: Tuple[float, float, float, float],
    buffer_cells: int = 10,
    min_dimension: int = 50
) -> Tuple[bool, List[str]]:
    """
    Validate crop bounding box and return warnings.

    Args:
        source_extent: (minx, miny, maxx, maxy) of source project
        crop_bbox: (minx, miny, maxx, maxy) of desired crop area
        buffer_cells: Minimum recommended buffer from edges (in cells)
        min_dimension: Minimum recommended dimension (in cells)

    Returns:
        Tuple of (is_valid, warnings) where:
            - is_valid: True if crop is usable (may still have warnings)
            - warnings: List of warning messages

    Example:
        >>> valid, warnings = validate_crop_bbox(
        ...     source_extent=(640000, 263000, 642000, 265000),
        ...     crop_bbox=(640100, 263100, 641900, 264900)
        ... )
        >>> if warnings:
        ...     for w in warnings:
        ...         print(f"Warning: {w}")
    """
    src_minx, src_miny, src_maxx, src_maxy = source_extent
    crop_minx, crop_miny, crop_maxx, crop_maxy = crop_bbox

    warnings = []
    is_valid = True

    # Check if crop is completely outside source
    if (crop_minx >= src_maxx or crop_maxx <= src_minx or
        crop_miny >= src_maxy or crop_maxy <= src_miny):
        is_valid = False
        warnings.append("Crop area is completely outside source extent")
        return is_valid, warnings

    # Check if crop extends beyond source
    if crop_minx < src_minx:
        warnings.append(f"Crop extends {src_minx - crop_minx:.1f}m west of source extent")
    if crop_maxx > src_maxx:
        warnings.append(f"Crop extends {crop_maxx - src_maxx:.1f}m east of source extent")
    if crop_miny < src_miny:
        warnings.append(f"Crop extends {src_miny - crop_miny:.1f}m south of source extent")
    if crop_maxy > src_maxy:
        warnings.append(f"Crop extends {crop_maxy - src_maxy:.1f}m north of source extent")

    # Check crop dimensions
    crop_width = crop_maxx - crop_minx
    crop_height = crop_maxy - crop_miny

    if crop_width < min_dimension:
        warnings.append(
            f"Crop width ({crop_width:.1f}m) is very small. "
            f"Minimum {min_dimension}m recommended for model stability"
        )

    if crop_height < min_dimension:
        warnings.append(
            f"Crop height ({crop_height:.1f}m) is very small. "
            f"Minimum {min_dimension}m recommended for model stability"
        )

    # Check buffer from edges (only if completely inside source)
    if (crop_minx >= src_minx and crop_maxx <= src_maxx and
        crop_miny >= src_miny and crop_maxy <= src_maxy):

        buffer_distance = buffer_cells  # Assume ~1m cells for warning
        if (crop_minx - src_minx) < buffer_distance:
            warnings.append(
                f"Crop is close to western edge ({crop_minx - src_minx:.1f}m). "
                f"Consider {buffer_distance}m buffer for boundary conditions"
            )
        if (src_maxx - crop_maxx) < buffer_distance:
            warnings.append(
                f"Crop is close to eastern edge ({src_maxx - crop_maxx:.1f}m). "
                f"Consider {buffer_distance}m buffer for boundary conditions"
            )

    return is_valid, warnings


def get_raster_files_in_project(cme) -> Dict[str, List]:
    """
    Discover all raster files referenced in a project configuration.

    Args:
        cme: CoastalmeTools.Cme object

    Returns:
        Dictionary with keys:
            - 'basement': Path to basement DEM
            - 'top': Path to top/initial surface elevation (if exists)
            - 'sediment_layers': List of tuples (layer_num, sediment_type, path)
            - 'interventions': List of intervention raster paths
            - 'other': List of other raster file paths

    Example:
        >>> from CoastalmeTools import Cme
        >>> cme = Cme(ini="project/cme.ini", run_path="project")
        >>> files = get_raster_files_in_project(cme)
        >>> print(f"Basement: {files['basement']}")
        >>> for layer, sed_type, path in files['sediment_layers']:
        ...     print(f"Layer {layer} {sed_type}: {path}")
    """
    from .Cme import Cme

    in_dir = cme.in_path.parent
    files = {
        'basement': None,
        'top': None,
        'sediment_layers': [],
        'interventions': [],
        'other': []
    }

    # Get basement DEM
    try:
        basement_file = cme.find_config("basement")
        if basement_file:
            files['basement'] = in_dir / basement_file
    except (KeyError, ValueError):
        logger.warning("No basement DEM found in configuration")

    # Look for top/initial surface file
    # This file may not be in config, but often exists in projects
    # Try common naming patterns
    for top_pattern in ['*_top.asc', '*_top.tif', 'top.asc', 'top.tif']:
        top_files = list(in_dir.glob(top_pattern))
        if top_files:
            files['top'] = top_files[0]  # Use first match
            break

    # Get sediment layers
    # Determine number of layers
    try:
        num_layers = int(cme.find_config("num_layers"))
    except (KeyError, ValueError):
        num_layers = 1  # Default to 1 layer

    # Define all possible sediment types
    # These are the keys after read_yaml() flattens the YAML structure
    sediment_types = [
        ('unconsolidated_fine', 'unconsolidated fine'),
        ('unconsolidated_sand', 'unconsolidated sand'),
        ('unconsolidated_coarse', 'unconsolidated coarse'),
        ('consolidated_fine', 'consolidated fine'),
        ('consolidated_sand', 'consolidated sand'),
        ('consolidated_coarse', 'consolidated coarse'),
    ]

    for layer_num in range(num_layers):
        for key_suffix, display_name in sediment_types:
            try:
                # Try to find sediment file for this layer
                # In YAML files, keys are flattened as "layer_X_TYPE"
                # In .dat files, keys might be just "Initial TYPE file"
                search_keys = [
                    f"layer_{layer_num}_{key_suffix}",  # YAML format
                    key_suffix,  # Direct key without prefix
                    f"Initial {display_name} file",  # .dat format
                ]

                sed_file = None
                for search_key in search_keys:
                    try:
                        sed_file = cme.find_config(search_key)
                        if sed_file and sed_file.strip():
                            break
                    except (KeyError, ValueError):
                        continue

                if sed_file and sed_file.strip():  # Found a valid file path
                    sed_path = in_dir / sed_file
                    # Only add if file actually exists
                    if sed_path.exists():
                        files['sediment_layers'].append(
                            (layer_num, display_name, sed_path)
                        )
            except Exception as e:
                # Log but don't fail - this sediment type might not be present
                logger.debug(f"Could not find {display_name} for layer {layer_num}: {e}")
                continue

    # Get intervention files
    try:
        intervention_class = cme.find_config("intervention_class")
        if intervention_class and intervention_class.strip():
            int_path = in_dir / intervention_class
            if int_path.exists():
                files['interventions'].append(int_path)
    except (KeyError, ValueError):
        pass

    try:
        intervention_height = cme.find_config("intervention_height")
        if intervention_height and intervention_height.strip():
            int_path = in_dir / intervention_height
            if int_path.exists():
                files['interventions'].append(int_path)
    except (KeyError, ValueError):
        pass

    return files


def check_wave_stations_in_domain(
    wave_shapefile: Path,
    domain_bbox: Tuple[float, float, float, float]
) -> Tuple[bool, List[str]]:
    """
    Check if wave station locations fall within the new domain.

    Args:
        wave_shapefile: Path to wave stations shapefile
        domain_bbox: (minx, miny, maxx, maxy) of new domain in same CRS

    Returns:
        Tuple of (all_inside, warnings) where:
            - all_inside: True if all stations are within domain
            - warnings: List of station IDs/names that fall outside

    Example:
        >>> all_ok, warnings = check_wave_stations_in_domain(
        ...     wave_shapefile=Path("in/wave_stations.shp"),
        ...     domain_bbox=(640000, 263000, 642000, 265000)
        ... )
        >>> if not all_ok:
        ...     print(f"⚠️  {len(warnings)} station(s) outside domain")
    """
    if not wave_shapefile.exists():
        logger.warning(f"Wave station file not found: {wave_shapefile}")
        return True, []  # Can't check, but not an error

    try:
        # Read wave stations shapefile
        stations_gdf = gpd.read_file(wave_shapefile)

        # Create domain polygon
        domain_poly = box(*domain_bbox)

        # Check each station
        outside_stations = []
        for idx, station in stations_gdf.iterrows():
            point = station.geometry

            if not domain_poly.contains(point):
                # Try to get station identifier
                station_id = None
                for id_col in ['id', 'ID', 'station_id', 'name', 'Name']:
                    if id_col in station.index:
                        station_id = station[id_col]
                        break

                if station_id is None:
                    station_id = f"Station {idx}"

                outside_stations.append(str(station_id))

        all_inside = len(outside_stations) == 0

        return all_inside, outside_stations

    except Exception as e:
        logger.error(f"Error checking wave stations: {e}")
        return True, []  # Don't fail the whole operation


def estimate_runtime_change(old_cells: int, new_cells: int) -> float:
    """
    Estimate computational time multiplier based on cell count change.

    CoastalME runtime is roughly proportional to the number of cells,
    though some operations scale non-linearly.

    Args:
        old_cells: Total cells in original grid (nx * ny)
        new_cells: Total cells in new grid

    Returns:
        Estimated runtime ratio (e.g., 0.25 = 4x faster, 2.0 = 2x slower)

    Example:
        >>> ratio = estimate_runtime_change(old_cells=1000*500, new_cells=500*250)
        >>> print(f"Estimated runtime: {ratio:.1%} of original")
        Estimated runtime: 25.0% of original
    """
    if old_cells == 0:
        return 1.0

    return new_cells / old_cells


# Summary class for reporting
class ProjectCopyReport:
    """
    Summary report of changes made during project copy operation.

    Attributes:
        old_extent: Original project extent (minx, miny, maxx, maxy)
        new_extent: New project extent
        old_cell_size: Original cell size (dx, dy)
        new_cell_size: New cell size
        old_grid_dims: Original grid dimensions (nx, ny)
        new_grid_dims: New grid dimensions
        runtime_ratio: Estimated computation time multiplier
        files_processed: Dictionary of file counts by type
        warnings: List of warning messages
    """

    def __init__(self):
        self.old_extent: Optional[Tuple] = None
        self.new_extent: Optional[Tuple] = None
        self.old_cell_size: Optional[Tuple] = None
        self.new_cell_size: Optional[Tuple] = None
        self.old_grid_dims: Optional[Tuple] = None
        self.new_grid_dims: Optional[Tuple] = None
        self.runtime_ratio: float = 1.0
        self.files_processed: Dict[str, int] = {}
        self.warnings: List[str] = []

    def print_summary(self):
        """Print a formatted summary of the project copy operation."""
        print("\n" + "=" * 70)
        print("Project Copy Summary")
        print("=" * 70)

        if self.old_extent and self.new_extent:
            print("\nExtent Changes:")
            print(f"  Original: {self.old_extent}")
            print(f"  New:      {self.new_extent}")

        if self.old_cell_size and self.new_cell_size:
            print("\nCell Size:")
            print(f"  Original: {self.old_cell_size[0]:.2f} x {self.old_cell_size[1]:.2f} m")
            print(f"  New:      {self.new_cell_size[0]:.2f} x {self.new_cell_size[1]:.2f} m")

        if self.old_grid_dims and self.new_grid_dims:
            print("\nGrid Dimensions:")
            print(f"  Original: {self.old_grid_dims[0]} x {self.old_grid_dims[1]} cells "
                  f"({self.old_grid_dims[0] * self.old_grid_dims[1]:,} total)")
            print(f"  New:      {self.new_grid_dims[0]} x {self.new_grid_dims[1]} cells "
                  f"({self.new_grid_dims[0] * self.new_grid_dims[1]:,} total)")

        print(f"\nEstimated Runtime: {self.runtime_ratio:.1%} of original")

        if self.files_processed:
            print("\nFiles Processed:")
            for file_type, count in self.files_processed.items():
                print(f"  {file_type}: {count}")

        if self.warnings:
            print("\n⚠️  Warnings:")
            for warning in self.warnings:
                print(f"  - {warning}")

        print("=" * 70 + "\n")
