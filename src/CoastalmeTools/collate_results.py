import xarray as xr
import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import os
import numpy as np
import time as timer
import rasterio
from rasterio.errors import RasterioIOError
import glob
import pandas as pd
from datetime import datetime, timedelta
from Cme import *
from nc_to_mesh import nc_to_mesh
from netCDF4 import *
from cftime import num2date, date2num
import geopandas as gpd
import fiona
import pyogrio
from shapely.geometry import shape
from fiona import collection, errors
os.environ['HDF5_USE_FILE_LOCKING'] = 'FALSE'


def collect_files(itters, path, f_type):
    df = pd.DataFrame()
    itter_l = np.arange(1,itters+1, 1)
    itter_l = np.append(itter_l,999)
    itter_l = ["{:03d}".format(x) for x in itter_l]
    files = []
    path_ls = []
    dir_path = path

    for file in glob.glob(str(dir_path) + '**/*.' + f_type, recursive=True):
    # print the path name of selected files
        files.append(file)

    temp = [x[:-7] for x in files]
    paths = list(set(temp))
    vars = [fi.split('/')[7] for fi in paths]
    df['variables'] = [x[:-1]for x in vars]

    for path in paths:
        path_l = [path + x + '.' + f_type for x in itter_l]
        path_ls.append(path_l)

    df['paths'] = path_ls
    df = df.sort_values(by =['variables'])
    df = df.reset_index(drop=True)

    return df

def vectors(t, df_v, path, vars_v):
    if 'all' not in vars_v:
        df_v = df_v[df_v["variables"].isin(vars_v)]
    v_path = path #/ 'vector'
    v_path.mkdir(parents=True, exist_ok=True)
    delta = t[1] - t[0]
    delta = delta - timedelta(hours=1)

    for index, row in df_v.iterrows():
        count = 0
        gdf = None
        for i_file in row.paths:
            file = os.path.basename(i_file)
            file = os.path.splitext(file)[0]+'.gpkg'
            o_path = v_path / file
            try:
                shape = gpd.read_file(i_file)
                shape['start_time'] = t[count]
                shape['end_time'] = t[count] + delta
                if 'gdf' in locals():
                    gdf = pd.concat([gdf, shape])
                else:
                    gdf = shape
            except fiona.errors.DriverError:
                pass
            except pyogrio.errors.DataSourceError:
                pass
            # shape.set_crs('epsg:27700')
            count += 1
        gdf.to_file(v_path / 'all_vect.gpkg', layer=row.variables, driver="GPKG")
        print('Done: ' + row.variables)
    print('Done: All Vectors')

def rasters(t, df, path, vars, sed_top=True):
    base_p = df.loc[df['variables'] == 'basement_elevation','paths'].values[0][0]
    base = rasterio.open(base_p)
    if sed_top == True:
        cs = ['cons_sed_coarse_layer_1','cons_sed_fine_layer_1','cons_sed_sand_layer_1']
        us = ['uncons_sed_coarse_layer_1','uncons_sed_fine_layer_1','uncons_sed_sand_layer_1']
        sl = ['sea_depth']
        wh = ['wave_height']
        c_sed_df = df[df["variables"].isin(cs)]
        u_sed_df = df[df["variables"].isin(us)]
        sl_df = df[df["variables"].isin(sl)]
        wh_df = df[df["variables"].isin(wh)]
    if 'all' not in vars:
        df = df[df["variables"].isin(vars)]
    s_path = (path /"all_vars.nc")
    # Create netCDF dataset
    rootgrp = Dataset(s_path, "w", format="NETCDF3_64BIT_OFFSET")
    time = rootgrp.createDimension("time", None)
    x = rootgrp.createDimension("x", base.width)
    y = rootgrp.createDimension("y", base.height)

    x = rootgrp.createVariable("x","f8",("x",),compression='zlib')
    y = rootgrp.createVariable("y","f8",("y",),compression='zlib')
    times = rootgrp.createVariable("time","f8",("time",),compression='zlib')

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
    x[:] = np.linspace(base.bounds[0],base.bounds[2],num=base.width)
    y[:] = np.linspace(base.bounds[1],base.bounds[3],num=base.height)

    rootgrp.close()
    # Loop over variable
    with Dataset(s_path, "a", format="NETCDF3_64BIT_OFFSET") as appnd:
        for index, row in df.iterrows():
            if len(row.paths) != len(t):
                raise ValueError('Not enough rasters for timesteps')
            else:
                # create variable for netcdf
                temp = appnd.createVariable(row.variables,"f4",("time","y","x"),compression='zlib')

                # Loop over timesteps
                count = 0
                for elm in row.paths:
                    # data_time = times[:].data[count]
                    try:
                        with rasterio.open(elm, 'r') as ds:
                            arr = ds.read()
                            # arr = arr[np.newaxis, : ,:]
                            temp[count] = np.flip(arr[0],0)
                    except RasterioIOError:
                        continue
                    count += 1
                # appnd.close()
                print('Done: ' + row.variables)

        temp = appnd.createVariable('_top_Consolidated',"f4",("time","y","x"),compression='zlib')
        temp_u = appnd.createVariable('_top_Unconsolidated',"f4",("time","y","x"),compression='zlib')
        temp_wl = appnd.createVariable('_top_Sea',"f4",("time","y","x"),compression='zlib')
        temp_wa = appnd.createVariable('_top_Wave',"f4",("time","y","x"),compression='zlib')
        
        for count in np.arange(0,len(t)):
            try:
                del sumy
            except NameError:
                pass
            for index, row in c_sed_df.iterrows():
                elm = row.paths[count]
                try:
                    with rasterio.open(elm, 'r') as ds:
                        arr = ds.read()
                        # arr = arr[np.newaxis, : ,:]
                except RasterioIOError:
                    continue
                if 'sumy' in locals():
                    sumy = sumy + arr
                else:
                    sumy = arr

            if 'sumy' in locals():
                temp[count] = np.flip(sumy[0],0)

            for index, row in u_sed_df.iterrows():
                elm = row.paths[count]
                try:
                    with rasterio.open(elm, 'r') as ds:
                        arr = ds.read()
                        # arr = arr[np.newaxis, : ,:]
                except RasterioIOError:
                    continue
                if 'sumy' in locals():
                    sumy = sumy + arr
                    # ind = arr==0
                    # sum[ind] = 0
                else:
                    sumy = arr

            if 'sumy' in locals():
                temp_u[count] = np.flip(sumy[0],0)

            for index, row in sl_df.iterrows():
                elm = row.paths[count]
                try:
                    with rasterio.open(elm, 'r') as ds:
                        arr = ds.read()
                        # arr = arr[np.newaxis, : ,:]
                        dry = (arr == 0)
                except RasterioIOError:
                    continue
                if 'sumy' in locals():
                    sumy = sumy + arr
                    # ind = arr==0
                    # sum[ind] = 0
                else:
                    sumy = arr

            if 'sumy' in locals():
                sumy[dry] = np.nan
                temp_wl[count] = np.flip(sumy[0],0)
            

            for index, row in wh_df.iterrows():
                elm = row.paths[count]
                try:
                    with rasterio.open(elm, 'r') as ds:
                        arr = ds.read()
                        # arr = arr[np.newaxis, : ,:]
                        dry = (arr == 0)
                except RasterioIOError:
                    continue
                if 'sumy' in locals():
                    sumy = sumy + arr/2
                    # ind = arr==0
                    # sum[ind] = 0
                else:
                    sumy = arr
            
            if 'sumy' in locals():
                sumy[dry] = np.nan
                temp_wa[count] = np.flip(sumy[0],0)
            

def profiles(t, path):
    files = []
    fig_path = path / 'fig'
    fig_path.mkdir(parents=True, exist_ok=True)
    for file in glob.glob(str(path) + '**/profile*.' + 'csv', recursive=True):
    # print the path name of selected files
        files.append(file)
    file_d = pd.DataFrame(files, columns=["path"])
    file_d['f_name'] =  [os.path.split(x)[1] for x in file_d['path']]
    file_d['p_name'] = [x.split('.')[0].split("_")[1] for x in file_d['path']]
    file_d['t_step'] = [x.split('.')[0].split("_")[3] for x in file_d['path']]
    file_d['t_step'] = [int(x) for x in file_d["t_step"]]
    # file_d["t"] = [t[x] for x in file_d["t_step"]]
    datas = []
    for index, file in file_d.iterrows():
        data = pd.read_csv(file["path"])
        data = data.iloc[:,:-1]
        data.columns = [j.strip().replace("\"","")for j in data.columns]
        data = data.set_index("Dist")
        datas.append(data)
        p_name = "profile_{0}_at_timestep_{1}".format(file.p_name, file.t_step)
        prof = data.loc[:,['Z (before erosion)']]
        ratio = data.loc[:,['Depth/DB','Slope']]
        value = data.loc[:,['Erosion Potential', 'Recession XY', 'Change Elev Z']]
        fig, axes = plt.subplots(3,1, figsize=(10, 10))
        prof.plot(ax=axes[0])
        ratio.plot(ax=axes[1])
        value.plot(ax=axes[2])
        fig.suptitle(p_name.replace("_"," "))
        fig.savefig(fig_path / str(p_name+'.png'))
        plt.close()
    file_d['data'] = datas
    pass




def collate_results(path,t,vars=['all'],vars_v=['all'],sed_top=True,crashed=True):
    if 'basement_elevation' not in vars:
        vars.append('basement_elevation')
    if crashed:
        finder = str(path/'basement_elevation*.tif')
        completed = len(glob.glob(finder))
        # if completed < len(t):
        t = t[:completed]
    print("found {} timesteps".format(len(t)))
    itters = len(t)
    if crashed:
        delta = t[-1] - t[-2]
        faux = t[-1] + delta
        t.append(faux)
        # t.append(datetime(9999, 9, 9, 0, 0))
    df = collect_files(itters, path, 'tif')
    df_v = collect_files(itters, path, 'shp')


    vectors(t, df_v,path,vars_v)
    rasters(t, df,path,vars)
    profiles(t, path)

    # rootgrp.close()

def explore_nc(path1, path2):
    exp = Dataset(path1, "r")
    my = Dataset(path2, "r")
    times = num2date(my.variables['time'][:],my.variables['time'].units).data.tolist()
    pass
