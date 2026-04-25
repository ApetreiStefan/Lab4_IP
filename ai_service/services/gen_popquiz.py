import os
import json
import re
import importlib
from google import genai
from ai_service.core.prompt_engine import prompt_popquiz


def generate_pop_quiz(lesson_type: str, lesson_text: str, difficulty: str) -> str:
    """
    Calls Google AI Studio's Gemma-3-27B to generate a 5-question pop quiz.
    Returns a valid JSON string containing the quiz.
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

    prompt = prompt_popquiz(lesson_type, lesson_text, difficulty)

    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemma-3-27b-it',
            contents=prompt,
        )

        raw_text = response.text

        match = re.search(r'(\{.*\}|\[.*\])', raw_text, re.DOTALL)

        if match:
            json_string = match.group(0)

            json.loads(json_string)
            return json_string
        else:
            return json.dumps({"error": "Failed to extract valid JSON from the AI response."})

    except json.JSONDecodeError:
        return json.dumps({"error": "The AI generated invalid JSON that could not be parsed."})
    except Exception as e:
        return json.dumps({"error": f"API or execution error: {str(e)}"})


if __name__ == "__main__":
    sample_lesson_type = "Biology"
    sample_lesson_text = "Photosynthesis is the process used by plants, algae and certain bacteria to harness energy from sunlight and turn it into chemical energy. Oxygen is a byproduct."

    print(generate_pop_quiz(sample_lesson_type, sample_lesson_text))
