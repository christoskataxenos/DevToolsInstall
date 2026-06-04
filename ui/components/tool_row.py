import webbrowser
import customtkinter as ctk
from typing import Dict, Any, Callable
from ui.theme import COLORS, FONTS
from core.config import TranslationManager

class ToolRow(ctk.CTkFrame):
    """
    A compact horizontal row widget representing a single tool item.
    Fits inside the 50% workspace view to save landscape space.
    """
    def __init__(self, parent, name: str, details: Dict[str, Any], on_check_changed: Callable[[bool], None], on_retry: Callable[[str, str], None]):
        super().__init__(
            parent,
            fg_color=COLORS["card"],
            border_color=COLORS["card_border"],
            border_width=1,
            corner_radius=6
        )
        self.tool_name = name
        self.details = details
        self.on_check_changed = on_check_changed
        self.on_retry = on_retry
        self.status = "PENDING"
        self._build_ui()

    def _build_ui(self) -> None:
        # Checkbox
        self.check_var = ctk.BooleanVar(value=False)
        self.checkbox = ctk.CTkCheckBox(
            self,
            text="",
            variable=self.check_var,
            width=20,
            command=self._on_checkbox_click,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"]
        )
        self.checkbox.pack(side="left", padx=(10, 5))

        # Status badge (using a small CTkLabel styled as a pill)
        self.status_badge = ctk.CTkLabel(
            self,
            text="PENDING",
            font=FONTS["small"],
            width=70,
            height=20,
            corner_radius=10,
            fg_color="#475569",
            text_color="#F8FAFC"
        )
        self.status_badge.pack(side="left", padx=5)

        # Tool Name
        self.name_label = ctk.CTkLabel(
            self,
            text=self.tool_name,
            font=FONTS["bold"],
            text_color=COLORS["text"],
            anchor="w"
        )
        self.name_label.pack(side="left", padx=10, fill="x", expand=True)

        # Action Buttons frame
        actions_frame = ctk.CTkFrame(self, fg_color="transparent")
        actions_frame.pack(side="right", padx=10)

        # Info/Note hover tooltip button
        self.info_btn = ctk.CTkButton(
            actions_frame,
            text="ℹ",
            font=("Segoe UI", 12),
            width=24,
            height=24,
            fg_color="transparent",
            text_color=COLORS["text_dim"],
            hover_color=COLORS["sidebar"],
            command=self.show_note_popup
        )
        self.info_btn.pack(side="left", padx=2)

        # External URL link button
        url = self.details.get("url", "")
        self.link_btn = ctk.CTkButton(
            actions_frame,
            text="🌐",
            font=("Segoe UI", 10),
            width=24,
            height=24,
            fg_color="transparent",
            text_color=COLORS["accent"],
            hover_color=COLORS["sidebar"],
            state="normal" if url else "disabled",
            command=lambda: webbrowser.open(url) if url else None
        )
        self.link_btn.pack(side="left", padx=2)

        # Single Retry action button
        self.retry_btn = ctk.CTkButton(
            actions_frame,
            text="Install",
            font=FONTS["small"],
            width=60,
            height=24,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=self._on_retry_click
        )
        self.retry_btn.pack(side="left", padx=(5, 0))

    def _on_checkbox_click(self) -> None:
        self.on_check_changed(self.check_var.get())

    def _on_retry_click(self) -> None:
        self.on_retry(self.tool_name, self.details["id"])

    def is_checked(self) -> bool:
        return self.check_var.get()

    def set_checked(self, checked: bool) -> None:
        self.check_var.set(checked)
        self._on_checkbox_click()

    def set_status(self, status: str) -> None:
        """
        Updates the tool row's status badge.
        Values: PENDING, INSTALLED, RUNNING, ERROR
        """
        self.status = status
        
        # Color palettes matching state
        if status == "INSTALLED":
            self.status_badge.configure(
                text="INSTALLED",
                fg_color=COLORS["success"][1],
                text_color="#ffffff"
            )
            self.retry_btn.configure(state="disabled", text="Install")
        elif status == "RUNNING":
            self.status_badge.configure(
                text="INSTALLING",
                fg_color=COLORS["accent"][1],
                text_color="#ffffff"
            )
            self.retry_btn.configure(state="disabled", text="Running")
        elif status == "ERROR":
            self.status_badge.configure(
                text="ERROR",
                fg_color=COLORS["error"][1],
                text_color="#ffffff"
            )
            self.retry_btn.configure(state="normal", text="Retry")
        else: # PENDING
            self.status_badge.configure(
                text="PENDING",
                fg_color="#475569",
                text_color="#F8FAFC"
            )
            self.retry_btn.configure(state="normal", text="Install")

    def show_note_popup(self) -> None:
        """Displays localized notes for this tool in a brief CustomTkinter popup."""
        lang = TranslationManager.get_language()
        note_dict = self.details.get("note", {})
        note_text = note_dict.get(lang, note_dict.get("en", "No description notes available."))

        popup = ctk.CTkToplevel(self)
        popup.title(self.tool_name)
        popup.geometry("350x200")
        popup.resizable(False, False)
        popup.after(200, lambda: popup.focus()) # Fix focus overlay

        # Modal layout
        frame = ctk.CTkFrame(popup, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(frame, text=self.tool_name, font=FONTS["subheader"], text_color=COLORS["text"]).pack(anchor="w", pady=(0, 10))
        
        textbox = ctk.CTkTextbox(frame, height=90, font=FONTS["small"], wrap="word", fg_color=COLORS["bg"], border_width=0)
        textbox.pack(fill="x")
        textbox.insert("1.0", note_text)
        textbox.configure(state="disabled")

        ctk.CTkButton(frame, text="Close", width=85, command=popup.destroy).pack(anchor="e", pady=(10, 0))
