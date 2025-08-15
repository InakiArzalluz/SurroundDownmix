import os
import threading
import customtkinter as ctk
from tkinter import filedialog, messagebox
import time
import json
from src.tools import Tools
from src.prober import Prober
from src.remuxer import Remuxer
from src.remuxerFactory import RemuxerFactory

CONFIG_FILE = "config.json"

ctk.set_appearance_mode("dark")       # "light", "dark", or "system"
ctk.set_default_color_theme("blue")   # "blue", "green", "dark-blue"

class App(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("🎬 MKV Remuxer")
        self.geometry("780x600")
        self.minsize(700, 550)

        self.input_folder : str = os.path.join(os.getcwd(), 'Inputs')
        self.output_folder : str = os.path.join(os.getcwd(), 'Outputs')
        self.selected_algorithm : str = next(iter(RemuxerFactory.getalgorithms().keys()))
        self.selected_muxer : str = next(iter(RemuxerFactory.getremuxers().keys()))
        self.processing_thread = None
        self.stop_event = threading.Event()

        # Load saved config
        self.load_config()

        # Header
        self.header_label = ctk.CTkLabel(self, text="MKV Remuxer", font=ctk.CTkFont(size=22, weight="bold"))
        self.header_label.pack(pady=(15, 0))
        self.header_label = ctk.CTkLabel(self, text="Easily batch downmix from 5.1 to 2.0!", font=ctk.CTkFont(size=12, weight="normal"), text_color='#777')
        self.header_label.pack(pady=(0, 10))

        # Folder selectors
        self.create_folder_selector("Input Folder", self.select_input, initial_path=self.input_folder)
        self.create_folder_selector("Output Folder", self.select_output, initial_path=self.output_folder)

        # Muxer selector frame
        muxer_frame = ctk.CTkFrame(self)
        muxer_frame.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(muxer_frame, text="Remuxer:").pack(side="left", padx=10, pady=10)

        # Populate dropdown from RemuxerFactory
        factory = RemuxerFactory()
        self.muxers = [muxer for muxer, isPresent in factory.getremuxers().items() if isPresent]
        self.muxer_menu = ctk.CTkOptionMenu(muxer_frame, values=self.muxers, command=self.set_muxer)
        self.muxer_menu.pack(side="right", padx=10)
        self.muxer_menu.set(self.selected_muxer)
        
        # Algorithm selector frame
        algo_frame = ctk.CTkFrame(self)
        algo_frame.pack(fill="x", padx=20, pady=5)
        ctk.CTkLabel(algo_frame, text="Downmix Algorithm:").pack(side="left", padx=10, pady=10)

        # Populate dropdown from RemuxerFactory
        algorithms = factory.getalgorithms() # dict: name -> description
        self.algorithms = list(algorithms.keys())
        self.algodescriptions = algorithms
        self.algo_menu = ctk.CTkOptionMenu(algo_frame, values=self.algorithms, command=self.set_algorithm)
        self.algo_menu.pack(side="right", padx=10)
        self.algo_menu.set(self.selected_algorithm)

        # Algorithm description label
        self.algo_desc_label = ctk.CTkLabel(self, text=self.algodescriptions.get(self.selected_algorithm, ""), wraplength=600, text_color="gray")
        self.algo_desc_label.pack(fill="x", padx=30, pady=(0, 10))

        # File count label
        self.file_count_label = ctk.CTkLabel(self, text="", font=ctk.CTkFont(size=12, slant="italic"))
        self.file_count_label.pack(pady=(0, 5))

        # Button frame for Start / Abort
        btn_frame = ctk.CTkFrame(self)
        btn_frame.pack(pady=10)

        self.start_btn = ctk.CTkButton(btn_frame, text="▶ Start Processing", command=self.start_processing, state="disabled", width=150)
        self.start_btn.pack(side="left", padx=15)

        self.abort_btn = ctk.CTkButton(btn_frame, text="⏹ Abort", command=self.abort_processing, state="disabled", fg_color="#b22222", width=100)
        self.abort_btn.pack(side="left", padx=15)

        # Progress bar
        self.progress = ctk.CTkProgressBar(self)
        self.progress.pack(fill="x", padx=20, pady=(0, 15))
        self.progress.set(0)

        # Status bar
        self.status_bar = ctk.CTkLabel(self, text="Idle", anchor="w", font=ctk.CTkFont(size=10), fg_color="#222222", corner_radius=5)
        self.status_bar.pack(fill="x", padx=20, pady=(0, 10))

        # Log area
        self.log_box = ctk.CTkTextbox(self, wrap="word", height=220)
        self.log_box.pack(fill="both", expand=True, padx=20, pady=10)
        self.log_box.configure(state="disabled")

        # Update start button state on init
        self.update_start_button_state()

    def create_folder_selector(self, label_text, command, initial_path=None):
        frame = ctk.CTkFrame(self)
        frame.pack(fill="x", padx=20, pady=5)

        label = ctk.CTkLabel(frame, text=label_text)
        label.pack(side="left", padx=10, pady=10)

        path_label = ctk.CTkLabel(frame, text="No folder selected", text_color="gray")
        path_label.pack(side="left", fill="x", expand=True, padx=10)

        btn = ctk.CTkButton(frame, text="Browse", command=command, width=100)
        btn.pack(side="right", padx=10)

        if initial_path:
            path_label.configure(text=initial_path, text_color="white")
            if "Input" in label_text:
                self.input_folder = initial_path
            else:
                self.output_folder = initial_path

        if "Input" in label_text:
            self.input_label = path_label
        else:
            self.output_label = path_label

    def set_algorithm(self, choice):
        self.selected_algorithm = choice
        desc = self.algodescriptions.get(choice, "")
        self.algo_desc_label.configure(text=desc)
        self.update_start_button_state()
        self.save_config()

    def set_muxer(self, choice):
        self.selected_muxer = choice
        self.update_start_button_state()
        self.save_config()

    def select_input(self):
        folder = filedialog.askdirectory(title="Select Input Folder")
        if folder:
            self.input_folder = folder
            self.input_label.configure(text=folder, text_color="white")
            self.update_start_button_state()
            self.update_file_count()
            self.save_config()

    def select_output(self):
        folder = filedialog.askdirectory(title="Select Output Folder")
        if folder:
            self.output_folder = folder
            self.output_label.configure(text=folder, text_color="white")
            self.update_start_button_state()
            self.save_config()

    def update_start_button_state(self):
        enabled = self.input_folder and self.output_folder and self.selected_algorithm and self.selected_muxer
        self.start_btn.configure(state="normal" if enabled else "disabled")

    def update_file_count(self):
        if not self.input_folder:
            self.file_count_label.configure(text="")
            return
        count = 0
        for _, _, files in os.walk(self.input_folder):
            count += len(files)
        self.file_count_label.configure(text=f"Found {count} file{'s' if count != 1 else ''} in input folder")

    def log(self, text):
        self.log_box.configure(state="normal")
        self.log_box.insert("end", text + "\n")
        self.log_box.see("end")
        self.log_box.configure(state="disabled")
        self.update_idletasks()

    def start_processing(self):
        if not self.input_folder or not self.output_folder:
            messagebox.showwarning("Missing Folders", "Please select both input and output folders first.")
            return
        self.start_btn.configure(state="disabled")
        self.abort_btn.configure(state="normal")
        self.stop_event.clear()
        self.processing_thread = threading.Thread(target=self.process_files, daemon=True)
        self.processing_thread.start()

    def abort_processing(self):
        if self.processing_thread and self.processing_thread.is_alive():
            self.stop_event.set()
            self.log("⏹️ Abort requested, finishing current file...")

    def process_files(self):
        start_time = time.time()
        files_to_process = []
        for root_dir, dirs, files in os.walk(self.input_folder):
            for f in files:
                files_to_process.append((root_dir, f))

        total_files = len(files_to_process)
        self.progress.set(0)
        self.update_status("Starting processing...")

        prober_inst = Prober(limitedToAudio=True)
        rem_factory = RemuxerFactory()
        remuxer_inst: Remuxer = rem_factory.getRemuxer(self.selected_muxer, self.selected_algorithm, self.log)

        for idx, (root_dir, filename) in enumerate(files_to_process, start=1):
            if self.stop_event.is_set():
                self.log("⚠️ Processing aborted by user.")
                break

            missingStructure = root_dir[len(self.input_folder)+1:].split(os.sep)
            Tools.createFolderStructure(self.output_folder, missingStructure)

            filepath = os.path.join(root_dir, filename)
            remuxLocation = os.path.join(self.output_folder, os.path.join(root_dir[len(self.input_folder)+1:]))
            newLocation = os.path.join(remuxLocation, filename)

            self.update_status(f"Processing: {idx}/{total_files}")

            if filename.rsplit(sep='.')[-1].lower() == 'mkv':
                self.log(f"Processing:  {filepath[len(self.input_folder)+1:]}")
                if prober_inst.has_surround(filepath):
                    remuxer_inst.remux(filepath, newLocation)
                    self.log(f"✅ Remuxed using {self.selected_algorithm}.")
                    self.log("________________________________________________\n")
                else:
                    os.replace(filepath, newLocation)
                    self.log("➡ Moved without remuxing (no surround).")
            else:
                os.replace(filepath, newLocation)
                self.log("➡ Moved (non-MKV file).")

            self.progress.set(idx / total_files)

        elapsed = time.time() - start_time
        self.update_status("Idle")
        self.log("Done")
        self.abort_btn.configure(state="disabled")
        self.start_btn.configure(state="normal")

        if not self.stop_event.is_set():
            messagebox.showinfo("Finished", f"Processing complete!\nElapsed time: {elapsed:.1f} seconds")

    def update_status(self, text):
        self.status_bar.configure(text=text)

    def load_config(self):
        if os.path.isfile(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r", encoding="utf-8") as f:
                    cfg = json.load(f)
                self.input_folder = cfg.get("input_folder", None)
                self.output_folder = cfg.get("output_folder", None)
                self.selected_algorithm = cfg.get("algorithm", None)
                self.selected_muxer = cfg.get("muxer", None)
            except Exception:
                pass

    def save_config(self):
        cfg = {
            "input_folder": self.input_folder,
            "output_folder": self.output_folder,
            "algorithm": self.selected_algorithm,
            "muxer": self.selected_muxer,
        }
        try:
            with open(CONFIG_FILE, "w", encoding="utf-8") as f:
                json.dump(cfg, f, indent=2)
        except Exception:
            pass


if __name__ == "__main__":
    app = App()
    app.mainloop()
