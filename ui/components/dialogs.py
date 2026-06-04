import threading
import customtkinter as ctk
from typing import List, Dict, Any, Callable
from ui.theme import COLORS, FONTS
from core.config import _
from core.diagnostic_agent import AIDiagnosticAgent

class BackupSelectionDialog(ctk.CTkToplevel):
    """
    Modal popup displaying checkboxes to let the user select which folders to backup or restore.
    """
    def __init__(self, parent, backup_options: Dict[str, str]):
        super().__init__(parent)
        self.title(_("backup_select_title"))
        self.geometry("380x320")
        self.resizable(False, False)
        
        self.backup_options = backup_options
        self.result: List[str] = []
        self.check_vars: Dict[str, ctk.BooleanVar] = {}

        self.transient(parent)
        self.grab_set()
        self._build_ui()
        
        # Center in parent
        self.geometry(f"+{parent.winfo_x() + 80}+{parent.winfo_y() + 80}")
        self.after(200, lambda: self.focus()) # Fix overlay focus

    def _build_ui(self) -> None:
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.pack(fill="both", expand=True, padx=20, pady=20)

        ctk.CTkLabel(
            frame,
            text=_("backup_select_label"),
            font=FONTS["subheader"],
            text_color=COLORS["text"]
        ).pack(anchor="w", pady=(0, 15))

        # Checkboxes list container
        list_frame = ctk.CTkScrollableFrame(frame, height=150, fg_color=COLORS["bg"], border_width=1, border_color=COLORS["card_border"])
        list_frame.pack(fill="x", pady=(0, 15))

        for option in self.backup_options.keys():
            var = ctk.BooleanVar(value=True)
            self.check_vars[option] = var
            cb = ctk.CTkCheckBox(
                list_frame,
                text=option,
                font=FONTS["body"],
                variable=var,
                fg_color=COLORS["accent"],
                hover_color=COLORS["accent_hover"],
                text_color=COLORS["text"]
            )
            cb.pack(anchor="w", pady=4, padx=5)

        # Buttons
        btn_frame = ctk.CTkFrame(frame, fg_color="transparent")
        btn_frame.pack(fill="x")

        cancel_btn = ctk.CTkButton(
            btn_frame,
            text=_("cancel"),
            font=FONTS["body"],
            width=80,
            fg_color="#475569",
            hover_color="#334155",
            command=self.destroy
        )
        cancel_btn.pack(side="left")

        confirm_btn = ctk.CTkButton(
            btn_frame,
            text="Confirm",
            font=FONTS["body"],
            width=100,
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=self._confirm
        )
        confirm_btn.pack(side="right")

    def _confirm(self) -> None:
        self.result = [opt for opt, var in self.check_vars.items() if var.get()]
        self.destroy()

    def get_selected(self) -> List[str]:
        self.master.wait_window(self)
        return self.result


class AIDiagnosticDialog(ctk.CTkToplevel):
    """
    Diagnostic popup triggered when winget installs fail.
    Uses DuckDuckGo searches and local Ollama diagnostic models.
    """
    def __init__(self, parent, tool_name: str, error_log: str, run_powershell_cmd: Callable[[str], None]):
        super().__init__(parent)
        self.title(_("diag_title"))
        self.geometry("720x620")
        self.resizable(True, True)
        
        self.tool_name = tool_name
        self.error_log = error_log
        self.run_powershell_cmd = run_powershell_cmd
        self.proposed_cmd = ""
        self.search_hits = []

        self.transient(parent)
        self.grab_set()
        self._build_ui()
        
        # Center in parent
        self.geometry(f"+{parent.winfo_x() + 50}+{parent.winfo_y() + 50}")
        self.after(200, lambda: self.focus())

    def _build_ui(self) -> None:
        main_frame = ctk.CTkFrame(self, fg_color="transparent")
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)

        # Header Title
        ctk.CTkLabel(
            main_frame,
            text=f"{_('diag_title')}: {self.tool_name}",
            font=FONTS["header"],
            text_color=COLORS["text"]
        ).pack(anchor="w", pady=(0, 10))

        # Error Logs Viewport
        ctk.CTkLabel(main_frame, text="System Error Logs:", font=FONTS["small"], text_color=COLORS["text_dim"]).pack(anchor="w")
        self.log_box = ctk.CTkTextbox(
            main_frame,
            height=100,
            fg_color="#090D16",
            text_color=COLORS["error"][1],
            font=FONTS["mono"],
            border_width=1,
            border_color=COLORS["card_border"]
        )
        self.log_box.pack(fill="x", pady=(0, 15))
        self.log_box.insert("1.0", self.error_log)
        self.log_box.configure(state="disabled")

        # Action panel buttons
        btn_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        btn_frame.pack(fill="x", pady=(0, 15))

        self.search_btn = ctk.CTkButton(
            btn_frame,
            text=_("diag_btn_search"),
            font=FONTS["body"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=self.run_web_search
        )
        self.search_btn.pack(side="left", padx=(0, 10))

        self.ollama_btn = ctk.CTkButton(
            btn_frame,
            text=_("diag_btn_ollama"),
            font=FONTS["body"],
            fg_color=COLORS["accent"],
            hover_color=COLORS["accent_hover"],
            command=self.run_ollama_analysis
        )
        self.ollama_btn.pack(side="left")

        # Status text label
        self.status_label = ctk.CTkLabel(
            btn_frame,
            text="Waiting for action...",
            font=FONTS["small"],
            text_color=COLORS["text_dim"]
        )
        self.status_label.pack(side="right", padx=10)

        # AI Explanation Text Viewport
        ctk.CTkLabel(main_frame, text=_("diag_expl_label"), font=FONTS["small"], text_color=COLORS["text_dim"]).pack(anchor="w")
        self.expl_box = ctk.CTkTextbox(
            main_frame,
            height=160,
            fg_color=COLORS["bg"],
            text_color=COLORS["text"],
            font=FONTS["body"],
            border_width=1,
            border_color=COLORS["card_border"],
            wrap="word"
        )
        self.expl_box.pack(fill="both", expand=True, pady=(0, 15))
        self.expl_box.configure(state="disabled")

        # Suggested Script Input
        ctk.CTkLabel(main_frame, text=_("diag_cmd_label"), font=FONTS["small"], text_color=COLORS["text_dim"]).pack(anchor="w")
        cmd_row = ctk.CTkFrame(main_frame, fg_color="transparent")
        cmd_row.pack(fill="x")

        self.cmd_entry = ctk.CTkEntry(
            cmd_row,
            font=FONTS["mono"],
            fg_color=COLORS["bg"],
            text_color=COLORS["text"],
            border_width=1,
            border_color=COLORS["card_border"]
        )
        self.cmd_entry.pack(side="left", fill="x", expand=True, padx=(0, 10))

        self.apply_btn = ctk.CTkButton(
            cmd_row,
            text=_("diag_exec_fix"),
            font=FONTS["body"],
            fg_color=COLORS["success"],
            hover_color=COLORS["success"],
            state="disabled",
            command=self.apply_fix_command
        )
        self.apply_btn.pack(side="right")

    def run_web_search(self) -> None:
        """Runs DuckDuckGo search for the tool error logs in a background thread."""
        self.search_btn.configure(state="disabled")
        self.status_label.configure(text="Searching web...", text_color=COLORS["accent"][1])
        
        def task():
            query = f"{self.tool_name} winget install error"
            hits = AIDiagnosticAgent.search_web(query)
            self.search_hits = hits
            
            # Post back to GUI thread
            self.after(0, lambda: self._on_search_complete(hits))

        threading.Thread(target=task, daemon=True).start()

    def _on_search_complete(self, hits: list) -> None:
        self.search_btn.configure(state="normal")
        if hits:
            self.status_label.configure(text=f"Found {len(hits)} articles.", text_color=COLORS["success"][1])
            text_feed = "\n".join([f"- {h['title']} ({h['link']})" for h in hits])
            self._write_explanation(f"Web Search Results:\n{text_feed}\n\nYou can now run local Ollama analysis to synthesize these results.")
        else:
            self.status_label.configure(text="No web results.", text_color=COLORS["warning"][1])
            self._write_explanation("No specific error articles found online. Trying local Ollama might still work.")

    def run_ollama_analysis(self) -> None:
        """Sends the log data to local Ollama agent model in a background thread."""
        self.ollama_btn.configure(state="disabled")
        self.status_label.configure(text="AI analyzing...", text_color=COLORS["accent"][1])

        def task():
            success, expl, cmd = AIDiagnosticAgent.diagnose_with_ollama(
                self.tool_name, 
                self.error_log, 
                self.search_hits
            )
            # Post back to GUI thread
            self.after(0, lambda: self._on_ollama_complete(success, expl, cmd))

        threading.Thread(target=task, daemon=True).start()

    def _on_ollama_complete(self, success: bool, explanation: str, cmd: str) -> None:
        self.ollama_btn.configure(state="normal")
        if success:
            self.status_label.configure(text="Diagnosis complete.", text_color=COLORS["success"][1])
            self._write_explanation(explanation)
            if cmd:
                self.proposed_cmd = cmd
                self.cmd_entry.delete(0, "end")
                self.cmd_entry.insert(0, cmd)
                self.apply_btn.configure(state="normal")
        else:
            self.status_label.configure(text="Analysis failed.", text_color=COLORS["error"][1])
            self._write_explanation(explanation)

    def apply_fix_command(self) -> None:
        """Executes the proposed PowerShell script directly in the parent console logs."""
        command = self.cmd_entry.get()
        if command.strip():
            self.run_powershell_cmd(command)
            self.destroy()

    def _write_explanation(self, text: str) -> None:
        self.expl_box.configure(state="normal")
        self.expl_box.delete("1.0", "end")
        self.expl_box.insert("1.0", text)
        self.expl_box.configure(state="disabled")
