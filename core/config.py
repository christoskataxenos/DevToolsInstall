import os
import json
from typing import Dict, Any, List

class TranslationManager:
    """
    Manages localization across the application.
    Supports English ('en') and Greek ('el').
    """
    _current_lang = "en"  # Defaulting to English as requested

    _strings = {
        "el": {
            "menu_header": "ΜΕΝΟΥ ΠΛΟΗΓΗΣΗΣ",
            "nav_install": "Εγκατάσταση Εργαλείων",
            "nav_stacks": "Πακέτα Stacks",
            "nav_backup_restore": "Backup & Επαναφορά",
            "nav_skills": "AI Agent Skills",
            "filter_all": "Όλα",
            "filter_selected": "Επιλεγμένα",
            "filter_installed": "Εγκατεστημένα",
            "filter_pending": "Εκκρεμή",
            "app_title": "DevTools Installer v3.0",
            "Dark Mode": "Σκοτεινή Λειτουργία",
            "categories": "ΚΑΤΗΓΟΡΙΕΣ",
            "stacks": "ΠΑΚΕΤΑ (STACKS)",
            "backup": "Backup",
            "restore": "Επαναφορά",
            "status_ready": "Status: Έτοιμο",
            "status_completed": "Status: Ολοκληρώθηκε",
            "status_prefix": "Status: ",
            "search_placeholder": "Αναζήτηση...",
            "tool_management": "Διαχείριση Εργαλείων",
            "show_console": "Εμφάνιση Κονσόλας",
            "hide_console": "Απόκρυψη Κονσόλας",
            "select_all": "Επιλογή Όλων",
            "deselect_all": "Αποεπιλογή Όλων",
            "install_selected": "Εγκατάσταση Επιλεγμένων",
            "select_at_least_one": "[ΠΡΟΣΟΧΗ] Παρακαλώ επιλέξτε τουλάχιστον μία εφαρμογή.",
            "starting_install": "Έναρξη εγκατάστασης {count} εφαρμογών...",
            "install_starting_tool": "Έναρξη εγκατάστασης: {name}...",
            "install_completed": "Ολοκληρώθηκε: {name}",
            "install_error_code": "Σφάλμα (Κωδικός {code}): {name}",
            "install_error_exception": "Σφάλμα κατά την εγκατάσταση του {name}: {error}",
            "install_all_completed": "Όλες οι εγκαταστάσεις ολοκληρώθηκαν!",
            "install_trying_fallback": "Η εγκατάσταση απέτυχε. Δοκιμή εναλλακτικής μεθόδου: {method}...",
            "install_fallback_success": "Η εγκατάσταση ολοκληρώθηκε επιτυχώς μέσω {method}!",
            "install_fallback_failed": "Η εναλλακτική μέθοδος {method} απέτυχε.",
            "install_choco_missing": "Το Chocolatey δεν είναι εγκατεστημένο. Εγκατάσταση του Chocolatey...",
            "install_choco_install_success": "Το Chocolatey εγκαταστάθηκε επιτυχώς!",
            "install_scoop_missing": "Το Scoop δεν είναι εγκατεστημένο. Εγκατάσταση του Scoop...",
            "install_scoop_install_success": "Το Scoop εγκαταστάθηκε επιτυχώς!",
            "install_downloading_url": "Λήψη αρχείου εγκατάστασης από: {url}...",
            "install_running_installer": "Εκτέλεση αρχείου εγκατάστασης. Παρακαλώ ελέγξτε αν εμφανίστηκε κάποιο παράθυρο εγκατάστασης...",
            "install_manual_fallback": "Όλες οι αυτόματες μέθοδοι απέτυχαν. Άνοιγμα της επίσημης ιστοσελίδας για χειροκίνητη εγκατάσταση: {url}",
            "backup_select_title": "Επιλογή Στοιχείων Backup",
            "backup_select_label": "Επιλέξτε στοιχεία για backup:",
            "backup_select_btn": "Backup Επιλεγμένων",
            "cancel": "Ακύρωση",
            "not_found": "(δεν βρέθηκε)",
            "backup_start": "Έναρξη Backup -> {target}",
            "backup_compressing": "  > Συμπίεση: {name}",
            "backup_compressing_antigravity": "  > Συμπίεση: Antigravity Extensions",
            "backup_success": "Το Backup ολοκληρώθηκε με επιτυχία!",
            "backup_error": "Σφάλμα στο Backup: {error}",
            "restore_select_title": "Επιλέξτε Backup ZIP",
            "restore_start": "Έναρξη Επαναφοράς από: {path}",
            "restore_extracting": "  > Εξαγωγή: {name}",
            "restore_extensions": "  > Επαναφορά επεκτάσεων VS Code...",
            "restore_extension_installing": "    > Εγκατάσταση: {ext}",
            "restore_antigravity": "  > Επαναφορά επεκτάσεων Antigravity...",
            "restore_antigravity_success": "    > Επαναφέρθηκε: {name}",
            "restore_success": "Η Επαναφορά ολοκληρώθηκε!",
            "restore_error": "Σφάλμα κατά την Επαναφορά: {error}",
            "export_no_selection": "Δεν έχουν επιλεγεί εργαλεία για εξαγωγή.",
            "export_title": "Εξαγωγή Επιλογής",
            "export_success": "Η εξαγωγή ολοκληρώθηκε: {path}",
            "export_error": "Σφάλμα εξαγωγής: {error}",
            "import_title": "Εισαγωγή Επιλογής",
            "import_success": "Εισήχθησαν {count} εργαλεία.",
            "import_error": "Σφάλμα εισαγωγής: {error}",
            "checking_installed": "Έλεγχος εγκατεστημένων εργαλείων...",
            "check_complete": "Ο έλεγχος ολοκληρώθηκε.",
            "Browsers": "Περιηγητές (Browsers)",
            "Office & Documents": "Γράφειο & Έγγραφα",
            "Communication": "Επικοινωνία",
            "Media & Entertainment": "Πολυμέσα & Ψυχαγωγία",
            "System & Cloud": "Σύστημα & Cloud",
            "Privacy & Security": "Ιδιωτικότητα & Ασφάλεια",
            "IDEs & Editors": "IDEs & Editors",
            "Version Control": "Έλεγχος Εκδόσεων (Git)",
            "Runtimes & Languages": "Runtimes & Γλώσσες",
            "Package Managers": "Package Managers",
            "Database Tools": "Εργαλεία Βάσεων Δεδομένων",
            "Virtualization": "Virtualization & Containers",
            "Hardware & AI": "Hardware & AI",
            "System & Shell": "Σύστημα & Shell",
            "AI Coding Assistants": "AI Coding Assistants",
            "Productivity": "Παραγωγικότητα",
            "Remote": "Απομακρυσμένη Πρόσβαση",
            "Design & Media": "Σχεδιασμός & Media",
            "C & Systems Dev": "C & Systems Dev",
            "API & Testing": "API & Testing",
            "Security & Networking": "Ασφάλεια & Δίκτυα",
            "Cloud & DevOps": "Cloud & DevOps",
            "warning_requirements_title": "Προειδοποίηση Απαιτήσεων",
            "warning_requirements_msg": "Το σύστημά σας δεν πληροί τις ελάχιστες απαιτήσεις για το εργαλείο {name}.\n\nΑπαιτήσεις:\n{reasons}\n\nΕίστε σίγουροι ότι θέλετε να το επιλέξετε;",
            "skills_title": "Διαχείριση AI Skills & Prompts",
            "skills_repo_label": "GitHub Repository URL:",
            "skills_btn_download": "Λήψη / Συγχρονισμός",
            "skills_destination": "Προορισμός Εξαγωγής (Project):",
            "skills_btn_export": "Εξαγωγή στο Project",
            "skills_global_path": "Global Φάκελος: {path}",
            "skills_status_prefix": "Κατάσταση: {status}",
            "diag_title": "AI Διάγνωση Σφάλματος",
            "diag_btn_search": "Αναζήτηση Λύσης στο Web",
            "diag_btn_ollama": "Ανάλυση με Τοπικό AI (Ollama)",
            "diag_exec_fix": "Εκτέλεση Διόρθωσης",
            "diag_expl_label": "Εξήγηση Σφάλματος:",
            "diag_cmd_label": "Προτεινόμενη Εντολή:"
        },
        "en": {
            "menu_header": "NAVIGATION MENU",
            "nav_install": "Install Tools",
            "nav_stacks": "System Stacks",
            "nav_backup_restore": "Backup & Restore",
            "nav_skills": "AI Agent Skills",
            "filter_all": "All",
            "filter_selected": "Selected",
            "filter_installed": "Installed",
            "filter_pending": "Pending",
            "app_title": "DevTools Installer v3.0",
            "Dark Mode": "Dark Mode",
            "categories": "CATEGORIES",
            "stacks": "STACKS",
            "backup": "Backup",
            "restore": "Restore",
            "status_ready": "Status: Ready",
            "status_completed": "Status: Completed",
            "status_prefix": "Status: ",
            "search_placeholder": "Search tools...",
            "tool_management": "Tool Management",
            "show_console": "Show Console",
            "hide_console": "Hide Console",
            "select_all": "Select All",
            "deselect_all": "Deselect All",
            "install_selected": "Install Selected",
            "select_at_least_one": "[WARNING] Please select at least one application.",
            "starting_install": "Starting installation of {count} applications...",
            "install_starting_tool": "Starting installation: {name}...",
            "install_completed": "Completed: {name}",
            "install_error_code": "Error (Code {code}): {name}",
            "install_error_exception": "Error installing {name}: {error}",
            "install_all_completed": "All installations completed!",
            "install_trying_fallback": "Installation failed. Trying fallback method: {method}...",
            "install_fallback_success": "Installation completed successfully via {method}!",
            "install_fallback_failed": "Fallback method {method} failed.",
            "install_choco_missing": "Chocolatey is not installed. Installing Chocolatey...",
            "install_choco_install_success": "Chocolatey installed successfully!",
            "install_scoop_missing": "Scoop is not installed. Installing Scoop...",
            "install_scoop_install_success": "Scoop installed successfully!",
            "install_downloading_url": "Downloading installer from: {url}...",
            "install_running_installer": "Running downloaded installer. Please check for any wizard windows...",
            "install_manual_fallback": "All automated methods failed. Opening official website for manual installation: {url}",
            "backup_select_title": "Select Backup Items",
            "backup_select_label": "Select items to backup:",
            "backup_select_btn": "Backup Selected",
            "cancel": "Cancel",
            "not_found": "(not found)",
            "backup_start": "Starting Backup -> {target}",
            "backup_compressing": "  > Compressing: {name}",
            "backup_compressing_antigravity": "  > Compressing: Antigravity Extensions",
            "backup_success": "Backup completed successfully!",
            "backup_error": "Backup Error: {error}",
            "restore_select_title": "Select Backup ZIP",
            "restore_start": "Starting Restore from: {path}",
            "restore_extracting": "  > Extracting: {name}",
            "restore_extensions": "  > Restoring VS Code extensions...",
            "restore_extension_installing": "    > Installing: {ext}",
            "restore_antigravity": "  > Restoring Antigravity extensions...",
            "restore_antigravity_success": "    > Restored: {name}",
            "restore_success": "Restore completed!",
            "restore_error": "Error during Restore: {error}",
            "export_no_selection": "No tools selected for export.",
            "export_title": "Export Selection",
            "export_success": "Export successful: {path}",
            "export_error": "Export error: {error}",
            "import_title": "Import Selection",
            "import_success": "Imported {count} tools.",
            "import_error": "Import error: {error}",
            "checking_installed": "Checking installed tools...",
            "check_complete": "Check complete.",
            "Browsers": "Browsers",
            "Office & Documents": "Office & Documents",
            "Communication": "Communication",
            "Media & Entertainment": "Media & Entertainment",
            "System & Cloud": "System & Cloud",
            "Privacy & Security": "Privacy & Security",
            "IDEs & Editors": "IDEs & Editors",
            "Version Control": "Version Control",
            "Runtimes & Languages": "Runtimes & Languages",
            "Package Managers": "Package Managers",
            "Database Tools": "Database Tools",
            "Virtualization": "Virtualization",
            "Hardware & AI": "Hardware & AI",
            "System & Shell": "System & Shell",
            "AI Coding Assistants": "AI Coding Assistants",
            "Productivity": "Productivity",
            "Remote": "Remote",
            "Design & Media": "Design & Media",
            "C & Systems Dev": "C & Systems Dev",
            "API & Testing": "API & Testing",
            "Security & Networking": "Security & Networking",
            "Cloud & DevOps": "Cloud & DevOps",
            "warning_requirements_title": "Requirements Warning",
            "warning_requirements_msg": "Your system does not meet the minimum requirements for {name}.\n\nRequirements:\n{reasons}\n\nAre you sure you want to select it?",
            "skills_title": "AI Agent Skills & Prompts",
            "skills_repo_label": "GitHub Repository URL:",
            "skills_btn_download": "Download / Sync",
            "skills_destination": "Export Destination (Project):",
            "skills_btn_export": "Export to Project",
            "skills_global_path": "Global Directory: {path}",
            "skills_status_prefix": "Status: {status}",
            "diag_title": "AI Error Diagnosis",
            "diag_btn_search": "Search Solution on Web",
            "diag_btn_ollama": "Analyze with Local AI (Ollama)",
            "diag_exec_fix": "Execute Fix",
            "diag_expl_label": "Error Explanation:",
            "diag_cmd_label": "Proposed Command:"
        }
    }

    @classmethod
    def set_language(cls, lang: str) -> None:
        """Sets the active translation language."""
        if lang in cls._strings:
            cls._current_lang = lang

    @classmethod
    def get_language(cls) -> str:
        """Gets the active translation language."""
        return cls._current_lang

    @classmethod
    def translate(cls, key: str, **kwargs) -> str:
        """Translates a given string key, formatting placeholders if provided."""
        text = cls._strings[cls._current_lang].get(key, key)
        if kwargs:
            return text.format(**kwargs)
        return text

def _(key: str, **kwargs) -> str:
    """Convenience alias for string translation."""
    return TranslationManager.translate(key, **kwargs)

class Config:
    """
    Handles registry loading, environment stacks, and directory configs.
    """
    @staticmethod
    def get_registry_path() -> str:
        """Returns the absolute path to the installers registry file."""
        return os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "installers.json")

    @staticmethod
    def load_registry() -> Dict[str, Any]:
        """Loads the registry details from installers.json."""
        path = Config.get_registry_path()
        if not os.path.exists(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    @staticmethod
    def load_stacks() -> Dict[str, List[str]]:
        """
        Defines and returns standard setup stacks of tool names.
        Matches the IDs listed in the registry.
        """
        return {
            "Python Dev": [
                "Python 3.14",
                "VS Code",
                "Git",
                "GitHub CLI (gh)",
                "Everything"
            ],
            "React / JS Dev": [
                "Node.js (LTS)",
                "VS Code",
                "Git",
                "GitHub Desktop",
                "Google Chrome"
            ],
            "C / Systems Dev": [
                "TDM-GCC",
                "MSYS2",
                "Dev-C++",
                "VS Code",
                "Git",
                "Sysinternals Suite"
            ],
            "AI Agent Builder": [
                "Python 3.14",
                "VS Code",
                "Git",
                "lazygit",
                "Everything"
            ]
        }

# Backup & Settings Restore Path Configuration
BACKUP_PATHS: Dict[str, str] = {
    "VS Code Settings": os.path.join(os.environ.get("APPDATA", ""), "Code", "User"),
    "Gemini CLI / Antigravity Rules": os.path.join(os.path.expanduser("~"), ".gemini"),
    "Antigravity Settings": os.path.join(os.environ.get("APPDATA", ""), "Antigravity"),
    "Cursor Settings": os.path.join(os.environ.get("APPDATA", ""), "Cursor", "User"),
    "Windsurf Settings": os.path.join(os.environ.get("APPDATA", ""), "Windsurf", "User"),
    "Warp Config": os.path.join(os.path.expanduser("~"), ".warp"),
}

BACKUP_EXCLUDE_DIRS = {
    "Cache",
    "cache",
    "node_modules",
    ".git",
    "Cache_Data",
    "chat-plans",
}

ANTIGRAVITY_EXTENSIONS_PATH = os.path.join(
    os.environ.get("APPDATA", ""), "Antigravity", "CachedExtensionVSIXs"
)

