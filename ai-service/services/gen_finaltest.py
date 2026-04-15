import os
import json
import re
import importlib
from google import genai

def generate_final_mcq_test(topic_name: str, lesson_text: str) -> str:
    """
    Calls Google AI Studio's Gemma-3-27B to generate a 10-question MCQ test.
    Returns a valid JSON string.
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
                "error": "No API key was provided. Set GEMINI_API_KEY (or GOOGLE_API_KEY) in your environment or in ai-service/.env.",
            }
        )

    prompt = f"""You are an expert curriculum designer creating a multiple-choice final test for the topic: {topic_name}.

CRITICAL REQUIREMENTS:
1. Generate exactly 10 questions based on the provided Lesson Text. Some can have one correct answer, and some can have multiple correct answers.
2. Output ONLY valid JSON. No conversational text and no markdown formatting blocks.
3. The JSON must be an array of exactly 10 objects.
4. Each object must have four fields:
   - "id" (integer 1-10)
   - "question" (string)
   - "options" (array of strings)
   - "num_correct" (integer representing how many correct answers there are)
5. The correct answer(s) MUST ALWAYS be placed at the very beginning of the "options" array (from index 0 up to `num_correct` - 1). 
6. All incorrect answers must follow the correct answers in the "options" array.

Lesson Text:
{lesson_text}
"""

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
            json.loads(json_string) # Validate syntax
            return json_string
        else:
            return json.dumps({"error": "Failed to extract valid JSON from the AI response."})

    except json.JSONDecodeError:
        return json.dumps({"error": "The AI generated invalid JSON that could not be parsed."})
    except Exception as e:
        return json.dumps({"error": f"API or execution error: {str(e)}"})