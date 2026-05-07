from ai_service.core.prompt_engine import prompt_finaltest
from ai_service.services.gemini_utils import call_gemini


def generate_final_mcq_test(topic_name: str, lesson_text: str, difficulty: str) -> str:
    """
    Apelează Gemini pentru a genera un test MCQ de 10 întrebări.
    Returnează un JSON string valid.
    """
    prompt = prompt_finaltest(topic_name, lesson_text, difficulty)
    return call_gemini(prompt)
