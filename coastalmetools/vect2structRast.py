import numpy as np
import geopandas as gpd
import rasterio as rio
from pathlib import Path

def loadVect(vectPath):
    '''
    This loads in a vector file from a given path
    This translates it into a consistent, standardised form
    '''
    pass

def genTemplate(geoRow):
    '''
    This takes in a geometry and converts it to a standard format.
    Output contains geometry (adjusted as required) and a scalar value array
    '''
    pass

def shape2rast(geometry, scalarArray):
    '''
    This takes in a geometry and scalar field
    This generates a raster of defined extents filled where scalar applied over geometry.
    Null elsewhere
    '''
    pass

def vect2structRast(vectPath, extents):
    '''
    This takes in a coastal defence in the form of a vector file
    This returns a pair of rasters of the format required by CME
    '''
    pass

if __name__ == "__main__":
    vect2structRast()