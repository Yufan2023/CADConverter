import os
import numpy as np
import trimesh
from stl import mesh
import ezdxf

from OCC.Core.XCAFApp import XCAFApp_Application
from OCC.Core.XCAFDoc import XCAFDoc_DocumentTool
from OCC.Core.TCollection import TCollection_ExtendedString
from OCC.Core.STEPCAFControl import STEPCAFControl_Reader, STEPCAFControl_Writer
from OCC.Core.IFSelect import IFSelect_RetDone
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh
from OCC.Core.BRep import BRep_Tool
from OCC.Core.TopExp import TopExp_Explorer
from OCC.Core.TopoDS import TopoDS_Compound, TopoDS_Face
from OCC.Core.TopAbs import TopAbs_FACE
from OCC.Core.gp import gp_Pnt
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeFace, BRepBuilderAPI_MakePolygon
from OCC.Core.BRep import BRep_Builder
from OCC.Core.STEPControl import STEPControl_Reader
from .exporter import save_mesh_as_stl, save_mesh_as_obj, save_mesh_as_dxf


def create_empty_xcaf_doc():
    app = XCAFApp_Application.GetApplication()
    fmt = TCollection_ExtendedString("BinXCAF")
    doc_handle = app.NewDocument(fmt)
    doc = doc_handle.get()
    shape_tool = XCAFDoc_DocumentTool.ShapeTool(doc.Main())
    return doc, shape_tool


def load_step_xcaf(filepath):
    doc, shape_tool = create_empty_xcaf_doc()
    reader = STEPCAFControl_Reader()
    status = reader.ReadFile(filepath)
    if status == IFSelect_RetDone:
        reader.Transfer(doc.GetHandle())
    else:
        print(f"Failed to read STEP: {filepath}")
    return doc, shape_tool


def merge_xcaf_docs_into(target_doc, target_shape_tool, source_doc):
    source_shape_tool = XCAFDoc_DocumentTool.ShapeTool(source_doc.Main())
    it = source_shape_tool.NewIterator()
    while it.More():
        source_label = it.Value()
        source_shape_tool.CopyShape(source_label, target_shape_tool)
        it.Next()


def save_xcaf_to_step(doc, out_path):
    writer = STEPCAFControl_Writer()
    writer.Transfer(doc.GetHandle())
    writer.Write(out_path)


def load_stl_as_mesh(stl_path):
    stl_mesh = mesh.Mesh.from_file(stl_path)
    raw_verts = stl_mesh.vectors.reshape(-1, 3)
    unique_verts, inv = np.unique(raw_verts, axis=0, return_inverse=True)
    faces = inv.reshape(-1, 3).tolist()
    vertices = unique_verts.tolist()
    return vertices, faces


def load_obj_as_mesh(obj_path):
    obj_mesh = trimesh.load(obj_path)
    return obj_mesh.vertices.tolist(), obj_mesh.faces.tolist()


def load_dxf_as_mesh(dxf_path):
    doc = ezdxf.readfile(dxf_path)
    msp = doc.modelspace()

    vertices = []
    faces = []
    vert_cache = {}
    idx_count = 0

    for entity in msp.query("3DFACE"):
        raw_pts = list(entity.wcs_vertices())
        unique_pts = []
        for pt in raw_pts:
            if pt not in unique_pts:
                unique_pts.append(pt)

        face_indices = []
        for pt in unique_pts:
            if pt not in vert_cache:
                vert_cache[pt] = idx_count
                vertices.append(pt)
                idx_count += 1
            face_indices.append(vert_cache[pt])

        if len(face_indices) == 3:
            faces.append(face_indices)
        elif len(face_indices) == 4:
            faces.append([face_indices[0], face_indices[1], face_indices[2]])
            faces.append([face_indices[0], face_indices[2], face_indices[3]])

    return vertices, faces


def mesh_to_occ_shape(vertices, faces):
    builder = BRep_Builder()
    compound = TopoDS_Compound()
    builder.MakeCompound(compound)

    for tri in faces:
        if len(tri) < 3:
            continue
        p1 = gp_Pnt(*vertices[tri[0]])
        p2 = gp_Pnt(*vertices[tri[1]])
        p3 = gp_Pnt(*vertices[tri[2]])

        polygon_maker = BRepBuilderAPI_MakePolygon(p1, p2, p3, True)
        wire = polygon_maker.Wire()
        face_maker = BRepBuilderAPI_MakeFace(wire)
        if face_maker.IsDone():
            face = face_maker.Face()
            builder.Add(compound, face)

    return compound


def add_occ_shape_to_xcaf(doc, shape_tool, shape, label_name="TessellatedMesh"):
    label = shape_tool.AddShape(shape)
    shape_tool.SetShapeName(label, TCollection_ExtendedString(label_name))
    return label


def tessellate_step_shape(shape, deflection=0.1):
    BRepMesh_IncrementalMesh(shape, deflection, True)
    all_verts = []
    all_faces = []
    vert_cache = {}
    idx_count = 0

    exp = TopExp_Explorer(shape, TopAbs_FACE)
    while exp.More():
        face = TopoDS_Face(exp.Current())
        triangulation = BRep_Tool.Triangulation(face, None)
        if triangulation:
            nodes = triangulation.Nodes()
            triangles = triangulation.Triangles()

            for i in range(1, nodes.Length() + 1):
                p = nodes.Value(i)
                coords = (p.X(), p.Y(), p.Z())
                if coords not in vert_cache:
                    vert_cache[coords] = idx_count
                    all_verts.append(coords)
                    idx_count += 1

            for i in range(1, triangles.Length() + 1):
                tri = triangles.Value(i)
                i1, i2, i3 = tri.Get()
                v1 = vert_cache[(nodes.Value(i1).X(), nodes.Value(i1).Y(), nodes.Value(i1).Z())]
                v2 = vert_cache[(nodes.Value(i2).X(), nodes.Value(i2).Y(), nodes.Value(i2).Z())]
                v3 = vert_cache[(nodes.Value(i3).X(), nodes.Value(i3).Y(), nodes.Value(i3).Z())]
                all_faces.append([v1, v2, v3])
        exp.Next()

    return all_verts, all_faces


def merge_files_to_step(filepaths, out_step):
    master_doc, master_tool = create_empty_xcaf_doc()

    for fpath in filepaths:
        ext = os.path.splitext(fpath)[1].lower()
        if ext == ".step":
            sub_doc, sub_tool = load_step_xcaf(fpath)
            merge_xcaf_docs_into(master_doc, master_tool, sub_doc)
        elif ext in [".stl", ".obj", ".dxf"]:
            if ext == ".stl":
                v, f = load_stl_as_mesh(fpath)
            elif ext == ".obj":
                v, f = load_obj_as_mesh(fpath)
            else:
                v, f = load_dxf_as_mesh(fpath)
            shape = mesh_to_occ_shape(v, f)
            add_occ_shape_to_xcaf(master_doc, master_tool, shape, label_name=os.path.basename(fpath))
        else:
            print(f"Skipping unsupported format: {fpath}")

    save_xcaf_to_step(master_doc, out_step)


def merge_files_to_mesh(filepaths, out_path, out_format):
    all_meshes = []

    for fpath in filepaths:
        ext = os.path.splitext(fpath)[1].lower()
        if ext == ".stl":
            v, fc = load_stl_as_mesh(fpath)
        elif ext == ".obj":
            v, fc = load_obj_as_mesh(fpath)
        elif ext == ".dxf":
            v, fc = load_dxf_as_mesh(fpath)
        elif ext == ".step":
            r = STEPControl_Reader()
            st = r.ReadFile(fpath)
            if st == IFSelect_RetDone:
                r.TransferRoot(1)
                shape = r.Shape()
                v, fc = tessellate_step_shape(shape, 0.1)
            else:
                continue
        else:
            print(f"Skipping unsupported format: {fpath}")
            continue
        all_meshes.append((v, fc))

    merged_vertices = []
    merged_faces = []
    offset = 0

    for (v, fc) in all_meshes:
        for face in fc:
            merged_faces.append([idx + offset for idx in face])
        merged_vertices.extend(v)
        offset += len(v)

    if out_format == "stl":
        save_mesh_as_stl(merged_vertices, merged_faces, out_path)
    elif out_format == "obj":
        save_mesh_as_obj(merged_vertices, merged_faces, out_path)
    elif out_format == "dxf":
        save_mesh_as_dxf(merged_vertices, merged_faces, out_path)








Commented Code:

# Import standard libraries and external modules
import os  # For file path handling
import numpy as np  # For numerical operations and array handling
import trimesh  # For loading and working with .obj mesh files
from stl import mesh  # For loading STL mesh files
import ezdxf  # For reading DXF files

# Import OpenCascade (OCC) modules for handling CAD geometry and STEP formats
from OCC.Core.XCAFApp import XCAFApp_Application  # To initiate XCAF document application
from OCC.Core.XCAFDoc import XCAFDoc_DocumentTool  # Tools to manipulate shapes in XCAF
from OCC.Core.TCollection import TCollection_ExtendedString  # For setting label names
from OCC.Core.STEPCAFControl import STEPCAFControl_Reader, STEPCAFControl_Writer  # For STEP read/write with XCAF
from OCC.Core.IFSelect import IFSelect_RetDone  # Status check for file read success
from OCC.Core.BRepMesh import BRepMesh_IncrementalMesh  # Tessellation of BRep shapes
from OCC.Core.BRep import BRep_Tool  # To access geometry like triangulations
from OCC.Core.TopExp import TopExp_Explorer  # To traverse shape topology
from OCC.Core.TopoDS import TopoDS_Compound, TopoDS_Face  # OCC shape types
from OCC.Core.TopAbs import TopAbs_FACE  # Enum for identifying face shapes
from OCC.Core.gp import gp_Pnt  # Point class for geometric definitions
from OCC.Core.BRepBuilderAPI import BRepBuilderAPI_MakeFace, BRepBuilderAPI_MakePolygon  # Tools to create faces and polygons
from OCC.Core.BRep import BRep_Builder  # Builder to assemble shapes
from OCC.Core.STEPControl import STEPControl_Reader  # For basic STEP file reading

# Exporter functions assumed to be in a separate module for writing to STL/OBJ/DXF
from .exporter import save_mesh_as_stl, save_mesh_as_obj, save_mesh_as_dxf

# Create a new empty XCAF document and return the document and shape tool
def create_empty_xcaf_doc():
    app = XCAFApp_Application.GetApplication()  # Initialize the XCAF application
    fmt = TCollection_ExtendedString("BinXCAF")  # Define binary XCAF format
    doc_handle = app.NewDocument(fmt)  # Create new document
    doc = doc_handle.get()  # Extract the document object
    shape_tool = XCAFDoc_DocumentTool.ShapeTool(doc.Main())  # Get shape manipulation tool
    return doc, shape_tool

# Load a STEP file into an XCAF document using STEPCAF reader
def load_step_xcaf(filepath):
    doc, shape_tool = create_empty_xcaf_doc()  # Create new empty XCAF doc
    reader = STEPCAFControl_Reader()  # Initialize STEP reader
    status = reader.ReadFile(filepath)  # Try to read STEP file
    if status == IFSelect_RetDone:  # Check if reading was successful
        reader.Transfer(doc.GetHandle())  # Transfer geometry into XCAF doc
    else:
        print(f"Failed to read STEP: {filepath}")
    return doc, shape_tool  # Return document and shape tool

# Merge all shapes from source_doc into target_doc
def merge_xcaf_docs_into(target_doc, target_shape_tool, source_doc):
    source_shape_tool = XCAFDoc_DocumentTool.ShapeTool(source_doc.Main())  # Get shape tool from source
    it = source_shape_tool.NewIterator()  # Create iterator for source shapes
    while it.More():
        source_label = it.Value()  # Get shape label
        source_shape_tool.CopyShape(source_label, target_shape_tool)  # Copy shape to target tool
        it.Next()

# Write the XCAF document to a STEP file using STEPCAF writer
def save_xcaf_to_step(doc, out_path):
    writer = STEPCAFControl_Writer()  # Initialize STEP writer
    writer.Transfer(doc.GetHandle())  # Transfer all shapes in doc to writer
    writer.Write(out_path)  # Write to file

# Load an STL file and convert it into vertex and face lists
def load_stl_as_mesh(stl_path):
    stl_mesh = mesh.Mesh.from_file(stl_path)  # Load STL mesh
    raw_verts = stl_mesh.vectors.reshape(-1, 3)  # Flatten triangle vectors into vertex list
    unique_verts, inv = np.unique(raw_verts, axis=0, return_inverse=True)  # Remove duplicate vertices
    faces = inv.reshape(-1, 3).tolist()  # Remap faces using unique indices
    vertices = unique_verts.tolist()  # Convert vertices to list
    return vertices, faces  # Return mesh data

# Load an OBJ file using trimesh and extract vertex and face data
def load_obj_as_mesh(obj_path):
    obj_mesh = trimesh.load(obj_path)  # Load mesh using trimesh
    return obj_mesh.vertices.tolist(), obj_mesh.faces.tolist()  # Return vertices and faces

# Load a DXF file and extract 3D faces as mesh
def load_dxf_as_mesh(dxf_path):
    doc = ezdxf.readfile(dxf_path)  # Open DXF document
    msp = doc.modelspace()  # Get model space

    vertices = []
    faces = []
    vert_cache = {}  # Cache to avoid duplicate vertices
    idx_count = 0  # Counter for indexing vertices

    # Iterate over 3DFACE entities in the DXF
    for entity in msp.query("3DFACE"):
        raw_pts = list(entity.wcs_vertices())  # Get 3D face points
        unique_pts = []
        for pt in raw_pts:
            if pt not in unique_pts:
                unique_pts.append(pt)

        face_indices = []
        for pt in unique_pts:
            if pt not in vert_cache:
                vert_cache[pt] = idx_count
                vertices.append(pt)
                idx_count += 1
            face_indices.append(vert_cache[pt])

        # Add triangular or quad face (split into two triangles)
        if len(face_indices) == 3:
            faces.append(face_indices)
        elif len(face_indices) == 4:
            faces.append([face_indices[0], face_indices[1], face_indices[2]])
            faces.append([face_indices[0], face_indices[2], face_indices[3]])

    return vertices, faces

# Convert a mesh (vertices and faces) into an OCC compound shape
def mesh_to_occ_shape(vertices, faces):
    builder = BRep_Builder()  # Create BRep builder
    compound = TopoDS_Compound()  # Create a compound shape
    builder.MakeCompound(compound)  # Initialize compound

    for tri in faces:
        if len(tri) < 3:
            continue
        # Convert vertex coordinates to OCC points
        p1 = gp_Pnt(*vertices[tri[0]])
        p2 = gp_Pnt(*vertices[tri[1]])
        p3 = gp_Pnt(*vertices[tri[2]])

        # Create polygon and face from triangle
        polygon_maker = BRepBuilderAPI_MakePolygon(p1, p2, p3, True)
        wire = polygon_maker.Wire()
        face_maker = BRepBuilderAPI_MakeFace(wire)
        if face_maker.IsDone():
            face = face_maker.Face()
            builder.Add(compound, face)  # Add face to compound

    return compound  # Return assembled compound shape

# Add OCC shape into XCAF document and assign a name
def add_occ_shape_to_xcaf(doc, shape_tool, shape, label_name="TessellatedMesh"):
    label = shape_tool.AddShape(shape)  # Add shape to shape tool
    shape_tool.SetShapeName(label, TCollection_ExtendedString(label_name))  # Assign label name
    return label

# Tessellate a STEP shape and extract mesh (vertices and faces)
def tessellate_step_shape(shape, deflection=0.1):
    BRepMesh_IncrementalMesh(shape, deflection, True)  # Perform tessellation
    all_verts = []
    all_faces = []
    vert_cache = {}
    idx_count = 0

    # Explore each face in the shape
    exp = TopExp_Explorer(shape, TopAbs_FACE)
    while exp.More():
        face = TopoDS_Face(exp.Current())
        triangulation = BRep_Tool.Triangulation(face, None)
        if triangulation:
            nodes = triangulation.Nodes()
            triangles = triangulation.Triangles()

            # Store unique vertex coordinates
            for i in range(1, nodes.Length() + 1):
                p = nodes.Value(i)
                coords = (p.X(), p.Y(), p.Z())
                if coords not in vert_cache:
                    vert_cache[coords] = idx_count
                    all_verts.append(coords)
                    idx_count += 1

            # Store triangle face indices
            for i in range(1, triangles.Length() + 1):
                tri = triangles.Value(i)
                i1, i2, i3 = tri.Get()
                v1 = vert_cache[(nodes.Value(i1).X(), nodes.Value(i1).Y(), nodes.Value(i1).Z())]
                v2 = vert_cache[(nodes.Value(i2).X(), nodes.Value(i2).Y(), nodes.Value(i2).Z())]
                v3 = vert_cache[(nodes.Value(i3).X(), nodes.Value(i3).Y(), nodes.Value(i3).Z())]
                all_faces.append([v1, v2, v3])
        exp.Next()

    return all_verts, all_faces  # Return tessellated mesh

# Merge various CAD files into a unified STEP file
def merge_files_to_step(filepaths, out_step):
    master_doc, master_tool = create_empty_xcaf_doc()  # Start master doc

    for fpath in filepaths:
        ext = os.path.splitext(fpath)[1].lower()
        if ext == ".step":
            sub_doc, sub_tool = load_step_xcaf(fpath)
            merge_xcaf_docs_into(master_doc, master_tool, sub_doc)
        elif ext in [".stl", ".obj", ".dxf"]:
            if ext == ".stl":
                v, f = load_stl_as_mesh(fpath)
            elif ext == ".obj":
                v, f = load_obj_as_mesh(fpath)
            else:
                v, f = load_dxf_as_mesh(fpath)
            shape = mesh_to_occ_shape(v, f)
            add_occ_shape_to_xcaf(master_doc, master_tool, shape, label_name=os.path.basename(fpath))
        else:
            print(f"Skipping unsupported format: {fpath}")

    save_xcaf_to_step(master_doc, out_step)

# Merge various CAD files and output as a unified mesh file (stl/obj/dxf)
def merge_files_to_mesh(filepaths, out_path, out_format):
    all_meshes = []

    for fpath in filepaths:
        ext = os.path.splitext(fpath)[1].lower()
        if ext == ".stl":
            v, fc = load_stl_as_mesh(fpath)
        elif ext == ".obj":
            v, fc = load_obj_as_mesh(fpath)
        elif ext == ".dxf":
            v, fc = load_dxf_as_mesh(fpath)
        elif ext == ".step":
            r = STEPControl_Reader()
            st = r.ReadFile(fpath)
            if st == IFSelect_RetDone:
                r.TransferRoot(1)
                shape = r.Shape()
                v, fc = tessellate_step_shape(shape, 0.1)
            else:
                continue
        else:
            print(f"Skipping unsupported format: {fpath}")
            continue
        all_meshes.append((v, fc))

    # Combine all meshes into one
    merged_vertices = []
    merged_faces = []
    offset = 0

    for (v, fc) in all_meshes:
        for face in fc:
            merged_faces.append([idx + offset for idx in face])
        merged_vertices.extend(v)
        offset += len(v)

    # Export to desired mesh format
    if out_format == "stl":
        save_mesh_as_stl(merged_vertices, merged_faces, out_path)
    elif out_format == "obj":
        save_mesh_as_obj(merged_vertices, merged_faces, out_path)
    elif out_format == "dxf":
        save_mesh_as_dxf(merged_vertices, merged_faces, out_path)

