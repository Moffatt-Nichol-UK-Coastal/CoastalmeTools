import xarray as xr
import rioxarray
import shutil
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import os
import numpy as np
import glob
from datetime import datetime, timedelta
import pandas as pd
import netCDF4
import datetime as dt
import matplotlib.pyplot as plt
from datetime import datetime, timedelta 
import xarray as xr
import numpy as np
import cmocean # for perceptually uniform colormaps
import cartopy as cr # for geographic mapping
import cartopy.crs as ccrs # for map projections
import matplotlib.pyplot as plt # plotting tool
import cartopy.feature as cfeature # to add coastlines, land and ocean
from cartopy.mpl.gridliner import LONGITUDE_FORMATTER, LATITUDE_FORMATTER

def parse_results(path, var):
    full_path = path / (var+".nc")
    f = netCDF4.Dataset(full_path)

    ds = xr.open_dataset(full_path)
    ds.data_vars
    ds.top_elevation.plot()

    pass