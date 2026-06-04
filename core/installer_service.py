import os
import queue
import shutil
import subprocess
import threading
import zipfile
import urllib.request
import webbrowser
from datetime import datetime
from typing import List, Tuple, Dict, Any, Callable, Optional, Set

from core.config import _, BACKUP_PATHS, BACKUP_EXCLUDE_DIRS, ANTIGRAVITY_EXTENSIONS_PATH, Config

def clean_log_line(line: str) -> Optional[str]:
    """
    Καθαρίζει μια γραμμή καταγραφής από θόρυβο (spinners, μπάρες προόδου).
    Επιστρέφει τη γραμμή καθαρισμένη ή None αν πρέπει να αγνοηθεί.
    """
    # Αφαίρεση κενών στην αρχή και στο τέλος της γραμμής
    cleaned = line.strip()
    if not cleaned:
        return None

    # Φιλτράρισμα χαρακτήρων spinner
    # Αν η γραμμή είναι μόνο ένας χαρακτήρας spinner ή τελείες, την αγνοούμε
    if cleaned in ["-", "\\", "|", "/", ".", "..", "..."]:
        return None

    # Φιλτράρισμα γραμμών που περιέχουν χαρακτήρες προόδου (blocks)
    # Ελέγχουμε για Unicode blocks ή CP1252 garbled αναπαραστάσεις
    block_chars = ["\u2588", "\u2591", "\u2592", "\u2593", "â–ˆ", "â–’"]
    if any(char in cleaned for char in block_chars):
        return None

    # Φιλτράρισμα γραμμών με πληροφορίες μεγέθους λήψης (π.χ. "1024 KB / 767 MB")
    if " / " in cleaned and any(unit in cleaned for unit in [" B", " KB", " MB", " GB"]):
        return None

    # Φιλτράρισμα γραμμών με ποσοστά και ρυθμό λήψης
    if "%" in cleaned and any(x in cleaned for x in ["MB/s", "KB/s", "B/s"]):
        return None

    return cleaned


class InstallerService:
    """
    Handles installation execution of development tools via winget, npm, powershell,
    and handles system settings backup/restore tasks in background threads.
    """
    def __init__(self, log_queue: queue.Queue):
        self.log_queue = log_queue
        self.is_running = False
        self.active_processes: List[subprocess.Popen] = []

    def cleanup(self) -> None:
        """Terminates any active subprocesses running in the service."""
        for process in list(self.active_processes):
            try:
                if process.poll() is None:  # Still running
                    process.terminate()
                    process.wait(timeout=1)
            except Exception:
                pass
        self.active_processes.clear()

    def is_tool_installed(self, tool_id: str) -> bool:
        """
        Queries winget to check if the specific tool is already installed.
        """
        try:
            process = subprocess.Popen(
                ["winget", "list", "--id", tool_id, "--exact"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            self.active_processes.append(process)
            stdout, stderr = process.communicate(timeout=20)
            if process in self.active_processes:
                self.active_processes.remove(process)
            return tool_id in stdout
        except Exception:
            return False

    def get_installed_tool_ids(self) -> Set[str]:
        """
        Queries winget once to retrieve all installed tool IDs.
        """
        installed_ids = set()
        try:
            process = subprocess.Popen(
                ["winget", "list", "--accept-source-agreements"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                encoding="utf-8",
                errors="ignore",
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            self.active_processes.append(process)
            stdout, stderr = process.communicate()
            if process in self.active_processes:
                self.active_processes.remove(process)
            
            if process.returncode == 0 or stdout:
                lines = stdout.splitlines()
                header_idx = -1
                for idx, line in enumerate(lines):
                    if "Name" in line and "Id" in line:
                        header_idx = idx
                        break
                
                if header_idx != -1 and header_idx + 1 < len(lines):
                    header = lines[header_idx]
                    id_pos = header.find("Id")
                    version_pos = header.find("Version")
                    if id_pos != -1 and version_pos != -1:
                        for line in lines[header_idx + 2:]:
                            if len(line) > id_pos:
                                tool_id = line[id_pos:version_pos].strip()
                                if tool_id:
                                    clean_id = tool_id.split()[0] if tool_id.split() else tool_id
                                    installed_ids.add(clean_id)
        except Exception:
            pass
        return installed_ids


    def _is_choco_installed(self) -> bool:
        # Έλεγχος αν το Chocolatey είναι εγκατεστημένο στο σύστημα
        # Ελέγχουμε αν η εντολή choco υπάρχει στο PATH
        if shutil.which("choco"):
            return True
        # Ελέγχουμε την προεπιλεγμένη διαδρομή εγκατάστασης του Chocolatey
        choco_path = os.path.expandvars(r"%ALLUSERSPROFILE%\chocolatey\bin\choco.exe")
        return os.path.exists(choco_path)

    def _is_scoop_installed(self) -> bool:
        # Έλεγχος αν το Scoop είναι εγκατεστημένο στο σύστημα
        # Ελέγχουμε αν η εντολή scoop υπάρχει στο PATH
        if shutil.which("scoop"):
            return True
        # Ελέγχουμε την προεπιλεγμένη διαδρομή εγκατάστασης του Scoop
        scoop_path = os.path.expandvars(r"%USERPROFILE%\scoop\shims\scoop.cmd")
        return os.path.exists(scoop_path)

    def _install_choco(self) -> bool:
        # Αυτόματη εγκατάσταση του Chocolatey
        self.log_queue.put({
            "type": "log",
            "text": _("install_choco_missing"),
            "tag": "info"
        })
        # Εντολή PowerShell για την εγκατάσταση του Chocolatey
        cmd = "Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))"
        try:
            # Εκτέλεση της εντολής PowerShell με παράκαμψη της πολιτικής εκτέλεσης (ExecutionPolicy Bypass)
            # για να επιτραπεί η εγκατάσταση του Chocolatey χωρίς σφάλματα δικαιωμάτων
            process = subprocess.Popen(
                ["powershell.exe", "-ExecutionPolicy", "Bypass", "-Command", cmd],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="ignore",
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            self.active_processes.append(process)
            process.wait()
            if process in self.active_processes:
                self.active_processes.remove(process)
            
            # Έλεγχος επιτυχίας
            if process.returncode == 0 or self._is_choco_installed():
                self.log_queue.put({
                    "type": "log",
                    "text": _("install_choco_install_success"),
                    "tag": "success"
                })
                # Προσθήκη του choco bin στο PATH της τρέχουσας διεργασίας
                choco_bin = os.path.expandvars(r"%ALLUSERSPROFILE%\chocolatey\bin")
                if choco_bin not in os.environ["PATH"]:
                    os.environ["PATH"] += os.path.pathsep + choco_bin
                return True
        except Exception as e:
            self.log_queue.put({
                "type": "log",
                "text": f"Error installing Chocolatey: {str(e)}",
                "tag": "error"
            })
        return False

    def _install_scoop(self) -> bool:
        # Αυτόματη εγκατάσταση του Scoop
        self.log_queue.put({
            "type": "log",
            "text": _("install_scoop_missing"),
            "tag": "info"
        })
        # Εντολή PowerShell για την εγκατάσταση του Scoop
        cmd = "Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope Process; iwr -useb get.scoop.sh | iex"
        try:
            # Εκτέλεση της εντολής PowerShell με παράκαμψη της πολιτικής εκτέλεσης (ExecutionPolicy Bypass)
            # για την απρόσκοπτη λήψη και εγκατάσταση του Scoop
            process = subprocess.Popen(
                ["powershell.exe", "-ExecutionPolicy", "Bypass", "-Command", cmd],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="ignore",
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            self.active_processes.append(process)
            process.wait()
            if process in self.active_processes:
                self.active_processes.remove(process)
            
            # Έλεγχος επιτυχίας
            if process.returncode == 0 or self._is_scoop_installed():
                self.log_queue.put({
                    "type": "log",
                    "text": _("install_scoop_install_success"),
                    "tag": "success"
                })
                # Προσθήκη του scoop shims στο PATH της τρέχουσας διεργασίας
                scoop_bin = os.path.expandvars(r"%USERPROFILE%\scoop\shims")
                if scoop_bin not in os.environ["PATH"]:
                    os.environ["PATH"] += os.path.pathsep + scoop_bin
                return True
        except Exception as e:
            self.log_queue.put({
                "type": "log",
                "text": f"Error installing Scoop: {str(e)}",
                "tag": "error"
            })
        return False

    def _run_installer_process(self, cmd: str) -> Tuple[int, List[str]]:
        # Εκτέλεση μιας εντολής εγκατάστασης και συλλογή/καταγραφή των αποτελεσμάτων της
        log_lines = []
        try:
            # Εκτέλεση της διεργασίας εγκατάστασης με παράκαμψη της πολιτικής εκτέλεσης (ExecutionPolicy Bypass)
            # για να επιτρέπεται η εκτέλεση PowerShell scripts (όπως τα scoop shims/ps1)
            process = subprocess.Popen(
                ["powershell.exe", "-ExecutionPolicy", "Bypass", "-Command", cmd],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                encoding="utf-8",
                errors="ignore",
                creationflags=subprocess.CREATE_NO_WINDOW
            )
            self.active_processes.append(process)
            
            if process.stdout:
                for line in process.stdout:
                    cleaned = clean_log_line(line)
                    if cleaned:
                        self.log_queue.put({
                            "type": "log",
                            "text": f"  > {cleaned}",
                            "tag": "info"
                        })
                        log_lines.append(cleaned)
            
            process.wait()
            if process in self.active_processes:
                self.active_processes.remove(process)
            return process.returncode, log_lines
        except Exception as e:
            return -1, [str(e)]

    def _download_and_install_url(self, name: str, url: str, tool_details: dict) -> bool:
        # Λήψη αρχείου εγκατάστασης από απευθείας σύνδεσμο και εκτέλεσή του
        self.log_queue.put({
            "type": "log",
            "text": _("install_downloading_url", url=url),
            "tag": "info"
        })
        try:
            # Καθορισμός του temp φακέλου και του ονόματος του αρχείου
            temp_dir = os.environ.get("TEMP", os.path.expanduser("~\\AppData\\Local\\Temp"))
            filename = url.split("/")[-1].split("?")[0] or f"installer_{name}.exe"
            if not filename.endswith((".exe", ".msi")):
                filename += ".exe"
            
            temp_path = os.path.join(temp_dir, f"devtools_{filename}")
            
            # Λήψη του αρχείου εγκατάστασης
            urllib.request.urlretrieve(url, temp_path)
            
            self.log_queue.put({
                "type": "log",
                "text": _("install_running_installer"),
                "tag": "info"
            })
            
            install_args = tool_details.get("install_args", "")
            
            # Επιλογή της σωστής εντολής ανάλογα με τον τύπο του αρχείου (.msi ή .exe)
            if filename.endswith(".msi"):
                # Χρήση msiexec για αθόρυβη εγκατάσταση MSI
                cmd = f'msiexec.exe /i "{temp_path}" /quiet /qn /norestart {install_args}'
            else:
                # Χρήση Start-Process για EXE. Αν δεν υπάρχουν args, δοκιμάζουμε κοινά silent args
                if install_args:
                    cmd = f'Start-Process -FilePath "{temp_path}" -ArgumentList "{install_args}" -Wait'
                else:
                    cmd = f'Start-Process -FilePath "{temp_path}" -ArgumentList "/S", "/silent", "/quiet", "/qn" -Wait'
            
            # Εκτέλεση της εγκατάστασης με ορατό παράθυρο (creationflags=0)
            # ώστε αν το πρόγραμμα απαιτεί αλληλεπίδραση ο χρήστης να μπορεί να το δει
            # Προσθήκη παραμέτρου -ExecutionPolicy Bypass για αποφυγή σφαλμάτων εκτέλεσης σε PowerShell
            process = subprocess.Popen(
                ["powershell.exe", "-ExecutionPolicy", "Bypass", "-Command", cmd],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                creationflags=0
            )
            self.active_processes.append(process)
            process.wait()
            if process in self.active_processes:
                self.active_processes.remove(process)
            
            # Διαγραφή του προσωρινού αρχείου μετά την εγκατάσταση
            try:
                if os.path.exists(temp_path):
                    os.remove(temp_path)
            except Exception:
                pass
            
            return process.returncode == 0
        except Exception as e:
            self.log_queue.put({
                "type": "log",
                "text": f"Error during direct URL download/install: {str(e)}",
                "tag": "error"
            })
            return False

    def _open_browser_fallback(self, url: str) -> None:
        # Άνοιγμα της επίσημης ιστοσελίδας του εργαλείου στον προεπιλεγμένο περιηγητή
        self.log_queue.put({
            "type": "log",
            "text": _("install_manual_fallback", url=url),
            "tag": "warning"
        })
        webbrowser.open(url)

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
            
            # Ενημέρωση της μπάρας προόδου στο UI
            on_progress_update(i, total)

            # Εύρεση των λεπτομερειών της εφαρμογής από το registry
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

            # Σύνθεση της αρχικής εντολής εγκατάστασης
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

            # Εκτέλεση της κύριας προσπάθειας εγκατάστασης
            ret_code, error_lines = self._run_installer_process(cmd)

            if ret_code == 0:
                self.log_queue.put({
                    "type": "log",
                    "text": _("install_completed", name=name),
                    "tag": "success"
                })
                on_status_change(name, "INSTALLED")
                continue

            # Η αρχική εγκατάσταση απέτυχε. Ξεκινάμε την εναλλακτική διαδικασία (fallbacks).
            installed = False

            # 1. Δοκιμή μέσω Chocolatey
            choco_id = tool_details.get("choco_id") if tool_details else None
            if not choco_id and winget_id:
                choco_id = winget_id.split(".")[-1].lower()

            if choco_id:
                self.log_queue.put({
                    "type": "log",
                    "text": _("install_trying_fallback", method="Chocolatey"),
                    "tag": "info"
                })
                # Αν το Chocolatey λείπει, προσπαθούμε να το εγκαταστήσουμε δυναμικά
                if not self._is_choco_installed():
                    self._install_choco()

                if self._is_choco_installed():
                    choco_cmd = f"choco install {choco_id} -y"
                    fallback_ret, fallback_logs = self._run_installer_process(choco_cmd)
                    if fallback_ret == 0:
                        self.log_queue.put({
                            "type": "log",
                            "text": _("install_fallback_success", method="Chocolatey"),
                            "tag": "success"
                        })
                        on_status_change(name, "INSTALLED")
                        installed = True
                    else:
                        self.log_queue.put({
                            "type": "log",
                            "text": _("install_fallback_failed", method="Chocolatey"),
                            "tag": "warning"
                        })
                        if fallback_logs:
                            error_lines.extend(fallback_logs)

            # 2. Δοκιμή μέσω Scoop (αν η εγκατάσταση εκκρεμεί ακόμη)
            if not installed:
                scoop_id = tool_details.get("scoop_id") if tool_details else None
                if not scoop_id and winget_id:
                    scoop_id = winget_id.split(".")[-1].lower()

                if scoop_id:
                    self.log_queue.put({
                        "type": "log",
                        "text": _("install_trying_fallback", method="Scoop"),
                        "tag": "info"
                    })
                    # Αν το Scoop λείπει, προσπαθούμε να το εγκαταστήσουμε δυναμικά
                    if not self._is_scoop_installed():
                        self._install_scoop()

                    if self._is_scoop_installed():
                        scoop_cmd = f"scoop install {scoop_id}"
                        fallback_ret, fallback_logs = self._run_installer_process(scoop_cmd)
                        if fallback_ret == 0:
                            self.log_queue.put({
                                "type": "log",
                                "text": _("install_fallback_success", method="Scoop"),
                                "tag": "success"
                            })
                            on_status_change(name, "INSTALLED")
                            installed = True
                        else:
                            self.log_queue.put({
                                "type": "log",
                                "text": _("install_fallback_failed", method="Scoop"),
                                "tag": "warning"
                            })
                            if fallback_logs:
                                error_lines.extend(fallback_logs)

            # 3. Δοκιμή μέσω Direct URL Download & Run
            if not installed and tool_details:
                download_url = tool_details.get("download_url")
                if download_url:
                    self.log_queue.put({
                        "type": "log",
                        "text": _("install_trying_fallback", method="Direct Download URL"),
                        "tag": "info"
                    })
                    if self._download_and_install_url(name, download_url, tool_details):
                        self.log_queue.put({
                            "type": "log",
                            "text": _("install_fallback_success", method="Direct Download URL"),
                            "tag": "success"
                        })
                        on_status_change(name, "INSTALLED")
                        installed = True
                    else:
                        self.log_queue.put({
                            "type": "log",
                            "text": _("install_fallback_failed", method="Direct Download URL"),
                            "tag": "warning"
                        })

            # 4. Χειροκίνητη λήψη μέσω ανοίγματος της ιστοσελίδας του εργαλείου
            if not installed:
                on_status_change(name, "ERROR")
                self.log_queue.put({
                    "type": "log",
                    "text": _("install_error_code", code=ret_code, name=name),
                    "tag": "warning"
                })
                
                web_url = tool_details.get("url") if tool_details else None
                if web_url:
                    self._open_browser_fallback(web_url)

                # Εμφάνιση της AI διάγνωσης σφάλματος
                error_log_str = "\n".join(error_lines) if error_lines else f"PowerShell returned exit code: {ret_code}"
                show_ai_diagnostic(name, error_log_str)

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
                
                # Ανάκτηση της λίστας επεκτάσεων VS Code για το αντίγραφο ασφαλείας
                # Χρήση -ExecutionPolicy Bypass για την ασφαλή εκτέλεση του PowerShell script
                proc = subprocess.Popen(
                    ["powershell.exe", "-ExecutionPolicy", "Bypass", "-Command", f"code --list-extensions > '{ext_file}'"],
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    creationflags=subprocess.CREATE_NO_WINDOW
                )
                self.active_processes.append(proc)
                proc.communicate()
                if proc in self.active_processes:
                    self.active_processes.remove(proc)

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
                            # Επανεγκατάσταση της επέκτασης VS Code
                            # Χρήση -ExecutionPolicy Bypass για την ασφαλή εκτέλεση της εντολής στο PowerShell
                            proc = subprocess.Popen(
                                ["powershell.exe", "-ExecutionPolicy", "Bypass", "-Command", f"code --install-extension {ext} --force"],
                                stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE,
                                creationflags=subprocess.CREATE_NO_WINDOW
                            )
                            self.active_processes.append(proc)
                            proc.communicate()
                            if proc in self.active_processes:
                                self.active_processes.remove(proc)

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
