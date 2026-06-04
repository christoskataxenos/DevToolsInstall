import os
import threading
import tkinter as tk
from tkinter import filedialog, messagebox
import customtkinter as ctk
from typing import Dict, Any, List

from ui.theme import COLORS, FONTS
from core.config import _, Config
from core.skills_manager import SkillsManager

class SkillsPanel(ctk.CTkFrame):
    """
    SkillsPanel handles pulling rules/prompts templates from GitHub repositories,
    displaying them, and copying them locally to developer project folders.
    """
    def __init__(self, parent):
        super().__init__(parent, fg_color="transparent")
        self.selected_file_path = ""
        self.local_files_map = {}
        self._build_ui()

    def _build_ui(self) -> None:
        # Title
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(10, 15))
        
        self.header_label = ctk.CTkLabel(
            header,
            text=_("skills_title"),
            font=FONTS["header"],
            text_color=COLORS["text"]
        )
        self.header_label.pack(side="left")

        # Split columns container frame
        grid_frame = ctk.CTkFrame(self, fg_color="transparent")
        grid_frame.pack(fill="both", expand=True, padx=10, pady=5)
        grid_frame.columnconfigure(0, weight=1, uniform="equal")
        grid_frame.columnconfigure(1, weight=1, uniform="equal")

        # 1. Left Card: Download Repositories
        left_card = ctk.CTkFrame(
            grid_frame,
            fg_color=COLORS["card"],
            border_color=COLORS["card_border"],
            border_width=1,
            corner_radius=8
        )
        left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=2)

        ctk.CTkLabel(
            left_card,
            text=_("skills_repo_label"),
            font=FONTS["subheader"],
            text_color=COLORS["text"]
        ).pack(anchor="w", padx=15, pady=(12, 10))

        # Repositories selection dropdown
        curated_repos = [repo["url"] for repo in SkillsManager.DEFAULT_REPOS]
        self.repo_dropdown = ctk.CTkComboBox(
            left_card,
            values=curated_repos,
            font=FONTS["body"],
            fg_color=COLORS["bg"],
            text_color=COLORS["text"],
            border_width=1,
            border_color=COLORS["card_border"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            dropdown_fg_color=COLORS["card"],
            dropdown_text_color=COLORS["text"],
            width=280
        )
        self.repo_dropdown.pack(anchor="w", padx=15, pady=(0, 15))
        if curated_repos:
            self.repo_dropdown.set(curated_repos[0])

        self.global_path_label = ctk.CTkLabel(
            left_card,
            text=_("skills_global_path", path=SkillsManager.get_global_dir()),
            font=FONTS["small"],
            text_color=COLORS["text_dim"]
        )
        self.global_path_label.pack(anchor="w", padx=15, pady=(0, 10))

        self.status_label = ctk.CTkLabel(
            left_card,
            text=_("skills_status_prefix", status=_("status_ready")),
            font=FONTS["bold"],
            text_color=COLORS["accent"]
        )
        self.status_label.pack(anchor="w", padx=15, pady=(0, 15))

        self.download_btn = ctk.CTkButton(
            left_card,
            text=_("skills_btn_download"),
            font=FONTS["body"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=self.start_download
        )
        self.download_btn.pack(anchor="w", padx=15, pady=(0, 15))

        # 2. Right Card: Project Export
        right_card = ctk.CTkFrame(
            grid_frame,
            fg_color=COLORS["card"],
            border_color=COLORS["card_border"],
            border_width=1,
            corner_radius=8
        )
        right_card.grid(row=0, column=1, sticky="nsew", padx=(10, 0), pady=2)

        ctk.CTkLabel(
            right_card,
            text=_("skills_destination"),
            font=FONTS["subheader"],
            text_color=COLORS["text"]
        ).pack(anchor="w", padx=15, pady=(12, 10))

        # Destination input field & Browse button
        dest_row = ctk.CTkFrame(right_card, fg_color="transparent")
        dest_row.pack(fill="x", padx=15, pady=(0, 15))

        self.dest_entry = ctk.CTkEntry(
            dest_row,
            font=FONTS["body"],
            fg_color=COLORS["bg"],
            text_color=COLORS["text"],
            border_width=1,
            border_color=COLORS["card_border"]
        )
        self.dest_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.browse_btn = ctk.CTkButton(
            dest_row,
            text="...",
            font=FONTS["body"],
            width=36,
            height=28,
            fg_color="#334155",
            hover_color="#475569",
            command=self.browse_dest
        )
        self.browse_btn.pack(side="right")

        ctk.CTkLabel(
            right_card,
            text="Local Prompts & Rules Templates Files:",
            font=FONTS["small"],
            text_color=COLORS["text_dim"]
        ).pack(anchor="w", padx=15, pady=(0, 5))

        # Tkinter Listbox container framed styled for dark theme integration
        self.files_listbox = tk.Listbox(
            right_card,
            bg=COLORS["bg"][1], # Slate background in dark mode
            fg=COLORS["text"][1],
            selectbackground=COLORS["accent"][1],
            selectforeground="#ffffff",
            relief="flat",
            font=("Segoe UI", 9),
            height=6,
            highlightbackground=COLORS["card_border"][1],
            highlightthickness=1
        )
        self.files_listbox.pack(fill="both", expand=True, padx=15, pady=(0, 15))
        self.files_listbox.bind("<<ListboxSelect>>", self.on_file_select)

        self.export_btn = ctk.CTkButton(
            right_card,
            text=_("skills_btn_export"),
            font=FONTS["bold"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=self.export_skill
        )
        self.export_btn.pack(anchor="w", padx=15, pady=(0, 15))

        # Load initial local skills templates files list
        self.refresh_local_files()

    def start_download(self) -> None:
        """Starts downloads of skills repo in a background worker thread."""
        url = self.repo_dropdown.get().strip()
        if not url:
            return
        
        self.download_btn.configure(state="disabled")
        self.status_label.configure(text=_("skills_status_prefix", status="Downloading..."), text_color=COLORS["accent"][1])
        
        def run():
            repo_name = url.split("/")[-1].replace(".git", "")
            success, msg = SkillsManager.download_repo(url, repo_name)
            
            # Post back to main GUI thread
            self.after(0, lambda: self._on_download_complete(success, msg))
            
        threading.Thread(target=run, daemon=True).start()

    def _on_download_complete(self, success: bool, msg: str) -> None:
        self.download_btn.configure(state="normal")
        color = COLORS["success"][1] if success else COLORS["error"][1]
        self.status_label.configure(text=_("skills_status_prefix", status=msg), text_color=color)
        self.refresh_local_files()

    def browse_dest(self) -> None:
        """Opens project folder directory explorer selector dialog."""
        path = filedialog.askdirectory(title="Select Project Workspace Directory")
        if path:
            self.dest_entry.delete(0, "end")
            self.dest_entry.insert(0, path)

    def refresh_local_files(self) -> None:
        """Scans global local skills dir and populates listbox."""
        self.files_listbox.delete(0, tk.END)
        self.local_files_map.clear()
        
        local_repos = SkillsManager.list_local_skills()
        for repo in local_repos:
            repo_path = repo["full_path"]
            repo_folder = repo["folder_name"]
            
            for root, dirs, files in os.walk(repo_path):
                if ".git" in root:
                    continue
                for f in files:
                    # Scan for rule or documentation text formats
                    if f.endswith("rules") or f.endswith(".cursorrules") or f.endswith(".windsurfrules") or f.endswith(".md") or "prompt" in f.lower():
                        rel_path = os.path.relpath(os.path.join(root, f), SkillsManager.get_global_dir())
                        display_name = f"{repo_folder} -> {os.path.basename(f)}"
                        self.files_listbox.insert(tk.END, display_name)
                        self.local_files_map[display_name] = os.path.join(root, f)

    def on_file_select(self, event) -> None:
        selection = self.files_listbox.curselection()
        if selection:
            display_name = self.files_listbox.get(selection[0])
            self.selected_file_path = self.local_files_map.get(display_name, "")

    def export_skill(self) -> None:
        """Copies the selected rules file into the specified project destination folder."""
        if not self.selected_file_path:
            messagebox.showwarning("Warning", "Please select a skills file from the list.")
            return
            
        dest = self.dest_entry.get().strip()
        if not dest or not os.path.exists(dest):
            messagebox.showwarning("Warning", "Please select a valid local project directory.")
            return
            
        file_name = os.path.basename(self.selected_file_path)
        if "cursorrules" in file_name.lower():
            file_name = ".cursorrules"
        elif "windsurfrules" in file_name.lower():
            file_name = ".windsurfrules"
            
        success, msg = SkillsManager.export_skill_to_project(self.selected_file_path, dest, file_name)
        if success:
            messagebox.showinfo("Success", msg)
        else:
            messagebox.showerror("Error", msg)

    def update_language(self) -> None:
        """Triggers translation refresh across local labels."""
        self.header_label.configure(text=_("skills_title"))
        self.global_path_label.configure(text=_("skills_global_path", path=SkillsManager.get_global_dir()))
        self.status_label.configure(text=_("skills_status_prefix", status=_("status_ready")))
        self.download_btn.configure(text=_("skills_btn_download"))
        self.export_btn.configure(text=_("skills_btn_export"))

    def set_ui_enabled(self, enabled: bool) -> None:
        """
        Ενεργοποιεί ή απενεργοποιεί τα στοιχεία ελέγχου των AI skills
        κατά τη διάρκεια εκτέλεσης εργασιών εγκατάστασης.
        """
        self.download_btn.configure(state="normal" if enabled else "disabled")
        self.export_btn.configure(state="normal" if enabled else "disabled")
        self.browse_btn.configure(state="normal" if enabled else "disabled")
        self.repo_dropdown.configure(state="normal" if enabled else "disabled")
        self.dest_entry.configure(state="normal" if enabled else "disabled")
