import customtkinter as ctk
from typing import Dict, List, Callable
from ui.theme import COLORS, FONTS
from core.config import _, Config

class StacksPanel(ctk.CTkFrame):
    """
    StacksPanel represents the pre-packaged setup stacks.
    Applying a stack automatically selects its matching tools in the ToolsPanel.
    """
    def __init__(self, parent, apply_stack_callback: Callable[[List[str]], None]):
        super().__init__(parent, fg_color="transparent")
        self.apply_stack_callback = apply_stack_callback
        self.stacks = Config.load_stacks()
        self._build_ui()

    def _build_ui(self) -> None:
        # Title Header
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", padx=10, pady=(10, 5))
        
        ctk.CTkLabel(
            header,
            text=_("stacks"),
            font=FONTS["header"],
            text_color=COLORS["text"]
        ).pack(side="left")

        # Scrollable container for cards
        scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=COLORS["card_border"],
            scrollbar_button_hover_color=COLORS["text_dim"]
        )
        scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Draw stack cards in a single-column list of frames
        for stack_name, tool_list in self.stacks.items():
            card = ctk.CTkFrame(
                scroll_frame,
                fg_color=COLORS["card"],
                border_color=COLORS["card_border"],
                border_width=1,
                corner_radius=8
            )
            card.pack(fill="x", pady=6, padx=2)

            # Details layouts
            info_frame = ctk.CTkFrame(card, fg_color="transparent")
            info_frame.pack(side="left", fill="both", expand=True, padx=15, pady=12)

            ctk.CTkLabel(
                info_frame,
                text=stack_name,
                font=FONTS["subheader"],
                text_color=COLORS["text"],
                anchor="w"
            ).pack(anchor="w", pady=(0, 5))

            # Join tool list in small labels
            tools_txt = ", ".join(tool_list)
            ctk.CTkLabel(
                info_frame,
                text=tools_txt,
                font=FONTS["small"],
                text_color=COLORS["text_dim"],
                anchor="w",
                wraplength=350
            ).pack(anchor="w")

            # Apply Button
            apply_btn = ctk.CTkButton(
                card,
                text="Apply Stack",
                font=FONTS["body"],
                width=100,
                height=32,
                fg_color=COLORS["accent"],
                hover_color=COLORS["accent_hover"],
                command=lambda lst=tool_list: self._apply_stack(lst)
            )
            apply_btn.pack(side="right", padx=15, pady=12)

    def _apply_stack(self, tool_list: List[str]) -> None:
        self.apply_stack_callback(tool_list)
