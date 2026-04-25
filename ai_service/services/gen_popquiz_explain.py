import os
import json
import re
import importlib
from typing import Any
from google import genai
from ai_service.core.prompt_engine import prompt_popquiz_explain


def generate_answer_explanations(
        lesson_text: str,
        quiz_json: str | list[dict[str, Any]],
        user_answers: list,
) -> str:
    """
    Takes the lesson text, the generated quiz, and the user's submitted answers.
    Calls Gemma-3-27B to generate a JSON array of explanations.
    
    :param lesson_text: The original text of the lesson.
    :param quiz_json: The JSON string returned by the `generate_pop_quiz` function.
    :param user_answers: A list of lists containing the user's chosen strings. 
                         (e.g., [["Oxygen"], ["Sunlight", "Water"], ...])
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

    if isinstance(quiz_json, list):
        quiz_data = quiz_json
    else:
        try:
            quiz_data = json.loads(quiz_json)
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid quiz_json provided. Must be a valid JSON string."})

    if not isinstance(quiz_data, list):
        return json.dumps({"error": "Invalid quiz_json provided. Must be a JSON array of questions."})

    if len(quiz_data) != len(user_answers):
        return json.dumps({"error": "Mismatch: The number of user answers does not match the number of questions."})

    evaluation_context = ""
    for i, (quiz_item, user_ans) in enumerate(zip(quiz_data, user_answers)):
        question = quiz_item.get("question", "Unknown Question")
        options = quiz_item.get("options", [])
        num_correct = quiz_item.get("num_correct", 1)

        correct_answers = options[:num_correct]

        evaluation_context += f"Question {i + 1}: {question}\n"
        evaluation_context += f"Actual Correct Answer(s): {correct_answers}\n"
        evaluation_context += f"User's Answer(s): {user_ans}\n\n"

    prompt = prompt_popquiz_explain(lesson_text, len(quiz_data), evaluation_context)

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
            json.loads(json_string)  # Validate syntax
            return json_string
        else:
            return json.dumps({"error": "Failed to extract valid JSON from the AI response."})

    except json.JSONDecodeError:
        return json.dumps({"error": "The AI generated invalid JSON that could not be parsed."})
    except Exception as e:
        return json.dumps({"error": f"API or execution error: {str(e)}"})


if __name__ == "__main__":
    sample_lesson = "Photosynthesis is the process used by plants, algae and certain bacteria to harness energy from sunlight and turn it into chemical energy. Oxygen is a byproduct."

    # Simulating the output from your first function
    sample_quiz_json = json.dumps([
        {
            "question": "What is a byproduct of photosynthesis?",
            "options": ["Oxygen", "Dirt", "Carbon Dioxide", "Heat"],
            "num_correct": 1
        },
        {
            "question": "Which organisms use photosynthesis?",
            "options": ["Plants", "Algae", "Mammals", "Fungi"],
            "num_correct": 2
        }
    ])

    sample_user_answers = [
        ["Oxygen"],
        ["Plants"]
    ]

    result = generate_answer_explanations(sample_lesson, sample_quiz_json, sample_user_answers)
    print(result)
