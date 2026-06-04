import shutil
import subprocess
from typing import Dict, Any, Optional, Tuple, List

class SystemSpecChecker:
    """
    Κλάση για τον έλεγχο των προδιαγραφών του συστήματος (RAM, Δίσκος, GPU) στα Windows.
    """

    @classmethod
    def get_system_specs(cls) -> Dict[str, Any]:
        # Αρχικοποίηση των specs με προκαθορισμένες τιμές σφάλματος
        specs = {
            "ram_gb": 0.0,
            "free_disk_gb": 0.0,
            "has_gpu": False,
            "gpu_name": ""
        }

        # 1. Έλεγχος διαθέσιμου χώρου στο δίσκο C:
        try:
            total, used, free = shutil.disk_usage("C:\\")
            specs["free_disk_gb"] = round(free / (1024 ** 3), 2)
        except Exception:
            # Σε περίπτωση σφάλματος πρόσβασης, θέτουμε μια ασφαλή τιμή
            specs["free_disk_gb"] = 0.0

        # 2. Έλεγχος συνολικής μνήμης RAM μέσω PowerShell
        try:
            # Χρήση Get-CimInstance για αξιοπιστία σε Windows 10 και 11
            command = "powershell -NoProfile -Command \"(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory\""
            output = subprocess.check_output(command, shell=True, text=True, stderr=subprocess.DEVNULL)
            bytes_val = int(output.strip())
            specs["ram_gb"] = round(bytes_val / (1024 ** 3), 2)
        except Exception:
            # Fallback αν αποτύχει η PowerShell: χρήση wmic
            try:
                output = subprocess.check_output("wmic ComputerSystem get TotalPhysicalMemory", shell=True, text=True, stderr=subprocess.DEVNULL)
                lines = output.strip().split("\n")
                if len(lines) > 1:
                    bytes_val = int(lines[1].strip())
                    specs["ram_gb"] = round(bytes_val / (1024 ** 3), 2)
            except Exception:
                # Αν αποτύχουν όλα, θέτουμε 0.0
                specs["ram_gb"] = 0.0

        # 3. Έλεγχος κάρτας γραφικών (GPU) μέσω PowerShell
        try:
            command = "powershell -NoProfile -Command \"Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name\""
            output = subprocess.check_output(command, shell=True, text=True, stderr=subprocess.DEVNULL)
            gpu_names = [line.strip() for line in output.strip().split("\n") if line.strip()]
            
            if gpu_names:
                specs["gpu_name"] = ", ".join(gpu_names)
                # Έλεγχος αν υπάρχει dedicated κάρτα γραφικών NVIDIA, AMD ή Intel Arc
                for name in gpu_names:
                    lower_name = name.lower()
                    if "nvidia" in lower_name or "geforce" in lower_name or "radeon" in lower_name or "amd" in lower_name or "intel arc" in lower_name:
                        specs["has_gpu"] = True
                        break
        except Exception:
            # Fallback αν αποτύχει η PowerShell: χρήση wmic
            try:
                output = subprocess.check_output("wmic path Win32_VideoController get Name", shell=True, text=True, stderr=subprocess.DEVNULL)
                lines = [line.strip() for line in output.strip().split("\n")[1:] if line.strip()]
                if lines:
                    specs["gpu_name"] = ", ".join(lines)
                    for name in lines:
                        lower_name = name.lower()
                        if "nvidia" in lower_name or "geforce" in lower_name or "radeon" in lower_name or "amd" in lower_name or "intel arc" in lower_name:
                            specs["has_gpu"] = True
                            break
            except Exception:
                specs["has_gpu"] = False
                specs["gpu_name"] = ""

        return specs

    @classmethod
    def check_requirements(cls, requirements: Dict[str, Any], system_specs: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Ελέγχει αν οι πόροι του συστήματος καλύπτουν τις απαιτήσεις ενός εργαλείου.
        Επιστρέφει ένα tuple (bool, list_of_missing_reasons).
        """
        is_ok = True
        missing_reasons = []

        # Έλεγχος RAM
        min_ram = requirements.get("min_ram_gb")
        if min_ram and system_specs["ram_gb"] > 0:
            if system_specs["ram_gb"] < min_ram:
                is_ok = False
                missing_reasons.append(f"Απαιτούνται {min_ram} GB RAM (Έχετε {system_specs['ram_gb']} GB)")

        # Έλεγχος Δίσκου
        min_disk = requirements.get("min_disk_gb")
        if min_disk and system_specs["free_disk_gb"] > 0:
            if system_specs["free_disk_gb"] < min_disk:
                is_ok = False
                missing_reasons.append(f"Απαιτούνται {min_disk} GB ελεύθερου χώρου στο δίσκο C: (Έχετε {system_specs['free_disk_gb']} GB)")

        # Έλεγχος GPU
        requires_gpu = requirements.get("requires_gpu")
        if requires_gpu:
            if not system_specs["has_gpu"]:
                is_ok = False
                missing_reasons.append("Απαιτείται κάρτα γραφικών (NVIDIA/AMD/Intel Arc) για αποδοτική λειτουργία")

        return is_ok, missing_reasons
