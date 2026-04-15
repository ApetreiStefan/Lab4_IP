import os
import json
import re
import importlib
from google import genai

def generate_pop_quiz(lesson_type: str, lesson_text: str) -> str:
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
                "error": "No API key was provided. Set GEMINI_API_KEY (or GOOGLE_API_KEY) in your environment or in ai-service/.env.",
            }
        )

    prompt = f"""You are an expert educational assistant. Create a pop quiz based on the provided {lesson_type} lesson.

CRITICAL REQUIREMENTS:
1. Generate exactly 5 questions. Some can have one correct answer, and some can have multiple correct answers.
2. Output ONLY valid JSON. No conversational text, no explanations, and no markdown formatting blocks.
3. The JSON must be an array of objects.
4. Each object must have three fields: 
   - "question" (string)
   - "options" (array of strings)
   - "num_correct" (integer representing how many correct answers there are).
5. The correct answer(s) MUST ALWAYS be placed at the very beginning of the "options" array (from index 0 up to `num_correct` - 1). 
6. All incorrect answers must follow the correct answers in the "options" array.

Lesson Text:
{lesson_text}
"""

    try:
        client = genai.Client(api_key=api_key)
        # Using the standard instruction-tuned model name for Gemma-3-27B on AI Studio
        response = client.models.generate_content(
            model='gemma-3-27b-it', 
            contents=prompt,
        )
        
        raw_text = response.text

        # Trim the response to extract only the JSON structure
        # This regex looks for the first '[' or '{' and the last ']' or '}'
        match = re.search(r'(\{.*\}|\[.*\])', raw_text, re.DOTALL)

        if match:
            json_string = match.group(0)
            
            # Verify it is actually valid JSON before returning
            # If it fails, it will jump to the except block
            json.loads(json_string) 
            return json_string
        else:
            # Fallback if no JSON structure is found
            return json.dumps({"error": "Failed to extract valid JSON from the AI response."})

    except json.JSONDecodeError:
        return json.dumps({"error": "The AI generated invalid JSON that could not be parsed."})
    except Exception as e:
        return json.dumps({"error": f"API or execution error: {str(e)}"})

# --- Example Usage ---
if __name__ == "__main__":
    sample_lesson_type = "Biology"
    sample_lesson_text = "Photosynthesis is the process used by plants, algae and certain bacteria to harness energy from sunlight and turn it into chemical energy. Oxygen is a byproduct."
    
    print(generate_pop_quiz(sample_lesson_type, sample_lesson_text))