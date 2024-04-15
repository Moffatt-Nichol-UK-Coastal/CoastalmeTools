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
from nc_to_mesh import nc_to_mesh
from grib_gen import grib_gen
import h5py
os.environ['HDF5_USE_FILE_LOCKING'] = 'FALSE'

def gen_t_series(path, t):

