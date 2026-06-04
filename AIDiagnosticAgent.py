import json
import urllib.request
import urllib.error
from typing import List, Dict, Any, Tuple

class AIDiagnosticAgent:
    """
    Κλάση AI Agent για τη διάγνωση σφαλμάτων εγκατάστασης μέσω DuckDuckGo και Ollama.
    """

    OLLAMA_URL = "http://localhost:11434"
    DEFAULT_MODEL = "qwen2.5-coder:1.5b"

    @classmethod
    def search_web(cls, query: str) -> List[Dict[str, str]]:
        """
        Εκτελεί αναζήτηση στο διαδίκτυο μέσω της βιβλιοθήκης duckduckgo_search.
        Επιστρέφει μια λίστα από λεξικά με τίτλο, σύνδεσμο και απόσπασμα (snippet).
        """
        results = []
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                # Αναζήτηση κειμένου με όριο 5 αποτελέσματα
                search_results = list(ddgs.text(query, max_results=5))
                for r in search_results:
                    results.append({
                        "title": r.get("title", ""),
                        "link": r.get("href", ""),
                        "snippet": r.get("body", "")
                    })
        except Exception as e:
            # Σε περίπτωση rate limit ή σφάλματος δικτύου, επιστρέφουμε άδεια λίστα
            # χωρίς να κρασάρει η εφαρμογή
            pass
        return results

    @classmethod
    def is_ollama_running(cls) -> bool:
        """
        Ελέγχει αν το Ollama εκτελείται τοπικά.
        """
        try:
            req = urllib.request.Request(f"{cls.OLLAMA_URL}/api/tags")
            with urllib.request.urlopen(req, timeout=2) as response:
                return response.status == 200
        except Exception:
            return False

    @classmethod
    def is_model_installed(cls, model_name: str = DEFAULT_MODEL) -> bool:
        """
        Ελέγχει αν το συγκεκριμένο μοντέλο είναι εγκατεστημένο στο Ollama.
        """
        try:
            req = urllib.request.Request(f"{cls.OLLAMA_URL}/api/tags")
            with urllib.request.urlopen(req, timeout=2) as response:
                data = json.loads(response.read().decode("utf-8"))
                models = [m["name"] for m in data.get("models", [])]
                # Έλεγχος αν υπάρχει το μοντέλο (και με το tag/version π.χ. :latest ή :1.5b)
                for m in models:
                    if model_name in m or m in model_name:
                        return True
                return False
        except Exception:
            return False

    @classmethod
    def pull_model(cls, model_name: str = DEFAULT_MODEL) -> Tuple[bool, str]:
        """
        Κατεβάζει (pull) το μοντέλο στο Ollama.
        """
        try:
            url = f"{cls.OLLAMA_URL}/api/pull"
            payload = json.dumps({"name": model_name, "stream": False}).encode("utf-8")
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as response:
                if response.status == 200:
                    return True, f"Το μοντέλο {model_name} κατέβηκε επιτυχώς!"
                return False, "Αποτυχία κατά τη λήψη του μοντέλου."
        except Exception as e:
            return False, f"Σφάλμα κατά τη σύνδεση με το Ollama: {str(e)}"

    @classmethod
    def diagnose_with_ollama(
        cls, 
        tool_name: str, 
        error_log: str, 
        search_results: List[Dict[str, str]], 
        model_name: str = DEFAULT_MODEL
    ) -> Tuple[bool, str, str]:
        """
        Στέλνει το σφάλμα και τα αποτελέσματα της αναζήτησης στο Ollama για διάγνωση.
        Επιστρέφει (success, explanation, proposed_command).
        """
        if not cls.is_ollama_running():
            return False, "Το Ollama δεν εκτελείται. Παρακαλώ εκκινήστε το Ollama και δοκιμάστε ξανά.", ""

        # Έλεγχος αν το μοντέλο είναι εγκατεστημένο
        if not cls.is_model_installed(model_name):
            # Προσπάθεια αυτόματης λήψης
            success, msg = cls.pull_model(model_name)
            if not success:
                return False, f"Αποτυχία αυτόματης λήψης του μοντέλου {model_name}. Λεπτομέρειες: {msg}", ""

        # Κατασκευή του prompt με σαφείς οδηγίες για ελληνική απάντηση και PowerShell εντολή διόρθωσης
        search_context = ""
        if search_results:
            search_context = "\n".join([
                f"- Τίτλος: {r['title']}\n  Απόσπασμα: {r['snippet']}"
                for r in search_results
            ])
        else:
            search_context = "Δεν βρέθηκαν αποτελέσματα στο διαδίκτυο."

        prompt = f"""Είσαι ένας έμπειρος AI Diagnostic Agent για σφάλματα εγκατάστασης λογισμικού στα Windows.
Ένας χρήστης προσπάθησε να εγκαταστήσει το εργαλείο '{tool_name}' και απέτυχε με το ακόλουθο σφάλμα:

[ERROR LOG]
{error_log}

Κάναμε μια αναζήτηση στο διαδίκτυο και βρήκαμε τις παρακάτω πληροφορίες:
{search_context}

Συνέθεσε μια σύντομη, σαφή εξήγηση στα Ελληνικά για το τι φταίει και πώς λύνεται το πρόβλημα.
Αν υπάρχει μια συγκεκριμένη εντολή PowerShell ή CLI που μπορεί να τρέξει ο χρήστης για να διορθώσει το σφάλμα (π.χ. καθαρισμός registry, εγκατάσταση κάποιου dependency, παράκαμψη hash check), γράψε την στο τέλος περικλειόμενη από τα tags [FIX_CMD] και [/FIX_CMD].

Παράδειγμα μορφής απάντησης:
Η εγκατάσταση απέτυχε επειδή...
Για να το διορθώσετε...
[FIX_CMD]winget install --id Dependency.ID --force[/FIX_CMD]

Αν δεν υπάρχει κάποια εντολή, μην βάλεις τα tags [FIX_CMD].
"""

        try:
            url = f"{cls.OLLAMA_URL}/api/generate"
            payload = json.dumps({
                "model": model_name,
                "prompt": prompt,
                "stream": False
            }).encode("utf-8")
            
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=30) as response:
                if response.status == 200:
                    result_data = json.loads(response.read().decode("utf-8"))
                    full_response = result_data.get("response", "").strip()
                    
                    # Διαχωρισμός της εξήγησης από την εντολή διόρθωσης
                    explanation = full_response
                    proposed_cmd = ""
                    
                    # Εξαγωγή της εντολής αν υπάρχουν τα tags
                    if "[FIX_CMD]" in full_response and "[/FIX_CMD]" in full_response:
                        parts = full_response.split("[FIX_CMD]")
                        explanation = parts[0].strip()
                        cmd_part = parts[1].split("[/FIX_CMD]")
                        proposed_cmd = cmd_part[0].strip()
                        
                        # Αν υπάρχει υπόλοιπο κείμενο μετά το [/FIX_CMD], το προσθέτουμε στην εξήγηση
                        if len(cmd_part) > 1 and cmd_part[1].strip():
                            explanation += "\n\n" + cmd_part[1].strip()
                            
                    return True, explanation, proposed_cmd
                    
                return False, "Αποτυχία επικοινωνίας με το API του Ollama.", ""
        except Exception as e:
            return False, f"Σφάλμα κατά τη διάγνωση με το Ollama: {str(e)}", ""
