from ai_service.core.prompt_engine import prompt_finaltest
from ai_service.services.gemini_utils import call_gemini
import sys


def generate_final_mcq_test(topic_name: str, lesson_text: str, difficulty: str) -> str:
    """
    Apelează Gemini pentru a genera un test MCQ de 10 întrebări.
    Returnează un JSON string valid.
    """
    prompt = prompt_finaltest(topic_name, lesson_text, difficulty)
    print(f"\n{'=' * 80}", file=sys.stderr, flush=True)
    print(f"[PROMPT_DEBUG] Topic: {topic_name}", file=sys.stderr, flush=True)
    print(f"[PROMPT_DEBUG] Difficulty: {difficulty}", file=sys.stderr, flush=True)
    print(f"[PROMPT_DEBUG] Prompt:\n{prompt}", file=sys.stderr, flush=True)
    print(f"{'=' * 80}\n", file=sys.stderr, flush=True)
    return call_gemini(prompt)
