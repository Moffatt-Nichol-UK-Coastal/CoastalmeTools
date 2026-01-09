import os

# Set HDF5 environment variable before any HDF5-related imports
os.environ["HDF5_USE_FILE_LOCKING"] = "FALSE"
os.environ["HDF5_DISABLE_VERSION_CHECK"] = "1"

import pandas as pd
from pathlib import Path
import matplotlib.pyplot as plt
import numpy as np
import time as timer
import logging
import rasterio
from rasterio.errors import RasterioIOError
import glob
import pandas as pd
from datetime import timedelta
import shutil
import xarray as xr

# from Cme import *
from netCDF4 import *
from cftime import num2date, date2num
import geopandas as gpd
import fiona
import pyogrio

# Configure module logger
logger = logging.getLogger(__name__)


def collect_files(itters, path, f_type, depth=None):
    """Collect output files from CME run and organize by variable name.

    Args:
        itters: Number of iterations/timesteps
        path: Path to output directory
        f_type: File extension to search for (e.g., 'tif', 'shp')
        depth: Optional depth for path splitting (deprecated, calculated automatically)

    Returns:
        DataFrame with 'variables' and 'paths' columns
    """
    df = pd.DataFrame()
    itter_l = np.arange(1, itters + 1, 1)
    itter_l = np.append(itter_l, 999)
    itter_l = ["{:03d}".format(x) for x in itter_l]
    files = []
    path_ls = []
    dir_path = path

    for file in glob.glob(str(dir_path) + "**/*." + f_type, recursive=True):
        # print the path name of selected files
        files.append(file)

    temp = [x[:-7] for x in files]
    paths = list(set(temp))

    # Extract variable names using Path instead of string splitting
    # This removes the timestep suffix (last character) from the filename
    vars = [Path(fi).name for fi in paths]
    df["variables"] = [x[:-1] for x in vars]

    for path in paths:
        path_l = [path + x + "." + f_type for x in itter_l]
        path_ls.append(path_l)

    df["paths"] = path_ls
    df = df.sort_values(by=["variables"])
    df = df.reset_index(drop=True)

    return df


def vectors(t, df_v, path, vars_v):
    if "all" not in vars_v:
        df_v = df_v[df_v["variables"].isin(vars_v)]
    v_path = path  # / 'vector'
    v_path.mkdir(parents=True, exist_ok=True)
    delta = t[1] - t[0]
    delta = delta - timedelta(hours=1)

    # Track if we've seen CRS warnings
    crs_warnings_seen = False

    # Suppress pyogrio CRS warnings temporarily
    import warnings

    for index, row in df_v.iterrows():
        count = 0
        gdf = None
        for i_file in row.paths:
            file = os.path.basename(i_file)
            file = os.path.splitext(file)[0] + ".gpkg"
            o_path = v_path / file
            try:
                shape = gpd.read_file(i_file)
                shape["start_time"] = t[count]
                shape["end_time"] = t[count] + delta
                if "gdf" in locals():
                    gdf = pd.concat([gdf, shape])
                else:
                    gdf = shape
            except fiona.errors.DriverError:
                pass
            except pyogrio.errors.DataSourceError:
                pass
            except IndexError:
                pass
            # shape.set_crs('epsg:27700')
            count += 1

        # Suppress CRS warnings when writing, but track if any occur
        with warnings.catch_warnings(record=True) as w:
            warnings.filterwarnings('always', category=UserWarning)
            gdf.to_file(v_path / "all_vect.gpkg", layer=row.variables, driver="GPKG")
            # Check if any CRS warnings were raised
            if any("crs" in str(warning.message).lower() for warning in w):
                crs_warnings_seen = True

        logger.info(f"Done: {row.variables}")

    # Log consolidated CRS warning once if any were seen
    if crs_warnings_seen:
        logger.warning(
            "Some vector outputs were written without CRS information. "
            "Output files may not have projection information defined."
        )

    logger.info("Done: All Vectors")


def rasters(t, df, path, vars, sed_top=True, crashed=False):
    """read a coastalme input file, either an .ini or a .dat

    Args:
        t (list): list of timestamps of outputs
        df (DataFrame): 2 column df of output variable and list of file paths
        path (Path): output folder path
        vars (list): list of out vars to add to ncdf
        sed_top (bool): do we want to produce some extra sedient layers in ncdf
        crashed (bool): are we here as a result of a cme crash

    Returns:
        void
    """
    base_p = df.loc[df["variables"] == "basement_elevation", "paths"].values[0][0]
    base = rasterio.open(base_p)
    if sed_top:
        cs = [
            # "cons_sed_coarse_layer_1",
            # "cons_sed_fine_layer_1",
            # "cons_sed_sand_layer_1",
            "cons_sed_coarse",
            "cons_sed_fine",
            "cons_sed_sand",
        ]
        us = [
            # "uncons_sed_coarse_layer_1",
            # "uncons_sed_fine_layer_1",
            # "uncons_sed_sand_layer_1",
            "uncons_sed_coarse",
            "uncons_sed_fine",
            "uncons_sed_sand",
        ]
        sl = ["sea_depth"]
        wh = ["wave_height"]
        c_sed_df = df[df["variables"].isin(cs)]
        u_sed_df = df[df["variables"].isin(us)]
        sl_df = df[df["variables"].isin(sl)]
        wh_df = df[df["variables"].isin(wh)]
    if "all" not in vars:
        df = df[df["variables"].isin(vars)]
    s_path = path / "all_vars.nc"
    # Create netCDF dataset with optimized format
    rootgrp = Dataset(s_path, "w", format="NETCDF4")
    time = rootgrp.createDimension("time", None)
    x = rootgrp.createDimension("x", base.width)
    y = rootgrp.createDimension("y", base.height)

    x = rootgrp.createVariable(
        "x",
        "f8",
        ("x",),
        compression="zlib",
        shuffle=True,
        complevel=9,
        fill_value=-9999.0,
    )
    y = rootgrp.createVariable(
        "y",
        "f8",
        ("y",),
        compression="zlib",
        shuffle=True,
        complevel=9,
        fill_value=-9999.0,
    )
    times = rootgrp.createVariable(
        "time", "f8", ("time",), compression="zlib", shuffle=True, complevel=9
    )

    rootgrp.description = "CoastalME Output"
    rootgrp.history = "Created " + timer.ctime(timer.time())
    rootgrp.source = "CoastalME Run"
    rootgrp.title = "CoastalME Output"
    crs = rootgrp.createVariable("GeoTransform", "i4")
    crs = base.transform

    times.units = "hours since {}".format(str(t[0]))
    times.calendar = "gregorian"
    times.standard_name = "time"
    times.long_name = "time"
    times.axis = "T"
    times[:] = date2num(t, units=times.units, calendar=times.calendar)

    x.axis = "X"
    y.axis = "Y"
    x[:] = np.linspace(base.bounds[0], base.bounds[2], num=base.width)
    y[:] = np.linspace(base.bounds[1], base.bounds[3], num=base.height)

    rootgrp.close()
    # Loop over variable
    with Dataset(s_path, "a", format="NETCDF4") as appnd:
        for index, row in df.iterrows():
            if not crashed:
                if "999" in row.paths[-1]:
                    del row.paths[-1]
            if len(row.paths) != len(t):
                raise ValueError("Not enough rasters for timesteps")
            else:
                # create variable for netcdf with optimal chunking and compression
                # Calculate optimal chunk size based on typical access patterns
                chunk_time = min(
                    10, len(t)
                )  # Chunk 10 timesteps or less if fewer available
                chunk_y = min(
                    100, base.height
                )  # Chunk spatial dimensions in 100x100 blocks
                chunk_x = min(100, base.width)

                temp = appnd.createVariable(
                    row.variables,
                    "f4",
                    ("time", "y", "x"),
                    compression="zlib",
                    shuffle=True,
                    complevel=9,
                    chunksizes=(chunk_time, chunk_y, chunk_x),
                    fill_value=-9999.0,
                )

                # Loop over timesteps
                count = 0
                for elm in row.paths:
                    # data_time = times[:].data[count]
                    try:
                        with rasterio.open(elm, "r") as ds:
                            arr = ds.read()
                            # arr = arr[np.newaxis, : ,:]
                            # Handle missing data with fill values
                            arr_flipped = np.flip(arr[0], 0)
                            # Replace any invalid values with fill value
                            arr_flipped = np.where(
                                np.isfinite(arr_flipped), arr_flipped, -9999.0
                            )
                            temp[count] = arr_flipped
                    except RasterioIOError:
                        continue
                    count += 1
                # appnd.close()
                logger.info(f"Done: {row.variables}")

        # Create composite variables with optimized settings
        chunk_time = min(10, len(t))
        chunk_y = min(100, base.height)
        chunk_x = min(100, base.width)

        temp = appnd.createVariable(
            "_top_Consolidated",
            "f4",
            ("time", "y", "x"),
            compression="zlib",
            shuffle=True,
            complevel=9,
            chunksizes=(chunk_time, chunk_y, chunk_x),
            fill_value=-9999.0,
        )
        temp_u = appnd.createVariable(
            "_top_Unconsolidated",
            "f4",
            ("time", "y", "x"),
            compression="zlib",
            shuffle=True,
            complevel=9,
            chunksizes=(chunk_time, chunk_y, chunk_x),
            fill_value=-9999.0,
        )
        temp_wl = appnd.createVariable(
            "_top_Sea",
            "f4",
            ("time", "y", "x"),
            compression="zlib",
            shuffle=True,
            complevel=9,
            chunksizes=(chunk_time, chunk_y, chunk_x),
            fill_value=-9999.0,
        )
        temp_wa = appnd.createVariable(
            "_top_Wave",
            "f4",
            ("time", "y", "x"),
            compression="zlib",
            shuffle=True,
            complevel=9,
            chunksizes=(chunk_time, chunk_y, chunk_x),
            fill_value=-9999.0,
        )

        for count in np.arange(0, len(t)):
            try:
                del sumy
            except NameError:
                pass
            for index, row in c_sed_df.iterrows():
                elm = row.paths[count]
                try:
                    with rasterio.open(elm, "r") as ds:
                        arr = ds.read()
                        # arr = arr[np.newaxis, : ,:]
                except RasterioIOError:
                    continue
                if "sumy" in locals():
                    sumy = sumy + arr
                else:
                    sumy = arr

            if "sumy" in locals():
                arr_flipped = np.flip(sumy[0], 0)
                arr_flipped = np.where(np.isfinite(arr_flipped), arr_flipped, -9999.0)
                temp[count] = arr_flipped

            for index, row in u_sed_df.iterrows():
                elm = row.paths[count]
                try:
                    with rasterio.open(elm, "r") as ds:
                        arr = ds.read()
                        # arr = arr[np.newaxis, : ,:]
                except RasterioIOError:
                    continue
                if "sumy" in locals():
                    sumy = sumy + arr
                    # ind = arr==0
                    # sum[ind] = 0
                else:
                    sumy = arr

            if "sumy" in locals():
                arr_flipped = np.flip(sumy[0], 0)
                arr_flipped = np.where(np.isfinite(arr_flipped), arr_flipped, -9999.0)
                temp_u[count] = arr_flipped

            if not sl_df.empty:
                for index, row in sl_df.iterrows():
                    elm = row.paths[count]
                    try:
                        with rasterio.open(elm, "r") as ds:
                            arr = ds.read()
                            # arr = arr[np.newaxis, : ,:]
                            dry = arr == 0
                    except RasterioIOError:
                        continue
                    if "sumy" in locals():
                        sumy = sumy + arr
                        # ind = arr==0
                        # sum[ind] = 0
                    else:
                        sumy = arr

                if "sumy" in locals():
                    sumy[dry] = -9999.0  # Use fill value instead of NaN
                    arr_flipped = np.flip(sumy[0], 0)
                    arr_flipped = np.where(np.isfinite(arr_flipped), arr_flipped, -9999.0)
                    temp_wl[count] = arr_flipped

            if not wh_df.empty:
                for index, row in wh_df.iterrows():
                    elm = row.paths[count]
                    try:
                        with rasterio.open(elm, "r") as ds:
                            arr = ds.read()
                            # arr = arr[np.newaxis, : ,:]
                            dry = arr == 0
                    except RasterioIOError:
                        continue
                    if "sumy" in locals():
                        sumy = sumy + arr / 2
                        # ind = arr==0
                        # sum[ind] = 0
                    else:
                        sumy = arr

                if "sumy" in locals():
                    sumy[dry] = -9999.0  # Use fill value instead of NaN
                    arr_flipped = np.flip(sumy[0], 0)
                    arr_flipped = np.where(np.isfinite(arr_flipped), arr_flipped, -9999.0)
                    temp_wa[count] = arr_flipped
    
    # Prune empty final timestep if detected (common with crashes)
    prune_netcdf(s_path)


def prune_netcdf(nc_path):
    """
    Checks if the last timestep of the NetCDF file is empty (all fill values/NaNs).
    If so, removes it.
    """
    if not os.path.exists(nc_path):
        return

    tmp_path = None
    try:
        # Open dataset
        with xr.open_dataset(nc_path) as ds:
            if "time" not in ds.dims or ds.sizes["time"] < 2:
                return

            # Check variables that have 'time' dimension
            time_vars = [v for v in ds.data_vars if "time" in ds[v].dims]
            if not time_vars:
                return

            is_empty = True
            for var in time_vars:
                # Check last timestep
                data = ds[var].isel(time=-1)
                # Assuming fill values are NaN after loading
                # Also check if all values are equal to -9999.0 (our fill value) just in case xarray didn't decode it
                # But typically xarray handles _FillValue automatically
                if not data.isnull().all():
                    is_empty = False
                    break
            
            if is_empty:
                logger.info("Pruning empty final timestep from NetCDF...")
                # Create pruned dataset
                ds_pruned = ds.isel(time=slice(0, -1))
                
                # Save to temp file
                tmp_path = str(nc_path) + ".tmp"
                ds_pruned.to_netcdf(tmp_path)
                
        # Move temp file to original (outside context manager)
        if tmp_path and os.path.exists(tmp_path):
             shutil.move(tmp_path, nc_path)
             logger.info("Pruning complete.")

    except Exception as e:
        logger.warning(f"Failed to prune NetCDF: {e}")
        if tmp_path and os.path.exists(tmp_path):
            os.remove(tmp_path)



def profiles(t, path):
    files = []
    fig_path = path / "fig"
    fig_path.mkdir(parents=True, exist_ok=True)
    for file in glob.glob(str(path) + "**/profile*." + "csv", recursive=True):
        # print the path name of selected files
        files.append(file)
    file_d = pd.DataFrame(files, columns=["path"])
    file_d["f_name"] = [os.path.split(x)[1] for x in file_d["path"]]
    file_d["p_name"] = [x.split(".")[0].split("_")[1] for x in file_d["path"]]
    file_d["t_step"] = [x.split(".")[0].split("_")[3] for x in file_d["path"]]
    file_d["t_step"] = [int(x) for x in file_d["t_step"]]
    # file_d["t"] = [t[x] for x in file_d["t_step"]]
    datas = []
    for index, file in file_d.iterrows():
        data = pd.read_csv(file["path"])
        data = data.iloc[:, :-1]
        data.columns = [j.strip().replace('"', "") for j in data.columns]
        data = data.set_index("Dist")
        datas.append(data)
        p_name = "profile_{0}_at_timestep_{1}".format(file.p_name, file.t_step)
        prof = data.loc[:, ["Z (before erosion)"]]
        ratio = data.loc[:, ["Depth/DB", "Slope"]]
        value = data.loc[:, ["Erosion Potential", "Recession XY", "Change Elev Z"]]
        fig, axes = plt.subplots(3, 1, figsize=(10, 10))
        prof.plot(ax=axes[0])
        ratio.plot(ax=axes[1])
        value.plot(ax=axes[2])
        fig.suptitle(p_name.replace("_", " "))
        fig.savefig(fig_path / str(p_name + ".png"))
        plt.close()
    file_d["data"] = datas
    pass


def explore_nc(path1, path2):
    exp = Dataset(path1, "r")
    my = Dataset(path2, "r")
    times = num2date(my.variables["time"][:], my.variables["time"].units).data.tolist()
    pass


def file_search(path, keyword=None, ext=None):
    files = next(os.walk(path), (None, None, []))[2]
    if ext:
        files = [fi for fi in files if fi.endswith(ext)]
    if keyword:
        files = [fi for fi in files if keyword in fi]
    if len(files) == 1:
        out_path = path / files[0]
    elif len(files) > 1:
        out_path = [path / file for file in files]
        # raise Exception("Multiple {}'s found".format(ext))
    elif len(files) < 1:
        # raise Exception("no {}'s found".format(ext))
        out_path = None
    return out_path
