#!/usr/bin/env python3
"""CoastalmeTools Full Workflow Template (Modern API)

This script demonstrates the complete CoastalME workflow using both:
1. Legacy Cme class API (for backward compatibility)
2. New modular API (Phases 1-2 refactoring)

The new API provides type-safe configuration management and cleaner interfaces
while maintaining full backward compatibility with existing code.

Usage:
    python scripts/template_full_modern.py
"""

import platform
import logging
import shutil
from pathlib import Path

# Legacy API - still fully supported
from CoastalmeTools import Cme
from CoastalmeTools.project_tools import copy_project, get_project_extent

# New modular API (Phases 1-2)
from CoastalmeTools.config import load_config
from CoastalmeTools.core.models import ConfigFormat

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ============================================================================
# Platform-Specific Configuration
# ============================================================================


def get_platform_config():
    """Get platform-specific paths for CoastalME executable and data.

    Returns:
        tuple: (ini_file, run_path, cme_path)
    """
    if platform.system() == "Darwin":
        # macOS paths
        ini_file = Path(
            "/Users/wilfchun/Documents/GitHub/CoastalMe/"
            "CoastalME_data_local/CSE/Thorpness/in/cme.ini"
        )
        run_path = Path(
            "/Users/wilfchun/Documents/GitHub/CoastalMe/CoastalME_data_local/"
        )
        cme_path = Path("/Users/wilfchun/Documents/GitHub/CoastalMe/coastalme/cme")

    elif platform.system() == "Linux":
        # Linux paths
        ini_file = Path(
            # CSE
            # "/home/wilfchun/CoastalME/CoastalME_data_local/CSE/Thorpness/cme.yaml"
            # "/home/wilfchun/CoastalME/CoastalME_data_local/CSE/Southwold/cme.yaml"
            # "/home/wilfchun/CoastalME/CoastalME_data_local/CSE/Winterbourne_Hemsby/cme.yaml"
            # "/home/wilfchun/CoastalME/CoastalME_data_local/CSE/CortonPakefield/cme.yaml"
            # Typology
            # "/home/wilfchun/CoastalME/CoastalME_data_local/Typology/Cliff/cme.yaml"
            # "/home/wilfchun/CoastalME/CoastalME_data_local/Typology/Dune/cme.yaml"
            "/home/wilfchun/CoastalME/CoastalME_data_local/Typology/Dune_hd/cme.yaml"
        )
        run_path = Path("/home/wilfchun/CoastalME/coastalmemn/")
        cme_path = Path("/home/wilfchun/CoastalME/coastalmemn/cme")

    else:
        raise OSError(f"Unsupported platform: {platform.system()}")

    return ini_file, run_path, cme_path


# ============================================================================
# Configuration Inspection (New API Demo)
# ============================================================================


def inspect_configuration(ini_file: Path, run_path: Path):
    """Demonstrate the new configuration API.

    This shows how to use the modern type-safe configuration system
    introduced in Phase 2 of the refactoring.

    Args:
        ini_file: Path to .ini file
        run_path: Execution directory path
    """
    logger.info("=== Configuration Inspection (New API) ===")

    # Load the .ini file to get the main config path
    ini_config = load_config(ini_file)
    logger.info(f"INI file format: {ini_config.format.value}")

    # Get the main configuration file path
    config_path_str = ini_config.find("input")
    config_path = run_path / config_path_str

    # Load the main configuration (auto-detects .dat or .yaml)
    config = load_config(config_path)
    logger.info(f"Main config format: {config.format.value}")

    # Query configuration values (both APIs shown)
    logger.info("\nKey configuration parameters:")

    # Method 1: find() - flexible partial matching (legacy compatible)
    basement = config.find("basement")
    logger.info(f"  Basement DEM: {basement}")

    # Method 2: get() - exact key matching
    output_folder = config.get("output folder", default="out")
    logger.info(f"  Output folder: {output_folder}")

    # Method 3: Dictionary-style access
    if "start date" in config:
        start_date = config["start date"]
        logger.info(f"  Start date: {start_date}")

    # Check simulation parameters
    try:
        duration = config.find("Duration simulation")
        logger.info(f"  Duration: {duration}")
    except KeyError:
        logger.warning("  Duration not found in config")

    # List all available configuration keys
    logger.info(f"\nTotal config parameters: {len(config.keys())}")
    logger.info(f"Config modified: {config.is_modified}")

    return config


# ============================================================================
# Main Workflow
# ============================================================================


def main():
    """Execute complete CoastalME workflow."""

    logger.info("=" * 70)
    logger.info("CoastalmeTools Full Workflow Template")
    logger.info(f"Platform: {platform.system()}")
    logger.info("=" * 70)

    # Get platform-specific configuration
    ini_file, run_path, cme_path = get_platform_config()

    logger.info(f"\nConfiguration:")
    logger.info(f"  INI file: {ini_file}")
    logger.info(f"  Run path: {run_path}")
    logger.info(f"  Executable: {cme_path}")

    # Verify paths exist
    if not ini_file.exists():
        logger.error(f"INI file not found: {ini_file}")
        return 1
    if not cme_path.exists():
        logger.error(f"CoastalME executable not found: {cme_path}")
        return 1

    # ========================================================================
    # Optional: Demonstrate new configuration API
    # ========================================================================
    logger.info("\n" + "=" * 70)
    try:
        config = inspect_configuration(ini_file, run_path)
    except Exception as e:
        logger.warning(f"Configuration inspection failed: {e}")
        logger.info("Continuing with legacy API...")

    # ========================================================================
    # Optional: Project Manipulation
    # ========================================================================
    # Uncomment to copy/crop/resample project before running
    """
    dune_crop = (650417,274952,651927,275692)
    dune_crop = (650417,274952,651927,275692)
    cliff_crop=(653696, 289701, 656062, 297949)  # Need to check

    logger.info("\n" + "=" * 70)
    logger.info("Project Manipulation")
    logger.info("=" * 70)

    source_extent = get_project_extent(str(ini_file))
    logger.info(f"Source extent: {source_extent}")

    dest = Path("/home/wilfchun/CoastalME/CoastalME_data_local/temp/crop/")
    cme = copy_project(
        source_ini_path=ini_file,
        dest_project_path=dest,
        crop_bbox=dune_crop,  # Optional cropping
        # target_cell_size=5.0,  # Optional resampling to 5m cells
        resampling_method="bilinear",
        verbose=True,
    )

    # Update paths to use copied project
    ini_file = dest / "cme.ini"
    run_path = dest
    """

    # ========================================================================
    # Setup Simulation (Legacy API)
    # ========================================================================
    logger.info("\n" + "=" * 70)
    logger.info("Setting up simulation (Legacy API)")
    logger.info("=" * 70)

    cme = Cme(ini_file, run_path)
    logger.info(f"Configuration type: {cme.conf_type}")
    logger.info(f"Input path: {cme.in_path}")
    logger.info(f"Output path: {cme.out_path}")

    # ========================================================================
    # Pre-run Checks
    # ========================================================================
    logger.info("\n" + "=" * 70)
    logger.info("Pre-run Checks")
    logger.info("=" * 70)

    # Check tide data (generates plot)
    try:
        logger.info("Checking tide data...")
        max, min = cme.tide_check()
        logger.info("✓ Tide check complete")
        logger.info(f"  Max tide level: {max}")
        logger.info(f"  Min tide level: {min}")
    except Exception as e:
        logger.warning(f"Tide check failed: {e}")

    # Optional: Interactive preflight checks
    # Uncomment to enable quick-start model generation, wave rose plots, etc.
    # cme.preflight_checks()
    # cme.wave_check(invert=True)
    cme.wave_check()

    # Build initial conditions (t=0)
    # logger.info("Building initial model state (t=0)...")
    # cme.build_model()
    # logger.info("✓ Initial state built")

    # ========================================================================
    # Run Simulation
    # ========================================================================
    logger.info("\n" + "=" * 70)
    logger.info("Running CoastalME Simulation")
    logger.info("=" * 70)

    logger.info("Starting CoastalME...")
    logger.info("(This may take several minutes depending on model size)")

    return_code = cme.run(cme_path)

    # Check if simulation succeeded
    # if return_code == 0:
    #     logger.info("✓ Simulation completed successfully")
    # else:
    #     logger.error(f"✗ Simulation failed with return code: {return_code}")
    #     logger.info("\nError Summary:")
    #     cme.return_rescue()
    #     return return_code

    # ========================================================================
    # Collate Results
    # ========================================================================
    logger.info("\n" + "=" * 70)
    logger.info("Collating Results")
    logger.info("=" * 70)

    # Define output variables to include in NetCDF
    raster_vars = [
        "landform_class",
        "polygon_raster",
        "rcoast",
        "rcoast_normal",
        "top_elevation",
        "total_actual_beach_erosion",
        "total_actual_platform_erosion",
        "total_cliff_collapse",
        "total_avalanche_deposition",
        "wave_height",
        "cliff",
        "dirty_cells",
        "sediment_transport"
    ]

    # Define vector outputs to include in GeoPackage
    vector_vars = [
        "breaking_wave_height",
        "cliff_notch",
        "coast",
        "coast_lower",
        "coast_upper",
        "cliff_edge",
        "run_up",
        "coast_curvature",
        "invalid_normals",
        "normals",
        "wave_energy",
        "wave_setup",
        "storm_surge",
        "wave_transect_points"
    ]

    logger.info(f"Raster variables: {len(raster_vars)}")
    logger.info(f"Vector variables: {len(vector_vars)}")

    try:
        logger.info("Creating NetCDF and GeoPackage outputs...")
        cme.collate_results(vars=raster_vars, vars_v=vector_vars)
        logger.info("✓ Results collated successfully")

        # Output file locations
        netcdf_file = cme.out_path / "all_vars.nc"
        gpkg_file = cme.out_path / "all_vect.gpkg"

        win_downloads = "/mnt/c/Users/wchun/Downloads/"
        shutil.copy(netcdf_file, win_downloads)
        shutil.copy(gpkg_file, win_downloads)

        if netcdf_file.exists():
            logger.info(f"  NetCDF: {netcdf_file}")
        if gpkg_file.exists():
            logger.info(f"  GeoPackage: {gpkg_file}")

    except ValueError as e:
        logger.error(f"✗ Result collation failed: {e}")
        return 1
    except Exception as e:
        logger.error(f"✗ Unexpected error during collation: {e}")
        return 1

    # ========================================================================
    # Summary
    # ========================================================================
    logger.info("\n" + "=" * 70)
    logger.info("Workflow Complete")
    logger.info("=" * 70)

    logger.info("\nOutput files:")
    logger.info(f"  Directory: {cme.out_path}")
    logger.info(f"  NetCDF: all_vars.nc")
    logger.info(f"  GeoPackage: all_vars.gpkg")
    logger.info(f"  Profile plots: *.png")

    logger.info("\nNext steps:")
    logger.info("  1. Open NetCDF in QGIS using the CoastalME viewer plugin")
    logger.info("  2. Inspect vector outputs in the GeoPackage")
    logger.info("  3. Review profile plots in the output directory")

    return 0


# ============================================================================
# Entry Point
# ============================================================================

if __name__ == "__main__":
    import sys

    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        logger.info("\n\nWorkflow interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.exception(f"Workflow failed with unexpected error: {e}")
        sys.exit(1)
