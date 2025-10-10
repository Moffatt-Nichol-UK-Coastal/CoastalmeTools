import numpy as np
import rasterio
from pathlib import Path
from lxml import etree
from scipy.interpolate import griddata
from rasterio.enums import Resampling
import matplotlib.pyplot as plt
from skimage.morphology import flood_fill


def parse_landxml_tin(file_path):
    """
    Parses a LandXML file to extract TIN surface elevation data.
    """
    tree = etree.parse(file_path)
    root = tree.getroot()

    # Adjust the namespace according to the LandXML schema version
    namespace = {"ns": "http://www.landxml.org/schema/LandXML-1.2"}

    # Find the TIN surface
    surfaces = root.findall(".//ns:Surface", namespaces=namespace)
    tin_points = []
    triangles = []

    for surface in surfaces:
        pnts = surface.find(".//ns:Pnts", namespaces=namespace)
        faces = surface.find(".//ns:Faces", namespaces=namespace)

        if pnts is not None and faces is not None:
            points_dict = {}
            for point in pnts.findall("ns:P", namespaces=namespace):
                coords = list(map(float, point.text.strip().split()))
                myorder = [1, 0, 2]
                coords = [coords[i] for i in myorder]
                point_id = point.get("id")
                if point_id and len(coords) == 3:
                    points_dict[point_id] = coords  # (x, y, z) by ID

            # Extract triangles (Faces) and store as vertex coordinates
            for face in faces.findall("ns:F", namespaces=namespace):
                pt1, pt2, pt3 = list(map(str, face.text.strip().split()))
                if pt1 in points_dict and pt2 in points_dict and pt3 in points_dict:
                    triangles.append(
                        [points_dict[pt1], points_dict[pt2], points_dict[pt3]]
                    )

    return triangles


def interpolate_triangle_to_grid(triangle, grid, grid_size=1):
    """
    Interpolates a triangle's elevation to the grid using barycentric coordinates.
    """
    # Vertices of the triangle
    v0, v1, v2 = triangle
    (x0, y0, z0), (x1, y1, z1), (x2, y2, z2) = v0, v1, v2

    # Calculate the bounding box in grid coordinates
    min_x, max_x = min(x0, x1, x2), max(x0, x1, x2)
    min_y, max_y = min(y0, y1, y2), max(y0, y1, y2)
    min_x_cell, min_y_cell = (min_x, min_y)
    max_x_cell, max_y_cell = (max_x, max_y)

    min_x_cell, min_y_cell = int(min_x_cell), int(min_y_cell)
    max_x_cell, max_y_cell = int(max_x_cell), int(max_y_cell)

    # Constrain the bounding box within grid dimensions
    min_x_cell = max(0, min_x_cell)
    max_x_cell = min(grid.shape[0], max_x_cell)
    min_y_cell = max(0, min_y_cell)
    max_y_cell = min(grid.shape[1], max_y_cell)

    # Compute the area of the triangle (determinant method)
    denom = np.abs(y1 - y2) * np.abs(x0 - x2) + np.abs(x2 - x1) * np.abs(y0 - y2)
    if denom == 0:
        return  # Skip degenerate triangles

    for x_cell in range(min_x_cell, max_x_cell + 1):
        for y_cell in range(min_y_cell, max_y_cell + 1):
            x, y = (x_cell, y_cell)

            # Barycentric coordinates
            w0 = ((y1 - y2) * (x - x2) + (x2 - x1) * (y - y2)) / denom
            w1 = ((y2 - y0) * (x - x2) + (x0 - x2) * (y - y2)) / denom
            w2 = 1 - w0 - w1

            if (0 <= w0 <= 1) and (0 <= w1 <= 1) and (0 <= w2 <= 1):
                z = w0 * z0 + w1 * z1 + w2 * z2
                try:
                    grid[x_cell, y_cell] = z
                except IndexError:
                    pass
    pass


def create_tiff_from_tin_rio(
    triangles, output_tiff_path, output_base_path, x_res=1, y_res=1
):
    """
    Creates a GeoTIFF file from TIN elevation data using rasterio.
    """

    # Find the bounding box for the data (min/max coordinates)
    all_points = np.vstack(triangles)
    min_x, min_y = np.min(all_points[:, :2], axis=0)
    max_x, max_y = np.max(all_points[:, :2], axis=0)

    # Calculate the size of the raster
    x_size = int((max_x - min_x) / x_res)
    y_size = int((max_y - min_y) / y_res)

    # Create an empty array for the elevation data
    elevation_array = np.full((x_size, y_size), -9999, dtype=np.float32)

    x = all_points[:, 0]
    y = all_points[:, 1]
    z = all_points[:, 2]
    # Define the grid
    grid_x, grid_y = np.meshgrid(
        np.linspace(
            min(x), max(x), int(max(x) - min(x))
        ),  # Adjust grid resolution as needed
        np.linspace(min(y), max(y), int(max(y) - min(y))),
    )

    # Interpolate using linear interpolation
    grid_z = griddata(
        (x, y), z, (grid_x, grid_y), method="linear"
    )  # , fill_value=-9999)

    for i in [0, -1]:
        if np.isnan(np.sum(grid_z[i, :])):
            grid_z = np.delete(grid_z, (i), axis=0)
            grid_y = np.delete(grid_y, (i), axis=0)

    if grid_z.min() < 0:
        grid_z = grid_z + np.abs(grid_z.min())

    if grid_z.shape != grid_y.shape:
        raise IndexError("Shapes dont match!")
    grid_base = np.full(grid_z.shape, 0)

    # grid_z now contains the interpolated z-values for each grid point

    # Write to GeoTIFF using rasterio
    with rasterio.open(
        output_tiff_path,
        "w",
        driver="AAIGrid",
        height=grid_y.shape[0],
        width=grid_y.shape[1],
        count=1,
        dtype=elevation_array.dtype,
        crs="EPSG:27700",  # Assuming WGS84, modify if necessary
        # transform=transform,
        nodata=-9999,
    ) as dst:
        dst.write(grid_z, 1)
    with rasterio.open(
        output_base_path,
        "w",
        driver="AAIGrid",
        height=grid_y.shape[0],
        width=grid_y.shape[1],
        count=1,
        dtype=elevation_array.dtype,
        crs="EPSG:27700",  # Assuming WGS84, modify if necessary
        # transform=transform,
        nodata=-9999,
    ) as dst:
        dst.write(grid_base, 1)


def xml2raster(xml_file, output_path, out_type="asc"):
    output_tiff = output_path / "gb.asc"  # Path to save the output TIFF file
    output_base = output_path / "basement.asc"  # Path to save the output TIFF file

    elevation_data = parse_landxml_tin(xml_file)
    create_tiff_from_tin_rio(elevation_data, output_tiff, output_base)


def genBase(file, output_path, out_type="asc"):
    output_tiff = output_path / "top.asc"  # Path to save the output TIFF file
    output_base = output_path / "basement.asc"  # Path to save the output TIFF file

    src = rasterio.open(file)
    res = src.res[0]
    ans = float(
        input(
            "Current file has a {}m cell size, what would you like to change that to: ".format(
                str(res)
            )
        )
    )
    if ans > res:
        sf = ans / res
    else:
        sf = 1

    proj = src.crs
    transform = src.transform * src.transform.scale((1 * sf), (1 * sf))
    elevation_array = src.read(1).round(3)
    elevation_array = np.where(elevation_array == src.nodata, np.nan, elevation_array)
    if np.nanmin(elevation_array) <= 0:
        uplift = np.round(np.abs(np.nanmin(elevation_array)) + 50, 0)
        elevation_array = elevation_array + np.abs(np.nanmin(elevation_array)) + 50
        elevation_array = np.round(elevation_array, 3)
    else:
        uplift = 0
    grid_base = np.full(src.shape, 0)
    ps = {
        np.nanmax(elevation_array): (elevation_array.shape[0] - 1, 0),
        np.nanmin(elevation_array): (0, elevation_array.shape[1] - 1),
    }
    elevation_array = rasterFill(elevation_array, sf, ps)

    # Write to GeoTIFF using rasterio
    with rasterio.open(
        output_tiff,
        "w",
        driver="AAIGrid",
        height=int(elevation_array.shape[0] / sf),
        width=int(elevation_array.shape[1] / sf),
        resampling=Resampling.bilinear,
        count=1,
        dtype=elevation_array.dtype,
        crs="EPSG:27700",  # Assuming WGS84, modify if necessary
        transform=transform,
        nodata=-9999,
    ) as dst:
        dst.write(elevation_array.round(3), 1)

    with rasterio.open(
        output_base,
        "w",
        driver="AAIGrid",
        height=int(elevation_array.shape[0] / sf),
        width=int(elevation_array.shape[1] / sf),
        resampling=Resampling.bilinear,
        count=1,
        dtype=elevation_array.dtype,
        crs="EPSG:27700",  # Assuming WGS84, modify if necessary
        transform=transform,
        nodata=-9999,
    ) as dst:
        dst.write(grid_base, 1)
    return output_base, output_tiff, uplift


def rasterFill(a, s, p={}):
    """Fill raster holes using flood fill algorithm.

    Args:
        a: Input raster array
        s: Scale factor
        p: Dictionary of {value: (x, y)} seed points for flood fill.
           If empty, uses default seed point.

    Returns:
        Filled raster array

    Note:
        Future enhancement: Add interactive point selection using matplotlib's
        ginput() or a GUI widget. For now, users must provide seed points
        programmatically or use the default.
    """
    a = np.where(a >= 0, a, -9999)
    max_elev = np.nanmax(a)
    if len(p) == 0:
        p = {max_elev: (541, 0)}
    plt.clf()
    null_a = np.where(a >= 0, 0, 1)
    im = plt.imshow(null_a, cmap="hot")
    # plt.show()

    for key, value in p.items():
        # value = tuple(int(i / 5 * s) for i in value)
        fill_point = value
        fill_val = key * 1000
        plt.close()
        a = a * 1000
        a = a.astype(int)
        a = flood_fill(a, fill_point, fill_val)
        a = a.astype(float)
        a = a / 1000
        plt.clf()
        null_a = np.where(a >= 0, 0, 1)
        im = plt.imshow(null_a, cmap="hot")
        plt.show()
    return a


# if __name__ == "__main__":
# 	# file = Path(r"/home/wilfc/CoastalME/in/Exploration/Scen014/GB.xml") # Path to your LandXML file
# 	file = Path(r"/home/wilfc/CoastalME/in/Exploration/Scen016/Cropped.tif") # Path to your LandXML file

# 	out_p = Path(r"/home/wilfc/CoastalME/in/Exploration/Scen016")

# 	if str(file).endswith(".xml"):
# 		xml2raster(file, out_p)
# 	else:
# 		src = rasterio.open(file)
# 		print("Uplifted by {}m to account for negative elevations".format(genBase(src, out_p)))
