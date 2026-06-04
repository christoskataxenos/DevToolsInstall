import json
import urllib.request
import urllib.error
from typing import List, Dict, Any, Tuple

class AIDiagnosticAgent:
    """
    AI Diagnostic Agent to search installation issues on DuckDuckGo and diagnose them using local Ollama.
    """

    OLLAMA_URL = "http://localhost:11434"
    DEFAULT_MODEL = "qwen2.5-coder:1.5b"

    @classmethod
    def search_web(cls, query: str) -> List[Dict[str, str]]:
        """
        Executes a web search via the duckduckgo_search library.
        Returns a list of search result hits containing title, link, and snippet.
        """
        results = []
        try:
            from duckduckgo_search import DDGS
            with DDGS() as ddgs:
                search_results = list(ddgs.text(query, max_results=5))
                for r in search_results:
                    results.append({
                        "title": r.get("title", ""),
                        "link": r.get("href", ""),
                        "snippet": r.get("body", "")
                    })
        except Exception:
            # Silence error logs to prevent GUI crashes on rate limits or offline states
            pass
        return results

    @classmethod
    def is_ollama_running(cls) -> bool:
        """Checks if a local Ollama server instance is active on localhost:11434."""
        try:
            req = urllib.request.Request(f"{cls.OLLAMA_URL}/api/tags")
            with urllib.request.urlopen(req, timeout=2) as response:
                return response.status == 200
        except Exception:
            return False

    @classmethod
    def is_model_installed(cls, model_name: str = DEFAULT_MODEL) -> bool:
        """Verifies if the selected model is pulled locally in Ollama."""
        try:
            req = urllib.request.Request(f"{cls.OLLAMA_URL}/api/tags")
            with urllib.request.urlopen(req, timeout=2) as response:
                data = json.loads(response.read().decode("utf-8"))
                models = [m["name"] for m in data.get("models", [])]
                for m in models:
                    if model_name in m or m in model_name:
                        return True
                return False
        except Exception:
            return False

    @classmethod
    def pull_model(cls, model_name: str = DEFAULT_MODEL) -> Tuple[bool, str]:
        """Pulls/downloads the selected LLM model to Ollama."""
        try:
            url = f"{cls.OLLAMA_URL}/api/pull"
            payload = json.dumps({"name": model_name, "stream": False}).encode("utf-8")
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=120) as response:
                if response.status == 200:
                    return True, f"Model {model_name} successfully downloaded!"
                return False, "Failed to download model from Ollama library."
        except Exception as e:
            return False, f"Error communicating with local Ollama: {str(e)}"

    @classmethod
    def diagnose_with_ollama(
        cls, 
        tool_name: str, 
        error_log: str, 
        search_results: List[Dict[str, str]], 
        model_name: str = DEFAULT_MODEL
    ) -> Tuple[bool, str, str]:
        """
        Sends the logs and web context to Ollama for error diagnosis.
        Returns a tuple (success_boolean, explanation_text, proposed_fix_command).
        Note: The LLM prompt asks for Greek response to explain to the user,
        supporting the Greek language settings on the app client interface.
        """
        if not cls.is_ollama_running():
            return False, "Ollama is not running. Please start Ollama local server and try again.", ""

        if not cls.is_model_installed(model_name):
            success, msg = cls.pull_model(model_name)
            if not success:
                return False, f"Failed to pull model {model_name} automatically. Details: {msg}", ""

        search_context = ""
        if search_results:
            search_context = "\n".join([
                f"- Title: {r['title']}\n  Snippet: {r['snippet']}"
                for r in search_results
            ])
        else:
            search_context = "No relevant internet search results found."

        # The prompt directs Ollama to return a Greek explanation of the error,
        # but wraps the suggested PowerShell fix script in [FIX_CMD] tags.
        prompt = f"""You are an expert AI Diagnostic Agent for Windows software installation errors.
A user tried to install '{tool_name}' and it failed with the following logs:

[ERROR LOG]
{error_log}

We searched the web and found this diagnostic context:
{search_context}

Provide a short, clear explanation in Greek of what went wrong and how the user can fix it.
If there is a specific PowerShell or command line instruction that can resolve the issue (e.g. running an installer bypass, installing a missing SDK dependency, cleaning registry), output the command at the end wrapped inside [FIX_CMD] and [/FIX_CMD] tags.

Example format:
Η εγκατάσταση απέτυχε επειδή...
Για να το διορθώσετε...
[FIX_CMD]winget install --id Dependency.ID --force[/FIX_CMD]

If no direct script applies, do not include the [FIX_CMD] tags.
"""

        try:
            url = f"{cls.OLLAMA_URL}/api/generate"
            payload = json.dumps({
                "model": model_name,
                "prompt": prompt,
                "stream": False
            }).encode("utf-8")
            
            req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
            with urllib.request.urlopen(req, timeout=45) as response:
                if response.status == 200:
                    result_data = json.loads(response.read().decode("utf-8"))
                    full_response = result_data.get("response", "").strip()
                    
                    explanation = full_response
                    proposed_cmd = ""
                    
                    if "[FIX_CMD]" in full_response and "[/FIX_CMD]" in full_response:
                        parts = full_response.split("[FIX_CMD]")
                        explanation = parts[0].strip()
                        cmd_part = parts[1].split("[/FIX_CMD]")
                        proposed_cmd = cmd_part[0].strip()
                        
                        if len(cmd_part) > 1 and cmd_part[1].strip():
                            explanation += "\n\n" + cmd_part[1].strip()
                            
                    return True, explanation, proposed_cmd
                    
                return False, "Failed connecting to local Ollama API endpoint.", ""
        except Exception as e:
            return False, f"Exception diagnosing via Ollama: {str(e)}", ""
