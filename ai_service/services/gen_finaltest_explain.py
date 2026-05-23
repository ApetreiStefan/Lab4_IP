import json
from typing import Any

from ai_service.core.prompt_engine import prompt_finaltest_explain
from ai_service.services.gemini_utils import call_gemini, get_api_key, missing_key_error


def grade_and_explain_mcq_test(
        lesson_text: str,
        test_json: str | list[dict[str, Any]],
        user_answers: list,
) -> str:
    """
    Primește textul lecției, testul MCQ generat și răspunsurile utilizatorului.
    Apelează Gemini pentru a evalua răspunsurile și a genera explicații JSON.

    :param lesson_text: Textul original al lecției.
    :param test_json: JSON string sau listă returnată de generate_final_mcq_test.
    :param user_answers: Listă de liste cu răspunsurile selectate de utilizator.
                         (ex: [["Oxygen"], ["Plants", "Algae"], ...])
    """
    if not get_api_key():
        return missing_key_error()

    # Parsare și validare test_json
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
        return json.dumps({
            "error": f"Mismatch: Expected 10 answers, but received {len(user_answers)}."
        })

    # Construire context de evaluare
    evaluation_context = ""
    for i, (q_item, user_ans) in enumerate(zip(test_data, user_answers)):
        question = q_item.get("question", "Unknown Question")
        options = q_item.get("options", [])
        correct_index = q_item.get("num_correct", 0)
        if isinstance(correct_index, int) and 0 <= correct_index < len(options):
            correct_answers = [options[correct_index]]
        else:
            correct_answers = []

        evaluation_context += f"--- Question {i + 1} ---\n"
        evaluation_context += f"Question: {question}\n"
        evaluation_context += f"Actual Correct Answer(s): {correct_answers}\n"
        evaluation_context += f"User's Selected Answer(s): {user_ans}\n\n"

    prompt = prompt_finaltest_explain(lesson_text, evaluation_context)
    return call_gemini(prompt)
