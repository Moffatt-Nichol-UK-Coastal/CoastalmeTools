#!/usr/bin/env python3
"""
Example script demonstrating how to create modified copies of CoastalME projects.

This script shows three common use cases:
1. Cropping to a smaller area
2. Changing resolution
3. Both cropping and resampling

Usage:
    python copy_project_example.py

Author: CoastalME Development Team
Date: 2025-01-13
"""

from pathlib import Path
import sys

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from CoastalmeTools.project_tools import copy_project, get_project_extent

def main():
    print("=" * 70)
    print("CoastalME Project Copy Examples")
    print("=" * 70)

    # Source project
    source_ini = Path("/home/wilfchun/CoastalME/CoastalME_data_local/CSE/Thorpness/cme.ini")

    if not source_ini.exists():
        print(f"❌ Error: Source project not found at {source_ini}")
        print("Please update the source_ini path in this script.")
        return 1

    # Get source extent for reference
    source_extent = get_project_extent(str(source_ini))
    print(f"\nSource project extent: {source_extent}")
    print(f"Width:  {source_extent[2] - source_extent[0]:.1f} m")
    print(f"Height: {source_extent[3] - source_extent[1]:.1f} m")

    # Calculate a reasonable crop box (80% of extent, centered)
    margin_x = (source_extent[2] - source_extent[0]) * 0.1
    margin_y = (source_extent[3] - source_extent[1]) * 0.1
    crop_bbox = (
        source_extent[0] + margin_x,
        source_extent[1] + margin_y,
        source_extent[2] - margin_x,
        source_extent[3] - margin_y
    )

    # ==========================================================================
    # Example 1: Crop Only
    # ==========================================================================
    print("\n" + "=" * 70)
    print("Example 1: Cropping to 80% of original extent")
    print("=" * 70)

    dest1 = Path("/home/wilfchun/CoastalME/CoastalME_data_local/CSE/Thorpness_cropped")

    try:
        cme1 = copy_project(
            source_ini_path=source_ini,
            dest_project_path=dest1,
            crop_bbox=crop_bbox,
            target_cell_size=None,  # Keep original cell size
            verbose=True
        )

        print(f"\n✅ Example 1 complete!")
        print(f"   New project at: {dest1}")
        print(f"   You can now run: cme = Cme(ini='{dest1}/cme.ini', run_path='{dest1}')")

    except Exception as e:
        print(f"\n❌ Example 1 failed: {e}")
        import traceback
        traceback.print_exc()

    # ==========================================================================
    # Example 2: Resample Only (coarser resolution for rapid prototyping)
    # ==========================================================================
    print("\n" + "=" * 70)
    print("Example 2: Resampling to 5m cells (rapid prototyping)")
    print("=" * 70)

    dest2 = Path("/home/wilfchun/CoastalME/CoastalME_data_local/CSE/Thorpness_5m")

    try:
        cme2 = copy_project(
            source_ini_path=source_ini,
            dest_project_path=dest2,
            crop_bbox=None,  # Keep full extent
            target_cell_size=5.0,  # Change to 5m cells
            resampling_method="bilinear",
            verbose=True
        )

        print(f"\n✅ Example 2 complete!")
        print(f"   New project at: {dest2}")
        print(f"   This project should run ~25x faster (if original was 1m cells)")

    except Exception as e:
        print(f"\n❌ Example 2 failed: {e}")
        import traceback
        traceback.print_exc()

    # ==========================================================================
    # Example 3: Crop AND Resample
    # ==========================================================================
    print("\n" + "=" * 70)
    print("Example 3: Crop to 80% and resample to 3m cells")
    print("=" * 70)

    dest3 = Path("/home/wilfchun/CoastalME/CoastalME_data_local/CSE/Thorpness_cropped_3m")

    try:
        cme3 = copy_project(
            source_ini_path=source_ini,
            dest_project_path=dest3,
            crop_bbox=crop_bbox,
            target_cell_size=3.0,
            resampling_method="bilinear",
            sediment_resampling="average",
            verbose=True
        )

        print(f"\n✅ Example 3 complete!")
        print(f"   New project at: {dest3}")

    except Exception as e:
        print(f"\n❌ Example 3 failed: {e}")
        import traceback
        traceback.print_exc()

    # ==========================================================================
    # Summary
    # ==========================================================================
    print("\n" + "=" * 70)
    print("All Examples Complete!")
    print("=" * 70)
    print("\nCreated projects:")
    print(f"  1. {dest1}")
    print(f"  2. {dest2}")
    print(f"  3. {dest3}")
    print("\nYou can now:")
    print("  - Inspect the new projects in QGIS")
    print("  - Run CoastalME simulations on them")
    print("  - Delete them if you don't need them:")
    print(f"      rm -rf {dest1}")
    print(f"      rm -rf {dest2}")
    print(f"      rm -rf {dest3}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
