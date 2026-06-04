import os
import shutil
import subprocess
import urllib.request
import zipfile
from typing import Dict, Any, List, Optional, Tuple

class SkillsManager:
    """
    Κλάση για τη διαχείριση (λήψη, ενημέρωση, εξαγωγή) των AI Agent Skills από το GitHub.
    """

    DEFAULT_REPOS = [
        {
            "name": "Cursor Rules (Curated)",
            "url": "https://github.com/PatrickJS/awesome-cursorrules",
            "desc": "Συλλογή από βελτιστοποιημένα αρχεία κανόνων για τον Cursor editor."
        },
        {
            "name": "Fabric Patterns",
            "url": "https://github.com/danielmiessler/fabric",
            "desc": "Έτοιμα AI prompt patterns για CLI και αυτοματοποιήσεις."
        }
    ]

    @classmethod
    def get_global_dir(cls) -> str:
        # Επιστρέφει τη διαδρομή του global φακέλου αποθήκευσης των skills
        user_profile = os.environ.get("USERPROFILE", os.path.expanduser("~"))
        global_dir = os.path.join(user_profile, ".ai_skills")
        if not os.path.exists(global_dir):
            os.makedirs(global_dir, exist_ok=True)
        return global_dir

    @classmethod
    def is_git_installed(cls) -> bool:
        # Ελέγχει αν το Git είναι διαθέσιμο στη γραμμή εντολών
        try:
            subprocess.run(["git", "--version"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
            return True
        except Exception:
            return False

    @classmethod
    def download_repo(cls, repo_url: str, repo_name: str) -> Tuple[bool, str]:
        """
        Κατεβάζει ή ενημερώνει ένα repository στο global φάκελο.
        Επιστρέφει (success, status_message).
        """
        # Καθαρισμός του ονόματος του repo για χρήση ως όνομα φακέλου
        clean_name = repo_name.replace(" ", "_").replace("/", "_").replace("\\", "_")
        target_dir = os.path.join(cls.get_global_dir(), clean_name)

        # Αν υπάρχει ήδη και έχουμε Git, κάνουμε git pull
        if os.path.exists(target_dir) and os.path.exists(os.path.join(target_dir, ".git")) and cls.is_git_installed():
            try:
                # Εκτέλεση git pull για ενημέρωση
                subprocess.run(["git", "-C", target_dir, "pull"], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True, f"Ενημερώθηκε επιτυχώς μέσω git pull: {repo_name}"
            except Exception as e:
                return False, f"Αποτυχία ενημέρωσης μέσω git pull: {str(e)}"

        # Διαγραφή παλαιού φακέλου αν υπάρχει αλλά δεν είναι σωστό git repo
        if os.path.exists(target_dir):
            try:
                shutil.rmtree(target_dir)
            except Exception as e:
                return False, f"Αποτυχία καθαρισμού παλαιού φακέλου: {str(e)}"

        # Προσπάθεια clone αν υπάρχει Git
        if cls.is_git_installed():
            try:
                subprocess.run(["git", "clone", repo_url, target_dir], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                return True, f"Λήψη επιτυχής μέσω git clone: {repo_name}"
            except Exception as e:
                # Αν αποτύχει το clone, θα δοκιμάσουμε το fallback με zip
                pass

        # Fallback λήψη μέσω zip αρχείου από το GitHub
        try:
            # Κατασκευή του zip url (π.χ. https://github.com/user/repo/archive/refs/heads/main.zip)
            # Αφαίρεση του .git από το url αν υπάρχει
            base_url = repo_url.strip()
            if base_url.endswith(".git"):
                base_url = base_url[:-4]
            
            # Προσθήκη zip κατάληξης
            zip_url = f"{base_url}/archive/refs/heads/main.zip"
            
            # Προσωρινή τοποθεσία zip αρχείου
            temp_zip = os.path.join(cls.get_global_dir(), f"{clean_name}_temp.zip")
            
            # Λήψη του αρχείου
            headers = {"User-Agent": "Mozilla/5.0"}
            req = urllib.request.Request(zip_url, headers=headers)
            with urllib.request.urlopen(req) as response, open(temp_zip, "wb") as out_file:
                shutil.copyfileobj(response, out_file)
                
            # Αποσυμπίεση του zip
            with zipfile.ZipFile(temp_zip, "r") as zip_ref:
                # Δημιουργία προσωρινού φακέλου εξαγωγής
                temp_extract_dir = os.path.join(cls.get_global_dir(), f"{clean_name}_extract_temp")
                os.makedirs(temp_extract_dir, exist_ok=True)
                zip_ref.extractall(temp_extract_dir)
                
                # Ο φάκελος zip του GitHub συνήθως περιέχει έναν υποφάκελο repo-main.
                # Μετακινούμε τα περιεχόμενά του στον τελικό φάκελο.
                extracted_subdirs = os.listdir(temp_extract_dir)
                if extracted_subdirs:
                    source_sub = os.path.join(temp_extract_dir, extracted_subdirs[0])
                    shutil.move(source_sub, target_dir)
                
                # Καθαρισμός προσωρινών αρχείων
                shutil.rmtree(temp_extract_dir)
            
            if os.path.exists(temp_zip):
                os.remove(temp_zip)
                
            return True, f"Λήψη επιτυχής μέσω ZIP αρχείου (Fallback): {repo_name}"
        except Exception as e:
            return False, f"Αποτυχία λήψης ZIP αρχείου: {str(e)}"

    @classmethod
    def list_local_skills(cls) -> List[Dict[str, str]]:
        """
        Επιστρέφει λίστα με τα τοπικά αποθηκευμένα repositories.
        """
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
        """
        Αντιγράφει ένα συγκεκριμένο skill αρχείο (π.χ. .cursorrules) στο project.
        """
        if not os.path.exists(skill_source_path):
            return False, "Το αρχείο πηγής δεν υπάρχει."
            
        if not os.path.exists(project_dir):
            return False, "Ο φάκελος προορισμού του project δεν υπάρχει."
            
        try:
            target_path = os.path.join(project_dir, file_name)
            shutil.copy2(skill_source_path, target_path)
            return True, f"Το αρχείο {file_name} αντιγράφηκε επιτυχώς στο {project_dir}"
        except Exception as e:
            return False, f"Αποτυχία αντιγραφής αρχείου: {str(e)}"
