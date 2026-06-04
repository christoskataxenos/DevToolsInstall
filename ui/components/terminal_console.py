import os
import customtkinter as ctk
from tkinter import filedialog
from ui.theme import COLORS, FONTS

class TerminalConsole(ctk.CTkFrame):
    """
    TerminalConsole represents the persistent 35% right-hand panel.
    Displays subprocess stdout/stderr and diagnostic messages.
    """
    def __init__(self, parent):
        super().__init__(
            parent,
            fg_color=COLORS["terminal_bg"],
            corner_radius=0,
            border_color=COLORS["card_border"],
            border_width=0
        )
        self.autoscroll = True
        self._build_ui()

    def _build_ui(self) -> None:
        # Title Label
        title_frame = ctk.CTkFrame(self, fg_color="transparent")
        title_frame.pack(fill="x", padx=10, pady=(10, 5))
        
        ctk.CTkLabel(
            title_frame,
            text="CONSOL LOGS & TERMINAL",
            font=FONTS["header"],
            text_color=COLORS["terminal_fg"]
        ).pack(side="left")

        # Text Console Box
        self.textbox = ctk.CTkTextbox(
            self,
            fg_color=COLORS["terminal_bg"][1],
            text_color=COLORS["terminal_fg"][1],
            font=FONTS["mono"],
            corner_radius=4,
            border_color=COLORS["card_border"][1],
            border_width=1,
            wrap="word"
        )
        self.textbox.pack(fill="both", expand=True, padx=10, pady=5)
        self.textbox.configure(state="disabled")

        # Console Toolbar at the bottom
        toolbar = ctk.CTkFrame(self, fg_color="transparent")
        toolbar.pack(fill="x", padx=10, pady=(5, 10))

        self.autoscroll_var = ctk.BooleanVar(value=True)
        self.autoscroll_check = ctk.CTkCheckBox(
            toolbar,
            text="Autoscroll",
            font=FONTS["small"],
            variable=self.autoscroll_var,
            command=self._toggle_autoscroll,
            text_color=COLORS["text"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"]
        )
        self.autoscroll_check.pack(side="left", padx=(0, 10))

        self.clear_btn = ctk.CTkButton(
            toolbar,
            text="Clear",
            font=FONTS["small"],
            width=60,
            height=24,
            fg_color="#334155",
            hover_color="#475569",
            command=self.clear_console
        )
        self.clear_btn.pack(side="right", padx=(5, 0))

        self.save_btn = ctk.CTkButton(
            toolbar,
            text="Save Log",
            font=FONTS["small"],
            width=80,
            height=24,
            fg_color="#334155",
            hover_color="#475569",
            command=self.save_log_file
        )
        self.save_btn.pack(side="right")

    def append_log(self, text: str, tag: str = "info") -> None:
        """
        Appends text into the console viewport.
        Formats line prefix depending on the level tag.
        """
        self.textbox.configure(state="normal")
        
        prefix = ""
        if tag == "success":
            prefix = "[OK] "
        elif tag == "warning":
            prefix = "[WARN] "
        elif tag == "error":
            prefix = "[ERR] "

        formatted_line = f"{prefix}{text}\n"
        self.textbox.insert("end", formatted_line)
        
        # Color styling depending on tags
        # Clean tags range coloring in tkinter
        if tag in ["success", "warning", "error"]:
            last_line = self.textbox.index("end-1c")
            line_num = last_line.split(".")[0]
            start_idx = f"{line_num}.0"
            end_idx = f"{line_num}.end"
            
            color = COLORS["terminal_fg"][1]
            if tag == "warning":
                color = COLORS["warning"][1]
            elif tag == "error":
                color = COLORS["error"][1]
            
            tag_name = f"tag_{last_line}"
            self.textbox.tag_config(tag_name, foreground=color)
            self.textbox.tag_add(tag_name, start_idx, end_idx)

        self.textbox.configure(state="disabled")
        
        if self.autoscroll_var.get():
            self.textbox.see("end")

    def clear_console(self) -> None:
        """Clears all text in the terminal frame."""
        self.textbox.configure(state="normal")
        self.textbox.delete("1.0", "end")
        self.textbox.configure(state="disabled")

    def save_log_file(self) -> None:
        """Saves current console buffer text to a local text file."""
        content = self.textbox.get("1.0", "end-1c")
        if not content.strip():
            return
            
        path = filedialog.asksaveasfilename(
            title="Save Terminal Log",
            defaultextension=".txt",
            filetypes=[("Text Files", "*.txt")],
            initialfile="devtools_install_log.txt"
        )
        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(content)
                self.append_log(f"Log exported successfully to: {path}", "success")
            except Exception as e:
                self.append_log(f"Failed exporting logs to file: {str(e)}", "error")

    def _toggle_autoscroll(self) -> None:
        self.autoscroll = self.autoscroll_var.get()
