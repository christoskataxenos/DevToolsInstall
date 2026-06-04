import customtkinter as ctk
from typing import Dict, Any, List, Tuple, Callable, Set
from ui.theme import COLORS, FONTS
from ui.components.tool_row import ToolRow
from core.config import _, Config

class ToolsPanel(ctk.CTkFrame):
    """
    ToolsPanel corresponds to the central 50% workspace column.
    Renders categorized list of installer tools, search, and category selectors.
    Optimized to dynamically instantiate widgets to prevent startup and theme swap lag.
    """
    def __init__(self, parent, on_selection_changed: Callable[[], None], on_retry_install: Callable[[str, str], None], start_installation: Callable[[], None]):
        super().__init__(parent, fg_color="transparent")
        
        self.on_selection_changed = on_selection_changed
        self.on_retry_install = on_retry_install
        self.start_installation = start_installation
        
        self.registry = Config.load_registry()
        self.tool_rows: List[ToolRow] = []
        self.active_category = "All"
        
        # State caches to allow dynamic destruction and recreation of widgets
        self.selected_tools: Set[str] = set()
        self.tool_statuses: Dict[str, str] = {}
        for category_tools in self.registry.values():
            for name in category_tools.keys():
                self.tool_statuses[name] = "PENDING"
        
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

        # Populates visible tools matching filter
        self._populate_tools()

    def _populate_tools(self) -> None:
        """Triggers dynamic rendering of filtered rows."""
        self._filter_rows()

    def _on_row_check_changed_name(self, name: str, is_checked: bool) -> None:
        if is_checked:
            self.selected_tools.add(name)
        else:
            self.selected_tools.discard(name)
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
        """Destroys and dynamically creates only matching rows to keep widget counts minimal."""
        query = self.search_entry.get().strip().lower()
        
        # Clean current active rows
        for row in self.tool_rows:
            row.destroy()
        self.tool_rows.clear()

        # Instantiate only matching rows
        for cat_name, cat_tools in self.registry.items():
            for name, details in cat_tools.items():
                # Category Filter check
                if self.active_category != "All" and cat_name != self.active_category:
                    continue
                # Search Filter check
                if query and not (query in name.lower() or query in details.get("id", "").lower()):
                    continue
                
                row = ToolRow(
                    self.scroll_frame,
                    name=name,
                    details=details,
                    on_check_changed=lambda is_ch, n=name: self._on_row_check_changed_name(n, is_ch),
                    on_retry=self.on_retry_install
                )
                
                # Apply cached status
                cached_status = self.tool_statuses.get(name, "PENDING")
                row.set_status(cached_status)
                
                # Apply cached selection
                if name in self.selected_tools:
                    row.check_var.set(True)
                    row.checkbox.select()

                row.pack(fill="x", pady=3, padx=2)
                self.tool_rows.append(row)

    def select_all(self) -> None:
        """Selects all currently visible tools in the active view list."""
        for row in self.tool_rows:
            row.set_checked(True)

    def deselect_all(self) -> None:
        """Deselects all tools globally."""
        self.selected_tools.clear()
        for row in self.tool_rows:
            row.set_checked(False)

    def get_selected_tools(self) -> List[Tuple[str, str]]:
        """Returns list of selected tool name and winget id tuples across categories."""
        res = []
        for cat_tools in self.registry.values():
            for name, details in cat_tools.items():
                if name in self.selected_tools:
                    res.append((name, details["id"]))
        return res

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
                row.set_status(row.status)
