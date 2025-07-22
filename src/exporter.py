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




Commented Code:

import numpy as np                     # NumPy is used for numerical operations and array handling
from stl import mesh                  # `mesh` from numpy-stl is used to create and manipulate STL meshes
import trimesh                        # Trimesh provides tools for loading/exporting 3D mesh data
import ezdxf                          # ezdxf is used to write DXF files with mesh geometry

# Function to save a mesh as an STL file
def save_mesh_as_stl(vertices, faces, out_path):
    # Create an empty mesh object with the same number of faces
    new_mesh = mesh.Mesh(np.zeros(len(faces), dtype=mesh.Mesh.dtype))
    
    # Iterate through each face (triangle) and assign its vertices to the mesh
    for i, tri in enumerate(faces):
        for j in range(3):
            # Assign each vertex (as 3D coordinate) to the STL mesh triangle
            new_mesh.vectors[i][j] = vertices[tri[j]]
    
    # Save the mesh to the given output path as an STL file
    new_mesh.save(out_path)

# Function to save a mesh as an OBJ file
def save_mesh_as_obj(vertices, faces, out_path):
    # Create a Trimesh object from vertices and faces
    out_m = trimesh.Trimesh(vertices=vertices, faces=faces)
    
    # Export the mesh to an OBJ file at the specified path
    out_m.export(out_path)

# Function to save a mesh as a DXF file
def save_mesh_as_dxf(vertices, faces, out_path):
    # Create a new DXF drawing
    d = ezdxf.new()
    
    # Get access to the model space where entities will be added
    msp = d.modelspace()
    
    # Iterate over each triangular face
    for tri in faces:
        if len(tri) == 3:
            # Retrieve the three vertices of the triangle
            p1 = vertices[tri[0]]  # First vertex (x, y, z)
            p2 = vertices[tri[1]]  # Second vertex (x, y, z)
            p3 = vertices[tri[2]]  # Third vertex (x, y, z)

            # Add a 3D face entity to the DXF (last point repeated for 4th vertex)
            msp.add_3dface([p1, p2, p3, p3])  # DXF requires 4 points; we repeat the last one here
    
    # Save the DXF file to the given output path
    d.saveas(out_path)
