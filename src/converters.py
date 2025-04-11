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
