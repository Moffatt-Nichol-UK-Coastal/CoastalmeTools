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

def sim_times(itters):
    start = datetime(1985,7,1)
    step = timedelta(days=1)
    end = datetime(1985,7,1) + itters * step
    start = start + step
    t = np.arange(start,end,step).astype(datetime)
    t = pd.DatetimeIndex(t)

    return t

def collect_files(itters):
    df = pd.DataFrame()
    itter_l = np.arange(1,itters, 1)
    itter_l = ["{:03d}".format(x) for x in itter_l]
    files = []
    path_ls = []
    path = Path.cwd()
    dir_path = path / 'out' / 'test_suite' / 'minimal_wave_angle_270'

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

def run():
    itters = 11
    t = sim_times(itters)
    df = collect_files(itters)
    for index, row in df.iterrows():
        if len(row.paths) != len(t):
            raise ValueError('Not enough rasters for timesteps')
        else:
            name = Path.cwd() /'out' / 'simple' / (row.variables + ".nc")
            time = xr.Variable('time', t)
            test = xr.open_dataset(row.paths[0],  engine="rasterio")
            count = 0
            list_da = []
            for elm in row.paths:
                geotiff_da = rioxarray.open_rasterio(elm, parse_coordinates=True)
                da = geotiff_da.to_dataset('band')
                # da = xr.open_dataset(elm, engine="rasterio", decode_coords='all')
                da = da.rename({1: row.variables})
                dt = t[count]

                da = da.assign_coords(time = dt)
                da = da.expand_dims(dim="time")

                list_da.append(da)
                count += 1
            list = list_da

            da = xr.concat(list, dim=time)

            da.to_netcdf(name)
        pass

    pass

if __name__ == "__main__":
    run()