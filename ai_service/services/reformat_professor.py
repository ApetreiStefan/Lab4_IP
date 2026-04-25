import os
import json
import re
import importlib
from google import genai
from ai_service.core.prompt_engine import prompt_reformat_professor


# This file is for the proffesor
def refine_academic_text(topic_name: str, ambiguous_text: str) -> str:
    """
    Calls the AI model acting as an expert Professor to fix grammar,
    resolve ambiguity, and elevate the academic tone of a text,
    while explaining the specific grammar rules violated.
    """
    try:
        dotenv_module = importlib.import_module("dotenv")
        load_dotenv = getattr(dotenv_module, "load_dotenv", None)
        if callable(load_dotenv):
            load_dotenv()
    except Exception:
        pass

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return json.dumps(
            {
                "error": "No API key was provided. Set GEMINI_API_KEY (or GOOGLE_API_KEY) in your environment or in ai_service/.env.",
            }
        )

    prompt = prompt_reformat_professor(topic_name, ambiguous_text)

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemma-3-27b-it',
            contents=prompt,
        )

        raw_text = response.text

        # Trim to extract only JSON
        match = re.search(r'(\{.*\}|\[.*\])', raw_text, re.DOTALL)

        if match:
            json_string = match.group(0)
            json.loads(json_string)  # Validate syntax before returning
            return json_string
        else:
            return json.dumps({"error": "Failed to extract valid JSON from the AI response."})

    except json.JSONDecodeError:
        return json.dumps({"error": "The AI generated invalid JSON that could not be parsed."})
    except Exception as e:
        return json.dumps({"error": f"API or execution error: {str(e)}"})


# --- Example Usage ---
if __name__ == "__main__":
    sample_topic = "Physics: Thermodynamics"
    sample_messy_text = "Heat is like going from the hot thing to the cold thing and it dont stop until they is the same hotness. this is called equilibrium i think."

    print(refine_academic_text(sample_topic, sample_messy_text))
