# -*- coding: utf-8 -*-
import pytest
import os
import shutil
import tempfile
from SystemChecker import SystemSpecChecker
from SkillsManager import SkillsManager
from AIDiagnosticAgent import AIDiagnosticAgent

def test_system_spec_checker_keys():
    # Έλεγχος ότι η μέθοδος get_system_specs επιστρέφει λεξικό με τα σωστά κλειδιά
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
    # Δοκιμή επιτυχούς ελέγχου απαιτήσεων συστήματος
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
    # Δοκιμή αποτυχίας ελέγχου απαιτήσεων συστήματος (π.χ. ανεπαρκής RAM και έλλειψη GPU)
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
    assert any("κάρτα γραφικών" in r for r in reasons)

def test_skills_manager_paths():
    # Έλεγχος ότι ο global φάκελος των skills είναι έγκυρος
    global_dir = SkillsManager.get_global_dir()
    assert os.path.exists(global_dir)
    assert os.path.isdir(global_dir)

def test_skills_manager_git_check():
    # Έλεγχος ότι η μέθοδος is_git_installed επιστρέφει boolean
    is_installed = SkillsManager.is_git_installed()
    assert isinstance(is_installed, bool)

def test_ai_diagnostic_agent_web_search():
    # Έλεγχος ότι η αναζήτηση επιστρέφει λίστα και χειρίζεται τυχόν σφάλματα / rate limit
    results = AIDiagnosticAgent.search_web("winget error 1603")
    assert isinstance(results, list)

def test_ai_diagnostic_agent_ollama_offline():
    # Έλεγχος ότι αν το Ollama είναι offline, η μέθοδος διαγνωστικών επιστρέφει False με κατάλληλο μήνυμα
    import unittest.mock as mock
    with mock.patch.object(AIDiagnosticAgent, "is_ollama_running", return_value=False):
        success, explanation, cmd = AIDiagnosticAgent.diagnose_with_ollama("Ollama", "Error occurred", [])
        assert success is False
        assert "δεν εκτελείται" in explanation
