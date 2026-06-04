import customtkinter as ctk
from typing import Dict, Any, List, Tuple, Callable
from ui.theme import COLORS, FONTS
from ui.components.tool_row import ToolRow
from core.config import _, Config

class ToolsPanel(ctk.CTkFrame):
    """
    ToolsPanel corresponds to the central 50% workspace column.
    Renders categorized list of installer tools, search, and category selectors.
    """
    def __init__(self, parent, on_selection_changed: Callable[[], None], on_retry_install: Callable[[str, str], None], start_installation: Callable[[], None]):
        super().__init__(parent, fg_color="transparent")
        
        self.on_selection_changed = on_selection_changed
        self.on_retry_install = on_retry_install
        self.start_installation = start_installation
        
        self.registry = Config.load_registry()
        self.tool_rows: List[ToolRow] = []
        self.active_category = "All"
        
        self._build_ui()

    def _build_ui(self) -> None:
        # Combined Top Search & Category Filter Bar
        top_bar = ctk.CTkFrame(self, fg_color="transparent")
        top_bar.pack(fill="x", padx=10, pady=(10, 5))

        # Search box taking up expanded space
        self.search_entry = ctk.CTkEntry(
            top_bar,
            placeholder_text=_("search_placeholder"),
            font=FONTS["body"],
            fg_color=COLORS["bg"],
            text_color=COLORS["text"],
            border_width=1,
            border_color=COLORS["card_border"],
            height=32
        )
        self.search_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))
        self.search_entry.bind("<KeyRelease>", self._on_search_key)

        # OptionMenu for clean, non-overflowing categories selection
        raw_categories = ["All"] + sorted(list(self.registry.keys()))
        localized_categories = [_(c) for c in raw_categories]
        self.category_option = ctk.CTkOptionMenu(
            top_bar,
            values=localized_categories,
            font=FONTS["body"],
            fg_color=COLORS["card"],
            button_color=COLORS["accent"],
            button_hover_color=COLORS["accent_hover"],
            text_color=COLORS["text"],
            dropdown_fg_color=COLORS["card"],
            dropdown_text_color=COLORS["text"],
            height=32,
            width=180,
            command=self._on_category_select
        )
        self.category_option.pack(side="right")
        self.category_option.set(_("All"))

        # Scrollable Container for Tool Rows
        self.scroll_frame = ctk.CTkScrollableFrame(
            self,
            fg_color="transparent",
            scrollbar_button_color=COLORS["card_border"],
            scrollbar_button_hover_color=COLORS["text_dim"]
        )
        self.scroll_frame.pack(fill="both", expand=True, padx=10, pady=5)

        # Batch Selection & Install Action Bar at the bottom
        action_bar = ctk.CTkFrame(self, fg_color="transparent")
        action_bar.pack(fill="x", padx=10, pady=(5, 10))

        self.select_all_btn = ctk.CTkButton(
            action_bar,
            text=_("select_all"),
            font=FONTS["small"],
            width=90,
            height=28,
            fg_color="#334155",
            hover_color="#475569",
            command=self.select_all
        )
        self.select_all_btn.pack(side="left", padx=(0, 5))

        self.deselect_all_btn = ctk.CTkButton(
            action_bar,
            text=_("deselect_all"),
            font=FONTS["small"],
            width=90,
            height=28,
            fg_color="#334155",
            hover_color="#475569",
            command=self.deselect_all
        )
        self.deselect_all_btn.pack(side="left")

        # Install Action Button
        self.install_btn = ctk.CTkButton(
            action_bar,
            text=_("install_selected"),
            font=FONTS["bold"],
            width=150,
            height=30,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            text_color="#ffffff",
            command=self.start_installation
        )
        self.install_btn.pack(side="right")

        # Populate all tool rows initially
        self._populate_tools()

    def _populate_tools(self) -> None:
        """Draws all tools rows inside the scrollable canvas viewport."""
        for row in self.tool_rows:
            row.destroy()
        self.tool_rows.clear()

        for category_name, category_tools in self.registry.items():
            for name, details in category_tools.items():
                row = ToolRow(
                    self.scroll_frame,
                    name=name,
                    details=details,
                    on_check_changed=self._on_row_check_changed,
                    on_retry=self.on_retry_install
                )
                self.tool_rows.append(row)

        self._filter_rows()

    def _on_row_check_changed(self, is_checked: bool) -> None:
        self.on_selection_changed()

    def _get_raw_category(self, localized_name: str) -> str:
        if localized_name == _("All") or localized_name == "All":
            return "All"
        for key in self.registry.keys():
            if _(key) == localized_name:
                return key
        return "All"

    def _on_category_select(self, category_localized: str) -> None:
        self.active_category = self._get_raw_category(category_localized)
        self._filter_rows()

    def update_language(self) -> None:
        """Updates translated categories values in option menu."""
        raw_categories = ["All"] + sorted(list(self.registry.keys()))
        localized_categories = [_(c) for c in raw_categories]
        self.category_option.configure(values=localized_categories)
        self.category_option.set(_(self.active_category))

    def _on_search_key(self, event) -> None:
        self._filter_rows()

    def _filter_rows(self) -> None:
        """Hides or reveals tool rows depending on active category and search text."""
        query = self.search_entry.get().strip().lower()
        
        # Hide all first
        for row in self.tool_rows:
            row.pack_forget()

        # Grid and unpack matching items
        for row in self.tool_rows:
            # Check search match
            name_match = query in row.tool_name.lower() or query in row.details.get("id", "").lower()
            
            # Check category match
            cat_match = True
            if self.active_category != "All":
                # Find category in registry
                cat_match = False
                for cat_name, cat_tools in self.registry.items():
                    if row.tool_name in cat_tools and cat_name == self.active_category:
                        cat_match = True
                        break
            
            if name_match and cat_match:
                row.pack(fill="x", pady=3, padx=2)

    def select_all(self) -> None:
        """Selects all currently visible tools in the active view list."""
        for row in self.tool_rows:
            if row.winfo_manager() == "pack": # Row is currently visible/filtered
                row.set_checked(True)

    def deselect_all(self) -> None:
        """Deselects all tools currently registered in the panel rows."""
        for row in self.tool_rows:
            row.set_checked(False)

    def get_selected_tools(self) -> List[Tuple[str, str]]:
        """Returns list of selected tool name and winget id tuples."""
        return [(r.tool_name, r.details["id"]) for r in self.tool_rows if r.is_checked()]

    def set_ui_enabled(self, enabled: bool) -> None:
        """Toggles action buttons active state during installations."""
        self.install_btn.configure(state="normal" if enabled else "disabled")
        self.select_all_btn.configure(state="normal" if enabled else "disabled")
        self.deselect_all_btn.configure(state="normal" if enabled else "disabled")
        self.search_entry.configure(state="normal" if enabled else "disabled")
        self.category_option.configure(state="normal" if enabled else "disabled")
        for row in self.tool_rows:
            row.checkbox.configure(state="normal" if enabled else "disabled")
            if not enabled:
                row.retry_btn.configure(state="disabled")
            else:
                row.set_status(row.status) # Restore correct state for retry button
