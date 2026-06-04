# DevTools Installer - Modern CustomTkinter UI/UX Refactor Design Document

## 1. Project Overview
This project is a complete UI/UX refactor of the `DevToolsInstaller` application, moving it from a monolithic Tkinter script to a modern, modular desktop application using **CustomTkinter** (`customtkinter`).

The application enables developer tool installations via Windows `winget`, settings backup/restore, environment stacks configuration, AI-based error diagnostics (local Ollama + DuckDuckGo search), and AI agent skills deployment (.cursorrules, fabric patterns).

---

## 2. Decision Log

| Decision Area | Chosen Approach | Alternatives Considered | Rationale |
| :--- | :--- | :--- | :--- |
| **GUI Framework** | **CustomTkinter** | React + FastAPI, PySide6 | Kept as a native, lightweight Python desktop application. CustomTkinter provides sleek, modern UI widgets (rounded corners, dark/light themes) without the complexity of a web-stack or heavy Qt boilerplate. |
| **Window Layout** | **Triple-Column Layout** | Vertical Split Layout | A 15% (Sidebar) - 50% (Content) - 35% (Terminal) layout. Gives a professional, IDE-like developer feel where logs/terminal output are persistent on the right side. |
| **Tool Representation** | **Compact Tool Rows** | Massive Tool Cards | Replaced large cards with slim horizontal rows containing a checkbox, status badge, description tooltips, and action buttons. Fits the 50% canvas width perfectly without scrolling fatigue. |
| **Architecture** | **Modular File Structure** | Single-file script | Split the 4,700-line script into logical layers (`main.py`, `core/` for business logic, `ui/` for CustomTkinter panels and widgets). |
| **Comments & Language** | **Strictly English** | Greek Comments | Switched the language of variable names, comments, and structure to English to target a global developer audience, overriding local preferences. |

---

## 3. Architecture & File Structure

```text
DevToolsInstall/
├── installers.json             # Tools Registry JSON
├── requirements.txt            # Python Dependencies
├── main.py                     # Entry point (initializes app)
├── core/                       # Backend & Integration Services
│   ├── __init__.py
│   ├── config.py               # Registry loading & localization
│   ├── installer_service.py    # Winget wrapper & threading queue
│   ├── system_checker.py       # System Spec checker service
│   ├── skills_manager.py       # AI Agent skills/prompt manager
│   └── diagnostic_agent.py     # DDG Search & Ollama diagnostic agent
└── ui/                         # CustomTkinter Views & Layouts
    ├── __init__.py
    ├── app_window.py           # Main window (app layout coordinator)
    ├── theme.py                # Visual styling, fonts, and dark mode configs
    ├── components/             # Reusable UI widgets
    │   ├── tool_row.py         # Compact program items (checkbox, badge, action)
    │   ├── terminal_console.py # 35% Column: Thread-safe custom terminal log
    │   └── dialogs.py          # AI Diagnostic and Backup Selection popups
    └── panels/                 # Main workspaces (50% Column contents)
        ├── tools_panel.py      # Compact grid/list of tools by category
        ├── stacks_panel.py     # Dev Environment Stacks selection
        ├── backup_panel.py     # Settings Backup/Restore options
        └── skills_panel.py     # AI rules and templates installer
```

---

## 4. Design Details

### 4.1 Left Pane (15% Width) - Sidebar
- **Tab Selection**: Vertical button navigation bar (Tools, Stacks, Backup, Skills, Diagnostics).
- **Theme Toggler**: Clean toggle switch between Dark and Light mode.
- **System Specs Summary**: Displays RAM, Free Disk, and GPU model in a compact card format.

### 4.2 Central Pane (50% Width) - Main Workspace
- **Search & Category Filters**: Search bar and tab selectors at the top.
- **Dynamic View**: Renders the currently selected panel in a scrollable frame.
- **Compact Tool Rows**: Each tool is a row inside a container:
  - Checkbox to select/deselect the tool.
  - Status indicator badge (e.g. `[Pending]`, `[Installing]`, `[OK]`, `[Error]`).
  - Tool Name and short description tooltip.
  - Web icon link and version info.

### 4.3 Right Pane (35% Width) - Persistent Terminal Console
- **Output Feed**: Live stdout/stderr outputs of subprocesses running `winget` installations, `git` commands, or `Ollama` status updates.
- **Console controls**: Buttons to clear the output or export it to a log file.
- **Font**: Monospace layout (e.g., Courier New or Consolas) inside a dark textbox, regardless of the app theme.

---

## 5. Non-Functional Requirements & Security
- **Thread Safety**: Long-running subprocess commands are spawned in separate `threading.Thread` instances. Output streams write to a `queue.Queue`, which is consumed by the GUI main thread via a periodic `.after()` tick to prevent UI locking.
- **Privacy & Diagnostics**: duckduckgo_search runs anonymously. Local Ollama uses `qwen2.5-coder:1.5b` (or custom model name) offline on `http://localhost:11434`.
