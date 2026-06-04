import os
import queue
import customtkinter as ctk
from tkinter import filedialog
from typing import Dict, Any, List

from ui.theme import COLORS, FONTS, init_theme
from ui.components.terminal_console import TerminalConsole
from ui.components.dialogs import BackupSelectionDialog, AIDiagnosticDialog
from ui.panels.tools_panel import ToolsPanel
from ui.panels.stacks_panel import StacksPanel
from ui.panels.backup_panel import BackupPanel
from ui.panels.skills_panel import SkillsPanel

from core.config import _, BACKUP_PATHS, TranslationManager, Config
from core.system_checker import SystemSpecChecker
from core.installer_service import InstallerService

class AppWindow(ctk.CTk):
    """
    Main CustomTkinter window orchestrating the 15% Sidebar / 50% Workspace / 35% Terminal Layout.
    """
    def __init__(self):
        super().__init__()
        
        # Initialize styling settings
        init_theme()

        self.title("DevTools Installer")
        self.geometry("1280x720")
        self.configure(fg_color=COLORS["bg"])
        
        # Central event queues & worker services
        self.log_queue = queue.Queue()
        self.installer_service = InstallerService(self.log_queue)
        
        # Navigation active state track
        self.active_tab = "install"
        self.system_specs = {}

        self._build_layout()
        self._load_specs()
        
        # Launch queue reader scheduler
        self.after(100, self._process_log_queue)

    def _build_layout(self) -> None:
        """Configures 3-column layout grids partitioning (15% Sidebar / 50% Main Workspace / 35% Terminal Panel)."""
        # Configure columns weights
        self.grid_columnconfigure(0, weight=15, minsize=190) # Sidebar
        self.grid_columnconfigure(1, weight=50, minsize=600) # Workspace
        self.grid_columnconfigure(2, weight=35, minsize=400) # Terminal
        self.grid_rowconfigure(0, weight=1)

        # 1. Left Column: Sidebar
        self.sidebar_frame = ctk.CTkFrame(self, fg_color=COLORS["sidebar"], corner_radius=0)
        self.sidebar_frame.grid(row=0, column=0, sticky="nsew")
        self._build_sidebar()

        # 2. Central Column: Main dynamic panels container
        self.workspace_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.workspace_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self._build_workspace()

        # 3. Right Column: Terminal Console log feed
        self.terminal = TerminalConsole(self)
        self.terminal.grid(row=0, column=2, sticky="nsew")

    def _build_sidebar(self) -> None:
        # Header Label
        self.menu_header = ctk.CTkLabel(
            self.sidebar_frame,
            text=_("menu_header"),
            font=FONTS["subheader"],
            text_color=COLORS["text_dim"]
        )
        self.menu_header.pack(anchor="w", padx=15, pady=(20, 15))

        # Nav Buttons list
        self.nav_buttons = {}
        tabs = [
            ("install", _("nav_install")),
            ("stacks", _("nav_stacks")),
            ("backup", _("nav_backup_restore")),
            ("skills", _("nav_skills"))
        ]

        for tab_id, label in tabs:
            btn = ctk.CTkButton(
                self.sidebar_frame,
                text=label,
                font=FONTS["body"],
                anchor="w",
                height=38,
                fg_color="transparent",
                text_color=COLORS["text"],
                hover_color=COLORS["card_border"],
                corner_radius=4,
                command=lambda tid=tab_id: self._select_tab(tid)
            )
            btn.pack(fill="x", padx=10, pady=2)
            self.nav_buttons[tab_id] = btn

        # Spacer
        specs_container = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        specs_container.pack(fill="both", expand=True, padx=15, pady=20)
        
        # Compact Specs Stats Card in sidebar
        self.specs_card = ctk.CTkFrame(
            specs_container,
            fg_color=COLORS["card"],
            border_color=COLORS["card_border"],
            border_width=1,
            corner_radius=6
        )
        self.specs_card.pack(fill="x", side="bottom", pady=10)
        
        self.specs_title = ctk.CTkLabel(self.specs_card, text="SYSTEM SPECS", font=FONTS["small"], text_color=COLORS["text_dim"])
        self.specs_title.pack(anchor="w", padx=10, pady=(8, 2))
        
        self.ram_lbl = ctk.CTkLabel(self.specs_card, text="RAM: Checking...", font=FONTS["small"], text_color=COLORS["text"])
        self.ram_lbl.pack(anchor="w", padx=10)
        self.disk_lbl = ctk.CTkLabel(self.specs_card, text="Disk C: Checking...", font=FONTS["small"], text_color=COLORS["text"])
        self.disk_lbl.pack(anchor="w", padx=10)
        self.gpu_lbl = ctk.CTkLabel(self.specs_card, text="GPU: Checking...", font=FONTS["small"], text_color=COLORS["text"], wraplength=150, justify="left")
        self.gpu_lbl.pack(anchor="w", padx=10, pady=(0, 8))

        # Bottom section: Language Selector & Theme Toggle
        bottom_frame = ctk.CTkFrame(self.sidebar_frame, fg_color="transparent")
        bottom_frame.pack(fill="x", side="bottom", padx=10, pady=15)

        # Language selection Combo Box
        lang_row = ctk.CTkFrame(bottom_frame, fg_color="transparent")
        lang_row.pack(fill="x", pady=(0, 10))

        self.lang_var = ctk.StringVar(value="Greek" if TranslationManager.get_language() == "el" else "English")
        self.lang_cb = ctk.CTkComboBox(
            lang_row,
            values=["English", "Greek"],
            font=FONTS["small"],
            width=90,
            height=24,
            variable=self.lang_var,
            fg_color=COLORS["bg"],
            text_color=COLORS["text"],
            border_width=1,
            border_color=COLORS["card_border"],
            dropdown_fg_color=COLORS["card"],
            dropdown_text_color=COLORS["text"],
            command=self._on_language_change
        )
        self.lang_cb.pack(side="left")

        # Dark/Light Appearance Toggle Switch
        self.theme_switch = ctk.CTkSwitch(
            bottom_frame,
            text=_("Dark Mode"),
            font=FONTS["small"],
            fg_color=COLORS["sidebar"],
            progress_color=COLORS["accent"],
            text_color=COLORS["text"],
            command=self._on_theme_toggle
        )
        self.theme_switch.select() # Set default state checkmark to Dark Mode active
        self.theme_switch.pack(side="right")

    def _build_workspace(self) -> None:
        """Initializes all dynamically swapped panel frames."""
        self.panels: Dict[str, ctk.CTkFrame] = {}

        # 1. Tools Panel
        self.panels["install"] = ToolsPanel(
            self.workspace_frame,
            on_selection_changed=self._on_selection_changed,
            on_retry_install=self.retry_tool,
            start_installation=self.start_installation
        )

        # 2. Stacks Panel
        self.panels["stacks"] = StacksPanel(
            self.workspace_frame,
            apply_stack_callback=self._apply_stack
        )

        # 3. Backup Panel
        self.panels["backup"] = BackupPanel(
            self.workspace_frame,
            on_backup=self.start_backup,
            on_restore=self.start_restore,
            on_export=self._export_selection,
            on_import=self._import_selection
        )

        # 4. Skills Panel
        self.panels["skills"] = SkillsPanel(self.workspace_frame)

        # Draw default panel
        self._select_tab("install")

    def _select_tab(self, tab_id: str) -> None:
        self.active_tab = tab_id
        
        # Hide all panel views first
        for name, panel in self.panels.items():
            panel.pack_forget()
            
        # Unhighlight other side navigation items
        for tid, btn in self.nav_buttons.items():
            btn.configure(fg_color="transparent")

        # Display select panel row layout and highlight matching navigation tab
        self.panels[tab_id].pack(fill="both", expand=True)
        self.nav_buttons[tab_id].configure(fg_color=COLORS["card"])

    def _load_specs(self) -> None:
        """Pulls system specification check list asynchronously."""
        def check():
            specs = SystemSpecChecker.get_system_specs()
            self.system_specs = specs
            
            # Post back results safely to main thread
            try:
                if self.winfo_exists():
                    self.after(0, lambda: self._on_specs_loaded(specs))
            except Exception:
                pass
            
        import threading
        threading.Thread(target=check, daemon=True).start()

    def _on_specs_loaded(self, specs: dict) -> None:
        self.ram_lbl.configure(text=f"RAM: {specs['ram_gb']} GB")
        self.disk_lbl.configure(text=f"Disk C: {specs['free_disk_gb']} GB")
        
        gpu = specs["gpu_name"]
        if len(gpu) > 22:
            gpu = gpu[:20] + "..."
        self.gpu_lbl.configure(text=f"GPU: {gpu if gpu else 'None Detected'}")

    def _on_selection_changed(self) -> None:
        selected = self.panels["install"].get_selected_tools()
        count = len(selected)
        if count > 0:
            self.terminal.append_log(f"Selection updated: {count} tools chosen.", "info")

    def start_installation(self) -> None:
        """Starts batch installs task."""
        selected = self.panels["install"].get_selected_tools()
        if not selected:
            self.terminal.append_log(_("select_at_least_one"), "warning")
            return

        self._set_ui_enabled(False)
        self.terminal.clear_console()
        self.terminal.append_log(_("starting_install", count=len(selected)), "info")

        self.installer_service.start_install_task(
            tools=selected,
            on_progress_update=self._update_progress,
            on_status_change=self._set_row_status,
            on_finished=self._on_install_finished,
            show_ai_diagnostic=self.show_ai_diagnostic_dialog
        )

    def retry_tool(self, name: str, winget_id: str) -> None:
        """Starts installation execution for a single tool row."""
        self._set_ui_enabled(False)
        self.terminal.clear_console()
        self.terminal.append_log(_("starting_install", count=1), "info")
        
        self.installer_service.start_install_task(
            tools=[(name, winget_id)],
            on_progress_update=self._update_progress,
            on_status_change=self._set_row_status,
            on_finished=self._on_install_finished,
            show_ai_diagnostic=self.show_ai_diagnostic_dialog
        )

    def _set_row_status(self, name: str, status: str) -> None:
        """Callback to update individual ToolRow statuses safely from installer service worker."""
        # Find row items inside the ToolsPanel grid list
        for row in self.panels["install"].tool_rows:
            if row.tool_name == name:
                row.set_status(status)
                break

    def _update_progress(self, current: int, total: int) -> None:
        pass # Optional visual loading updates can be tied in here

    def _on_install_finished(self) -> None:
        self._set_ui_enabled(True)

    def show_ai_diagnostic_dialog(self, tool_name: str, error_log: str) -> None:
        """Triggers the Ollama diagnosis helper popup modal dialog."""
        # Invoke callback method on diagnosis completion to let the console run commands
        dialog = AIDiagnosticDialog(self, tool_name, error_log, self.run_custom_powershell)

    def run_custom_powershell(self, command: str) -> None:
        """Executes a diagnostic proposed fix command line instruction."""
        self.terminal.append_log(f"Applying AI Fix Command: {command}", "warning")
        
        def run():
            try:
                process = subprocess.Popen(
                    ["powershell.exe", "-Command", command],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                if process.stdout:
                    for line in process.stdout:
                        if line.strip():
                            self.log_queue.put({"type": "log", "text": f"  > {line.strip()}", "tag": "info"})
                process.wait()
                if process.returncode == 0:
                    self.log_queue.put({"type": "log", "text": "Fix command executed successfully!", "tag": "success"})
                else:
                    self.log_queue.put({"type": "log", "text": f"Fix failed with exit code: {process.returncode}", "tag": "error"})
            except Exception as e:
                self.log_queue.put({"type": "log", "text": f"Exception applying fix: {str(e)}", "tag": "error"})
        
        import subprocess
        import threading
        threading.Thread(target=run, daemon=True).start()

    def start_backup(self) -> None:
        dialog = BackupSelectionDialog(self, BACKUP_PATHS)
        selected_items = dialog.get_selected()
        
        if selected_items:
            default_name = f"DevTools_Backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
            target_path = filedialog.asksaveasfilename(
                title=_("backup_select_title"),
                defaultextension=".zip",
                filetypes=[("Zip Files", "*.zip")],
                initialfile=default_name,
                initialdir=os.path.join(os.path.expanduser("~"), "Documents"),
            )
            if target_path:
                self._set_ui_enabled(False)
                self.installer_service.start_backup_task(
                    selected_items, 
                    target_path, 
                    on_finished=lambda: self.after(0, lambda: self._set_ui_enabled(True))
                )

    def start_restore(self) -> None:
        path = filedialog.askopenfilename(
            title=_("restore_select_title"),
            filetypes=[("Zip Files", "*.zip")]
        )
        if path:
            self._set_ui_enabled(False)
            self.installer_service.start_restore_task(
                path, 
                on_finished=lambda: self.after(0, lambda: self._set_ui_enabled(True))
            )

    def _export_selection(self) -> None:
        selected = [r.tool_name for r in self.panels["install"].tool_rows if r.is_checked()]
        if not selected:
            self.terminal.append_log(_("export_no_selection"), "warning")
            return

        path = filedialog.asksaveasfilename(
            title=_("export_title"),
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")],
            initialfile="devtools_selection.json",
        )
        if path:
            try:
                import json
                with open(path, "w", encoding="utf-8") as f:
                    json.dump({"selected_tools": selected}, f, ensure_ascii=False, indent=2)
                self.terminal.append_log(_("export_success", path=path), "success")
            except Exception as e:
                self.terminal.append_log(_("export_error", error=str(e)), "error")

    def _import_selection(self) -> None:
        path = filedialog.askopenfilename(
            title=_("import_title"),
            filetypes=[("JSON Files", "*.json")]
        )
        if path:
            try:
                import json
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    selected = data.get("selected_tools", [])

                self.panels["install"].deselect_all()
                for row in self.panels["install"].tool_rows:
                    if row.tool_name in selected:
                        row.set_checked(True)

                self.terminal.append_log(_("import_success", count=len(selected)), "success")
            except Exception as e:
                self.terminal.append_log(_("import_error", error=str(e)), "error")

    def _apply_stack(self, tool_list: List[str]) -> None:
        self.panels["install"].deselect_all()
        for row in self.panels["install"].tool_rows:
            if row.tool_name in tool_list:
                row.set_checked(True)
        # Shift back viewport focus to ToolsPanel list view
        self._select_tab("install")
        self.terminal.append_log(f"Applied environment stack selection. {len(tool_list)} tools matches checked.", "success")

    def _set_ui_enabled(self, enabled: bool) -> None:
        """Toggles all control panels active states while background installers runs."""
        self.panels["install"].set_ui_enabled(enabled)
        self.panels["backup"].set_ui_enabled(enabled)
        self.theme_switch.configure(state="normal" if enabled else "disabled")
        self.lang_cb.configure(state="normal" if enabled else "disabled")
        for tid, btn in self.nav_buttons.items():
            btn.configure(state="normal" if enabled else "disabled")

    def _process_log_queue(self) -> None:
        """Periodic checker looping queue logs thread-safely."""
        try:
            while True:
                msg = self.log_queue.get_nowait()
                if msg["type"] == "log":
                    self.terminal.append_log(msg["text"], msg.get("tag", "info"))
                self.log_queue.task_done()
        except queue.Empty:
            pass
        self.after(100, self._process_log_queue)

    def _on_theme_toggle(self) -> None:
        """Toggles appearance between Light and Dark mode."""
        if self.theme_switch.get() == 1:
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("light")

    def _on_language_change(self, lang_name: str) -> None:
        """Triggers application-wide localization strings translations updates."""
        lang_code = "el" if lang_name == "Greek" else "en"
        TranslationManager.set_language(lang_code)
        
        # Reload text representations across views
        self.menu_header.configure(text=_("menu_header"))
        self.theme_switch.configure(text=_("Dark Mode"))
        self.nav_buttons["install"].configure(text=_("nav_install"))
        self.nav_buttons["stacks"].configure(text=_("nav_stacks"))
        self.nav_buttons["backup"].configure(text=_("nav_backup_restore"))
        self.nav_buttons["skills"].configure(text=_("nav_skills"))
        
        # Forward translation updates to active subpanels
        self.panels["install"].install_btn.configure(text=_("install_selected"))
        self.panels["install"].select_all_btn.configure(text=_("select_all"))
        self.panels["install"].deselect_all_btn.configure(text=_("deselect_all"))
        self.panels["install"].search_entry.configure(placeholder_text=_("search_placeholder"))
        self.panels["backup"]._build_ui() # Redraw card labels translation
        self.panels["skills"].update_language()
        
        self.terminal.append_log(f"Language changed to: {lang_name}", "success")

# Helper date time import
from datetime import datetime
