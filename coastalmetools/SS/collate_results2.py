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

def sim_times(itters):
    start = datetime(1985,7,1)
    step = timedelta(days=1)
    end = datetime(1985,7,1) + itters * step
    start = start + step
    t = np.arange(start,end,step).astype(datetime)
    t = pd.DatetimeIndex(t)

    return t

def collect_files(itters, path):
    df = pd.DataFrame()
    itter_l = np.arange(1,itters+1, 1)
    itter_l = ["{:03d}".format(x) for x in itter_l]
    files = []
    path_ls = []
    dir_path = path

    for file in glob.glob(str(dir_path) + '**/*.tif', recursive=True):
    # print the path name of selected files
        files.append(file)

    temp = [x[:-7] for x in files]
    paths = list(set(temp))
    vars = [fi.split('/')[7] for fi in paths]
    df['variables'] = [x[:-1]for x in vars]

    for path in paths:
        path_l = [path + x + '.tif' for x in itter_l]
        path_ls.append(path_l)

    df['paths'] = path_ls

    return df

def collate_results(path,t):
    itters = len(t)
    # t = sim_times(itters)
    t = pd.DatetimeIndex(t)
    df = collect_files(itters, path)
    for index, row in df.iterrows():
        if len(row.paths) != len(t):
            raise ValueError('Not enough rasters for timesteps')
        else:
            s_path = path / '_simple' 
            n_path = path / '_nc' 
            name = (row.variables + ".nc")
            time = xr.Variable('time', t)
            test = xr.open_dataset(row.paths[0],  engine="rasterio")
            count = 0
            list_da = []
            for elm in row.paths:
                geotiff_da = rioxarray.open_rasterio(elm, parse_coordinates=True)
                geotiff_da = geotiff_da.rio.write_crs(
                                27700,
                                inplace=True,
                                ).rio.set_spatial_dims(
                                x_dim='x',
                                y_dim='y'
                                ).rio.write_coordinate_system(inplace=True)
                da = geotiff_da.to_dataset('band')
                # da = xr.open_dataset(elm, engine="rasterio", decode_coords='all')
                da = da.rename({1: row.variables})
                da.attrs['long_name'] = row.variables
                dt = t[count]

                da = da.assign_coords(time = dt)
                da = da.expand_dims(dim="time")

                tnm = (row.variables + '_' + str(count) + ".nc")
                da.to_netcdf(n_path / tnm)



                list_da.append(da)
                count += 1
            list = list_da

            # ds = xr.concat(list, dim=time, coords='all')
            ds = xr.combine_by_coords(list, combine_attrs='drop_conflicts')
            try:
                ds.to_netcdf(s_path / name)
            except PermissionError:
                os.mkdir(s_path)
                ds.to_netcdf(s_path / name)
    return s_path
