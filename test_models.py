"""
Smoke test local pentru AI service.

Rulează: python smoke_test.py

Testează toate endpoint-urile cu body-uri minimale, măsoară latența,
și-ți arată ce a picat. Pentru fiecare success, te uiți în terminalul
FastAPI (unde rulează uvicorn) ca să vezi ce model din cascade a răspuns
(log-urile [CASCADE]).
"""

import json
import sys
import time
from typing import Any

try:
    import httpx
except ImportError:
    print("❌ httpx not installed. Run: pip install httpx")
    sys.exit(1)

BASE = "http://127.0.0.1:8000"
TIMEOUT = 250.0  # secunde — Gemini poate dura mult

# Lecție comună pentru toate testele
LESSON = (
    "Photosynthesis is the biochemical process by which plants, algae, and certain bacteria "
    "convert light energy from the sun into chemical energy stored in glucose. "
    "The process occurs primarily in the chloroplasts, organelles containing chlorophyll. "
    "Light-dependent reactions in thylakoid membranes split water, release oxygen, and produce ATP and NADPH. "
    "The Calvin cycle in the stroma uses ATP and NADPH to fix CO2 into glucose. "
    "Overall equation: 6 CO2 + 6 H2O + light → C6H12O6 + 6 O2."
)

# UUID valid pentru testele cu DB (nu trebuie să existe în DB, codul cade pe default 0.5)
TEST_UUID = "550e8400-e29b-41d4-a716-446655440000"

# Sample quiz pentru endpoint-urile de explain
SAMPLE_QUIZ = [
    {
        "question": "What is the main pigment?",
        "options": ["Chlorophyll", "Hemoglobin", "Melanin", "Carotene"],
        "num_correct": 0,
    },
    {
        "question": "Byproduct?",
        "options": ["Oxygen", "Methane", "Hydrogen", "Nitrogen"],
        "num_correct": 0,
    },
    {
        "question": "Where does Calvin cycle occur?",
        "options": ["Stroma", "Thylakoid", "Nucleus", "Cytosol"],
        "num_correct": 0,
    },
    {
        "question": "What is fixed?",
        "options": ["CO2", "O2", "N2", "H2O"],
        "num_correct": 0,
    },
    {
        "question": "Energy carriers?",
        "options": ["ATP and NADPH", "ADP only", "Glucose", "Water"],
        "num_correct": 0,
    },
]

SAMPLE_TEST = [
    {"id": i + 1, **q} for i, q in enumerate(SAMPLE_QUIZ * 2)
]  # 10 întrebări

TESTS = [
    {
        "name": "Health check",
        "method": "GET",
        "path": "/healthz",
        "body": None,
    },
    {
        "name": "Pop quiz generate",
        "method": "POST",
        "path": "/api/v1/subcapitols/check-quiz/questions/generate",
        "body": {"lesson_type": "Biology", "lesson_text": LESSON, "difficulty": "easy"},
    },
    {
        "name": "Pop quiz adaptive",
        "method": "POST",
        "path": "/api/v1/subcapitols/check-quiz/questions/generate/adaptive",
        "body": {"user_id": TEST_UUID, "topic_name": "Biology", "lesson_text": LESSON},
    },
    {
        "name": "Pop quiz explain",
        "method": "POST",
        "path": "/api/v1/subcapitols/check-quiz/explain",
        "body": {
            "lesson_text": LESSON,
            "quiz_json": SAMPLE_QUIZ,
            "user_answers": [
                ["Chlorophyll"],
                ["Methane"],
                ["Stroma"],
                ["CO2"],
                ["ADP only"],
            ],
        },
    },
    {
        "name": "Final test generate",
        "method": "POST",
        "path": "/api/v1/lessons/final-quiz/questions/generate",
        "body": {
            "topic_name": "Biology",
            "lesson_text": LESSON,
            "difficulty": "medium",
        },
    },
    {
        "name": "Final test adaptive",
        "method": "POST",
        "path": "/api/v1/lessons/final-quiz/questions/generate/adaptive",
        "body": {"user_id": TEST_UUID, "topic_name": "Biology", "lesson_text": LESSON},
    },
    {
        "name": "Final test explain",
        "method": "POST",
        "path": "/api/v1/lessons/final-quiz/explain",
        "body": {
            "lesson_text": LESSON,
            "test_json": SAMPLE_TEST,
            "user_answers": [
                ["Chlorophyll"],
                ["Methane"],
                ["Stroma"],
                ["CO2"],
                ["ATP and NADPH"],
                ["Chlorophyll"],
                ["Oxygen"],
                ["Stroma"],
                ["N2"],
                ["ATP and NADPH"],
            ],
        },
    },
    {
        "name": "Paragraph explain",
        "method": "POST",
        "path": "/api/v1/blocks/explain",
        "body": {
            "topic_name": "Biology",
            "confusing_paragraph": LESSON,
            "education_level": "High School",
        },
    },
    {
        "name": "Professor reformat",
        "method": "POST",
        "path": "/api/v1/content-blocks/rewrite",
        "body": {
            "topic_name": "Biology",
            "ambiguous_text": "plants do photosynthesis and stuff and make oxygen idk",
        },
    },
]


def validate_response(test_name: str, status_code: int, body: Any) -> tuple[bool, str]:
    """
    Validări minime per endpoint. Returnează (success, message).
    """
    if status_code != 200:
        # Extrage detail-ul dacă e structurat
        if isinstance(body, dict) and "detail" in body:
            return False, f"HTTP {status_code}: {body['detail'][:150]}"
        return False, f"HTTP {status_code}: {str(body)[:150]}"

    if test_name == "Health check":
        return (body == {"status": "ok"}), f"body={body}"

    if "generate" in test_name and "explain" not in test_name:
        # Pop quiz / final test generate — array de 5 sau 10 obiecte
        if not isinstance(body, list):
            return False, f"Expected list, got {type(body).__name__}"
        expected = 10 if "Final" in test_name else 5
        if len(body) != expected:
            return False, f"Expected {expected} questions, got {len(body)}"
        for i, q in enumerate(body):
            if not all(k in q for k in ["question", "options", "num_correct"]):
                return False, f"Question {i} missing required fields"
            if len(q.get("options", [])) != 4:
                return (
                    False,
                    f"Question {i} has {len(q.get('options', []))} options, expected 4",
                )
        return True, f"{len(body)} questions OK"

    if test_name == "Pop quiz explain":
        if not isinstance(body, list):
            return False, f"Expected list, got {type(body).__name__}"
        if len(body) != 5:
            return False, f"Expected 5 explanations, got {len(body)}"
        return True, f"{len(body)} explanations OK"

    if test_name == "Final test explain":
        # Returnează {content: stringified JSON} pentru Java DTO
        if not isinstance(body, dict) or "content" not in body:
            return False, f"Expected {{content: ...}}, got {type(body).__name__}"
        try:
            inner = json.loads(body["content"])
            if not isinstance(inner, list) or len(inner) != 10:
                return (
                    False,
                    f"content has {len(inner) if isinstance(inner, list) else '?'} items, expected 10",
                )
        except json.JSONDecodeError:
            return False, "content is not valid JSON"
        return True, "10 explanations OK (wrapped in content)"

    if test_name == "Paragraph explain":
        if not isinstance(body, dict) or "content" not in body:
            return False, f"Expected {{content: ...}}, got {type(body).__name__}"
        return True, "content present"

    if test_name == "Professor reformat":
        if not isinstance(body, dict):
            return False, f"Expected dict, got {type(body).__name__}"
        if "corrected_text" not in body:
            return False, "corrected_text missing"
        return True, "corrected_text present"

    return True, "OK"


def run_test(client: httpx.Client, test: dict) -> dict:
    """Execută un test și returnează rezultatul."""
    t0 = time.time()
    try:
        if test["method"] == "GET":
            r = client.get(test["path"])
        else:
            r = client.post(test["path"], json=test["body"])
        dt = (time.time() - t0) * 1000

        try:
            body = r.json()
        except Exception:
            body = r.text

        success, message = validate_response(test["name"], r.status_code, body)
        return {
            "name": test["name"],
            "success": success,
            "status": r.status_code,
            "duration_ms": dt,
            "message": message,
            "body_preview": str(body)[:300] if not success else None,
        }
    except httpx.TimeoutException:
        return {
            "name": test["name"],
            "success": False,
            "status": "TIMEOUT",
            "duration_ms": (time.time() - t0) * 1000,
            "message": f"Timeout after {TIMEOUT}s",
            "body_preview": None,
        }
    except Exception as e:
        return {
            "name": test["name"],
            "success": False,
            "status": "ERROR",
            "duration_ms": (time.time() - t0) * 1000,
            "message": f"{type(e).__name__}: {e}",
            "body_preview": None,
        }


def main():
    print(f"\n{'=' * 80}")
    print(f"  AI Service Smoke Test")
    print(f"  Target: {BASE}")
    print(f"  Timeout: {TIMEOUT}s per request")
    print(f"{'=' * 80}\n")
    print(f"  💡 Uită-te în terminalul FastAPI pentru log-urile [CASCADE]")
    print(f"     ca să vezi ce model răspunde la fiecare request.\n")

    results = []
    with httpx.Client(base_url=BASE, timeout=TIMEOUT) as client:
        for test in TESTS:
            print(f"  ⏳ {test['name']:30s} ", end="", flush=True)
            result = run_test(client, test)
            results.append(result)

            icon = "✅" if result["success"] else "❌"
            print(
                f"\r  {icon} {test['name']:30s} [{result['duration_ms']:6.0f}ms] {result['message']}"
            )

            if result["body_preview"]:
                print(f"     └─ {result['body_preview']}")

    # Summary
    print(f"\n{'=' * 80}")
    passed = sum(1 for r in results if r["success"])
    total = len(results)
    print(f"  Rezultat: {passed}/{total} teste trecute")

    if passed < total:
        print(f"\n  ❌ Teste eșuate:")
        for r in results:
            if not r["success"]:
                print(f"     - {r['name']}: {r['message']}")

    avg_ms = sum(r["duration_ms"] for r in results if r["success"]) / max(passed, 1)
    print(f"\n  Latență medie (success): {avg_ms:.0f}ms")
    print(f"{'=' * 80}\n")

    sys.exit(0 if passed == total else 1)


if __name__ == "__main__":
    main()
