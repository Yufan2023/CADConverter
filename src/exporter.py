import numpy as np
from stl import mesh
import trimesh
import ezdxf

def save_mesh_as_stl(vertices, faces, out_path):
    new_mesh = mesh.Mesh(np.zeros(len(faces), dtype=mesh.Mesh.dtype))
    for i, tri in enumerate(faces):
        for j in range(3):
            new_mesh.vectors[i][j] = vertices[tri[j]]
    new_mesh.save(out_path)

def save_mesh_as_obj(vertices, faces, out_path):
    out_m = trimesh.Trimesh(vertices=vertices, faces=faces)
    out_m.export(out_path)

def save_mesh_as_dxf(vertices, faces, out_path):
    d = ezdxf.new()
    msp = d.modelspace()
    for tri in faces:
        if len(tri) == 3:
            p1, p2, p3 = vertices[tri[0]], vertices[tri[1]], vertices[tri[2]]
            msp.add_3dface([p1, p2, p3, p3])
    d.saveas(out_path)
