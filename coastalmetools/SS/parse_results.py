from nc_to_mesh import nc_to_mesh

def parse_results(path, var):
    full_path = path / (var+".nc")
    full_path2 = path

    nc_to_mesh(full_path, full_path2)
    
    pass