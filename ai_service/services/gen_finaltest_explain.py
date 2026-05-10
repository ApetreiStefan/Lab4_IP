import json
from typing import Any

from ai_service.core.prompt_engine import prompt_finaltest_explain
from ai_service.services.gemini_utils import call_gemini, get_api_key, missing_key_error


def _normalize_test_json(test_json: str | list[dict[str, Any]]) -> list[dict[str, Any]]:
    """
    Acceptă:
    - list[dict] (ideal)
    - string JSON normal
    - string JSON dublu-encodat (bug din Java)
    """

    if isinstance(test_json, list):
        return test_json

    if not isinstance(test_json, str):
        raise ValueError("test_json must be string or list")

    # primul parse
    try:
        data = json.loads(test_json)
    except json.JSONDecodeError:
        raise ValueError("Invalid JSON string in test_json")

    # dacă încă e string => dublu-encodat
    if isinstance(data, str):
        try:
            data = json.loads(data)
        except json.JSONDecodeError:
            raise ValueError("Double-encoded JSON is invalid")

    if not isinstance(data, list):
        raise ValueError("test_json must be a JSON array (list)")

    return data


def grade_and_explain_mcq_test(
        lesson_text: str,
        test_json: str | list[dict[str, Any]],
        user_answers: list,
) -> str:

    if not get_api_key():
        return missing_key_error()

    # ✅ normalize JSON (FIX PRINCIPAL)
    try:
        test_data = _normalize_test_json(test_json)
    except ValueError as e:
        return json.dumps({"error": str(e)})

    # validare răspunsuri
    if not user_answers:
        return json.dumps({"error": "user_answers must not be empty"})

    if len(test_data) != len(user_answers):
        return json.dumps({
            "error": f"Mismatch: expected {len(test_data)} answers, got {len(user_answers)}"
        })

    # construire context evaluare
    evaluation_context = ""

    for i, (q_item, user_ans) in enumerate(zip(test_data, user_answers)):
        question = q_item.get("question", "Unknown Question")
        options = q_item.get("options", [])
        num_correct = q_item.get("num_correct", 1)

        correct_answers = options[:num_correct] if isinstance(options, list) else []

        evaluation_context += f"--- Question {i + 1} ---\n"
        evaluation_context += f"Question: {question}\n"
        evaluation_context += f"Correct Answer(s): {correct_answers}\n"
        evaluation_context += f"User Answer(s): {user_ans}\n\n"

    prompt = prompt_finaltest_explain(lesson_text, evaluation_context)

    return call_gemini(prompt)
