import pytest
import os
import shutil
import tempfile
from core.system_checker import SystemSpecChecker
from core.skills_manager import SkillsManager
from core.diagnostic_agent import AIDiagnosticAgent

def test_system_spec_checker_keys():
    # Verifies get_system_specs returns expected dictionary keys
    specs = SystemSpecChecker.get_system_specs()
    assert isinstance(specs, dict)
    assert "ram_gb" in specs
    assert "free_disk_gb" in specs
    assert "has_gpu" in specs
    assert "gpu_name" in specs
    assert isinstance(specs["ram_gb"], float)
    assert isinstance(specs["free_disk_gb"], float)
    assert isinstance(specs["has_gpu"], bool)
    assert isinstance(specs["gpu_name"], str)

def test_system_spec_checker_requirements_pass():
    # Verifies requirements verification meets system resources specs successfully
    specs = {
        "ram_gb": 16.0,
        "free_disk_gb": 50.0,
        "has_gpu": True,
        "gpu_name": "NVIDIA RTX 4070"
    }
    reqs = {
        "min_ram_gb": 8,
        "min_disk_gb": 10,
        "requires_gpu": True
    }
    is_ok, reasons = SystemSpecChecker.check_requirements(reqs, specs)
    assert is_ok is True
    assert len(reasons) == 0

def test_system_spec_checker_requirements_fail():
    # Verifies requirements fail when specs are low (e.g. low RAM and no GPU)
    specs = {
        "ram_gb": 4.0,
        "free_disk_gb": 100.0,
        "has_gpu": False,
        "gpu_name": ""
    }
    reqs = {
        "min_ram_gb": 8,
        "min_disk_gb": 20,
        "requires_gpu": True
    }
    is_ok, reasons = SystemSpecChecker.check_requirements(reqs, specs)
    assert is_ok is False
    assert len(reasons) == 2
    assert any("RAM" in r for r in reasons)
    assert any("GPU" in r for r in reasons)

def test_skills_manager_paths():
    # Verifies global skills repository workspace folder exists
    global_dir = SkillsManager.get_global_dir()
    assert os.path.exists(global_dir)
    assert os.path.isdir(global_dir)

def test_skills_manager_git_check():
    # Verifies git CLI presence checker returns a boolean
    is_installed = SkillsManager.is_git_installed()
    assert isinstance(is_installed, bool)

def test_ai_diagnostic_agent_web_search():
    # Verifies search_web handles query calls safely
    results = AIDiagnosticAgent.search_web("winget error 1603")
    assert isinstance(results, list)

def test_ai_diagnostic_agent_ollama_offline():
    # Verifies offline Ollama agent reports is not running error safely
    import unittest.mock as mock
    with mock.patch.object(AIDiagnosticAgent, "is_ollama_running", return_value=False):
        success, explanation, cmd = AIDiagnosticAgent.diagnose_with_ollama("Ollama", "Error occurred", [])
        assert success is False
        assert "not running" in explanation


def test_clean_log_line():
    # Έλεγχος ότι η συνάρτηση clean_log_line φιλτράρει σωστά τις γραμμές θορύβου
    from core.installer_service import clean_log_line

    # Γραμμές που πρέπει να παραμείνουν
    assert clean_log_line("Starting package install...") == "Starting package install..."
    assert clean_log_line("Successfully verified installer hash") == "Successfully verified installer hash"

    # Γραμμές με spinners που πρέπει να φιλτραριστούν (επιστρέφουν None)
    assert clean_log_line("-") is None
    assert clean_log_line("\\") is None
    assert clean_log_line("|") is None
    assert clean_log_line("/") is None
    assert clean_log_line("...") is None

    # Γραμμές με μπάρες προόδου (block characters)
    assert clean_log_line("â–’â–’â–’â–’â–’â–’â–’â–’â–’â–’") is None
    assert clean_log_line("░░░░░░░░░░") is None
    assert clean_log_line("██████████") is None

    # Γραμμές με μεγέθη λήψης και ποσοστά
    assert clean_log_line("1024 KB / 767 MB") is None
    assert clean_log_line("13.0 MB / 767 MB") is None
    assert clean_log_line("50% 10 MB/s") is None

