"""
Utilitare comune pentru serviciile AI.
Elimină codul duplicat de dotenv loading, API key retrieval și apel Gemini.
Include protecție la rate-limits (Tenacity) și Fallback pe model secundar.
"""

import os
import json
import re
import importlib
import time

from google import genai
from tenacity import retry, stop_after_attempt, wait_exponential


def _load_dotenv() -> None:
    """Încearcă să încarce .env dacă python-dotenv este instalat."""
    try:
        dotenv_module = importlib.import_module("dotenv")
        load_dotenv = getattr(dotenv_module, "load_dotenv", None)
        if callable(load_dotenv):
            load_dotenv()
    except Exception:
        pass


def get_api_key() -> str | None:
    """Returnează GEMINI_API_KEY sau GOOGLE_API_KEY din environment."""
    _load_dotenv()
    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


def missing_key_error() -> str:
    """JSON de eroare standard pentru API key lipsă."""
    return json.dumps({
        "error": (
            "No API key was provided. "
            "Set GEMINI_API_KEY (or GOOGLE_API_KEY) in your environment or in ai_service/.env."
        )
    })


# --- LAYER 1: Reîncercare (Tenacity) ---
# Încearcă de max 3 ori. Pauză exponențială (ex: 2s, 4s, 8s) între încercări.
@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10), reraise=True)
def _execute_gemini_call(client: genai.Client, model_name: str, prompt: str) -> str:
    response = client.models.generate_content(
        model=model_name,
        contents=prompt,
    )
    return response.text


def call_gemini(prompt: str) -> str:
    """
    Apelează Gemini cu prompt-ul dat, protejat de retries și model fallback.
    Returnează un JSON string — fie rezultatul valid, fie un dict {"error": "..."}.
    """
    api_key = get_api_key()
    if not api_key:
        return missing_key_error()

    client = genai.Client(api_key=api_key)
    raw_text = ""

    try:
        # Încercăm cu modelul principal (cu retries)
        raw_text = _execute_gemini_call(client, "gemini-2.5-flash", prompt)
    except Exception as e:
        error_msg = str(e).lower()

        # --- LAYER 2: Fallback Logic ---
        # Verificăm dacă eroarea ține de suprasolicitare sau limită de cotă
        if any(k in error_msg for k in ["quota", "exhausted", "overloaded", "503", "429"]):
            print(f"[Fallback] Modelul gemini-2.5-flash a eșuat. Comutare pe gemini-1.5-flash... Motiv: {error_msg}")
            try:
                time.sleep(1)  # Pauză scurtă de siguranță înainte de fallback
                # Executăm fallback (tot cu retries, direct pe modelul vechi)
                raw_text = _execute_gemini_call(client, "gemini-1.5-flash", prompt)
            except Exception as fallback_e:
                return json.dumps({"error": f"API fallback error: {str(fallback_e)}"})
        else:
            return json.dumps({"error": f"API execution error: {str(e)}"})

    # Extragerea JSON-ului
    try:
        match = re.search(r"(\{.*\}|\[.*\])", raw_text, re.DOTALL)
        if match:
            json_string = match.group(0)
            json.loads(json_string)  # validare sintaxă
            return json_string

        return json.dumps({"error": "Failed to extract valid JSON from the AI response."})

    except json.JSONDecodeError:
        return json.dumps({"error": "The AI generated invalid JSON that could not be parsed."})
    except Exception as e:
        return json.dumps({"error": f"Parsing error: {str(e)}"})
