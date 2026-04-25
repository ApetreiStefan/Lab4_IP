import os
import json
import re
import importlib
from typing import Any
from google import genai
from ai_service.core.prompt_engine import prompt_finaltest_explain


def grade_and_explain_mcq_test(
        lesson_text: str,
        test_json: str | list[dict[str, Any]],
        user_answers: list,
) -> str:
    """
    Takes the lesson text, the generated 10-question MCQ test, and the user's answers.
    Calls Gemma-3-27B to evaluate the answers and generate a JSON array of explanations.
    
    :param lesson_text: The original lesson text.
    :param test_json: The JSON string returned by `generate_final_mcq_test`.
    :param user_answers: A list of lists containing the user's selected strings. 
                         (e.g., [["Oxygen"], ["Plants", "Algae"], ...])
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

    # 1. Parse the original test JSON
    if isinstance(test_json, list):
        test_data = test_json
    else:
        try:
            test_data = json.loads(test_json)
        except json.JSONDecodeError:
            return json.dumps({"error": "Invalid test_json provided. Must be a valid JSON string."})

    if not isinstance(test_data, list):
        return json.dumps({"error": "Invalid test_json provided. Must be a JSON array of questions."})

    if len(test_data) != len(user_answers):
        return json.dumps({"error": f"Mismatch: Expected 10 answers, but received {len(user_answers)}."})

    # 2. Build the evaluation context for MCQs only
    evaluation_context = ""
    for i, (q_item, user_ans) in enumerate(zip(test_data, user_answers)):
        question = q_item.get("question", "Unknown Question")
        num_correct = q_item.get("num_correct", 1)

        # Extract correct answers based on the num_correct index rule
        correct_answers = q_item.get("options", [])[:num_correct]

        evaluation_context += f"--- Question {i + 1} ---\n"
        evaluation_context += f"Question: {question}\n"
        evaluation_context += f"Actual Correct Answer(s): {correct_answers}\n"
        evaluation_context += f"User's Selected Answer(s): {user_ans}\n\n"

    # 3. Construct the prompt
    prompt = prompt_finaltest_explain(lesson_text, evaluation_context)

    # 4. Call the API
    try:
        client = genai.Client(api_key=api_key)
        response = client.models.generate_content(
            model='gemma-3-27b-it',
            contents=prompt,
        )

        raw_text = response.text

        # 5. Extract JSON
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
