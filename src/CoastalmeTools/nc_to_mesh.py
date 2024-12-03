# from mdal import *
import matplotlib.pyplot as plt
from mpl_toolkits import mplot3d



def nc_to_mesh(in_f):
    ds = Datasource(in_f)

    with ds.load(0) as mesh:
        vertex = mesh.vertices
        faces = mesh.faces
        edges = mesh.edges

        group = mesh.group(0)
        data = []
        time = []
        for i in range(0, group.dataset_count):
            data.append(group.data(i))
            time.append(group.dataset_time(i))


        out = PyMesh()
        out.deep_copy(mesh)
        out.data_copy(mesh)

        mio = MDAL_transform.to_meshio(out)
        # mio.write(str(out_f))
        return mio


