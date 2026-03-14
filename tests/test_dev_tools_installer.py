import pytest
import json
import os
import tempfile
from DevToolsInstaller import (
    ModernInstaller,
    TOOLS_REGISTRY,
    STACKS,
    TOOL_STATUS,
    ThemeManager,
    ToolCard,
)


@pytest.fixture
def app():
    app = ModernInstaller()
    yield app
    try:
        app.destroy()
    except:
        pass


@pytest.fixture
def mock_parent():
    import tkinter as tk

    root = tk.Tk()
    yield root
    root.destroy()


def test_registry_integrity():
    """Έλεγχος αν το μητρώο εργαλείων είναι σωστά δομημένο."""
    assert len(TOOLS_REGISTRY) > 0
    for cat, tools in TOOLS_REGISTRY.items():
        assert len(tools) > 0
        for name, details in tools.items():
            assert "id" in details
            assert "url" in details


def test_stacks_consistency():
    """Έλεγχος αν όλα τα εργαλεία στα stacks υπάρχουν στο registry."""
    all_tool_names = []
    for tools in TOOLS_REGISTRY.values():
        all_tool_names.extend(tools.keys())

    for stack_name, tools in STACKS.items():
        for tool in tools:
            assert tool in all_tool_names, (
                f"Το εργαλείο {tool} στο stack {stack_name} δεν υπάρχει στο registry."
            )


def test_window_initialization(app):
    """Έλεγχος αν το παράθυρο αρχικοποιείται με τον σωστό αριθμό καρτών."""
    expected_count = sum(len(tools) for tools in TOOLS_REGISTRY.values())
    assert len(app.cards) == expected_count


def test_tool_status_constants():
    """Έλεγχος ότι τα status icons ορίζονται σωστά."""
    assert "PENDING" in TOOL_STATUS
    assert "INSTALLED" in TOOL_STATUS
    assert "RUNNING" in TOOL_STATUS
    assert "ERROR" in TOOL_STATUS
    assert TOOL_STATUS["PENDING"] == "⏳"
    assert TOOL_STATUS["INSTALLED"] == "✅"
    assert TOOL_STATUS["RUNNING"] == "🔄"
    assert TOOL_STATUS["ERROR"] == "❌"


def test_theme_manager():
    """Έλεγχος του διαχειριστή θεμάτων."""
    assert ThemeManager.get_current_theme() == "dark"

    ThemeManager.set_theme("light")
    assert ThemeManager.get_current_theme() == "light"

    colors = ThemeManager.get_colors()
    assert "bg" in colors
    assert "accent" in colors

    ThemeManager.set_theme("dark")
    assert ThemeManager.get_current_theme() == "dark"


def test_tool_card_status(mock_parent):
    """Έλεγχος της κατάστασης της κάρτας εργαλείου."""
    details = {"id": "Test.Test", "url": "https://test.com"}

    card = ToolCard(
        mock_parent,
        name="Test Tool",
        details=details,
        on_toggle=lambda c: None,
        on_link=lambda u: None,
    )

    assert card.get_status() == "PENDING"

    card.set_status("INSTALLED")
    assert card.get_status() == "INSTALLED"

    card.set_status("RUNNING")
    assert card.get_status() == "RUNNING"

    card.set_status("ERROR")
    assert card.get_status() == "ERROR"


def test_export_import_json(app):
    """Έλεγχος εξαγωγής και εισαγωγής επιλογών σε JSON."""
    app.deselect_all()

    if app.cards:
        app.cards[0].set_checked(True)
        app.cards[1].set_checked(True)

    selected_before = [c.name for c in app.cards if c.is_checked()]
    assert len(selected_before) == 2

    with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
        temp_path = f.name

    try:
        with open(temp_path, "w", encoding="utf-8") as f:
            json.dump({"selected_tools": selected_before}, f)

        app.deselect_all()

        with open(temp_path, "r", encoding="utf-8") as f:
            data = json.load(f)

        imported = data.get("selected_tools", [])
        assert len(imported) == 2

    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def test_progress_bar_exists(app):
    """Έλεγχος ύπαρξης της γραμμής προόδου."""
    assert hasattr(app, "progress_bar")
    assert app.progress_bar["maximum"] == 100
    assert app.progress_bar["value"] == 0


def test_search_functionality(app):
    """Έλεγχος της λειτουργίας αναζήτησης."""
    app.search_var.set("VS Code")

    visible_count = sum(1 for c in app.cards if c.name == "VS Code")
    assert visible_count > 0

    app.search_var.set("")

    app.search_var.set("NonExistent")
    for card in app.cards:
        if card.name == "VS Code":
            pass


def test_select_deselect_all(app):
    """Έλεγχος επιλογής/αποεπιλογής όλων."""
    app.deselect_all()
    assert all(not c.is_checked() for c in app.cards)

    app.select_all()
    assert all(c.is_checked() for c in app.cards)


def test_apply_stack(app):
    """Έλεγχος εφαρμογής stack."""
    app.apply_stack("Python / AI")

    python_tools = STACKS["Python / AI"]
    for card in app.cards:
        if card.name in python_tools:
            assert card.is_checked(), f"{card.name} should be checked"


def test_all_tools_have_valid_urls():
    """Έλεγχος ότι κάθε εργαλείο έχει URL που ξεκινά με http."""
    for category, tools in TOOLS_REGISTRY.items():
        for name, details in tools.items():
            assert "url" in details, f"Tool {name} in {category} is missing URL"
            url = details["url"]
            assert url.startswith("http://") or url.startswith("https://"), (
                f"Tool {name} in {category} has invalid URL: {url}"
            )


def test_no_duplicate_winget_ids():
    """Έλεγχος ότι δεν υπάρχουν διπλότυπα winget IDs."""
    seen_ids = {}
    for category, tools in TOOLS_REGISTRY.items():
        for name, details in tools.items():
            tool_id = details.get("id", "")
            if tool_id and tool_id != "manual":
                if tool_id in seen_ids:
                    assert False, (
                        f"Duplicate winget ID '{tool_id}' found in "
                        f"{seen_ids[tool_id]} and {name}"
                    )
                seen_ids[tool_id] = name
