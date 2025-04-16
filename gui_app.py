import os
import sys
import customtkinter as ctk
from tkinter import filedialog, messagebox, ttk
from tkinterdnd2 import TkinterDnD
import threading
import subprocess

# Force check Blender availability early
try:
    from logic.blender_cleaner import run_blender_cleaner, BLENDER_PATH, prompt_blender_missing
    if not os.path.isfile(BLENDER_PATH):
        prompt_blender_missing()
except Exception as e:
    messagebox.showerror("Fatal Error", f"Error while checking Blender: {e}")
    sys.exit(1)

def check_dependencies():
    try:
        import customtkinter
        import tkinterdnd2
    except ImportError:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "customtkinter", "tkinterdnd2"])
        return check_dependencies()

    if sys.version_info < (3, 8):
        messagebox.showerror("Python Version Error", "Python 3.8+ is required to run this tool.")
        return False

    return True

class OBJFixerGUI(TkinterDnD.Tk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        self.title("Blockbench OBJ Fixer")
        self.geometry("1000x700")
        self.configure(bg="#1a1a1a")

        self.selected_files = []
        self.output_dir = None
        self.entry_boxes = []
        self.create_java = ctk.BooleanVar(value=True)
        self.create_txt = ctk.BooleanVar(value=False)

        self.setup_widgets()

    def setup_widgets(self):
        main = ctk.CTkFrame(self, fg_color="#1a1a1a")
        main.pack(fill='both', expand=True, padx=0, pady=0)
        main.columnconfigure((0, 1, 2), weight=1)
        main.rowconfigure((1, 2, 3), weight=1)

        self.file_input_frame_border = ctk.CTkFrame(main, fg_color="#1a1a1a", border_color="#1a1a1a", border_width=2)
        self.file_input_frame_border.grid(row=1, column=0, columnspan=2, sticky='nsew', padx=5, pady=5)
        self.file_input_frame = ctk.CTkScrollableFrame(self.file_input_frame_border)
        self.file_input_frame.pack(fill='both', expand=True)

        self.preview_wrapper_border = ctk.CTkFrame(main, fg_color="#1a1a1a", border_color="#1a1a1a", border_width=2)
        self.preview_wrapper_border.grid(row=1, column=2, sticky='nsew', padx=5, pady=5)
        self.preview_wrapper = ctk.CTkFrame(self.preview_wrapper_border)
        self.preview_wrapper.pack(fill='both', expand=True)

        self.output_tree_label = ctk.CTkLabel(self.preview_wrapper, text="Folder Selected: (No Output Folder)", anchor="w")
        self.output_tree_label.pack(fill='x', padx=5, pady=(5, 0))

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#2b2b2b", foreground="white", fieldbackground="#2b2b2b", borderwidth=0, relief="flat")
        style.map("Treeview", background=[("selected", "#404040")])

        self.output_tree = ttk.Treeview(self.preview_wrapper, show='tree')
        self.output_tree.pack(fill='both', expand=True)

        self.left_btn_frame = ctk.CTkFrame(main, fg_color="transparent")
        self.left_btn_frame.grid(row=0, column=0, columnspan=2, sticky="n", pady=10)
        self.browse_btn = ctk.CTkButton(self.left_btn_frame, text="Browse .OBJ Files", command=self.browse_files, border_width=2)
        self.browse_btn.pack()

        self.right_btn_frame = ctk.CTkFrame(main, fg_color="transparent")
        self.right_btn_frame.grid(row=0, column=2, sticky="n", pady=10)
        self.folder_btn = ctk.CTkButton(self.right_btn_frame, text="Select Output Folder", command=self.choose_output_dir, border_width=2)
        self.folder_btn.pack()

        toggle_frame = ctk.CTkFrame(main, fg_color="transparent")
        toggle_frame.grid(row=2, column=0, sticky='n', pady=5)
        ctk.CTkCheckBox(toggle_frame, text="Generate Java Class", variable=self.create_java, command=self.toggle_txt_option).pack(anchor='w', padx=20)
        ctk.CTkCheckBox(toggle_frame, text="Generate .txt Groupings", variable=self.create_txt).pack(anchor='w', padx=20, pady=5)

        ctk.CTkButton(main, text="Run Conversion", height=40, font=("Arial", 18), command=self.run_conversion).grid(row=2, column=1, pady=10)
        self.log_box = ctk.CTkTextbox(main, height=150)
        self.log_box.grid(row=3, column=0, columnspan=3, sticky='nsew', padx=5, pady=5)

    def toggle_txt_option(self):
        if self.create_java.get():
            self.create_txt.set(False)
        for _, java_field, _ in self.entry_boxes:
            java_field.configure(state="normal" if self.create_java.get() else "disabled")
            if not self.create_java.get():
                java_field.configure(border_color="#3a3a3a")

    def refresh_fields(self):
        for widget in self.file_input_frame.winfo_children():
            widget.destroy()
        self.entry_boxes.clear()

        for file in self.selected_files:
            filename = os.path.basename(file)
            row = ctk.CTkFrame(self.file_input_frame)
            row.pack(fill='x', padx=2, pady=2)

            ctk.CTkLabel(row, text=filename, width=160, anchor='w').pack(side='left', padx=5)
            model_name = ctk.CTkEntry(row, placeholder_text="Model Output Name", border_width=2)
            model_name.pack(side='left', fill='x', expand=True, padx=(5, 5))
            java_field = ctk.CTkEntry(row, placeholder_text="Java Class Name", border_width=2)
            java_field.pack(side='left', fill='x', expand=True)

            model_name.bind("<KeyRelease>", lambda e, entry=model_name: entry.configure(border_color="#3a3a3a"))
            java_field.bind("<KeyRelease>", lambda e, entry=java_field: entry.configure(border_color="#3a3a3a"))

            self.entry_boxes.append((file, java_field, model_name))
        self.toggle_txt_option()

    def browse_files(self):
        self.browse_btn.configure(border_color="#3a3a3a")
        files = filedialog.askopenfilenames(filetypes=[("OBJ files", "*.obj")])
        for file in files:
            if file not in self.selected_files:
                self.selected_files.append(file)
        self.refresh_fields()

    def choose_output_dir(self):
        self.folder_btn.configure(border_color="#3a3a3a")
        directory = filedialog.askdirectory()
        if not directory:
            return
        self.output_dir = directory
        self.preview_wrapper_border.configure(border_color="#1a1a1a")
        self.log(f"Output directory set to: {self.output_dir}")
        self.update_output_preview()

    def update_output_preview(self):
        self.output_tree.delete(*self.output_tree.get_children())
        folder_name = os.path.basename(self.output_dir) if self.output_dir else "(No Output Folder)"
        self.output_tree_label.configure(text=f"Folder Selected: {folder_name}")
        def insert_node(parent, path):
            for item in sorted(os.listdir(path)):
                full_path = os.path.join(path, item)
                node = self.output_tree.insert(parent, 'end', text=item, open=False)
                if os.path.isdir(full_path):
                    insert_node(node, full_path)
        if self.output_dir:
            insert_node('', self.output_dir)

    def log(self, message):
        self.log_box.insert('end', message + '\n')
        self.log_box.see('end')

    def run_conversion(self):
        self.file_input_frame_border.configure(border_color="#1a1a1a")
        self.preview_wrapper_border.configure(border_color="#1a1a1a")
        self.browse_btn.configure(border_color="#3a3a3a")
        self.folder_btn.configure(border_color="#3a3a3a")

        errors = []
        if not self.entry_boxes:
            self.browse_btn.configure(border_color="red")
            self.file_input_frame_border.configure(border_color="red")
            errors.append("No OBJ files selected.")

        if not self.output_dir:
            self.folder_btn.configure(border_color="red")
            self.preview_wrapper_border.configure(border_color="red")
            errors.append("No Output Folder selected.")

        for file, java_field, model_field in self.entry_boxes:
            model_name = model_field.get().strip()
            java_name = java_field.get().strip()
            file_label = os.path.basename(file)
            if not model_name:
                model_field.configure(border_color="red")
                errors.append(f"Missing Model Output Name for: {file_label}")
            else:
                model_field.configure(border_color="#3a3a3a")
            if self.create_java.get():
                if not java_name:
                    java_field.configure(border_color="red")
                    errors.append(f"Missing Java Class Name for: {file_label}")
                else:
                    java_field.configure(border_color="#3a3a3a")

        if errors:
            messagebox.showerror("Validation Error", "\n".join(errors))
            return

        self.log("Starting conversion...")

        def run():
            from logic.converter_core import process_obj_file
            had_error = False
            for file, java_field, model_field in self.entry_boxes:
                try:
                    model_name = model_field.get().strip()
                    java_name = java_field.get().strip() if self.create_java.get() else None
                    generate_txt = self.create_txt.get()

                    out_subdir = os.path.join(self.output_dir, os.path.splitext(os.path.basename(file))[0])
                    os.makedirs(out_subdir, exist_ok=True)

                    self.log(f"\nProcessing: {file}")
                    process_obj_file(file, out_subdir, java_name, self.log, generate_txt=generate_txt, output_name=model_name)
                    self.log(f"Saved to: {out_subdir}")
                except Exception as e:
                    had_error = True
                    self.log(f"❌ Error processing {file}: {str(e)}")

            self.update_output_preview()
            if not had_error:
                self.log("\n✅ All conversions complete.")
            else:
                self.log("\n⚠️ Some conversions failed. Check logs above.")

        threading.Thread(target=run).start()

if __name__ == '__main__':
    if not check_dependencies():
        sys.exit(1)
    app = OBJFixerGUI()
    app.mainloop()