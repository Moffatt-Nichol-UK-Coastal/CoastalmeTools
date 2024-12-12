import xarray as xr
import geopandas as gpd
import pandas as pd

def wave_read(path, t_step=6):
    """This reads in a grib file (currently focused around ECMWF hindcast data)

    Args:
        path (path/string): path to grib file
        t_step (int)): timestep that the wave data will be resampled to in hours

    Raises:
        ValueError: if there is some error with the grib file

    Returns:
        tuple: lat/long of wave data point
        DataFrame: wave data at desired timestep, with time index and height direction and period columns
    """ 
    ds = xr.open_dataset(path, engine="cfgrib")
    df = ds.to_dataframe()
    vars = list(ds)
    df = df[vars]
    df = df.reset_index()
    gdf = gpd.GeoDataFrame(df, geometry=gpd.points_from_xy(df.longitude, df.latitude), crs="EPSG:4326"    )
    gdf = gdf.drop(columns=["latitude","longitude"])
    gdf = gdf.set_index("time", drop=True)
    wave_points = gdf.geometry.unique()
    num_wave_points = len(wave_points)
    if num_wave_points == 1:
        wave_points = wave_points[0]
    if len(gdf.index.diff().unique().dropna()) ==1:
        # we have a consistant time step
        pass
    else:
        raise ValueError("Grib file contains inconsistent time steps")
    
    gdf = gdf.rename(columns={'mwd':'orientation', 'mwp':'period','swh':'height'})
    gdf_unfiltered = gdf
    gdf = gdf.resample(f'{t_step}h').first()
    df = gdf[['height', 'orientation', 'period']]

    return wave_points, df