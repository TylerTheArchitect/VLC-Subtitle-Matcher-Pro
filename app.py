import threading
import customtkinter as ctk
from pathlib import Path
from tkinter import filedialog, messagebox
from core import rename_subtitles, preview_renames, scan_folder, download_online_subtitles, save_config, load_config, load_api_key

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class SubtitleMatcherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("VLC Subtitle Matcher Pro")
        self.root.geometry("720x640")
        self.root.minsize(650, 550)
        
        self.video_paths = []
        self.subtitle_paths = []
        
        self.build_ui()
        self.load_initial_state()
        
    def build_ui(self):
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        # --- Sidebar ---
        sidebar_frame = ctk.CTkFrame(self.root, width=200, corner_radius=0)
        sidebar_frame.grid(row=0, column=0, sticky="nsew")
        sidebar_frame.grid_rowconfigure(5, weight=1)

        logo_label = ctk.CTkLabel(sidebar_frame, text="Subtitle\nMatcher Pro", font=ctk.CTkFont(size=18, weight="bold"))
        logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        # Reset Button
        self.reset_btn = ctk.CTkButton(sidebar_frame, text="Reset All", fg_color="#d9534f", hover_color="#c9302c", command=self.reset_app)
        self.reset_btn.grid(row=1, column=0, padx=15, pady=5, sticky="ew")

        # API Key Section
        api_frame = ctk.CTkFrame(sidebar_frame, fg_color="transparent")
        api_frame.grid(row=2, column=0, padx=10, pady=15, sticky="ew")
        
        api_title = ctk.CTkLabel(api_frame, text="OpenSubtitles API Key:", font=ctk.CTkFont(size=11, weight="bold"))
        api_title.pack(anchor="w", padx=5, pady=(0, 2))
        
        self.api_entry = ctk.CTkEntry(api_frame, placeholder_text="Enter API Key", show="*", font=ctk.CTkFont(size=11), height=28)
        self.api_entry.pack(fill="x", padx=5, pady=(0, 5))
        
        self.save_key_btn = ctk.CTkButton(api_frame, text="Save Key", command=self.save_key_action, height=26, font=ctk.CTkFont(size=11), fg_color="#1f538d")
        self.save_key_btn.pack(fill="x", padx=5)

        # Theme Selector
        self.appearance_mode_menu = ctk.CTkOptionMenu(sidebar_frame, values=["Dark", "Light", "System"],
                                                       command=lambda m: ctk.set_appearance_mode(m))
        self.appearance_mode_menu.grid(row=6, column=0, padx=15, pady=20, sticky="s")
        self.appearance_mode_menu.set("Dark")

        # --- Main Content Area ---
        main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(4, weight=1)

        header_label = ctk.CTkLabel(main_frame, text="Batch Subtitle Renamer & Matcher", font=ctk.CTkFont(size=16, weight="bold"))
        header_label.grid(row=0, column=0, sticky="w", pady=(0, 10))

        # --- Folder Selection Card ---
        folder_card = ctk.CTkFrame(main_frame, corner_radius=10)
        folder_card.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        folder_card.grid_columnconfigure(0, weight=1)

        self.folder_status_label = ctk.CTkLabel(folder_card, text="No folder selected", text_color="gray")
        self.folder_status_label.grid(row=0, column=0, padx=15, pady=12, sticky="w")

        self.folder_btn = ctk.CTkButton(folder_card, text="Select Folder", command=self.load_folder, width=130, fg_color="#1f538d")
        self.folder_btn.grid(row=0, column=1, padx=15, pady=12, sticky="e")

        # --- Manual File Selection Card ---
        file_card = ctk.CTkFrame(main_frame, corner_radius=10)
        file_card.grid(row=2, column=0, sticky="ew", pady=(0, 15))
        file_card.grid_columnconfigure(0, weight=1)

        self.vid_status_label = ctk.CTkLabel(file_card, text="Videos: 0 selected", text_color="gray")
        self.vid_status_label.grid(row=0, column=0, padx=15, pady=8, sticky="w")
        self.vid_btn = ctk.CTkButton(file_card, text="Browse Videos", command=self.load_videos, width=130)
        self.vid_btn.grid(row=0, column=1, padx=15, pady=8, sticky="e")

        self.sub_status_label = ctk.CTkLabel(file_card, text="Subtitles: 0 selected", text_color="gray")
        self.sub_status_label.grid(row=1, column=0, padx=15, pady=8, sticky="w")
        self.sub_btn = ctk.CTkButton(file_card, text="Browse Subtitles", command=self.load_subtitles, width=130)
        self.sub_btn.grid(row=1, column=1, padx=15, pady=8, sticky="e")

        # --- Action & Log Section ---
        action_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        action_frame.grid(row=4, column=0, sticky="nsew")
        action_frame.grid_columnconfigure(0, weight=1)
        action_frame.grid_columnconfigure(1, weight=1)
        action_frame.grid_rowconfigure(2, weight=1)

        self.preview_btn = ctk.CTkButton(action_frame, text="Preview Changes", command=self.run_preview,
                                     font=ctk.CTkFont(size=12, weight="bold"), height=35,
                                     fg_color="#f0ad4e", hover_color="#ec971f", text_color="black")
        self.preview_btn.grid(row=0, column=0, sticky="ew", padx=(0, 5), pady=(0, 8))

        self.run_btn = ctk.CTkButton(action_frame, text="Execute Rename", command=self.run_renamer,
                                     font=ctk.CTkFont(size=12, weight="bold"), height=35, 
                                     fg_color="#2fa572", hover_color="#248259")
        self.run_btn.grid(row=0, column=1, sticky="ew", padx=(5, 0), pady=(0, 8))

        self.online_btn = ctk.CTkButton(action_frame, text="Fetch Online Subtitles", command=self.run_online_download,
                                    font=ctk.CTkFont(size=12, weight="bold"), height=35,
                                    fg_color="#3b5998", hover_color="#2d4373")
        self.online_btn.grid(row=1, column=0, columnspan=2, sticky="ew", pady=(0, 10))

        self.log_text = ctk.CTkTextbox(action_frame, corner_radius=8, font=("Consolas", 11))
        self.log_text.grid(row=2, column=0, columnspan=2, sticky="nsew")

    def load_initial_state(self):
        # Automatically load API key from config.json or .env fallback
        api_key = load_api_key()
        if api_key and api_key != "YOUR_API_KEY_HERE":
            self.api_entry.insert(0, api_key)
            
        config = load_config()
        last_folder = config.get("last_folder")
        if last_folder and Path(last_folder).exists():
            videos, subtitles = scan_folder(last_folder)
            self.video_paths = [str(v) for v in videos]
            self.subtitle_paths = [str(s) for s in subtitles]
            self.folder_status_label.configure(text=f"Folder: {last_folder}", text_color=("black", "white"))
            self.vid_status_label.configure(text=f"Videos found: {len(self.video_paths)}", text_color=("black", "white"))
            self.sub_status_label.configure(text=f"Subtitles found: {len(self.subtitle_paths)}", text_color=("black", "white"))
            self.log_message(f"Restored last session folder: {last_folder}")

    def set_ui_busy(self, busy: bool):
        state = "disabled" if busy else "normal"
        self.folder_btn.configure(state=state)
        self.vid_btn.configure(state=state)
        self.sub_btn.configure(state=state)
        self.preview_btn.configure(state=state)
        self.run_btn.configure(state=state)
        self.online_btn.configure(state=state)

    def load_folder(self):
        folder = filedialog.askdirectory(title="Select Media Folder")
        if folder:
            videos, subtitles = scan_folder(folder)
            self.video_paths = [str(v) for v in videos]
            self.subtitle_paths = [str(s) for s in subtitles]
            
            save_config(last_folder=folder)
            
            self.folder_status_label.configure(text=f"Folder: {folder}", text_color=("black", "white"))
            self.vid_status_label.configure(text=f"Videos found: {len(self.video_paths)}", text_color=("black", "white"))
            self.sub_status_label.configure(text=f"Subtitles found: {len(self.subtitle_paths)}", text_color=("black", "white"))
            
            self.log_message(f"Scanned folder successfully. Found {len(self.video_paths)} video(s) and {len(self.subtitle_paths)} subtitle(s).")

    def load_videos(self):
        files = filedialog.askopenfilenames(
            title="Select Video Files",
            filetypes=[("Video Files", "*.mp4 *.mkv *.avi *.mov *.m4v *.flv *.webm"), ("All Files", "*.*")]
        )
        if files:
            self.video_paths = list(files)
            self.vid_status_label.configure(text=f"Videos: {len(self.video_paths)} selected", text_color=("black", "white"))
            self.log_message(f"Loaded {len(self.video_paths)} video file(s).")

    def load_subtitles(self):
        files = filedialog.askopenfilenames(
            title="Select Subtitle Files",
            filetypes=[("Subtitle Files", "*.srt *.ass *.sub *.vtt"), ("All Files", "*.*")]
        )
        if files:
            self.subtitle_paths = list(files)
            self.sub_status_label.configure(text=f"Subtitles: {len(self.subtitle_paths)} selected", text_color=("black", "white"))
            self.log_message(f"Loaded {len(self.subtitle_paths)} subtitle file(s).")

    def run_preview(self):
        if not self.video_paths or not self.subtitle_paths:
            messagebox.showerror("Error", "Please select or scan files before previewing!")
            return
            
        previews = preview_renames(self.video_paths, self.subtitle_paths)
        self.log_message("\n--- Dry-Run Preview ---")
        for p in previews:
            self.log_message(p)
        self.log_message("--- End of Preview ---\n")

    def run_renamer(self):
        if not self.video_paths or not self.subtitle_paths:
            messagebox.showerror("Error", "Please select or scan files before running!")
            return
            
        if len(self.video_paths) != len(self.subtitle_paths):
            messagebox.showerror("Mismatch Error", f"Count mismatch! {len(self.video_paths)} videos vs {len(self.subtitle_paths)} subtitles.")
            return

        self.set_ui_busy(True)
        def worker():
            results = rename_subtitles(self.video_paths, self.subtitle_paths)
            def update_ui():
                self.log_message("\n--- Starting Rename Process ---")
                for res in results:
                    self.log_message(res)
                self.log_message("--- Process Completed ---\n")
                self.set_ui_busy(False)
            self.root.after(0, update_ui)

        threading.Thread(target=worker, daemon=True).start()

    def run_online_download(self):
        if not self.video_paths:
            messagebox.showerror("Error", "Please select or scan video files first before fetching subtitles online!")
            return
            
        self.set_ui_busy(True)
        self.log_message("\n--- Connecting to OpenSubtitles API (Concurrent) ---")
        
        def thread_safe_log(msg):
            self.root.after(0, lambda: self.log_message(msg))

        def background_worker():
            download_online_subtitles(self.video_paths, log_callback=thread_safe_log)
            def finalize():
                self.log_message("--- Online Process Completed ---\n")
                self.set_ui_busy(False)
            self.root.after(0, finalize)

        threading.Thread(target=background_worker, daemon=True).start()

    def save_key_action(self):
        key = self.api_entry.get()
        if key:
            success = save_config(api_key=key)
            if success:
                messagebox.showinfo("Success", "API Key saved securely to local config!")
                self.log_message("API Key updated and saved locally.")
            else:
                messagebox.showerror("Error", "Failed to save API key.")
        else:
            messagebox.showerror("Error", "API Key field cannot be empty.")

    def reset_app(self):
        self.video_paths = []
        self.subtitle_paths = []
        self.folder_status_label.configure(text="No folder selected", text_color="gray")
        self.vid_status_label.configure(text="Videos: 0 selected", text_color="gray")
        self.sub_status_label.configure(text="Subtitles: 0 selected", text_color="gray")
        self.log_text.delete("0.1", "end")
        self.log_message("Application reset successfully.")

    def log_message(self, message):
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")

if __name__ == "__main__":
    root = ctk.CTk()
    app = SubtitleMatcherApp(root)
    root.mainloop()
