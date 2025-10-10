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

def loadStudyElev(rasterFolder, x_size, y_size):
    layers = ['basement', 'cape']

    array = np.zeros((y_size, x_size))

    for layer in layers:
        rasterP = rasterFolder / str(layer + ".asc")
        with rio.open(rasterP) as f:
            data = f.read(1)
            array = array + data

    return array



def loadVect(vectPath, mask):
    '''
    This loads in a vector file from a given path
    This translates it into a consistent, standardised form
    '''
    gdf = gpd.read_file(vectPath)#, mask=mask)
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
    elif geom.geom_type == 'MultiLineString':
        area = geom.buffer(width)
    
    cat = geoRow['struct_type']
    if cat in ['groyne', 'wall', 'breakwater']:
        cat = 1
    else:
        cat = 0
    cat = np.int16(cat)

    elev = geoRow['elev']
    
    return (area, cat, elev)

def shape2rast(templates, extent, atrib, height_adjust=False):
    '''
    This takes in a geometry and scalar field
    This generates a raster of defined extents filled where scalar applied over geometry.
    Null elsewhere
    '''
    x_size = int(abs(extent.bounds.loc[0,'minx'] - extent.bounds.loc[0,'maxx']))
    y_size = int(abs(extent.bounds.loc[0,'miny'] - extent.bounds.loc[0,'maxy']))
    gdf = gpd.GeoDataFrame(templates, columns=['geometry','type','elev'])
    features = [(geom, value) for geom, value in zip(gdf.geometry, gdf[atrib])]
    
    raster = rasterize(
        features,
        out_shape=(y_size, x_size),
        transform=trans,
        fill=0,  # Value to use for areas outside geometries
        all_touched=True  # Rasterize all pixels touched by geometries
    )

    if height_adjust:
        studyTop = loadStudyElev(path, x_size, y_size)
        raster = raster - studyTop
        raster = raster.clip(min=0)
    
    plt.imshow(raster)
    # plt.gca().invert_yaxis()

    plt.savefig('figs/{}.png'.format(atrib))
    return raster

def exportRaster(rasDict, folder, espg):
    '''
    '''
    for key, value in rasDict.items():
        out_path = folder / str(key+".asc")
        with rio.open(
            out_path,
            'w',
            driver='AAIGrid',
            height= value.shape[0],
            width= value.shape[1],
            count=1,
            dtype=value.dtype,
            crs='EPSG:27700',  # Assuming WGS84, modify if necessary
            # transform=transform,
            nodata=-9999
        ) as dst:
            dst.write(value, 1)

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
    
    rasterList = {}
    rasterList['intervention_height'] = shape2rast(tmpList, extent, atrib='elev', height_adjust=True)
    rasterList['intervention_class'] = shape2rast(tmpList, extent, atrib='type')

    exportRaster(rasterList, path, 27700)

    pass

if __name__ == "__main__":
    # Example usage - update these paths to your actual data location
    import sys
    if len(sys.argv) < 2:
        print("Usage: python vect2structRast.py <path_to_scenario_folder>")
        print("Example: python vect2structRast.py /home/user/CoastalME/in/Exploration/Scen013")
        sys.exit(1)

    path = Path(sys.argv[1])
    vect_p = path / 'defences.gdb'
    base_p = path / "basement.asc"
    vect2structRast(vect_p, base_p)