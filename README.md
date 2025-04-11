# CADConverter

# 🛠️ Multi-CAD Converter

A user-friendly Python application for merging and converting 3D model files across the most widely used CAD file formats: `.STL`, `.OBJ`, `.DXF`, and `.STEP`. With just a few clicks, engineers, designers, and researchers can consolidate geometry from various sources and export in the format best suited for their workflow — all through a clean, interactive GUI powered by `tkinter`.

---

## 💡 Why These Four Formats?

The selected formats represent a comprehensive cross-section of CAD ecosystems — balancing simplicity, interoperability, and geometric richness:

- **`.STL`**: The standard format for 3D printing and rapid prototyping, supported by virtually all slicers and modeling tools. Its simplicity makes it ideal for mesh-based workflows, though it lacks color and material metadata.

- **`.OBJ`**: A flexible mesh format used in visual effects, gaming, and modeling. It supports color, UV mapping, and is natively supported in platforms like Blender, Maya, and Unity.

- **`.DXF`**: A 2D/3D drawing format developed by Autodesk for interoperability between CAD platforms. Particularly useful for transferring engineering drawings or simple 3D faces into platforms like AutoCAD, DraftSight, or Fusion 360.

- **`.STEP` (ISO 10303)**: The industry-standard format for exchanging precise, parametric geometry (B-Rep) between solid modeling systems like SolidWorks, CATIA, Siemens NX, and Autodesk Inventor. It retains structure, hierarchy, and design intent better than any mesh format.

Together, these formats allow seamless transition between **mesh-based**, **drawing-based**, and **solid-model-based** environments, supporting a wide range of downstream tasks — from additive manufacturing to CAD simulation, visualization, and collaborative design.

---

## 🚀 Features

- ✅ **Multi-format support**: Import `.stl`, `.obj`, `.dxf`, and `.step` files from any source
- 🧠 **Preserves geometry**: Utilizes `pythonOCC` to retain B-Rep fidelity in STEP files
- 🧩 **Merging capability**: Combine heterogeneous files into a single unified mesh or STEP assembly
- 📤 **Export flexibility**: Output your final file in `.step`, `.stl`, `.obj`, or `.dxf` formats
- 🖥 **GUI-based**: Designed with `tkinter` for a no-code, intuitive experience
- 🔄 **Extensible**: Modular Python backend supports easy extension to formats like `.3mf`, `.igs`, or `.glTF`

---


