
import xarray as xr

import rioxarray
import shutil
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import os
import numpy as np
import glob
import pandas as pd
from datetime import datetime, timedelta
from mdal import Datasource, Info, last_status, PyMesh, drivers, MDAL_DataLocation
from cme import *
import netCDF4
import h5py

import eccodes

def grib_gen(data_arrays, timesteps, out_f):
    # GRIB file settings
    output_file = out_f
    param_id = 129  # Assuming you know the parameter ID

    # Open the GRIB file for writing
    with open(output_file, 'wb') as f:
        # Loop over timesteps and corresponding data arrays
        for t_value, data in zip(timesteps, data_arrays):
            # Create a new GRIB message using the template
            gid = eccodes.codes_any_new_from_samples(template_gid)

            # Set data values
            eccodes.codes_set_array(gid, "values", data.values.flatten())

            # Set metadata
            eccodes.codes_set(gid, 'paramId', param_id)
            eccodes.codes_set(gid, 'shortName', 'data')
            eccodes.codes_set(gid, 'units', 'unknown')
            eccodes.codes_set(gid, 'level', 0)  # Assuming it's a surface level data
            eccodes.codes_set(gid, 'dataDate', t_value.strftime('%Y%m%d'))
            eccodes.codes_set(gid, 'dataTime', t_value.strftime('%H%M%S'))
            eccodes.codes_set(gid, 'stepUnits', 1)
            eccodes.codes_set(gid, 'endStep', 0)

            # Set latitudes and longitudes
            eccodes.codes_set_array(gid, 'latitudes', data.latitude.values)
            eccodes.codes_set_array(gid, 'longitudes', data.longitude.values)

            # Write message to file
            eccodes.codes_write(gid, f)

            # Clean up
            eccodes.codes_release(gid)

    # Release the template GRIB message
    eccodes.codes_release(template_gid)