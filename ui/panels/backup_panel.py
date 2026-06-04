import customtkinter as ctk
from typing import Callable, List
from ui.theme import COLORS, FONTS
from core.config import _

class BackupPanel(ctk.CTkFrame):
    """
    BackupPanel manages options to save settings configurations
    and export/import checked applications selections lists to JSON.
    """
    def __init__(self, parent, on_backup: Callable[[], None], on_restore: Callable[[], None], on_export: Callable[[], None], on_import: Callable[[], None]):
        super().__init__(parent, fg_color="transparent")
        
        self.on_backup = on_backup
        self.on_restore = on_restore
        self.on_export = on_export
        self.on_import = on_import
        
        self._build_ui()

    def _build_ui(self) -> None:
        # Title
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(10, 15))
        
        ctk.CTkLabel(
            header,
            text=_("nav_backup_restore"),
            font=FONTS["header"],
            text_color=COLORS["text"]
        ).pack(side="left")

        # Layout Container
        container = ctk.CTkFrame(self, fg_color="transparent")
        container.pack(fill="both", expand=True, padx=10, pady=5)

        # 1. System Settings Card
        settings_card = ctk.CTkFrame(
            container,
            fg_color=COLORS["card"],
            border_color=COLORS["card_border"],
            border_width=1,
            corner_radius=8
        )
        settings_card.pack(fill="x", pady=10, padx=2)

        ctk.CTkLabel(
            settings_card,
            text="Application Settings Sync",
            font=FONTS["subheader"],
            text_color=COLORS["text"]
        ).pack(anchor="w", padx=15, pady=(12, 5))

        ctk.CTkLabel(
            settings_card,
            text="Backup or restore configurations for VS Code, Cursor, Windsurf, Warp, and local CLI tools configurations.",
            font=FONTS["small"],
            text_color=COLORS["text_dim"],
            wraplength=450,
            justify="left"
        ).pack(anchor="w", padx=15, pady=(0, 15))

        btn_row_1 = ctk.CTkFrame(settings_card, fg_color="transparent")
        btn_row_1.pack(fill="x", padx=15, pady=(0, 15))

        self.backup_btn = ctk.CTkButton(
            btn_row_1,
            text=_("backup"),
            font=FONTS["body"],
            width=120,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=self.on_backup
        )
        self.backup_btn.pack(side="left", padx=(0, 10))

        self.restore_btn = ctk.CTkButton(
            btn_row_1,
            text=_("restore"),
            font=FONTS["body"],
            width=120,
            fg_color="#334155",
            hover_color="#475569",
            command=self.on_restore
        )
        self.restore_btn.pack(side="left")

        # 2. Tool Checklist Profile Card
        checklist_card = ctk.CTkFrame(
            container,
            fg_color=COLORS["card"],
            border_color=COLORS["card_border"],
            border_width=1,
            corner_radius=8
        )
        checklist_card.pack(fill="x", pady=10, padx=2)

        ctk.CTkLabel(
            checklist_card,
            text="Tool Checklist Profiles",
            font=FONTS["subheader"],
            text_color=COLORS["text"]
        ).pack(anchor="w", padx=15, pady=(12, 5))

        ctk.CTkLabel(
            checklist_card,
            text="Export your current checked tool select checklist profile to a JSON file or import a saved select file to restore checks.",
            font=FONTS["small"],
            text_color=COLORS["text_dim"],
            wraplength=450,
            justify="left"
        ).pack(anchor="w", padx=15, pady=(0, 15))

        btn_row_2 = ctk.CTkFrame(checklist_card, fg_color="transparent")
        btn_row_2.pack(fill="x", padx=15, pady=(0, 15))

        self.export_btn = ctk.CTkButton(
            btn_row_2,
            text="Export JSON Profile",
            font=FONTS["body"],
            width=140,
            fg_color="#334155",
            hover_color="#475569",
            command=self.on_export
        )
        self.export_btn.pack(side="left", padx=(0, 10))

        self.import_btn = ctk.CTkButton(
            btn_row_2,
            text="Import JSON Profile",
            font=FONTS["body"],
            width=140,
            fg_color="#334155",
            hover_color="#475569",
            command=self.on_import
        )
        self.import_btn.pack(side="left")

    def set_ui_enabled(self, enabled: bool) -> None:
        """Disables/enables backup/restore action buttons while active tasks run."""
        self.backup_btn.configure(state="normal" if enabled else "disabled")
        self.restore_btn.configure(state="normal" if enabled else "disabled")
        self.export_btn.configure(state="normal" if enabled else "disabled")
        self.import_btn.configure(state="normal" if enabled else "disabled")
