import shutil
import subprocess
from typing import Dict, Any, Tuple, List

class SystemSpecChecker:
    """
    Checker utility to retrieve and validate system specifications (RAM, disk space, and GPU).
    """

    @classmethod
    def get_system_specs(cls) -> Dict[str, Any]:
        """
        Gathers system specs such as RAM in GB, free disk on C: in GB, and GPU details.
        """
        specs = {
            "ram_gb": 0.0,
            "free_disk_gb": 0.0,
            "has_gpu": False,
            "gpu_name": ""
        }

        # 1. Fetch free disk space on C: Drive
        try:
            total, used, free = shutil.disk_usage("C:\\")
            specs["free_disk_gb"] = round(free / (1024 ** 3), 2)
        except Exception:
            specs["free_disk_gb"] = 0.0

        # 2. Ανάκτηση της συνολικής μνήμης RAM του συστήματος μέσω PowerShell cmdlet
        try:
            # Χρήση CimInstance για αξιόπιστη άντληση στοιχείων σε σύγχρονα Windows με παράκαμψη της πολιτικής εκτέλεσης
            command = "powershell -NoProfile -ExecutionPolicy Bypass -Command \"(Get-CimInstance Win32_ComputerSystem).TotalPhysicalMemory\""
            output = subprocess.check_output(command, shell=True, text=True, stderr=subprocess.DEVNULL)
            bytes_val = int(output.strip())
            specs["ram_gb"] = round(bytes_val / (1024 ** 3), 2)
        except Exception:
            # Fallback to wmic tool if PowerShell query failed
            try:
                output = subprocess.check_output("wmic ComputerSystem get TotalPhysicalMemory", shell=True, text=True, stderr=subprocess.DEVNULL)
                lines = output.strip().split("\n")
                if len(lines) > 1:
                    bytes_val = int(lines[1].strip())
                    specs["ram_gb"] = round(bytes_val / (1024 ** 3), 2)
            except Exception:
                specs["ram_gb"] = 0.0

        # 3. Ανάκτηση του ονόματος της κάρτας γραφικών (GPU)
        try:
            # Εκτέλεση με παράκαμψη της πολιτικής εκτέλεσης (ExecutionPolicy Bypass) για αποφυγή περιορισμών
            command = "powershell -NoProfile -ExecutionPolicy Bypass -Command \"Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name\""
            output = subprocess.check_output(command, shell=True, text=True, stderr=subprocess.DEVNULL)
            gpu_names = [line.strip() for line in output.strip().split("\n") if line.strip()]
            
            if gpu_names:
                specs["gpu_name"] = ", ".join(gpu_names)
                # Check for dedicated high-performance GPUs (NVIDIA, AMD, Intel Arc)
                for name in gpu_names:
                    lower_name = name.lower()
                    if any(x in lower_name for x in ["nvidia", "geforce", "radeon", "amd", "intel arc"]):
                        specs["has_gpu"] = True
                        break
        except Exception:
            # Fallback to wmic tool for GPU controller info
            try:
                output = subprocess.check_output("wmic path Win32_VideoController get Name", shell=True, text=True, stderr=subprocess.DEVNULL)
                lines = [line.strip() for line in output.strip().split("\n")[1:] if line.strip()]
                if lines:
                    specs["gpu_name"] = ", ".join(lines)
                    for name in lines:
                        lower_name = name.lower()
                        if any(x in lower_name for x in ["nvidia", "geforce", "radeon", "amd", "intel arc"]):
                            specs["has_gpu"] = True
                            break
            except Exception:
                specs["has_gpu"] = False
                specs["gpu_name"] = ""

        return specs

    @classmethod
    def check_requirements(cls, requirements: Dict[str, Any], system_specs: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Verifies if system resources meet the specific minimum demands of a selected application tool.
        Returns a tuple of (bool_is_met, list_of_reasons_if_unmet).
        """
        is_ok = True
        missing_reasons = []

        # Check RAM size
        min_ram = requirements.get("min_ram_gb")
        if min_ram and system_specs["ram_gb"] > 0:
            if system_specs["ram_gb"] < min_ram:
                is_ok = False
                missing_reasons.append(f"Requires at least {min_ram} GB RAM (System has {system_specs['ram_gb']} GB)")

        # Check C: disk space
        min_disk = requirements.get("min_disk_gb")
        if min_disk and system_specs["free_disk_gb"] > 0:
            if system_specs["free_disk_gb"] < min_disk:
                is_ok = False
                missing_reasons.append(f"Requires at least {min_disk} GB free space on C: (System has {system_specs['free_disk_gb']} GB)")

        # Check GPU availability
        requires_gpu = requirements.get("requires_gpu")
        if requires_gpu:
            if not system_specs["has_gpu"]:
                is_ok = False
                missing_reasons.append("Requires a dedicated GPU card (NVIDIA/AMD/Intel Arc) for optimal operation")

        return is_ok, missing_reasons
