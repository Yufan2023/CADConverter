# CADConverter

# 🛠️ Multi-CAD Converter

A user-friendly Python application for merging and converting 3D model files across the most widely used CAD file formats: `.STL`, `.OBJ`, `.DXF`, and `.STEP`. With just a few clicks, you can pull together 3D models from different sources, merge them seamlessly, and export the result in whatever format fits your workflow best — all through a simple, interactive interface that doesn't require writing a single line of code.

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


## 🛠 Installation

### 1. Clone this repository

```bash
git clone https://github.com/YOUR_USERNAME/multi-cad-converter.git
cd multi-cad-converter
```

### 2. Create a virtual environment (optional but recommended)
```bash
python -m venv venv
source venv/bin/activate
```

### 3. Install required packages
```bash
pip install -r requirements.txt
```

### 4. Launch the app
```bash
python src/gui.py
```


## 📂 Supported Formats

| Format  | Read | Write | Notes                                        |
|---------|------|-------|----------------------------------------------|
| `.step` | ✅   | ✅    | Ideal for CAD software interoperability       |
| `.stl`  | ✅   | ✅    | Perfect for 3D printing                       |
| `.obj`  | ✅   | ✅    | Used in 3D modeling and game development      |
| `.dxf`  | ✅   | ✅    | Supports 3DFACE-based 3D geometry in drawings |


## 🔍 How It Works
STEP files are loaded using ```pythonOCC``` to preserve parametric geometry.

STL, OBJ, and DXF files are tessellated into triangle meshes.

All inputs are converted into OpenCASCADE shapes.

The shapes are merged and exported to your chosen format.

## 📸 GUI Preview
(Add a screenshot and update the path below if available)


## 🔧 Extend It
You can easily extend this tool by:

Adding new formats (like .3mf, .igs, or .glb)

Integrating file alignment or scaling

Creating a CLI mode

Automating file naming and versioning

Supporting texture/material data for .obj

The code is organized and modular — so it’s easy to build on.












