# src/gui.py

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
from converters import merge_files_to_step, merge_files_to_mesh

root = tk.Tk()
root.title("Multi-CAD Converter")
root.geometry("650x450")

file_list = []

def select_files():
    chosen = filedialog.askopenfilenames(filetypes=[("3D Files", "*.stl;*.obj;*.dxf;*.step")])
    for f in chosen:
        file_list.append(f)
        listbox_files.insert(tk.END, os.path.basename(f))

def convert_and_merge():
    if not file_list:
        messagebox.showwarning("No Files", "Please select files first!")
        return

    out_format = combo_format.get().lower()
    out_ext = "." + out_format
    save_path = filedialog.asksaveasfilename(defaultextension=out_ext,
        filetypes=[(f"{out_format.upper()} Files", f"*{out_ext}")])
    if not save_path:
        return

    try:
        if out_format == "step":
            merge_files_to_step(file_list, save_path)
        else:
            merge_files_to_mesh(file_list, save_path, out_format)
        messagebox.showinfo("Success", f"✅ File saved: {save_path}")
    except Exception as ex:
        messagebox.showerror("Error", str(ex))

label_title = tk.Label(root, text="Select 3D Files to Merge", font=("Arial", 14))
label_title.pack(pady=10)

listbox_files = tk.Listbox(root, width=60, height=10)
listbox_files.pack(pady=5)

btn_select = tk.Button(root, text="Select Files", command=select_files, font=("Arial", 12))
btn_select.pack(pady=5)

frame_out = tk.Frame(root)
frame_out.pack()

label_format = tk.Label(frame_out, text="Output Format:", font=("Arial", 12))
label_format.pack(side=tk.LEFT, padx=5)

combo_format = ttk.Combobox(frame_out, values=["step", "stl", "obj", "dxf"], width=6)
combo_format.set("step")
combo_format.pack(side=tk.LEFT)

btn_convert = tk.Button(root, text="Convert & Merge", command=convert_and_merge, font=("Arial", 12))
btn_convert.pack(pady=20)

root.mainloop()



Commented Code:

# src/gui.py

import tkinter as tk  # Standard GUI toolkit
from tkinter import filedialog, messagebox, ttk  # Common widgets and dialogs
import os  # For file path operations
from converters import merge_files_to_step, merge_files_to_mesh  # Custom functions to merge and convert CAD files

# Initialize the main GUI window
root = tk.Tk()
root.title("Multi-CAD Converter")  # Set window title
root.geometry("650x450")  # Set window size

file_list = []  # List to store paths of selected 3D files

# Function to handle file selection
def select_files():
    # Open file dialog to choose multiple 3D files of supported formats
    chosen = filedialog.askopenfilenames(filetypes=[("3D Files", "*.stl;*.obj;*.dxf;*.step")])
    for f in chosen:
        file_list.append(f)  # Add selected file to internal list
        listbox_files.insert(tk.END, os.path.basename(f))  # Display filename in listbox

# Function to merge and convert selected files to the chosen output format
def convert_and_merge():
    if not file_list:
        messagebox.showwarning("No Files", "Please select files first!")  # Alert if no files selected
        return

    out_format = combo_format.get().lower()  # Get output format selected in combo box
    out_ext = "." + out_format  # Format extension (e.g., .step)

    # Prompt user to choose save path for merged file
    save_path = filedialog.asksaveasfilename(
        defaultextension=out_ext,
        filetypes=[(f"{out_format.upper()} Files", f"*{out_ext}")]
    )
    if not save_path:
        return  # Cancel if user didn't provide a path

    try:
        # Call appropriate merge function based on format
        if out_format == "step":
            merge_files_to_step(file_list, save_path)
        else:
            merge_files_to_mesh(file_list, save_path, out_format)

        # Notify user of success
        messagebox.showinfo("Success", f"✅ File saved: {save_path}")
    except Exception as ex:
        # Show any error that occurs during conversion
        messagebox.showerror("Error", str(ex))

# --- GUI Layout Section ---

# Title label
label_title = tk.Label(root, text="Select 3D Files to Merge", font=("Arial", 14))
label_title.pack(pady=10)

# Listbox to show selected files
listbox_files = tk.Listbox(root, width=60, height=10)
listbox_files.pack(pady=5)

# Button to open file selector
btn_select = tk.Button(root, text="Select Files", command=select_files, font=("Arial", 12))
btn_select.pack(pady=5)

# Frame to hold output format controls
frame_out = tk.Frame(root)
frame_out.pack()

# Label for output format
label_format = tk.Label(frame_out, text="Output Format:", font=("Arial", 12))
label_format.pack(side=tk.LEFT, padx=5)

# Dropdown combo box for format selection
combo_format = ttk.Combobox(frame_out, values=["step", "stl", "obj", "dxf"], width=6)
combo_format.set("step")  # Default selection
combo_format.pack(side=tk.LEFT)

# Button to trigger file merge and export
btn_convert = tk.Button(root, text="Convert & Merge", command=convert_and_merge, font=("Arial", 12))
btn_convert.pack(pady=20)

# Start the Tkinter main event loop
root.mainloop()


