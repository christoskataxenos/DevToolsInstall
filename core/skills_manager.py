import os
import shutil
import subprocess
import urllib.request
import zipfile
from typing import Dict, Any, List, Optional, Tuple

class SkillsManager:
    """
    Handles fetching, updating, listing, and exporting AI Agent Skills (.cursorrules, prompts, templates) from GitHub.
    """

    # Λίστα με τα προεπιλεγμένα αποθετήρια (repositories) για AI Skills.
    # Περιλαμβάνει curated κανόνες για Cursor, patterns του Fabric,
    # καθώς και awesome-skills για τη βελτιστοποίηση των builds.
    DEFAULT_REPOS = [
        {
            "name": "Antigravity Awesome Skills",
            "url": "https://github.com/sickn33/antigravity-awesome-skills",
            "desc": "Installable library of 1,500+ agentic skills for Claude Code, Cursor, Codex, Gemini, Antigravity, and more."
        },
        {
            "name": "Cursor Rules (Curated)",
            "url": "https://github.com/PatrickJS/awesome-cursorrules",
            "desc": "Curated collection of system instructions and rule files for Cursor editor."
        },
        {
            "name": "Fabric Patterns",
            "url": "https://github.com/danielmiessler/fabric",
            "desc": "Sleek and modular prompt patterns for terminal-based AI orchestration."
        },
        {
            "name": "Continue Dev Awesome Rules",
            "url": "https://github.com/continuedev/awesome-rules",
            "desc": "High-quality collection of rules compatible with Cursor, Continue, and other assistants."
        },
        {
            "name": "Awesome Windsurf Rules",
            "url": "https://github.com/detailobsessed/awesome-windsurf",
            "desc": "Key resources, community prompts, and best practices for the Windsurf IDE."
        }
    ]


    @classmethod
    def get_global_dir(cls) -> str:
        """Returns the global target storage path for downloaded skills repositories."""
        user_profile = os.environ.get("USERPROFILE", os.path.expanduser("~"))
        global_dir = os.path.join(user_profile, ".ai_skills")
        if not os.path.exists(global_dir):
            os.makedirs(global_dir, exist_ok=True)
        return global_dir

    @classmethod
    def is_git_installed(cls) -> bool:
        """Verifies if Git CLI command is globally accessible in PATH."""
        try:
            subprocess.run(["git", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            return True
        except Exception:
            return False

    @classmethod
    def download_repo(cls, repo_url: str, repo_name: str) -> Tuple[bool, str]:
        """
        Clones a Git repository or pulls updates to the global skills directory.
        Falls back to a direct ZIP archive download if Git command is not available.
        """
        clean_name = repo_name.replace(" ", "_").replace("/", "_").replace("\\", "_")
        target_dir = os.path.join(cls.get_global_dir(), clean_name)

        # 1. Update using git pull if directory exists and is a git repository
        if os.path.exists(target_dir) and os.path.exists(os.path.join(target_dir, ".git")) and cls.is_git_installed():
            try:
                subprocess.run(["git", "-C", target_dir, "pull"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True, f"Successfully updated repo via git pull: {repo_name}"
            except Exception as e:
                return False, f"Failed updating repo via git pull: {str(e)}"

        # Clean old directory if it exists but is not a valid git repository
        if os.path.exists(target_dir):
            try:
                shutil.rmtree(target_dir)
            except Exception as e:
                return False, f"Failed cleaning obsolete directory: {str(e)}"

        # 2. Clone via git clone if Git CLI is available
        if cls.is_git_installed():
            try:
                subprocess.run(["git", "clone", repo_url, target_dir], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True, f"Successfully cloned repo via git clone: {repo_name}"
            except Exception:
                pass  # Fallback to ZIP download on failure

        # 3. Fallback: Download repository as a ZIP archive from GitHub
        try:
            base_url = repo_url.strip()
            if base_url.endswith(".git"):
                base_url = base_url[:-4]
            
            # Construct GitHub ZIP zipball URL
            zip_url = f"{base_url}/archive/refs/heads/main.zip"
            temp_zip = os.path.join(cls.get_global_dir(), f"{clean_name}_temp.zip")
            
            headers = {"User-Agent": "Mozilla/5.0"}
            req = urllib.request.Request(zip_url, headers=headers)
            with urllib.request.urlopen(req) as response, open(temp_zip, "wb") as out_file:
                shutil.copyfileobj(response, out_file)
                
            # Extract downloaded ZIP content
            with zipfile.ZipFile(temp_zip, "r") as zip_ref:
                temp_extract_dir = os.path.join(cls.get_global_dir(), f"{clean_name}_extract_temp")
                os.makedirs(temp_extract_dir, exist_ok=True)
                zip_ref.extractall(temp_extract_dir)
                
                # Relocate inner root directory contents to the clean target location
                extracted_subdirs = os.listdir(temp_extract_dir)
                if extracted_subdirs:
                    source_sub = os.path.join(temp_extract_dir, extracted_subdirs[0])
                    shutil.move(source_sub, target_dir)
                
                # Cleanup temp folders
                shutil.rmtree(temp_extract_dir)
            
            if os.path.exists(temp_zip):
                os.remove(temp_zip)
                
            return True, f"Successfully downloaded ZIP package (Fallback): {repo_name}"
        except Exception as e:
            return False, f"Failed downloading repository ZIP file: {str(e)}"

    @classmethod
    def list_local_skills(cls) -> List[Dict[str, str]]:
        """Returns a list of local repositories synced in the global directory."""
        local_repos = []
        global_dir = cls.get_global_dir()
        if not os.path.exists(global_dir):
            return local_repos
            
        for name in os.listdir(global_dir):
            full_path = os.path.join(global_dir, name)
            if os.path.isdir(full_path) and not name.startswith(".") and not name.endswith("_extract_temp"):
                local_repos.append({
                    "folder_name": name,
                    "full_path": full_path
                })
        return local_repos

    @classmethod
    def export_skill_to_project(cls, skill_source_path: str, project_dir: str, file_name: str) -> Tuple[bool, str]:
        """Copies a target skill config file (e.g. .cursorrules) into the target project folder."""
        if not os.path.exists(skill_source_path):
            return False, "Source skill file does not exist."
            
        if not os.path.exists(project_dir):
            return False, "Target project directory does not exist."
            
        try:
            target_path = os.path.join(project_dir, file_name)
            shutil.copy2(skill_source_path, target_path)
            return True, f"Successfully exported {file_name} to {project_dir}"
        except Exception as e:
            return False, f"Failed exporting file to destination: {str(e)}"
