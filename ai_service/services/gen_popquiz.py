from ai_service.core.prompt_engine import prompt_popquiz
from ai_service.services.gemini_utils import call_gemini


def generate_pop_quiz(lesson_type: str, lesson_text: str, difficulty: str) -> str:
    """
    Apelează Gemini pentru a genera un pop quiz de 5 întrebări.
    Returnează un JSON string valid.
    """
    prompt = prompt_popquiz(lesson_type, lesson_text, difficulty)
    return call_gemini(prompt)


if __name__ == "__main__":
    print(generate_pop_quiz(
        "Biology",
        "Photosynthesis is the process used by plants, algae and certain bacteria "
        "to harness energy from sunlight and turn it into chemical energy. Oxygen is a byproduct.",
        "medium"
    ))