import os
import queue
import shutil
import subprocess
import threading
import webbrowser
import zipfile
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import tkinter as tk
from tkinter import ttk

"""
DevTools Installer - Developer Tools Management Application
==============================================================
Main Features:
- Tool installation via winget
- Settings backup and restore
- Predefined environment stacks (Python, React, C/Systems, etc.)
- Check for installed tools
- Export/Import selection to JSON

Author: Christos Kataxenos
Version: 2.1
"""

TOOL_STATUS = {
    "PENDING": "⚪",
    "INSTALLED": "🟢",
    "RUNNING": "🔵",
    "ERROR": "🔴",
}

TOOLS_REGISTRY: Dict[str, Dict[str, Dict[str, str]]] = {
    "Browsers": {
        "Google Chrome": {
            "id": "Google.Chrome",
            "url": "https://www.google.com/chrome/",
            "note": "Ο πιο δημοφιλής περιηγητής ιστού από την Google."
        },
        "Mozilla Firefox": {
            "id": "Mozilla.Firefox",
            "url": "https://www.mozilla.org/firefox/",
            "note": "Περιηγητής ιστού με έμφαση στην ιδιωτικότητα και τον ανοιχτό κώδικα."
        },
        "Brave Browser": {
            "id": "Brave.Brave",
            "url": "https://brave.com/",
            "note": "Περιηγητής που εστιάζει στην ταχύτητα και τον αποκλεισμό διαφημίσεων."
        },
        "Vivaldi Browser": {
            "id": "Vivaldi.Vivaldi",
            "url": "https://vivaldi.com/",
            "note": "Ευρωπαϊκός περιηγητής με απαράμιλλη δυνατότητα παραμετροποίησης."
        },
    },
    "Office & Documents": {
        "Microsoft 365": {
            "id": "Microsoft.Office",
            "url": "https://www.office.com/",
            "note": "Η σουίτα εφαρμογών γραφείου της Microsoft (Word, Excel, κλπ)."
        },
        "Apache OpenOffice": {
            "id": "Apache.OpenOffice",
            "url": "https://www.openoffice.org/",
            "note": "Κλασική ανοιχτού κώδικα σουίτα εφαρμογών γραφείου."
        },
        "LibreOffice": {
            "id": "TheDocumentFoundation.LibreOffice",
            "url": "https://www.libreoffice.org/",
            "note": "Η πιο ισχυρή δωρεάν και ανοιχτού κώδικα σουίτα γραφείου."
        },
        "ONLYOFFICE": {
            "id": "ONLYOFFICE.DesktopEditors",
            "url": "https://www.onlyoffice.com/",
            "note": "Ευρωπαϊκή σουίτα γραφείου με υψηλή συμβατότητα με αρχεία MS Office."
        },
    },
    "Communication": {
        "Discord": {
            "id": "Discord.Discord",
            "url": "https://discord.com/",
            "note": "Πλατφόρμα επικοινωνίας για κοινότητες και gamers."
        },
        "WhatsApp": {
            "id": "WhatsApp.WhatsApp",
            "url": "https://www.whatsapp.com/",
            "note": "Δημοφιλής εφαρμογή για μηνύματα και κλήσεις."
        },
        "Telegram": {
            "id": "Telegram.TelegramDesktop",
            "url": "https://telegram.org/",
            "note": "Γρήγορη και ασφαλής εφαρμογή μηνυμάτων, ευρωπαϊκής προέλευσης."
        },
        "Element": {
            "id": "Element.Element",
            "url": "https://element.io/",
            "note": "Ανοιχτού κώδικα εφαρμογή επικοινωνίας βασισμένη στο πρωτόκολλο Matrix."
        },
        "Zoom": {
            "id": "Zoom.Zoom",
            "url": "https://zoom.us/",
            "note": "Πλατφόρμα για βιντεοκλήσεις και τηλεδιασκέψεις."
        },
        "Webex": {
            "id": "Cisco.Webex",
            "url": "https://www.webex.com/",
            "note": "Επαγγελματικό εργαλείο για συναντήσεις και συνεργασία."
        },
        "Slack": {
            "id": "SlackTechnologies.Slack",
            "url": "https://slack.com/",
            "note": "Η standard εφαρμογή επικοινωνίας για ομάδες εργασίας."
        },
        "Viber": {
            "id": "Rakuten.Viber",
            "url": "https://www.viber.com/",
            "note": "Δημοφιλής εφαρμογή για δωρεάν μηνύματα και κλήσεις παγκοσμίως."
        },
    },
    "Media & Entertainment": {
        "VLC media player": {
            "id": "VideoLAN.VLC",
            "url": "https://www.videolan.org/",
            "note": "Universal player για κάθε είδους αρχείο βίντεο και ήχου."
        },
        "Spotify": {
            "id": "Spotify.Spotify",
            "url": "https://www.spotify.com/",
            "note": "Η κορυφαία υπηρεσία streaming μουσικής."
        },
        "K-Lite Codec Pack": {
            "id": "CodecGuide.K-LiteCodecPack.Full",
            "url": "https://codecguide.com/",
            "note": "Συλλογή από codecs για αναπαραγωγή οποιασδήποτε ταινίας."
        },
        "Steam": {
            "id": "Valve.Steam",
            "url": "https://store.steampowered.com/",
            "note": "Η μεγαλύτερη πλατφόρμα διανομής παιχνιδιών."
        },
    },
    "System & Cloud": {
        "7-Zip": {
            "id": "7zip.7zip",
            "url": "https://www.7-zip.org/",
            "note": "Κορυφαίο εργαλείο για συμπίεση και αποσυμπίεση αρχείων."
        },
        "pCloud": {
            "id": "pCloudAG.pCloudDrive",
            "url": "https://www.pcloud.com/",
            "note": "Ασφαλής ευρωπαϊκή υπηρεσία cloud storage (Ελβετία)."
        },
        "Proton Drive": {
            "id": "Proton.ProtonDrive",
            "url": "https://proton.me/drive",
            "note": "Πλήρως κρυπτογραφημένο cloud storage από την Proton (Ελβετία)."
        },
        "Nextcloud Desktop": {
            "id": "Nextcloud.NextcloudDesktop",
            "url": "https://nextcloud.com/",
            "note": "Ανοιχτού κώδικα πλατφόρμα για προσωπικό cloud και συγχρονισμό."
        },
        "Google Earth Pro": {
            "id": "Google.EarthPro",
            "url": "https://www.google.com/earth/",
            "note": "Εξερευνήστε τον κόσμο με τρισδιάστατες δορυφορικές εικόνες."
        },
        "Everything": {
            "id": "voidtools.Everything",
            "url": "https://www.voidtools.com/",
            "note": "Άμεση αναζήτηση αρχείων στο σύστημα."
        },
    },
    "Privacy & Security": {
        "ProtonVPN": {
            "id": "Proton.ProtonVPN",
            "url": "https://protonvpn.com/",
            "note": "Ασφαλές και γρήγορο VPN από την Proton."
        },
        "Proton Mail": {
            "id": "Proton.ProtonMail",
            "url": "https://proton.me/mail",
            "note": "Η κορυφαία υπηρεσία κρυπτογραφημένου email παγκοσμίως."
        },
    },
    "IDEs & Editors": {
        "VS Code": {
            "id": "Microsoft.VisualStudioCode",
            "url": "https://code.visualstudio.com/",
            "note": "Ο πιο δημοφιλής open-source editor από την Microsoft."
        },
        "VS Code Insiders": {
            "id": "Microsoft.VisualStudioCode.Insiders",
            "url": "https://code.visualstudio.com/insiders/",
            "note": "Η έκδοση προεπισκόπησης του VS Code με νέες δυνατότητες."
        },
        "PyCharm Community": {
            "id": "JetBrains.PyCharm.Community",
            "url": "https://www.jetbrains.com/pycharm/",
            "note": "Πανίσχυρο IDE για Python ανάπτυξη."
        },
        "Android Studio": {
            "id": "Google.AndroidStudio",
            "url": "https://developer.android.com/studio",
            "note": "Το επίσημο IDE για ανάπτυξη εφαρμογών Android."
        },
        "Arduino IDE": {
            "id": "Arduino.IDE.2",
            "url": "https://www.arduino.cc/en/software",
            "note": "Περιβάλλον προγραμματισμού για Arduino και hardware."
        },
        "Notepad++": {
            "id": "Notepad++.Notepad++",
            "url": "https://notepad-plus-plus.org/",
            "note": "Ελαφρύς και ταχύτατος text editor."
        },
        "Dev-C++": {
            "id": "Embarcadero.Dev-CPP",
            "url": "https://sourceforge.net/projects/orwelldevcpp/",
            "note": "Κλασικό IDE για C/C++ (TDM-GCC)."
        },
    },
    "Version Control": {
        "Git": {
            "id": "Git.Git", 
            "url": "https://git-scm.com/",
            "note": "Το standard σύστημα ελέγχου εκδόσεων."
        },
        "GitHub Desktop": {
            "id": "GitHub.GitHubDesktop",
            "url": "https://desktop.github.com/",
            "note": "Γραφικό περιβάλλον για την διαχείριση Git repos."
        },
        "GitHub CLI (gh)": {
            "id": "GitHub.cli", 
            "url": "https://cli.github.com/",
            "note": "Εργαλείο γραμμής εντολών για το GitHub."
        },
        "lazygit": {
            "id": "JesseDuffield.lazygit",
            "url": "https://github.com/jesseduffield/lazygit",
            "note": "Τερματικό περιβάλλον (TUI) για Git."
        },
        "Git LFS": {
            "id": "GitHub.GitLFS",
            "url": "https://git-lfs.github.com/",
            "note": "Διαχείριση μεγάλων αρχείων στο Git."
        },
    },
    "Runtimes & Languages": {
        "Node.js (LTS)": {
            "id": "OpenJS.NodeJS.LTS", 
            "url": "https://nodejs.org/",
            "note": "JavaScript runtime για server-side ανάπτυξη."
        },
        "Python 3.14": {
            "id": "Python.Python.3.14", 
            "url": "https://www.python.org/",
            "note": "Η τελευταία έκδοση της γλώσσας Python."
        },
        "Go": {
            "id": "Google.Go", 
            "url": "https://go.dev/",
            "note": "Η γλώσσα προγραμματισμού της Google."
        },
        "TDM-GCC": {
            "id": "jmeubank.tdm-gcc",
            "url": "https://jmeubank.github.io/tdm-gcc/",
            "note": "Compiler suite για C/C++ στα Windows."
        },
        "MSYS2": {
            "id": "MSYS2.MSYS2", 
            "url": "https://www.msys2.org/",
            "note": "Περιβάλλον Unix-like για Windows ανάπτυξη."
        },
        "Rust (rustup)": {
            "id": "Rustlang.Rustup",
            "url": "https://rustup.rs/",
            "note": "Installer για την γλώσσα Rust."
        },
        "Zig": {
            "id": "zig.zig", 
            "url": "https://ziglang.org/",
            "note": "Σύγχρονη και ασφαλής γλώσσα επιπέδου συστήματος."
        },
        "Bun": {
            "id": "Oven-sh.Bun", 
            "url": "https://bun.sh/",
            "note": "Ταχύτατο JavaScript runtime & package manager."
        },
        "Deno": {
            "id": "DenoLand.Deno", 
            "url": "https://deno.land/",
            "note": "Ασφαλές runtime για JavaScript και TypeScript."
        },
        "Java 21 (Temurin)": {
            "id": "EclipseAdoptium.Temurin.21.JDK",
            "url": "https://adoptium.net/",
            "note": "Open source διανομή της Java (JDK)."
        },
    },
    "Package Managers": {
        "Chocolatey": {
            "id": "Chocolatey.Chocolatey", 
            "url": "https://chocolatey.org/",
            "note": "Package manager για Windows παρόμοιο με το apt."
        },
        "uv (Fast Python)": {
            "id": "astral-sh.uv",
            "url": "https://github.com/astral-sh/uv",
            "note": "Ταχύτατος Python package & project manager."
        },
        "pnpm": {
            "id": "pnpm.pnpm", 
            "url": "https://pnpm.io/",
            "note": "Αποδοτικός Node package manager με symlinks."
        },
    },
    "Database Tools": {
        "DB Browser (SQLite)": {
            "id": "DBBrowserForSQLite.DBBrowserForSQLite",
            "url": "https://sqlitebrowser.org/",
            "note": "Γραφικό περιβάλλον για βάσεις δεδομένων SQLite."
        },
        "DBeaver Community": {
            "id": "dbeaver.dbeaver", 
            "url": "https://dbeaver.io/",
            "note": "Universal database manager για όλες τις βάσεις."
        },
    },
    "Virtualization": {
        "Docker Desktop": {
            "id": "Docker.DockerDesktop",
            "url": "https://www.docker.com/",
            "note": "Διαχείριση containers για ανάπτυξη εφαρμογών."
        },
        "VMware Player": {
            "id": "VMware.WorkstationPlayer",
            "url": "https://www.vmware.com/",
            "note": "Δωρεάν virtualization για εκτέλεση εικονικών μηχανών."
        },
        "WSL": {
            "id": "Microsoft.WSL",
            "url": "https://learn.microsoft.com/en-us/windows/wsl/",
            "note": "Υποσύστημα Linux μέσα στα Windows."
        },
    },
    "Hardware & AI": {
        "Raspberry Pi Imager": {
            "id": "RaspberryPi.RaspberryPiImager",
            "url": "https://www.raspberrypi.com/software/",
            "note": "Εργαλείο εγγραφής OS σε SD κάρτες για Raspberry Pi."
        },
        "Logisim Evolution": {
            "id": "Logisim-Evolution.Logisim-Evolution",
            "url": "https://github.com/logisim-evolution/logisim-evolution",
            "note": "Προσομοιωτής ψηφιακών κυκλωμάτων."
        },
        "LM Studio": {
            "id": "LMStudio.LMStudio", 
            "url": "https://lmstudio.ai/",
            "note": "Τοπική εκτέλεση μεγάλων γλωσσικών μοντέλων (LLMs)."
        },
    },
    "System & Shell": {
        "Windows Terminal": {
            "id": "Microsoft.WindowsTerminal",
            "url": "https://aka.ms/terminal",
            "note": "Σύγχρονο τερματικό για command line εργαλεία."
        },
        "Oh My Posh": {
            "id": "JanDeDobbeleer.OhMyPosh", 
            "url": "https://ohmyposh.dev/",
            "note": "Engine για πανέμορφα prompt στα shells."
        },
        "zoxide": {
            "id": "ajeetdsouza.zoxide",
            "url": "https://github.com/ajeetdsouza/zoxide",
            "note": "Έξυπνη εντολή cd που μαθαίνει τις συνήθειές σας."
        },
        "PowerShell 7": {
            "id": "Microsoft.PowerShell",
            "url": "https://github.com/PowerShell/PowerShell",
            "note": "Η τελευταία έκδοση του PowerShell."
        },
        "PuTTY": {
            "id": "PuTTY.PuTTY", 
            "url": "https://www.putty.org/",
            "note": "SSH και Telnet client για Windows."
        },
        "fastfetch": {
            "id": "fastfetch-cli.fastfetch",
            "url": "https://github.com/fastfetch-cli/fastfetch",
            "note": "Εργαλείο πληροφοριών συστήματος."
        },
        "FileZilla": {
            "id": "FileZilla.FileZilla",
            "url": "https://filezilla-project.org/",
            "note": "Κλασικός FTP/SFTP client."
        },
        "Warp Terminal": {
            "id": "Warp.Warp",
            "url": "https://www.warp.dev/",
            "note": "Σύγχρονο AI-powered τερματικό."
        },
        "Starship Prompt": {
            "id": "Starship.Starship",
            "url": "https://starship.rs/",
            "note": "Customizable και γρήγορο shell prompt."
        },
        "bat": {
            "id": "sharkdp.bat",
            "url": "https://github.com/sharkdp/bat",
            "note": "Βελτιωμένη έκδοση της εντολής cat με syntax highlighting."
        },
        "ripgrep": {
            "id": "BurntSushi.ripgrep.MSVC",
            "url": "https://github.com/BurntSushi/ripgrep",
            "note": "Ταχύτατη αναζήτηση κειμένου σε αρχεία."
        },
        "fd": {
            "id": "sharkdp.fd",
            "url": "https://github.com/sharkdp/fd",
            "note": "Γρήγορη και φιλική εναλλακτική της εντολής find."
        },
        "fzf": {
            "id": "junegunn.fzf",
            "url": "https://github.com/junegunn/fzf",
            "note": "Fuzzy finder για την γραμμή εντολών."
        },
        "tldr": {
            "id": "tldr-pages.tlrc",
            "url": "https://tldr.sh/",
            "note": "Συνοπτικά help pages για εντολές τερματικού."
        },
    },
    "AI Coding Assistants": {
        "Claude Code (CLI)": {
            "id": "Anthropic.ClaudeCode",
            "url": "https://claude.com/claude-code",
            "note": "Agentic τερματικό για AI-assisted προγραμματισμό."
        },
        "Cursor IDE": {
            "id": "Anysphere.Cursor",
            "url": "https://cursor.sh/",
            "note": "AI-first editor, βασισμένος στον VS Code."
        },
        "Windsurf IDE": {
            "id": "Codeium.Windsurf",
            "url": "https://codeium.com/windsurf",
            "note": "Agentic IDE από την ομάδα του Codeium."
        },
        "OpenCode": {
            "id": "SST.opencode",
            "url": "https://opencode.ai/",
            "note": "AI coding agent για το τερματικό."
        },
        "Gemini CLI": {
            "id": "npm install -g @google/gemini-cli",
            "url": "https://github.com/google/gemini-cli",
            "note": "CLI για το μοντέλο Gemini της Google."
        },
        "GitHub Copilot": {
            "id": "gh extension install github/gh-copilot",
            "url": "https://github.com/github/copilot-cli",
            "note": "Extension για το GitHub CLI."
        },
    },
    "Productivity": {
        "PowerToys": {
            "id": "Microsoft.PowerToys", 
            "url": "https://aka.ms/powertoys",
            "note": "Σχρήσιμα utilities για Windows power users."
        },
        "Fira Code Font": {
            "id": "SoftwareDesign.FiraCode",
            "url": "https://github.com/tonsky/FiraCode",
            "note": "Γραμματοσειρά με προγραμματιστικά ligatures."
        },
        "Notion": {
            "id": "Notion.Notion", 
            "url": "https://www.notion.so/",
            "note": "Πλατφόρμα οργάνωσης σημειώσεων και tasks."
        },
        "Obsidian": {
            "id": "Obsidian.Obsidian", 
            "url": "https://obsidian.md/",
            "note": "Εργαλείο διαχείρισης γνώσης με Markdown."
        },
        "Flameshot": {
            "id": "Flameshot.Flameshot",
            "url": "https://flameshot.org/",
            "note": "Ευέλικτο εργαλείο για screenshots."
        },
    },
    "Remote": {
        "AnyDesk": {
            "id": "AnyDeskSoftwareGmbH.AnyDesk", 
            "url": "https://anydesk.com/",
            "note": "Εφαρμογή απομακρυσμένης επιφάνειας εργασίας."
        },
        "RealVNC Viewer": {
            "id": "RealVNC.VNCViewer",
            "url": "https://www.realvnc.com/",
            "note": "Viewer για συνδέσεις VNC."
        },
        "RustDesk": {
            "id": "RustDesk.RustDesk", 
            "url": "https://rustdesk.com/",
            "note": "Open source εναλλακτική του AnyDesk/TeamViewer."
        },
        "TeamViewer": {
            "id": "TeamViewer.TeamViewer",
            "url": "https://www.teamviewer.com/",
            "note": "Επαγγελματική απομακρυσμένη πρόσβαση και υποστήριξη."
        },
    },
    "Design & Media": {
        "Figma": {
            "id": "Figma.Figma", 
            "url": "https://www.figma.com/",
            "note": "Εργαλείο design για UI/UX επαγγελματίες."
        },
        "DaVinci Resolve": {
            "id": "BlackmagicDesign.DaVinciResolve",
            "url": "https://www.blackmagicdesign.com/",
            "note": "Κορυφαίο πρόγραμμα video editing & color grading."
        },
        "OBS Studio": {
            "id": "OBSProject.OBSStudio", 
            "url": "https://obsproject.com/",
            "note": "Λογισμικό για live streaming και εγγραφή οθόνης."
        },
        "Adobe Cloud": {
            "id": "Adobe.CreativeCloud", 
            "url": "https://www.adobe.com/",
            "note": "Πρόσβαση στις εφαρμογές της Adobe (Photoshop, κλπ)."
        },
    },
    "C & Systems Dev": {
        "CMake": {
            "id": "Kitware.CMake", 
            "url": "https://cmake.org/",
            "note": "Standard εργαλείο build automation για C/C++."
        },
        "Ninja": {
            "id": "ninja-build.ninja", 
            "url": "https://ninja-build.org/",
            "note": "Ταχύτατο build system με έμφαση στην ταχύτητα."
        },
        "LLVM / Clang": {
            "id": "LLVM.LLVM", 
            "url": "https://llvm.org/",
            "note": "Σύγχρονο compiler infrastructure."
        },
        "Make (GnuWin32)": {
            "id": "GnuWin32.Make",
            "url": "http://gnuwin32.sourceforge.net/",
            "note": "Το κλασικό εργαλείο Make για Windows."
        },
    },
    "API & Testing": {
        "Postman": {
            "id": "Postman.Postman", 
            "url": "https://www.postman.com/",
            "note": "Η κορυφαία πλατφόρμα για ανάπτυξη και δοκιμή APIs."
        },
        "Bruno": {
            "id": "Bruno.Bruno", 
            "url": "https://www.usebruno.com/",
            "note": "Open-source, local-first API client (ελαφρύς)."
        },
        "Insomnia": {
            "id": "Insomnia.Insomnia", 
            "url": "https://insomnia.rest/",
            "note": "Σχεδιασμός και δοκιμή REST, GraphQL, gRPC APIs."
        },
    },
    "Security & Networking": {
        "Wireshark": {
            "id": "WiresharkFoundation.Wireshark",
            "url": "https://www.wireshark.org/",
            "note": "Αναλυτής πακέτων δικτύου (packet sniffer)."
        },
        "Nmap": {
            "id": "Insecure.Nmap", 
            "url": "https://nmap.org/",
            "note": "Εργαλείο ανακάλυψης δικτύου και ελέγχου ασφαλείας."
        },
        "Burp Suite Community": {
            "id": "manual",
            "url": "https://portswigger.net/burp/communitydownload",
            "note": "Manual λήψη: Εργαλείο ελέγχου ασφαλείας web εφαρμογών."
        },
    },
    "Cloud & DevOps": {
        "Kubectl": {
            "id": "Kubernetes.kubectl",
            "url": "https://kubernetes.io/docs/tasks/tools/",
            "note": "CLI για την διαχείριση clusters Kubernetes."
        },
        "Terraform": {
            "id": "Hashicorp.Terraform",
            "url": "https://www.terraform.io/",
            "note": "Infrastructure as Code (IaC) από την HashiCorp."
        },
        "Azure CLI": {
            "id": "Microsoft.AzureCLI",
            "url": "https://docs.microsoft.com/en-us/cli/azure/install-azure-cli",
            "note": "Εργαλείο γραμμής εντολών για το Microsoft Azure."
        },
    },
}

STACKS = {
    "Fresh Windows Kit": [
        "Google Chrome",
        "7-Zip",
        "VLC media player",
        "Discord",
        "Spotify",
        "Microsoft 365",
        "WhatsApp",
    ],
    "React / Web": [
        "Node.js (LTS)",
        "pnpm",
        "VS Code",
        "Git",
        "GitHub CLI (gh)",
        "Figma",
        "Windows Terminal",
    ],
    "Python / AI": [
        "Python 3.14",
        "uv (Fast Python)",
        "PyCharm Community",
        "Docker Desktop",
        "LM Studio",
    ],
    "Data Analysis": [
        "Python 3.14",
        "uv (Fast Python)",
        "DBeaver Community",
        "Git",
    ],
    "C / Systems": [
        "Git",
        "CMake",
        "Ninja",
        "LLVM / Clang",
        "Dev-C++",
        "MSYS2",
        "WSL",
        "Windows Terminal",
    ],
    "Core Utils": [
        "Git",
        "Windows Terminal",
        "Oh My Posh",
        "zoxide",
        "PowerToys",
        "Fira Code Font",
        "Everything",
    ],
    "AI Coding": [
        "Claude Code (CLI)",
        "Cursor IDE",
        "OpenCode",
        "Git",
        "GitHub CLI (gh)",
        "Windows Terminal",
        "Python 3.14",
        "uv (Fast Python)",
    ],
    "Full Stack Web": [
        "Node.js (LTS)",
        "Bun",
        "pnpm",
        "VS Code",
        "Git",
        "GitHub CLI (gh)",
        "Docker Desktop",
        "Bruno",
        "Figma",
        "Windows Terminal",
    ],
    "DevOps / Cloud": [
        "Docker Desktop",
        "Kubectl",
        "Terraform",
        "Azure CLI",
        "Git",
        "Windows Terminal",
        "WSL",
    ],
}

BACKUP_PATHS: Dict[str, str] = {
    "VS Code Settings": os.path.join(os.environ.get("APPDATA", ""), "Code", "User"),
    "Gemini CLI Data": os.path.join(os.path.expanduser("~"), ".gemini"),
    "Antigravity Settings": os.path.join(os.environ.get("APPDATA", ""), "Antigravity"),
    "Cursor Settings": os.path.join(os.environ.get("APPDATA", ""), "Cursor", "User"),
    "Windsurf Settings": os.path.join(
        os.environ.get("APPDATA", ""), "Windsurf", "User"
    ),
    "Warp Config": os.path.join(os.path.expanduser("~"), ".warp"),
}


class ThemeManager:
    """
    Theme Manager - Central color management
    ========================================
    Supports theme switching (light/dark)
    and easy color modification.
    """

    _themes = {
        "dark": {
            "bg": "#0a0a0a",
            "card_bg": "#161616",
            "card_hover": "#1e1e1e",
            "accent": "#007acc",
            "accent_hover": "#0098ff",
            "text": "#e0e0e0",
            "text_dim": "#888888",
            "border": "#333333",
            "sidebar_bg": "#121212",
            "success": "#4caf50",
            "warning": "#ff9800",
            "error": "#f44336",
        },
        "light": {
            "bg": "#f5f5f5",
            "card_bg": "#ffffff",
            "card_hover": "#e8e8e8",
            "accent": "#0078d4",
            "accent_hover": "#106ebe",
            "text": "#1a1a1a",
            "text_dim": "#666666",
            "border": "#d0d0d0",
            "sidebar_bg": "#f0f0f0",
            "success": "#28a745",
            "warning": "#ffc107",
            "error": "#dc3545",
        },
    }

    _current_theme = "dark"

    @classmethod
    def get_colors(cls) -> Dict[str, str]:
        """Returns the colors of the current theme."""
        return cls._themes[cls._current_theme].copy()

    @classmethod
    def set_theme(cls, theme_name: str):
        """Sets the current theme."""
        if theme_name in cls._themes:
            cls._current_theme = theme_name

    @classmethod
    def get_current_theme(cls) -> str:
        """Returns the name of the current theme."""
        return cls._current_theme


COLORS = ThemeManager.get_colors()

FONTS = {
    "title": ("Segoe UI Semibold", 18),
    "header": ("Segoe UI", 12, "bold"),
    "body": ("Segoe UI", 9),
    "mono": ("Cascadia Code", 8),
    "small": ("Segoe UI", 7),
    "button": ("Segoe UI", 9, "bold"),
}


class GradientButton(tk.Canvas):
    def __init__(
        self,
        parent,
        text,
        command,
        width=200,
        height=36,
        gradient=("#007acc", "#5b4cf5"),
        **kwargs,
    ):
        super().__init__(
            parent,
            width=width,
            height=height,
            highlightthickness=0,
            bg=COLORS["sidebar_bg"],
            **kwargs,
        )
        self.command = command
        self.text = text
        self.gradient = gradient
        self.hovered = False
        self.enabled = True

        self._draw_button()

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        self.bind("<Configure>", lambda e: self._draw_button())

    def _draw_button(self):
        self.delete("all")
        color = self.gradient[0] if self.enabled else "#444444"
        self._rounded_rect(
            2, 2, self.winfo_width() - 2, self.winfo_height() - 2, 8, fill=color
        )
        self.create_text(
            self.winfo_width() // 2,
            self.winfo_height() // 2,
            text=self.text,
            fill="white",
            font=FONTS["button"],
        )

    def _rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):
        """Draws a rounded rectangle using arcs and rectangles."""
        fill = kwargs.pop("fill", None)
        outline = kwargs.pop("outline", "")
        
        try:
            # Arcs for corners
            self.create_arc(x1, y1, x1 + 2 * radius, y1 + 2 * radius, 
                           start=90, extent=90, fill=fill, outline=outline, **kwargs)
            self.create_arc(x2 - 2 * radius, y1, x2, y1 + 2 * radius, 
                           start=0, extent=90, fill=fill, outline=outline, **kwargs)
            self.create_arc(x1, y2 - 2 * radius, x1 + 2 * radius, y2, 
                           start=180, extent=90, fill=fill, outline=outline, **kwargs)
            self.create_arc(x2 - 2 * radius, y2 - 2 * radius, x2, y2, 
                           start=270, extent=90, fill=fill, outline=outline, **kwargs)
        except Exception:
            # Fallback to plain rectangle if arcs fail (e.g. radius too large)
            self.create_rectangle(x1, y1, x2, y2, fill=fill, outline=outline, **kwargs)
            return

        # Rectangles for the middle
        self.create_rectangle(x1 + radius, y1, x2 - radius, y2, fill=fill, outline=outline, **kwargs)
        self.create_rectangle(x1, y1 + radius, x2, y2 - radius, fill=fill, outline=outline, **kwargs)

    def _on_enter(self, event):
        if self.enabled:
            self.hovered = True
            self._draw_button()

    def _on_leave(self, event):
        self.hovered = False
        self._draw_button()

    def _on_click(self, event):
        if self.enabled:
            self.command()

    def set_enabled(self, enabled):
        self.enabled = enabled
        self._draw_button()


class ToggleSwitch(tk.Frame):
    def __init__(self, parent, command=None, **kwargs):
        super().__init__(parent, bg=COLORS["card_bg"], **kwargs)
        self.command = command
        self.var = tk.BooleanVar(value=False)

        self.canvas = tk.Canvas(
            self, width=44, height=24, highlightthickness=0, bg=COLORS["card_bg"]
        )
        self.canvas.pack(pady=2)

        self._draw()
        self.canvas.bind("<Button-1>", self._toggle)
        self.canvas.bind("<Configure>", lambda e: self._draw())

    def _draw(self):
        self.canvas.delete("all")
        w = self.canvas.winfo_width() if self.canvas.winfo_width() > 1 else 44
        h = self.canvas.winfo_height() if self.canvas.winfo_height() > 1 else 24
        
        # Center the toggle in the canvas
        r = min(w, h) - 4
        bg = COLORS["accent"] if self.var.get() else COLORS["border"]
        
        # Draw track
        self._rounded_rect(2, 4, w-2, h-4, 8, fill=bg, outline="")
        
        # Draw knob
        knob_pos = w - h + 2 if self.var.get() else 2
        self.canvas.create_oval(knob_pos, 2, knob_pos + h - 4, h - 2, fill="white", outline="")

    def _rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):
        self.canvas.create_arc(x1, y1, x1+2*radius, y1+2*radius, start=90, extent=90, **kwargs)
        self.canvas.create_arc(x2-2*radius, y1, x2, y1+2*radius, start=0, extent=90, **kwargs)
        self.canvas.create_arc(x1, y2-2*radius, x1+2*radius, y2, start=180, extent=90, **kwargs)
        self.canvas.create_arc(x2-2*radius, y2-2*radius, x2, y2, start=270, extent=90, **kwargs)
        self.canvas.create_rectangle(x1+radius, y1, x2-radius, y2, **kwargs)
        self.canvas.create_rectangle(x1, y1+radius, x2, y2-radius, **kwargs)

    def _toggle(self, event=None):
        self.var.set(not self.var.get())
        self._draw()
        if self.command:
            self.command()

    def get(self):
        return self.var.get()

    def set(self, value):
        self.var.set(value)
        self._draw()


class CategoryButton(tk.Frame):
    """Modern sidebar button with active state indicator."""
    def __init__(self, parent, text, command, **kwargs):
        super().__init__(parent, bg=COLORS["sidebar_bg"], **kwargs)
        self.command = command
        self.text = text
        self.active = False
        
        self.canvas = tk.Canvas(self, height=40, highlightthickness=0, bg=COLORS["sidebar_bg"])
        self.canvas.pack(fill="x")
        
        self.indicator = None
        self.text_id = None
        
        self.canvas.bind("<Enter>", self._on_enter)
        self.canvas.bind("<Leave>", self._on_leave)
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Configure>", lambda e: self._draw())

    def _draw(self):
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        
        bg = COLORS["card_hover"] if self.active else self.canvas.cget("bg")
        indicator_color = COLORS["accent"] if self.active else COLORS["sidebar_bg"]
        text_color = "white" if self.active else COLORS["text"]
        
        # We handle hover bg via config(bg=...) in events, but redraw ensures state is correct
        self.indicator = self.canvas.create_rectangle(0, 4, 4, h-4, fill=indicator_color, outline="")
        self.text_id = self.canvas.create_text(20, h // 2, text=self.text, fill=text_color, anchor="w", font=FONTS["body"])

    def _on_enter(self, e):
        if not self.active:
            self.canvas.config(bg=COLORS["card_hover"])
            self._draw()

    def _on_leave(self, e):
        if not self.active:
            self.canvas.config(bg=COLORS["sidebar_bg"])
            self._draw()

    def _on_click(self, e):
        self.command()

    def set_active(self, active):
        self.active = active
        self._draw()


class RoundedEntry(tk.Frame):
    def __init__(self, parent, placeholder="", width=250, **kwargs):
        super().__init__(parent, bg=COLORS["card_bg"], **kwargs)
        self.placeholder = placeholder

        self.canvas = tk.Canvas(
            self, width=width, height=36, highlightthickness=0, bg=COLORS["card_bg"]
        )
        self.canvas.pack(fill="x", expand=True)

        self.entry = tk.Entry(
            self.canvas,
            bg=COLORS["card_bg"],
            fg=COLORS["text"],
            font=FONTS["body"],
            insertbackground=COLORS["text"],
            relief="flat",
            bd=0,
        )
        
        self.canvas.bind("<Configure>", self._draw)
        
        if placeholder:
            self.entry.insert(0, placeholder)
            self.entry.config(fg=COLORS["text_dim"])
            self.entry.bind("<FocusIn>", self._on_focus_in)
            self.entry.bind("<FocusOut>", self._on_focus_out)

    def _draw(self, event=None):
        self.canvas.delete("all")
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        
        self._rounded_rect(
            1, 1, w - 2, h - 2, 8, fill=COLORS["card_bg"], outline=COLORS["border"]
        )
        
        self.entry.place(x=12, y=h // 2, anchor="w", width=w - 24)

    def _rounded_rect(self, x1, y1, x2, y2, radius, **kwargs):
        try:
            self.canvas.create_arc(x1, y1, x1 + 2 * radius, y1 + 2 * radius, start=90, extent=90, **kwargs)
            self.canvas.create_arc(x2 - 2 * radius, y1, x2, y1 + 2 * radius, start=0, extent=90, **kwargs)
            self.canvas.create_arc(x1, y2 - 2 * radius, x1 + 2 * radius, y2, start=180, extent=90, **kwargs)
            self.canvas.create_arc(x2 - 2 * radius, y2 - 2 * radius, x2, y2, start=270, extent=90, **kwargs)
        except Exception:
            self.canvas.create_rectangle(x1, y1, x2, y2, **kwargs)
        self.canvas.create_rectangle(x1 + radius, y1, x2 - radius, y2, **kwargs)
        self.canvas.create_rectangle(x1, y1 + radius, x2, y2 - radius, **kwargs)

    def _on_focus_in(self, e):
        if self.entry.get() == self.placeholder:
            self.entry.delete(0, "end")
            self.entry.config(fg=COLORS["text"])

    def _on_focus_out(self, e):
        if not self.entry.get():
            self.entry.insert(0, self.placeholder)
            self.entry.config(fg=COLORS["text_dim"])

    def get(self):
        val = self.entry.get()
        return "" if val == self.placeholder else val

    def set(self, value):
        self.entry.delete(0, "end")
        self.entry.insert(0, value)


class StyledButton(tk.Canvas):
    def __init__(
        self, parent, text, command, primary=True, width=140, height=32, **kwargs
    ):
        super().__init__(
            parent,
            width=width,
            height=height,
            highlightthickness=0,
            bg=COLORS["sidebar_bg"],
            **kwargs,
        )
        self.command = command
        self.text = text
        self.primary = primary
        self.hovered = False
        self.enabled = True

        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        self.bind("<Button-1>", self._on_click)
        self.bind("<Configure>", lambda e: self._draw())

    def _draw(self):
        self.delete("all")
        w = self.winfo_width()
        h = self.winfo_height()
        
        bg_color = COLORS["accent"] if self.primary else COLORS["border"]
        if self.hovered and self.enabled:
            bg_color = COLORS["accent_hover"] if self.primary else "#444444"
        
        if not self.enabled:
            bg_color = "#333333" if self.primary else "#222222"

        self.rounded_rect(2, 2, w - 2, h - 2, radius=6, fill=bg_color, tags="bg")
        self.create_text(
            w // 2,
            h // 2,
            text=self.text,
            fill="white" if self.enabled else "#888888",
            font=FONTS["button"],
            tags="text",
        )

    def rounded_rect(self, x1, y1, x2, y2, radius, fill, **kwargs):
        self.create_arc(x1, y1, x1 + 2 * radius, y1 + 2 * radius, start=90, extent=90, fill=fill, outline="", **kwargs)
        self.create_arc(x2 - 2 * radius, y1, x2, y1 + 2 * radius, start=0, extent=90, fill=fill, outline="", **kwargs)
        self.create_arc(x1, y2 - 2 * radius, x1 + 2 * radius, y2, start=180, extent=90, fill=fill, outline="", **kwargs)
        self.create_arc(x2 - 2 * radius, y2 - 2 * radius, x2, y2, start=270, extent=90, fill=fill, outline="", **kwargs)
        self.create_rectangle(x1 + radius, y1, x2 - radius, y2, fill=fill, outline="", **kwargs)
        self.create_rectangle(x1, y1 + radius, x2, y2 - radius, fill=fill, outline="", **kwargs)

    def _on_enter(self, event):
        if self.enabled:
            self.hovered = True
            self._draw()

    def _on_leave(self, event):
        if self.enabled:
            self.hovered = False
            self._draw()

    def _on_click(self, event):
        if self.enabled:
            self.command()

    def set_enabled(self, enabled):
        self.enabled = enabled
        self._draw()


class ScrollableFrame(tk.Frame):
    """
    A reusable scrollable container.
    =================================
    Uses a Canvas to allow scrolling of
    a Frame containing widgets.
    """
    def __init__(self, parent, **kwargs):
        bg = kwargs.pop("bg", COLORS["bg"])
        width = kwargs.pop("width", None)
        super().__init__(parent, bg=bg, **kwargs)

        self.canvas = tk.Canvas(self, bg=bg, highlightthickness=0, width=width)
        self.scrollbar = ttk.Scrollbar(self, orient="vertical", command=self.canvas.yview)
        self.scrollable_frame = tk.Frame(self.canvas, bg=bg, width=width)

        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        )

        self.canvas_window = self.canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")

        self.canvas.configure(yscrollcommand=self.scrollbar.set)

        self.canvas.pack(side="left", fill="both", expand=True)
        self.scrollbar.pack(side="right", fill="y")

        self.canvas.bind("<Configure>", self._on_canvas_configure)
        
        # Mouse wheel support - Use add="+" to avoid clobbering other bindings
        self.canvas.bind_all("<MouseWheel>", self._on_mousewheel, add="+")

    def _on_canvas_configure(self, event):
        # Update the width of the inner frame to match the canvas
        self.canvas.itemconfig(self.canvas_window, width=event.width)

    def _on_mousewheel(self, event):
        # Only scroll if this specific instance is mapped (visible in the UI)
        if not self.winfo_ismapped():
            return
            
        # Check if the mouse is actually over this widget or its children
        x, y = self.winfo_pointerxy()
        target = self.winfo_containing(x, y)
        
        # If target is None or not a descendant of this widget, don't scroll
        is_descendant = False
        curr = target
        while curr:
            if curr == self:
                is_descendant = True
                break
            try:
                curr = self.nametowidget(curr.winfo_parent())
            except:
                break
        
        if is_descendant:
            self.canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")


class ToolCard(tk.Frame):
    def __init__(self, parent, name, details, on_toggle, on_link, **kwargs):
        super().__init__(parent, bg=COLORS["card_bg"], relief="flat", bd=0, **kwargs)
        self.name = name
        self.details = details
        self.on_toggle = on_toggle
        self.on_link = on_link
        self._hovered = False
        self._selected = False
        self._status = "PENDING"
        self.visible = True

        self.config(highlightbackground=COLORS["border"], highlightthickness=1, bd=0)

        # Using grid for internal layout
        self.columnconfigure(0, weight=1)
        self.rowconfigure(3, weight=1)

        # Top Section: Name and Icons
        self.header_frame = tk.Frame(self, bg=COLORS["card_bg"])
        self.header_frame.grid(row=0, column=0, sticky="ew", padx=10, pady=(10, 5))
        self.header_frame.columnconfigure(0, weight=1)

        self.name_label = tk.Label(
            self.header_frame,
            text=name,
            bg=COLORS["card_bg"],
            fg=COLORS["text"],
            font=FONTS["body"],
            anchor="w"
        )
        self.name_label.grid(row=0, column=0, sticky="w")

        self.link_btn = tk.Button(
            self.header_frame,
            text="↗",
            command=lambda: self.on_link(self.details["url"]),
            bg=COLORS["card_bg"],
            fg=COLORS["text_dim"],
            relief="flat",
            font=("Segoe UI", 11),
            cursor="hand2",
            bd=0,
            padx=4,
        )
        self.link_btn.grid(row=0, column=1, sticky="e")

        # Middle Section: ID and Note
        self.id_label = tk.Label(
            self,
            text=f"ID: {details['id']}",
            bg=COLORS["card_bg"],
            fg=COLORS["text_dim"],
            font=FONTS["small"],
            anchor="w"
        )
        self.id_label.grid(row=1, column=0, sticky="w", padx=10, pady=(0, 2))

        if details.get("note"):
            self.note_label = tk.Label(
                self,
                text=details["note"],
                bg=COLORS["card_bg"],
                fg=COLORS["text_dim"],
                font=FONTS["small"],
                anchor="w",
                justify="left",
                wraplength=260
            )
            # Give the note room and ensure it breathes
            self.note_label.grid(row=2, column=0, sticky="w", padx=10, pady=(0, 15))
        else:
            # Spacer
            tk.Frame(self, bg=COLORS["card_bg"], height=10).grid(row=2, column=0)

        # Bottom Section: Toggle and Status
        self.actions_frame = tk.Frame(self, bg=COLORS["card_bg"])
        self.actions_frame.grid(row=3, column=0, sticky="sew", padx=10, pady=(0, 10))
        self.actions_frame.columnconfigure(1, weight=1)

        self.toggle = ToggleSwitch(self.actions_frame, command=self._on_check)
        self.toggle.grid(row=0, column=0, sticky="w")

        self.status_dot = tk.Label(
            self.actions_frame,
            text=TOOL_STATUS["PENDING"],
            bg=COLORS["card_bg"],
            fg=COLORS["text"],
            font=("Segoe UI", 10),
        )
        self.status_dot.grid(row=0, column=1, sticky="e")

        # Events
        self.bind("<Enter>", self._on_enter)
        self.bind("<Leave>", self._on_leave)
        for child in self.winfo_children():
            child.bind("<Enter>", self._on_enter)
            child.bind("<Leave>", self._on_leave)

    def set_status(self, status: str):
        self._status = status
        if status in TOOL_STATUS:
            self.status_dot.config(text=TOOL_STATUS[status])

    def get_status(self) -> str:
        return self._status

    def _on_check(self):
        self._selected = self.toggle.get()
        self.on_toggle(self)

    def _on_enter(self, event):
        self._hovered = True
        self._update_style()

    def _on_leave(self, event):
        self._hovered = False
        self._update_style()

    def _update_style(self):
        bg = COLORS["card_hover"] if (self._hovered or self._selected) else COLORS["card_bg"]
        border = COLORS["accent"] if (self._hovered or self._selected) else COLORS["border"]
        
        self.config(bg=bg, highlightbackground=border)
        
        # Recursively update bg for all children that support it
        def _update_bg(widget):
            try:
                if not isinstance(widget, ToggleSwitch): # ToggleSwitch handles its own bg
                    widget.config(bg=bg)
            except:
                pass
            for child in widget.winfo_children():
                _update_bg(child)

        _update_bg(self)
        
        # Specific overrides
        self.toggle.config(bg=bg)
        if hasattr(self.toggle, "canvas"):
            self.toggle.canvas.config(bg=bg)

    def is_checked(self) -> bool:
        return self.toggle.get()

    def set_checked(self, checked: bool):
        self.toggle.set(checked)
        self._selected = checked
        self._update_style()

    def set_visible(self, visible: bool):
        self.visible = visible
        if not visible:
            self.grid_forget()


class ModernInstaller(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("DevTools Installer v2.0")
        self.geometry("1400x850")
        self.minsize(1000, 700)
        self.configure(bg=COLORS["bg"])

        self.cards: List[ToolCard] = []
        self.install_queue: queue.Queue = queue.Queue()
        self.is_installing = False

        self._setup_styles()
        self._init_ui()
        self._process_queue()
        self.after(500, self.check_installed_tools)

    def _setup_styles(self):
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Vertical.TScrollbar",
            gripcount=0,
            background=COLORS["border"],
            troughcolor=COLORS["bg"],
        )
        style.map("Vertical.TScrollbar", background=[("active", COLORS["accent"])])

        style.configure(
            "TNotebook", background=COLORS["bg"], borderwidth=0, tabposition="n"
        )
        style.configure(
            "TNotebook.Tab",
            background=COLORS["card_bg"],
            foreground=COLORS["text"],
            padding=(15, 8),
            font=("Segoe UI", 10),
            borderwidth=0,
        )
        style.map(
            "TNotebook.Tab",
            background=[
                ("selected", COLORS["accent"]),
                ("active", COLORS["card_hover"]),
            ],
            foreground=[("selected", "white"), ("active", COLORS["text"])],
        )

    def _build_category_grid(self, parent: tk.Frame, category: str):
        tools = TOOLS_REGISTRY[category]

        scroll_area = ScrollableFrame(parent)
        scroll_area.pack(fill="both", expand=True)
        
        scrollable_frame = scroll_area.scrollable_frame

        def _on_resize(event):
            _reposition_cards(event.width)

        scroll_area.canvas.bind("<Configure>", _on_resize, add="+")

        # Listen for search updates to reposition the grid
        self.bind("<<SearchUpdate>>", lambda e: _reposition_cards(), add="+")

        def _reposition_cards(width=None):
            if width is None:
                width = scroll_area.canvas.winfo_width() / self.tk.call('tk', 'scaling') * 72 / 96 # Rough DPI compensation
            
            # Simple column calculation
            card_width = 280 # Fixed target width for cards
            columns = max(1, int(width // card_width))
            
            visible_children = [c for c in scrollable_frame.winfo_children() if getattr(c, "visible", True)]
            
            for i, child in enumerate(visible_children):
                row = i // columns
                col = i % columns
                child.grid(row=row, column=col, sticky="nsew", padx=10, pady=10)
            
            # Hide non-visible children
            for child in scrollable_frame.winfo_children():
                if child not in visible_children:
                    child.grid_forget()
            
            for col in range(columns):
                scrollable_frame.columnconfigure(col, weight=1)

        for name in tools.keys():
            card = ToolCard(
                scrollable_frame,
                name,
                tools[name],
                on_toggle=self._on_card_toggle,
                on_link=lambda url: webbrowser.open(url),
            )
            self.cards.append(card)
        
        self.after(200, _reposition_cards)

    def _init_ui(self):
        # Configure Root Grid
        self.columnconfigure(0, weight=0, minsize=240) # Sidebar
        self.columnconfigure(1, weight=1)              # Content
        self.rowconfigure(0, weight=1)

        self.sidebar_area = ScrollableFrame(self, bg=COLORS["sidebar_bg"], width=240)
        self.sidebar_area.grid(row=0, column=0, sticky="nsew")
        self.sidebar_area.pack_propagate(False)
        self.sidebar = self.sidebar_area.scrollable_frame

        self.content = tk.Frame(self, bg=COLORS["bg"])
        self.content.grid(row=0, column=1, sticky="nsew")
        
        # Content Grid
        self.content.columnconfigure(0, weight=1)
        self.content.rowconfigure(1, weight=1) # Main category area
        self.content.rowconfigure(3, weight=0) # Console area

        self._build_sidebar(self.sidebar)
        self._build_content(self.content)

    def _build_sidebar(self, sidebar: tk.Frame):
        # Sidebar using Grid for better control
        sidebar.columnconfigure(0, weight=1)
        # We'll use several rows and push the last one to the bottom
        sidebar.rowconfigure(10, weight=1) # Spacer row

        logo = tk.Label(
            sidebar,
            text="DevTools",
            bg=COLORS["sidebar_bg"],
            fg="white",
            font=FONTS["title"],
        )
        logo.grid(row=0, column=0, sticky="w", padx=25, pady=(40, 10))

        tk.Frame(sidebar, bg=COLORS["border"], height=1).grid(row=1, column=0, sticky="ew", padx=25, pady=20)

        tk.Label(
            sidebar,
            text="CATEGORIES",
            bg=COLORS["sidebar_bg"],
            fg=COLORS["text_dim"],
            font=("Segoe UI", 9, "bold"),
        ).grid(row=2, column=0, sticky="w", padx=25, pady=(0, 10))

        cat_container = tk.Frame(sidebar, bg=COLORS["sidebar_bg"])
        cat_container.grid(row=3, column=0, sticky="ew")
        cat_container.columnconfigure(0, weight=1)

        self.category_buttons = {}
        for i, category in enumerate(TOOLS_REGISTRY.keys()):
            cat_btn = CategoryButton(
                cat_container,
                text=category,
                command=lambda c=category: self.show_category(c)
            )
            cat_btn.grid(row=i, column=0, sticky="ew")
            self.category_buttons[category] = cat_btn

        tk.Frame(sidebar, bg=COLORS["border"], height=1).grid(row=4, column=0, sticky="ew", padx=25, pady=20)

        # Maintenance Section
        current_row = 5
        self.backup_btn = StyledButton(sidebar, "Backup", command=self.start_backup, primary=True)
        self.backup_btn.grid(row=current_row, column=0, sticky="ew", padx=20, pady=5)
        
        current_row += 1
        self.restore_btn = StyledButton(sidebar, "Restore", command=self.start_restore, primary=False)
        self.restore_btn.grid(row=current_row, column=0, sticky="ew", padx=20, pady=5)

        current_row += 1
        tk.Label(sidebar, text="STACKS", bg=COLORS["sidebar_bg"], fg=COLORS["text_dim"], font=("Segoe UI", 8, "bold")
                ).grid(row=current_row, column=0, sticky="w", padx=25, pady=(20, 5))

        # Stacks in a small scrollable or limited area if many? Let's just grid them for now
        for stack_name in list(STACKS.keys())[:4]: # Limit to first 4 to avoid overflow
            current_row += 1
            stack_btn = StyledButton(sidebar, f"{stack_name}", command=lambda s=stack_name: self.apply_stack(s), primary=False, height=28)
            stack_btn.grid(row=current_row, column=0, sticky="ew", padx=20, pady=2)

        # Status at the very bottom
        self.status_label = tk.Label(
            sidebar,
            text="Status: Ready",
            bg=COLORS["sidebar_bg"],
            fg=COLORS["text_dim"],
            font=FONTS["small"],
            wraplength=200,
        )
        self.status_label.grid(row=11, column=0, sticky="sw", padx=15, pady=15)

    def _build_content(self, content: tk.Frame):
        # Header
        header_frame = tk.Frame(content, bg=COLORS["bg"])
        header_frame.grid(row=0, column=0, sticky="ew", padx=25, pady=(30, 10))
        header_frame.columnconfigure(0, weight=1)

        tk.Label(
            header_frame,
            text="Tool Management",
            bg=COLORS["bg"],
            fg="white",
            font=FONTS["title"],
        ).grid(row=0, column=0, sticky="w")

        self.search_var = tk.StringVar()
        self.search_var.trace_add("write", self._on_search)

        search_entry = RoundedEntry(header_frame, placeholder="🔍 Search tools...", width=300)
        search_entry.grid(row=0, column=1, sticky="e")

        # Main Area (Notebook/Category Grid)
        self.category_notebook = tk.Frame(content, bg=COLORS["bg"])
        self.category_notebook.grid(row=1, column=0, sticky="nsew", padx=15, pady=5)
        self.category_notebook.columnconfigure(0, weight=1)
        self.category_notebook.rowconfigure(0, weight=1)

        self.category_frames = {}
        self.category_visible = {}

        for category in TOOLS_REGISTRY.keys():
            frame = tk.Frame(self.category_notebook, bg=COLORS["bg"])
            self.category_frames[category] = frame
            # frame is gridded in show_category
            self._build_category_grid(frame, category)
            self.category_visible[category] = False

        self.current_category = None
        self.show_category(list(TOOLS_REGISTRY.keys())[0])

        # Console area
        self.console_expanded = False
        self.console_container = tk.Frame(content, bg=COLORS["bg"])
        self.console_container.grid(row=2, column=0, sticky="ew", padx=25, pady=(10, 0))
        self.console_container.columnconfigure(0, weight=1)

        self.console_toggle = tk.Button(
            self.console_container,
            text="▶ Show Console",
            command=self._toggle_console,
            bg=COLORS["bg"],
            fg=COLORS["accent"],
            font=("Segoe UI", 9, "bold"),
            relief="flat",
            cursor="hand2",
            activebackground=COLORS["bg"],
            activeforeground=COLORS["accent_hover"]
        )
        self.console_toggle.grid(row=0, column=0, sticky="w")

        self.log_frame = tk.Frame(content, bg=COLORS["bg"])
        self.log_frame.grid(row=3, column=0, sticky="ew", padx=25, pady=(0, 5))
        self.log_frame.columnconfigure(0, weight=1)

        self.log_text = tk.Text(
            self.log_frame,
            height=0, # Start hidden
            bg="#0d0d0d",
            fg="#00ff00",
            font=FONTS["mono"],
            relief="flat",
            bd=0,
            highlightthickness=1,
            highlightbackground=COLORS["border"],
        )
        # Use log_text.grid_remove() initially or height=0
        self.log_text.grid(row=0, column=0, sticky="ew")
        
        self.progress_bar = ttk.Progressbar(
            self.log_frame,
            mode="determinate",
            length=400,
            style="Custom.Horizontal.TProgressbar",
        )
        self.progress_bar.grid(row=1, column=0, sticky="ew", pady=(10, 0))

        # Footer Actions
        footer_frame = tk.Frame(content, bg=COLORS["bg"])
        footer_frame.grid(row=4, column=0, sticky="ew", padx=25, pady=(15, 30))
        footer_frame.columnconfigure(1, weight=1)

        self.select_all_btn = StyledButton(footer_frame, "Select All", command=self.select_all, width=140, primary=False)
        self.select_all_btn.grid(row=0, column=0, padx=(0, 10))

        self.deselect_all_btn = StyledButton(footer_frame, "Deselect All", command=self.deselect_all, width=140, primary=False)
        self.deselect_all_btn.grid(row=0, column=1, sticky="w")

        self.install_btn = GradientButton(
            footer_frame,
            "Install Selected",
            command=self.start_installation,
            width=240,
            height=40
        )
        self.install_btn.grid(row=0, column=2, sticky="e")

    def show_category(self, category: str):
        if self.current_category == category:
            return

        for cat, frame in self.category_frames.items():
            if cat == category:
                frame.grid(row=0, column=0, sticky="nsew") # Inside category_notebook
                self.category_visible[cat] = True
                if cat in self.category_buttons:
                    self.category_buttons[cat].set_active(True)
            else:
                frame.grid_forget()
                self.category_visible[cat] = False
                if cat in self.category_buttons:
                    self.category_buttons[cat].set_active(False)

        self.current_category = category

    def _toggle_console(self):
        self.console_expanded = not self.console_expanded
        if self.console_expanded:
            self.log_text.config(height=8)
            self.console_toggle.config(text="▼ Hide Console")
        else:
            self.log_text.config(height=0)
            self.console_toggle.config(text="▶ Show Console")
        self.update_idletasks()

    def _on_card_toggle(self, card: ToolCard):
        pass

    def _on_search(self, *args):
        try:
            query = self.search_var.get().lower()
        except:
            query = ""

        for card in self.cards:
            match = query in card.name.lower() or query in card.details["id"].lower()
            card.set_visible(match)
        
        # Trigger repositioning in all visible frames
        self.event_generate("<<SearchUpdate>>")

    def _process_queue(self):
        try:
            while True:
                msg = self.install_queue.get_nowait()
                self._handle_queue_message(msg)
        except queue.Empty:
            pass
        self.after(100, self._process_queue)

    def _handle_queue_message(self, msg: Dict):
        msg_type = msg.get("type")

        if msg_type == "log":
            self._append_log(msg["text"], msg.get("tag", "info"))
        elif msg_type == "progress":
            pass
        elif msg_type == "finished":
            self._on_install_finished()
        elif msg_type == "status":
            self.status_label.config(text=msg["text"])

    def _append_log(self, text: str, tag: str = "info"):
        self.log_text.insert("end", text + "\n", tag)
        self.log_text.see("end")

    def select_all(self):
        """Select all tools."""
        for card in self.cards:
            card.set_checked(True)

    def deselect_all(self):
        """Deselect all tools."""
        for card in self.cards:
            card.set_checked(False)

    def apply_stack(self, stack_name: str):
        """
        Apply a predefined stack
        ========================
        Automatically selects tools belonging to a stack.
        """
        self.deselect_all()
        active_tools = STACKS.get(stack_name, [])
        for card in self.cards:
            if card.name in active_tools:
                card.set_checked(True)
        self.status_label.config(text=f"Selected Stack: {stack_name}")

    def start_installation(self):
        """
        Start Installation - Main method
        ================================
        Collects selected tools and starts installation
        in a separate thread to keep the UI responsive.
        """
        selected = [(c.name, c.details["id"]) for c in self.cards if c.is_checked()]

        if not selected:
            self._append_log("⚠️ Please select at least one application.", "warning")
            return

        self.is_installing = True
        self._set_ui_enabled(False)
        self.log_text.delete("1.0", "end")

        self._append_log(
            f"🚀 Starting installation of {len(selected)} applications...", "info"
        )

        thread = threading.Thread(
            target=self._run_installation, args=(selected,), daemon=True
        )
        thread.start()

    def _run_installation(self, tools: List[Tuple[str, str]]):
        total = len(tools)

        for i, (name, winget_id) in enumerate(tools):
            card = next((c for c in self.cards if c.name == name), None)
            if card:
                card.set_status("RUNNING")

            self.install_queue.put(
                {
                    "type": "log",
                    "text": f"🚀 Starting installation: {name}...",
                    "tag": "info",
                }
            )

            self.after(0, lambda: self.update_progress(i, total))

            if name == "WSL":
                cmd = "wsl --install"
            else:
                cmd = f"winget install --id {winget_id} --silent --accept-package-agreements --accept-source-agreements"

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
                            self.install_queue.put(
                                {
                                    "type": "log",
                                    "text": f"  > {line.strip()}",
                                    "tag": "info",
                                }
                            )

                process.wait()

                if process.returncode == 0:
                    self.install_queue.put(
                        {
                            "type": "log",
                            "text": f"✅ Completed: {name}",
                            "tag": "success",
                        }
                    )
                    if card:
                        card.set_status("INSTALLED")
                else:
                    self.install_queue.put(
                        {
                            "type": "log",
                            "text": f"⚠️ Error (Code {process.returncode}): {name}",
                            "tag": "warning",
                        }
                    )
                    if card:
                        card.set_status("ERROR")

            except Exception as e:
                self.install_queue.put(
                    {
                        "type": "log",
                        "text": f"❌ Error installing {name}: {str(e)}",
                        "tag": "error",
                    }
                )

        self.install_queue.put(
            {
                "type": "log",
                "text": "🏁 All installations completed!",
                "tag": "success",
            }
        )
        self.install_queue.put({"type": "finished"})

    def _on_install_finished(self):
        self.is_installing = False
        self._set_ui_enabled(True)
        self.progress_bar["value"] = 0
        self.status_label.config(text="Status: Completed")

    def _set_ui_enabled(self, enabled: bool):
        self.install_btn.set_enabled(enabled)

    def start_backup(self):
        """
        Create Backup
        =============
        Starts backup creation in a separate thread.
        """
        threading.Thread(target=self._run_backup, daemon=True).start()

    def _run_backup(self):
        """
        Execute Backup - Create ZIP
        ===========================
        Creates a backup of VS Code, Gemini CLI, Antigravity settings
        and saves them to a ZIP file in Documents.
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        doc_path = os.path.join(os.path.expanduser("~"), "Documents")
        target_zip = os.path.join(doc_path, f"DevTools_Backup_{timestamp}.zip")

        try:
            self.install_queue.put(
                {
                    "type": "log",
                    "text": f"📦 Starting Backup -> {target_zip}",
                    "tag": "info",
                }
            )

            with zipfile.ZipFile(target_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
                ext_file = os.path.join(doc_path, "vscode_extensions.txt")
                subprocess.run(
                    [
                        "powershell.exe",
                        "-Command",
                        f"code --list-extensions > '{ext_file}'",
                    ],
                    capture_output=True,
                )

                if os.path.exists(ext_file):
                    zipf.write(ext_file, "vscode_extensions.txt")
                    os.remove(ext_file)

                for name, path in BACKUP_PATHS.items():
                    if os.path.exists(path):
                        self.install_queue.put(
                            {
                                "type": "log",
                                "text": f"  > Compressing: {name}",
                                "tag": "info",
                            }
                        )
                        for root, _, files in os.walk(path):
                            for file in files:
                                full_path = os.path.join(root, file)
                                zipf.write(
                                    full_path,
                                    os.path.join(
                                        name, os.path.relpath(full_path, path)
                                    ),
                                )

            self.install_queue.put(
                {
                    "type": "log",
                    "text": "✅ Backup completed successfully!",
                    "tag": "success",
                }
            )

        except Exception as e:
            self.install_queue.put(
                {"type": "log", "text": f"❌ Σφάλμα στο Backup: {e}", "tag": "error"}
            )

    def start_restore(self):
        """
        Restore from Backup
        ===================
        Opens a ZIP file selection dialog.
        """
        from tkinter import filedialog

        path = filedialog.askopenfilename(
            title="Select Backup ZIP", filetypes=[("Zip Files", "*.zip")]
        )

        if path:
            threading.Thread(
                target=self._run_restore, args=(path,), daemon=True
            ).start()

    def _run_restore(self, zip_path: str):
        """
        Execute Restore - Extract ZIP
        ============================
        Extracts files from ZIP to their original locations.
        """
        try:
            self.install_queue.put(
                {
                    "type": "log",
                    "text": f"📥 Starting Restore from: {zip_path}",
                    "tag": "info",
                }
            )

            with zipfile.ZipFile(zip_path, "r") as zipf:
                for name, dest in BACKUP_PATHS.items():
                    prefix = f"{name}/"
                    members = [m for m in zipf.namelist() if m.startswith(prefix)]

                    if members:
                        self.install_queue.put(
                            {
                                "type": "log",
                                "text": f"  > Extracting: {name}",
                                "tag": "info",
                            }
                        )

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

            self.install_queue.put(
                {
                    "type": "log",
                    "text": "✅ Restore completed!",
                    "tag": "success",
                }
            )

        except Exception as e:
            self.install_queue.put(
                {
                    "type": "log",
                    "text": "❌ Error during Restore: {e}", "tag": "error"
                }
            )

    def export_selection(self):
        from tkinter import filedialog
        import json

        selected = [c.name for c in self.cards if c.is_checked()]
        if not selected:
            self._append_log(
                "⚠️ No tools selected for export.", "warning"
            )
            return

        path = filedialog.asksaveasfilename(
            title="Export Selection",
            defaultextension=".json",
            filetypes=[("JSON Files", "*.json")],
            initialfile="devtools_selection.json",
        )

        if path:
            try:
                with open(path, "w", encoding="utf-8") as f:
                    json.dump(
                        {"selected_tools": selected}, f, ensure_ascii=False, indent=2
                    )
                self._append_log(f"✅ Export successful: {path}", "success")
            except Exception as e:
                self._append_log(f"❌ Export error: {e}", "error")

    def import_selection(self):
        from tkinter import filedialog
        import json

        path = filedialog.askopenfilename(
            title="Import Selection",
            filetypes=[("JSON Files", "*.json")],
        )

        if path:
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    selected = data.get("selected_tools", [])

                self.deselect_all()
                for card in self.cards:
                    if card.name in selected:
                        card.set_checked(True)

                self._append_log(f"✅ Imported {len(selected)} tools.", "success")
            except Exception as e:
                self._append_log(f"❌ Import error: {e}", "error")

    def check_installed_tools(self):
        self._append_log("🔍 Checking installed tools...", "info")

        def check():
            for card in self.cards:
                tool_id = card.details["id"]
                is_installed = self._is_tool_installed(tool_id)
                if is_installed:
                    card.set_status("INSTALLED")
                else:
                    card.set_status("PENDING")

            self.install_queue.put(
                {"type": "log", "text": "✅ Check complete.", "tag": "success"}
            )

        threading.Thread(target=check, daemon=True).start()

    def _is_tool_installed(self, tool_id: str) -> bool:
        try:
            result = subprocess.run(
                ["winget", "list", "--id", tool_id, "--exact"],
                capture_output=True,
                text=True,
                timeout=30,
            )
            return tool_id in result.stdout
        except Exception:
            return False

    def update_progress(self, current: int, total: int):
        if total > 0:
            percentage = (current / total) * 100
            self.progress_bar["value"] = percentage
            self.update_idletasks()


if __name__ == "__main__":
    app = ModernInstaller()
    app.mainloop()
