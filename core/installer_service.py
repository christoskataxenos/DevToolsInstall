import os
import queue
import shutil
import subprocess
import threading
import zipfile
from datetime import datetime
from typing import List, Tuple, Dict, Any, Callable, Optional

from core.config import _, BACKUP_PATHS, BACKUP_EXCLUDE_DIRS, ANTIGRAVITY_EXTENSIONS_PATH, Config

class InstallerService:
    """
    Handles installation execution of development tools via winget, npm, powershell,
    and handles system settings backup/restore tasks in background threads.
    """
    def __init__(self, log_queue: queue.Queue):
        self.log_queue = log_queue
        self.is_running = False

    def is_tool_installed(self, tool_id: str) -> bool:
        """
        Queries winget to check if the specific tool is already installed.
        """
        try:
            result = subprocess.run(
                ["winget", "list", "--id", tool_id, "--exact"],
                capture_output=True,
                text=True,
                timeout=20,
            )
            return tool_id in result.stdout
        except Exception:
            return False

    def start_install_task(
        self, 
        tools: List[Tuple[str, str]], 
        on_progress_update: Callable[[int, int], None],
        on_status_change: Callable[[str, str], None],
        on_finished: Callable[[], None],
        show_ai_diagnostic: Callable[[str, str], None]
    ) -> None:
        """
        Spawns a background thread to execute tool installations sequentially.
        """
        self.is_running = True
        thread = threading.Thread(
            target=self._run_installation,
            args=(tools, on_progress_update, on_status_change, on_finished, show_ai_diagnostic),
            daemon=True
        )
        thread.start()

    def _run_installation(
        self,
        tools: List[Tuple[str, str]],
        on_progress_update: Callable[[int, int], None],
        on_status_change: Callable[[str, str], None],
        on_finished: Callable[[], None],
        show_ai_diagnostic: Callable[[str, str], None]
    ) -> None:
        total = len(tools)
        registry = Config.load_registry()

        for i, (name, winget_id) in enumerate(tools):
            on_status_change(name, "RUNNING")
            self.log_queue.put({
                "type": "log",
                "text": _("install_starting_tool", name=name),
                "tag": "info"
            })
            
            # Request UI thread to update progress bar
            on_progress_update(i, total)

            # Find installation details in registry
            tool_details = None
            for category, category_tools in registry.items():
                if name in category_tools:
                    tool_details = category_tools[name]
                    break

            install_type = "winget"
            install_cmd = ""
            if tool_details:
                install_type = tool_details.get("type", "winget")
                install_cmd = tool_details.get("install_command", "")

            # Compose commands
            if install_type == "powershell" and install_cmd:
                cmd = install_cmd
            elif install_type == "npm":
                cmd = f"npm install -g {winget_id}"
            elif install_type == "gh_extension":
                cmd = f"gh extension install {winget_id}"
            elif name == "WSL":
                cmd = "wsl --install"
            else:
                cmd = f"winget install --id {winget_id} --silent --accept-package-agreements --accept-source-agreements"

            error_lines = []
            try:
                process = subprocess.Popen(
                    ["powershell.exe", "-Command", cmd],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    creationflags=subprocess.CREATE_NO_WINDOW,
                )

                if process.stdout:
                    for line in process.stdout:
                        if line.strip():
                            self.log_queue.put({
                                "type": "log",
                                "text": f"  > {line.strip()}",
                                "tag": "info"
                            })
                            error_lines.append(line.strip())

                process.wait()

                if process.returncode == 0:
                    self.log_queue.put({
                        "type": "log",
                        "text": _("install_completed", name=name),
                        "tag": "success"
                    })
                    on_status_change(name, "INSTALLED")
                else:
                    self.log_queue.put({
                        "type": "log",
                        "text": _("install_error_code", code=process.returncode, name=name),
                        "tag": "warning"
                    })
                    on_status_change(name, "ERROR")
                    
                    error_log_str = "\n".join(error_lines) if error_lines else f"PowerShell returned non-zero exit code: {process.returncode}"
                    show_ai_diagnostic(name, error_log_str)

            except Exception as e:
                self.log_queue.put({
                    "type": "log",
                    "text": _("install_error_exception", name=name, error=str(e)),
                    "tag": "error"
                })
                on_status_change(name, "ERROR")
                show_ai_diagnostic(name, f"Exception: {str(e)}")

        on_progress_update(total, total)
        self.log_queue.put({
            "type": "log",
            "text": _("install_all_completed"),
            "tag": "success"
        })
        self.is_running = False
        on_finished()

    def start_backup_task(self, selected_items: List[str], target_zip: str, on_finished: Callable[[], None]) -> None:
        """
        Spawns a thread to backup VS Code settings and local directories into a target ZIP.
        """
        thread = threading.Thread(
            target=self._run_backup,
            args=(selected_items, target_zip, on_finished),
            daemon=True
        )
        thread.start()

    def _run_backup(self, selected_items: List[str], target_zip: str, on_finished: Callable[[], None]) -> None:
        try:
            self.log_queue.put({
                "type": "log",
                "text": _("backup_start", target=target_zip),
                "tag": "info"
            })

            with zipfile.ZipFile(target_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
                temp_dir = os.path.dirname(target_zip) or os.path.expanduser("~")
                ext_file = os.path.join(temp_dir, "vscode_extensions.txt")
                
                # Retrieve VS Code extensions list in backup
                subprocess.run(
                    ["powershell.exe", "-Command", f"code --list-extensions > '{ext_file}'"],
                    capture_output=True,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )

                if os.path.exists(ext_file):
                    zipf.write(ext_file, "vscode_extensions.txt")
                    os.remove(ext_file)

                # Compress Antigravity extensions if directory path exists
                if os.path.exists(ANTIGRAVITY_EXTENSIONS_PATH):
                    self.log_queue.put({
                        "type": "log",
                        "text": _("backup_compressing_antigravity"),
                        "tag": "info"
                    })
                    for root, _, files in os.walk(ANTIGRAVITY_EXTENSIONS_PATH):
                        for file in files:
                            if file.endswith(".vsix"):
                                full_path = os.path.join(root, file)
                                zipf.write(
                                    full_path,
                                    os.path.join("Antigravity_Extensions", os.path.relpath(full_path, ANTIGRAVITY_EXTENSIONS_PATH))
                                )

                # Compress other user selection folders
                for name in selected_items:
                    path = BACKUP_PATHS.get(name)
                    if path and os.path.exists(path):
                        self.log_queue.put({
                            "type": "log",
                            "text": _("backup_compressing", name=name),
                            "tag": "info"
                        })
                        for root, _, files in os.walk(path):
                            for file in files:
                                full_path = os.path.join(root, file)
                                rel_path = os.path.relpath(full_path, path)
                                # Avoid compressing cached or junk directories
                                if any(excl in rel_path.split(os.sep) for excl in BACKUP_EXCLUDE_DIRS):
                                    continue
                                try:
                                    zipf.write(full_path, os.path.join(name, rel_path))
                                except PermissionError:
                                    continue

            self.log_queue.put({
                "type": "log",
                "text": _("backup_success"),
                "tag": "success"
            })
        except Exception as e:
            self.log_queue.put({
                "type": "log",
                "text": _("backup_error", error=str(e)),
                "tag": "error"
            })
        on_finished()

    def start_restore_task(self, zip_path: str, on_finished: Callable[[], None]) -> None:
        """
        Spawns a thread to restore directories from a backup ZIP.
        """
        thread = threading.Thread(
            target=self._run_restore,
            args=(zip_path, on_finished),
            daemon=True
        )
        thread.start()

    def _run_restore(self, zip_path: str, on_finished: Callable[[], None]) -> None:
        try:
            self.log_queue.put({
                "type": "log",
                "text": _("restore_start", path=zip_path),
                "tag": "info"
            })

            with zipfile.ZipFile(zip_path, "r") as zipf:
                for name, dest in BACKUP_PATHS.items():
                    prefix = f"{name}/"
                    members = [m for m in zipf.namelist() if m.startswith(prefix)]

                    if members:
                        self.log_queue.put({
                            "type": "log",
                            "text": _("restore_extracting", name=name),
                            "tag": "info"
                        })
                        os.makedirs(dest, exist_ok=True)
                        for m in members:
                            rel = os.path.relpath(m, prefix)
                            target = os.path.join(dest, rel)
                            if m.endswith("/"):
                                os.makedirs(target, exist_ok=True)
                            else:
                                os.makedirs(os.path.dirname(target), exist_ok=True)
                                with zipf.open(m) as s, open(target, "wb") as t:
                                    shutil.copyfileobj(s, t)

                # Reinstall VS Code extensions
                if "vscode_extensions.txt" in zipf.namelist():
                    self.log_queue.put({
                        "type": "log",
                        "text": _("restore_extensions"),
                        "tag": "info"
                    })
                    with zipf.open("vscode_extensions.txt") as f:
                        extensions = f.read().decode("utf-8").strip().split("\n")

                    for ext in extensions:
                        ext = ext.strip()
                        if ext:
                            self.log_queue.put({
                                "type": "log",
                                "text": _("restore_extension_installing", ext=ext),
                                "tag": "info"
                            })
                            subprocess.run(
                                ["powershell.exe", "-Command", f"code --install-extension {ext} --force"],
                                capture_output=True,
                                creationflags=subprocess.CREATE_NO_WINDOW
                            )

                # Restore Antigravity extension files
                if any(x.startswith("Antigravity_Extensions/") for x in zipf.namelist()):
                    self.log_queue.put({
                        "type": "log",
                        "text": _("restore_antigravity"),
                        "tag": "info"
                    })
                    os.makedirs(ANTIGRAVITY_EXTENSIONS_PATH, exist_ok=True)
                    for name in zipf.namelist():
                        if name.startswith("Antigravity_Extensions/") and not name.endswith("/"):
                            target = os.path.join(
                                ANTIGRAVITY_EXTENSIONS_PATH,
                                os.path.relpath(name, "Antigravity_Extensions"),
                            )
                            os.makedirs(os.path.dirname(target), exist_ok=True)
                            with zipf.open(name) as s, open(target, "wb") as t:
                                shutil.copyfileobj(s, t)
                            ext_name = os.path.basename(target)
                            self.log_queue.put({
                                "type": "log",
                                "text": _("restore_antigravity_success", name=ext_name),
                                "tag": "info"
                            })

            self.log_queue.put({
                "type": "log",
                "text": _("restore_success"),
                "tag": "success"
            })
        except Exception as e:
            self.log_queue.put({
                "type": "log",
                "text": _("restore_error", error=str(e)),
                "tag": "error"
            })
        on_finished()
