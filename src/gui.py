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
