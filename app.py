import customtkinter as ctk
from tkinter import filedialog, messagebox
from core import rename_subtitles

# Set up the default look and feel
ctk.set_appearance_mode("Dark")  # Options: "System", "Dark", "Light"
ctk.set_default_color_theme("blue")  # Options: "blue", "green", "dark-blue"

class SubtitleMatcherApp:
    def __init__(self, root):
        self.root = root
        self.root.title("VLC Subtitle Matcher")
        self.root.geometry("650x500")
        self.root.minsize(600, 450)
        
        # Internal storage for file paths
        self.video_paths = []
        self.subtitle_paths = []
        
        self.build_ui()
        
    def build_ui(self):
        # Configure grid weight for a clean layout layout
        self.root.grid_columnconfigure(1, weight=1)
        self.root.grid_rowconfigure(0, weight=1)

        # --- Sidebar ---
        sidebar_frame = ctk.CTkFrame(self.root, width=180, corner_radius=0)
        sidebar_frame.grid(row=0, column=0, sticky="nsew")
        sidebar_frame.grid_rowconfigure(4, weight=1)

        logo_label = ctk.CTkLabel(sidebar_frame, text="Subtitle\nMatcher", font=ctk.CTkFont(size=18, weight="bold"))
        logo_label.grid(row=0, column=0, padx=20, pady=(25, 15))

        # Theme Selector at the bottom of the sidebar
        self.appearance_mode_menu = ctk.CTkOptionMenu(sidebar_frame, values=["Dark", "Light", "System"],
                                                       command=self.change_appearance_mode)
        self.appearance_mode_menu.grid(row=5, column=0, padx=15, pady=20, sticky="s")
        self.appearance_mode_menu.set("Dark")

        # --- Main Content Area ---
        main_frame = ctk.CTkFrame(self.root, fg_color="transparent")
        main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        main_frame.grid_columnconfigure(0, weight=1)
        main_frame.grid_rowconfigure(3, weight=1)

        # Header Title
        header_label = ctk.CTkLabel(main_frame, text="Batch Subtitle Renamer", font=ctk.CTkFont(size=16, weight="bold"))
        header_label.grid(row=0, column=0, sticky="w", pady=(0, 15))

        # --- Video Selection Card ---
        vid_card = ctk.CTkFrame(main_frame, corner_radius=10)
        vid_card.grid(row=1, column=0, sticky="ew", pady=(0, 10))
        vid_card.grid_columnconfigure(0, weight=1)

        self.vid_status_label = ctk.CTkLabel(vid_card, text="No video files selected", text_color="gray")
        self.vid_status_label.grid(row=0, column=0, padx=15, pady=15, sticky="w")

        vid_btn = ctk.CTkButton(vid_card, text="Browse Videos", command=self.load_videos, width=120)
        vid_btn.grid(row=0, column=1, padx=15, pady=15, sticky="e")

        # --- Subtitle Selection Card ---
        sub_card = ctk.CTkFrame(main_frame, corner_radius=10)
        sub_card.grid(row=2, column=0, sticky="ew", pady=(0, 15))
        sub_card.grid_columnconfigure(0, weight=1)

        self.sub_status_label = ctk.CTkLabel(sub_card, text="No subtitle files selected", text_color="gray")
        self.sub_status_label.grid(row=0, column=0, padx=15, pady=15, sticky="w")

        sub_btn = ctk.CTkButton(sub_card, text="Browse Subtitles", command=self.load_subtitles, width=120)
        sub_btn.grid(row=0, column=1, padx=15, pady=15, sticky="e")

        # --- Action & Log Section ---
        action_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        action_frame.grid(row=3, column=0, sticky="nsew")
        action_frame.grid_columnconfigure(0, weight=1)
        action_frame.grid_rowconfigure(1, weight=1)

        self.run_btn = ctk.CTkButton(action_frame, text="Match & Rename Subtitles", command=self.run_renamer,
                                     font=ctk.CTkFont(size=13, weight="bold"), height=38, 
                                     fg_color="#2fa572", hover_color="#248259")
        self.run_btn.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        # Modern Textbox for Logs
        self.log_text = ctk.CTkTextbox(action_frame, corner_radius=8, font=("Consolas", 11))
        self.log_text.grid(row=1, column=0, sticky="nsew")

    def load_videos(self):
        files = filedialog.askopenfilenames(
            title="Select Video Files",
            filetypes=[("Video Files", "*.mp4 *.mkv *.avi *.mov *.m4v"), ("All Files", "*.*")]
        )
        if files:
            self.video_paths = list(files)
            self.vid_status_label.configure(text=f"{len(self.video_paths)} video(s) selected", text_color=("black", "white"))
            self.log_message(f"Loaded {len(self.video_paths)} video file(s).")

    def load_subtitles(self):
        files = filedialog.askopenfilenames(
            title="Select Subtitle Files",
            filetypes=[("Subtitle Files", "*.srt *.ass *.sub"), ("All Files", "*.*")]
        )
        if files:
            self.subtitle_paths = list(files)
            self.sub_status_label.configure(text=f"{len(self.subtitle_paths)} subtitle(s) selected", text_color=("black", "white"))
            self.log_message(f"Loaded {len(self.subtitle_paths)} subtitle file(s).")

    def run_renamer(self):
        if not self.video_paths or not self.subtitle_paths:
            messagebox.showerror("Selection Error", "Please select both video and subtitle files before running!")
            return
            
        # Call core logic function
        results = rename_subtitles(self.video_paths, self.subtitle_paths)
        
        # If the core engine returns a critical error message (like count mismatch), pop up an alert
        if results and results[0].startswith("Error:"):
            messagebox.showerror("Batch Error", results[0])
            self.log_message(f"\n[ERROR] {results[0]}")
            return
        
        # Otherwise, stream log results normally
        self.log_message("\n--- Starting Rename Process ---")
        for res in results:
            self.log_message(res)
        self.log_message("--- Process Completed ---\n")


    def log_message(self, message):
        self.log_text.insert("end", message + "\n")
        self.log_text.see("end")

    def change_appearance_mode(self, new_appearance_mode: str):
        ctk.set_appearance_mode(new_appearance_mode)

if __name__ == "__main__":
    root = ctk.CTk()
    app = SubtitleMatcherApp(root)
    root.mainloop()
