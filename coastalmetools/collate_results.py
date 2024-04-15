import xarray as xr
import rioxarray
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import os
import numpy as np
import time as timer
import rasterio
import glob
import pandas as pd
from datetime import datetime, timedelta
from cme import *
from nc_to_mesh import nc_to_mesh
import meshio
from netCDF4 import *
from datetime import datetime, timedelta
from cftime import num2date, date2num
os.environ['HDF5_USE_FILE_LOCKING'] = 'FALSE'


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
    df = df.sort_values(by =['variables'])
    df = df.reset_index(drop=True)

    return df

def to_msh(inp_path, path, var, i):
    n_path = path / '_nc' 
    m_path = path / '_ncm'
    name = (var + ".nc")

    geotiff_da = rioxarray.open_rasterio(inp_path, parse_coordinates=True)
    geotiff_da = geotiff_da.rio.write_crs(
                    27700,
                    inplace=True,
                    ).rio.set_spatial_dims(
                    x_dim='x',
                    y_dim='y'
                    ).rio.write_coordinate_system(inplace=True)
    da = geotiff_da.to_dataset('band')
    da = da.rename({1: var})
    da.attrs['long_name'] = var

    tnm = (var+ '_' + str(i) + ".nc")
    da.to_netcdf((n_path / tnm))

    mesh = nc_to_mesh((n_path / tnm))

    return mesh

def collate_results(path,t,vars=['all']):
    if 'basement_elevation' not in vars:
        vars.append('basement_elevation')
    itters = len(t)
    df = collect_files(itters, path)
    if 'all' not in vars: 
        df = df[df["variables"].isin(vars)]
    base_p = df.loc[df['variables'] == 'basement_elevation','paths'].values[0][0]
    base = rasterio.open(base_p)
    s_path = (path /"all_vars.nc")
    rootgrp = Dataset(s_path, "w", format="NETCDF3_64BIT_OFFSET")
    time = rootgrp.createDimension("time", None)
    x = rootgrp.createDimension("x", base.width)
    y = rootgrp.createDimension("y", base.height)

    x = rootgrp.createVariable("x","f8",("x",))
    y = rootgrp.createVariable("y","f8",("y",))
    times = rootgrp.createVariable("time","f8",("time",))

    rootgrp.description = "CoastalME Output"
    rootgrp.history = "Created " + timer.ctime(timer.time())
    rootgrp.source = "CoastalME Run"
    rootgrp.title = "CoastalME Output"
    crs = rootgrp.createVariable('GeoTransform', 'i4')
    crs = base.transform

    times.units = "hours since {}".format(str(t[0]))
    times.calendar = "gregorian"
    times.standard_name = 'time'
    times.long_name = 'time'
    times.axis = 'T'
    times[:] = date2num(t,units=times.units,calendar=times.calendar)

    x.axis = 'X'
    y.axis = 'Y'
    x[:] = np.arange(base.bounds[0],base.bounds[2], base.res[0])
    y[:] = np.arange(base.bounds[1],base.bounds[3], base.res[1])
    # Loop over variable
    for index, row in df.iterrows():
        if len(row.paths) != len(t):
            raise ValueError('Not enough rasters for timesteps')
        else:
            # create variable for netcdf
            temp = rootgrp.createVariable(row.variables,"f4",("time","y","x"))

            # Loop over timesteps
            count = 0
            for elm in row.paths:
                data_time = times[:].data[count]
                # with rioxarray.open_rasterio(elm, parse_coordinates=True) as geotiff_da:
                #     da = geotiff_da.to_dataset('band')
                #     da = da[1]
                #     temp[count] = da
                # mesh = to_msh(elm, path,row.variables, count)
                with rasterio.open(elm, 'r') as ds:
                    arr = ds.read()
                    # arr = arr[np.newaxis, : ,:]
                    temp[count] = np.flip(arr[0],0)
                count += 1
            print('Done: ' + row.variables)

    rootgrp.close()
    return s_path

def explore_nc(path1, path2):
    exp = Dataset(path1, "r")
    my = Dataset(path2, "r")
    times = num2date(my.variables['time'][:],my.variables['time'].units).data.tolist()
    pass