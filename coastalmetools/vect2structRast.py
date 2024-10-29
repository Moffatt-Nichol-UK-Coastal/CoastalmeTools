import numpy as np
import geopandas as gpd
import rasterio as rio
from pathlib import Path
from pathlib import PosixPath
from shapely import LineString, Point, Polygon, BufferCapStyle, BufferJoinStyle
from rasterio.features import rasterize
import matplotlib.pyplot as plt

def baseExtents(rasterPath):
    '''
    This loads in the CME basement raster and extracts the extents
    '''
    global trans
    with rio.open(rasterPath) as f:
        extents = f.bounds
        rCrs = f.crs
        trans = f.transform
    coords = ((extents[0], extents[1]), (extents[0], extents[3]), (extents[2], extents[1]), (extents[2], extents[3]))
    polygon = Polygon(coords)
    extents = gpd.GeoSeries(polygon, crs=27700)

    return extents

def loadVect(vectPath, mask):
    '''
    This loads in a vector file from a given path
    This translates it into a consistent, standardised form
    '''
    gdf = gpd.read_file(vectPath, mask=mask)
    return gdf

def genTemplate(geoRow):
    '''
    This takes in a geometry and converts it to a standard format.
    Output contains geometry (adjusted as required) and a scalar value array
    '''
    try:
        width = geoRow['width']
    except KeyError:
        width = 1
    geom = geoRow['geometry']
    if geom.geom_type == 'Polygon':
        pass
    elif geom.geom_type == 'LineString':
        area = geom.buffer(width)
    
    cat = geoRow['struct_type']
    if cat in ['Groyne', 'wall', 'breakwater']:
        cat = 1
    else:
        cat = 0

    elev = geoRow['crest_elev']
    
    return (area, cat, elev)

def shape2rast(templates, extent, atrib):
    '''
    This takes in a geometry and scalar field
    This generates a raster of defined extents filled where scalar applied over geometry.
    Null elsewhere
    '''
    x_size = int(abs(extent.bounds.loc[0,'minx'] - extent.bounds.loc[0,'maxx']))
    y_size = int(abs(extent.bounds.loc[0,'miny'] - extent.bounds.loc[0,'maxy']))
    gdf = gpd.GeoDataFrame(templates, columns=['geometry','type','elev'])
    features = [(geom, value) for geom, value in zip(gdf.geometry, gdf["elev"])]
    
    raster = rasterize(
        features,
        out_shape=(y_size, x_size),
        # transform=transform,
        fill=0,  # Value to use for areas outside geometries
        all_touched=True  # Rasterize all pixels touched by geometries
    )
    
    fig, ax = plt.subplots(1, figsize = (10, 10))
    plt.imshow(raster)
    plt.gca().invert_yaxis()

    plt.savefig('figs/tmp.png')
    return raster

def vect2structRast(vectPath, extent):
    '''
    This takes in a coastal defence in the form of a vector file
    This returns a pair of rasters of the format required by CME
    '''
    if type(extent) == PosixPath:
        extent = baseExtents(extent)
    else:
        raise ValueError("Extent not basement path")

    vect_gpd = loadVect(vectPath, extent)
    tmpList = []
    for feat, geom in vect_gpd.iterrows():
        tmpList.append(genTemplate(geom))
    
    crestRaster = shape2rast(tmpList, extent, atrib='elev')
    pass

if __name__ == "__main__":
    path = Path(r"/home/wilfc/CoastalME/in/Exploration/Scen013")
    vect_p = path / 'defences.gpkg'
    base_p = path / "basement.asc"
    vect2structRast(vect_p, base_p)