"""
Utilitare comune pentru serviciile AI.
Elimină codul duplicat de dotenv loading, API key retrieval și apel Gemini.
"""

import os
import json
import re
import importlib

from google import genai


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


def call_gemini(prompt: str) -> str:
    """
    Apelează Gemini cu prompt-ul dat și returnează primul bloc JSON extras.
    Returnează un JSON string — fie rezultatul valid, fie un dict {"error": "..."}.
    """
    api_key = get_api_key()
    if not api_key:
        return missing_key_error()

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt,
        )
        raw_text = response.text

        match = re.search(r"(\{.*\}|\[.*\])", raw_text, re.DOTALL)
        if match:
            json_string = match.group(0)
            json.loads(json_string)  # validare sintaxă
            return json_string

        return json.dumps({"error": "Failed to extract valid JSON from the AI response."})

    except json.JSONDecodeError:
        return json.dumps({"error": "The AI generated invalid JSON that could not be parsed."})
    except Exception as e:
        return json.dumps({"error": f"API or execution error: {str(e)}"})