import json
from typing import Any

from ai_service.core.prompt_engine import prompt_popquiz_explain
from ai_service.services.gemini_utils import call_gemini, get_api_key, missing_key_error


def generate_answer_explanations(
        lesson_text: str,
        quiz_json: str | list[dict[str, Any]],
        user_answers: list,
) -> str:
    """
    Primește textul lecției, quiz-ul generat și răspunsurile utilizatorului.
    Apelează Gemini pentru a genera un array JSON de explicații.

    :param lesson_text: Textul original al lecției.
    :param quiz_json: JSON string sau listă returnată de generate_pop_quiz.
    :param user_answers: Listă de liste cu răspunsurile selectate de utilizator.
                         (ex: [["Oxygen"], ["Plants", "Algae"], ...])
    """
    if not get_api_key():
        return missing_key_error()

    # Parsare și validare quiz_json
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

    # Construire context de evaluare
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
    return call_gemini(prompt)


if __name__ == "__main__":
    sample_lesson = (
        "Photosynthesis is the process used by plants, algae and certain bacteria "
        "to harness energy from sunlight and turn it into chemical energy. "
        "Oxygen is a byproduct."
    )
    sample_quiz_json = json.dumps([
        {
            "question": "What is a byproduct of photosynthesis?",
            "options": ["Oxygen", "Dirt", "Carbon Dioxide", "Heat"],
            "num_correct": 1,
        },
        {
            "question": "Which organisms use photosynthesis?",
            "options": ["Plants", "Algae", "Mammals", "Fungi"],
            "num_correct": 2,
        },
    ])
    sample_user_answers = [["Oxygen"], ["Plants"]]
    print(generate_answer_explanations(sample_lesson, sample_quiz_json, sample_user_answers))