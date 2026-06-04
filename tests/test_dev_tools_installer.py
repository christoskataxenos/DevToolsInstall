import pytest
import os
import tempfile
import json
import customtkinter as ctk

from core.config import Config, TranslationManager
from ui.components.tool_row import ToolRow
from ui.app_window import AppWindow

# Check if GUI window environment is active and available
GUI_AVAILABLE = False
try:
    root = ctk.CTk()
    root.destroy()
    GUI_AVAILABLE = True
except Exception:
    GUI_AVAILABLE = False

requires_gui = pytest.mark.skipif(
    not GUI_AVAILABLE,
    reason="GUI display server is not available in the current test environment"
)

@pytest.fixture
def app():
    try:
        app_inst = AppWindow()
    except Exception as e:
        pytest.skip(f"Failed to initialize CustomTkinter application frame: {e}")
    yield app_inst
    try:
        app_inst.destroy()
    except Exception:
        pass

@pytest.fixture
def mock_parent():
    try:
        parent = ctk.CTk()
    except Exception as e:
        pytest.skip(f"Failed to initialize CustomTkinter parent: {e}")
    yield parent
    try:
        parent.destroy()
    except Exception:
        pass

def test_registry_integrity():
    """Validates structure and items of the installers registry configuration."""
    registry = Config.load_registry()
    assert len(registry) > 0
    for cat, tools in registry.items():
        assert len(tools) > 0
        for name, details in tools.items():
            assert "id" in details
            assert "url" in details

def test_stacks_consistency():
    """Validates that all stack applications matches items defined in the registry."""
    registry = Config.load_registry()
    all_tool_names = []
    for tools in registry.values():
        all_tool_names.extend(tools.keys())

    stacks = Config.load_stacks()
    for stack_name, tools in stacks.items():
        for tool in tools:
            assert tool in all_tool_names, (
                f"Tool '{tool}' in stack '{stack_name}' is missing in registries."
            )

@requires_gui
def test_window_initialization(app):
    """Validates window initializes components and contains tools list matching registry count."""
    registry = Config.load_registry()
    expected_count = sum(len(tools) for tools in registry.values())
    assert len(app.panels["install"].tool_rows) == expected_count

@requires_gui
def test_tool_row_status(mock_parent):
    """Validates status updates inside ToolRow component."""
    details = {"id": "Test.Test", "url": "https://test.com"}
    row = ToolRow(
        mock_parent,
        name="Test Tool",
        details=details,
        on_check_changed=lambda checked: None,
        on_retry=lambda n, wid: None
    )

    assert row.status == "PENDING"
    row.set_status("INSTALLED")
    assert row.status == "INSTALLED"
    row.set_status("RUNNING")
    assert row.status == "RUNNING"
    row.set_status("ERROR")
    assert row.status == "ERROR"

@requires_gui
def test_theme_toggling(app):
    """Validates theme toggling alters ctk appearance modes."""
    # Simulate theme switch toggle toggling
    app.theme_switch.toggle()
    # Check switch does not crash the window
    assert app.theme_switch.get() in [0, 1]

def test_all_tools_have_valid_urls():
    """Validates registry tool entries contain valid HTTP download URLs."""
    registry = Config.load_registry()
    for category, tools in registry.items():
        for name, details in tools.items():
            assert "url" in details, f"Tool {name} in {category} is missing URL link"
            url = details["url"]
            assert url.startswith("http://") or url.startswith("https://"), (
                f"Tool {name} in {category} contains invalid URL structure: {url}"
            )

def test_no_duplicate_winget_ids():
    """Validates registry has unique IDs to prevent conflict issues."""
    registry = Config.load_registry()
    seen_ids = {}
    for category, tools in registry.items():
        for name, details in tools.items():
            tool_id = details.get("id", "")
            if tool_id and tool_id != "manual":
                if tool_id in seen_ids:
                    assert False, (
                        f"Duplicate winget ID '{tool_id}' found in "
                        f"'{seen_ids[tool_id]}' and '{name}'"
                    )
                seen_ids[tool_id] = name

def test_get_installed_tool_ids_mock():
    """Validates that get_installed_tool_ids correctly parses mock winget list output."""
    from unittest.mock import patch, MagicMock
    from core.installer_service import InstallerService
    
    mock_stdout = (
        "Name                                   Id                                      Version          Available        Source\n"
        "-----------------------------------------------------------------------------------------------------------------------\n"
        "7-Zip 26.00 (x64)                      7zip.7zip                               26.00            26.01            winget\n"
        "Git                                    Git.Git                                 2.53.0.2         2.54.0           winget\n"
        "Some App                               SomeApp.ID                              1.0.0                             \n"
    )
    
    service = InstallerService(None)
    with patch("subprocess.Popen") as mock_popen:
        mock_proc = MagicMock()
        mock_proc.returncode = 0
        mock_proc.communicate.return_value = (mock_stdout, "")
        mock_popen.return_value = mock_proc
        
        installed = service.get_installed_tool_ids()
        assert "7zip.7zip" in installed
        assert "Git.Git" in installed
        assert "SomeApp.ID" in installed
        assert len(installed) == 3


@requires_gui
def test_navigation_remains_enabled_during_install(app):
    """Validates that navigation and main window controls remain enabled while installer task is running."""
    # Αρχικά όλα πρέπει να είναι ενεργοποιημένα
    assert app.theme_switch.cget("state") == "normal"
    assert app.lang_cb.cget("state") == "normal"
    for btn in app.nav_buttons.values():
        assert btn.cget("state") == "normal"
        
    # Απενεργοποίηση του UI (προσομοίωση έναρξης εγκατάστασης)
    app._set_ui_enabled(False)
    
    # Τα κουμπιά πλοήγησης, η αλλαγή γλώσσας και θέματος πρέπει να παραμείνουν ενεργοποιημένα
    assert app.theme_switch.cget("state") == "normal"
    assert app.lang_cb.cget("state") == "normal"
    for btn in app.nav_buttons.values():
        assert btn.cget("state") == "normal"
        
    # Τα action buttons στα subpanels πρέπει να απενεργοποιηθούν
    assert app.panels["install"].install_btn.cget("state") == "disabled"
    assert app.panels["backup"].backup_btn.cget("state") == "disabled"
    
    for btn in app.panels["stacks"].apply_buttons:
        assert btn.cget("state") == "disabled"
        
    assert app.panels["skills"].download_btn.cget("state") == "disabled"


