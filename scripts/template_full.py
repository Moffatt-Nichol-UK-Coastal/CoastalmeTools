from CoastalmeTools import Cme
from CoastalmeTools.project_tools import copy_project, get_project_extent
import platform
from pathlib import Path


if platform.system() == "Darwin":
    # Provide path of cme ini file
    ini_file = (
        # r"/Users/wilfchun/Documents/GitHub/CoastalMe/in/Exploration/Scen016/cme.ini"
        # r"/Users/wilfchun/Documents/GitHub/CoastalMe/in/test_suite/Manuel_C003_0001/cme.ini"
        # r"/Users/wilfchun/Documents/GitHub/CoastalMe/coastalme/in/test_suite/Happisburgh/cme.ini"
        # r"/Users/wilfchun/Documents/GitHub/CoastalMe/in/test_suite/Happisburgh/cme.ini"
        r"/Users/wilfchun/Documents/GitHub/CoastalMe/CoastalME_data_local/CSE/Thorpness/in/cme.ini"
    )
    # Provide path where we want cme to run, this is the --home cmd ln arg
    run_path = r"/Users/wilfchun/Documents/GitHub/CoastalMe/CoastalME_data_local/"
    # Provide path of cme executable
    cme_path = r"/Users/wilfchun/Documents/GitHub/CoastalMe/coastalme/cme"

elif platform.system() == "Linux":
    # Provide path of cme ini file
    # ini_file = r"/home/wilfc/CoastalME/in/Exploration/Scen017/cme.ini"
    ini_file = r"/home/wilfchun/CoastalME/CoastalME_data_local/CSE/Thorpness/cme.ini"
    # Provide path where we want cme to run, this is the --home cmd ln arg
    run_path = r"/home/wilfchun/CoastalME/coastalme/"
    # Provide path of cme executable
    cme_path = r"/home/wilfchun/CoastalME/coastalme/cme"

# Setup
cme = Cme(ini_file, run_path)

source_extent = get_project_extent(str(ini_file))
print(source_extent)
dest = Path("/home/wilfchun/CoastalME/CoastalME_data_local/Typology/Cliff2/")
cme = copy_project(
    source_ini_path=ini_file,
    dest_project_path=dest,
    crop_bbox=(647310, 259950, 648742, 260600),  # Keep full extent
    # target_cell_size=5.0,  # Change to 5m cells
    target_cell_size=None,  # Change to 5m cells
    resampling_method="bilinear",
    verbose=True,
)

cme.tide_check()
# check if were good to run, also do we want to do quick start
# cme.preflight_checks()

# Build t0
cme.build_model()

# Now we run cme
cme.run(cme_path)

out_vars = [
    "landform_class",
    "polygon_raster",
    "rcoast",
    "rcoast_normal",
    "top_elevation",
    "total_actual_beach_erosion",
    "total_actual_platform_erosion",
    "wave_height",
    "cliff",
]

out_vars_v = [
    "breaking_wave_height",
    "cliff_notch",
    "coast",
    "cliff_edge",
    "run_up",
    "coast_curvature",
    "invalid_normals",
    "normals",
    "wave_energy",
    "wave_setup",
    "storm_surge",
]

# Generate netcdf
try:
    results = cme.collate_results(vars=out_vars, vars_v=out_vars_v)
except ValueError as W:
    print(W)
    # cme.return_rescue()

# cme.return_rescue()
# All Done
print("Done!")
