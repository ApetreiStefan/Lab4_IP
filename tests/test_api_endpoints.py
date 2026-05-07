import pytest
import json
import uuid
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from ai_service.main import app
from ai_service.db.database import get_db

client = TestClient(app)


# ==========================================
# HELPERS
# ==========================================

def make_db_override(scalar_value):
    """Creează un override pentru get_db care returnează un scalar fix."""
    class MockResult:
        def scalar_one_or_none(self):
            return scalar_value

    async def override():
        db = AsyncMock()
        db.execute.return_value = MockResult()
        yield db

    return override


def apply_db_override(scalar_value):
    app.dependency_overrides[get_db] = make_db_override(scalar_value)


def clear_db_override():
    app.dependency_overrides.pop(get_db, None)


def null_db_override():
    """DB override care yielduiește None — pentru endpoint-uri care nu îl folosesc real."""
    async def override():
        yield None
    app.dependency_overrides[get_db] = override


# ==========================================
# 1. POP QUIZ — ENDPOINT NORMAL
# ==========================================

@patch("ai_service.api.ai_endpoints.generate_pop_quiz")
def test_pop_quiz_success(mock_ai):
    mock_ai.return_value = '{"questions": ["Q1"]}'
    payload = {"lesson_type": "Bio", "lesson_text": "Text", "difficulty": "easy"}
    response = client.post("/api/v1/subcapitols/check-quiz/questions/generate", json=payload)
    assert response.status_code == 200
    assert response.json() == {"questions": ["Q1"]}


@patch("ai_service.api.ai_endpoints.generate_pop_quiz")
def test_pop_quiz_invalid_json(mock_ai):
    mock_ai.return_value = "Nu sunt un JSON"
    payload = {"lesson_type": "Bio", "lesson_text": "Text", "difficulty": "easy"}
    response = client.post("/api/v1/subcapitols/check-quiz/questions/generate", json=payload)
    assert response.status_code == 500
    assert "invalid JSON" in response.json()["detail"]


@patch("ai_service.api.ai_endpoints.generate_pop_quiz")
def test_pop_quiz_api_key_error(mock_ai):
    mock_ai.return_value = '{"error": "GEMINI_API_KEY not found"}'
    payload = {"lesson_type": "Bio", "lesson_text": "Text", "difficulty": "easy"}
    response = client.post("/api/v1/subcapitols/check-quiz/questions/generate", json=payload)
    assert response.status_code == 400


@patch("ai_service.api.ai_endpoints.generate_pop_quiz")
def test_pop_quiz_google_api_key_error(mock_ai):
    mock_ai.return_value = '{"error": "google_api_key is missing"}'
    payload = {"lesson_type": "Bio", "lesson_text": "Text", "difficulty": "easy"}
    response = client.post("/api/v1/subcapitols/check-quiz/questions/generate", json=payload)
    assert response.status_code == 400


@patch("ai_service.api.ai_endpoints.generate_pop_quiz")
def test_pop_quiz_generic_500_error(mock_ai):
    """Eroare AI fara legatura cu API key → 500."""
    mock_ai.return_value = '{"error": "Model overloaded, try again"}'
    payload = {"lesson_type": "Bio", "lesson_text": "Text", "difficulty": "easy"}
    response = client.post("/api/v1/subcapitols/check-quiz/questions/generate", json=payload)
    assert response.status_code == 500


# ==========================================
# 2. POP QUIZ — ENDPOINT ADAPTIV (DB)
# ==========================================

@patch("ai_service.api.ai_endpoints.generate_pop_quiz")
def test_db_pop_quiz_hard(mock_ai):
    """Scor 0.9 → hard."""
    mock_ai.return_value = '{"quiz": "data"}'
    apply_db_override(0.9)
    try:
        payload = {"user_id": str(uuid.uuid4()), "topic_name": "Math", "lesson_text": "Text"}
        response = client.post("/api/v1/subcapitols/check-quiz/questions/generate/adaptive", json=payload)
        assert response.status_code == 200
        mock_ai.assert_called_once_with(lesson_type="Math", lesson_text="Text", difficulty="hard")
    finally:
        clear_db_override()


@patch("ai_service.api.ai_endpoints.generate_pop_quiz")
def test_db_pop_quiz_medium(mock_ai):
    """Scor 0.55 (intre 0.4 si 0.7) → medium."""
    mock_ai.return_value = '{"quiz": "data"}'
    apply_db_override(0.55)
    try:
        payload = {"user_id": str(uuid.uuid4()), "topic_name": "Math", "lesson_text": "Text"}
        response = client.post("/api/v1/subcapitols/check-quiz/questions/generate/adaptive", json=payload)
        assert response.status_code == 200
        mock_ai.assert_called_once_with(lesson_type="Math", lesson_text="Text", difficulty="medium")
    finally:
        clear_db_override()


@patch("ai_service.api.ai_endpoints.generate_pop_quiz")
def test_db_pop_quiz_easy(mock_ai):
    """Scor 0.2 (sub 0.4) → easy."""
    mock_ai.return_value = '{"quiz": "data"}'
    apply_db_override(0.2)
    try:
        payload = {"user_id": str(uuid.uuid4()), "topic_name": "Math", "lesson_text": "Text"}
        response = client.post("/api/v1/subcapitols/check-quiz/questions/generate/adaptive", json=payload)
        assert response.status_code == 200
        mock_ai.assert_called_once_with(lesson_type="Math", lesson_text="Text", difficulty="easy")
    finally:
        clear_db_override()


@patch("ai_service.api.ai_endpoints.generate_pop_quiz")
def test_db_pop_quiz_no_mastery_defaults_medium(mock_ai):
    """Niciun rand in DB (None) → default 0.5 → medium."""
    mock_ai.return_value = '{"quiz": "data"}'
    apply_db_override(None)
    try:
        payload = {"user_id": str(uuid.uuid4()), "topic_name": "Math", "lesson_text": "Text"}
        response = client.post("/api/v1/subcapitols/check-quiz/questions/generate/adaptive", json=payload)
        assert response.status_code == 200
        mock_ai.assert_called_once_with(lesson_type="Math", lesson_text="Text", difficulty="medium")
    finally:
        clear_db_override()


def test_db_pop_quiz_invalid_uuid():
    payload = {"user_id": "not-a-uuid", "topic_name": "Math", "lesson_text": "Text"}
    response = client.post("/api/v1/subcapitols/check-quiz/questions/generate/adaptive", json=payload)
    assert response.status_code == 400
    assert "Invalid UUID" in response.json()["detail"]


@patch("ai_service.api.ai_endpoints.generate_pop_quiz")
def test_db_pop_quiz_ai_invalid_json(mock_ai):
    mock_ai.return_value = "not json"
    apply_db_override(0.5)
    try:
        payload = {"user_id": str(uuid.uuid4()), "topic_name": "Math", "lesson_text": "Text"}
        response = client.post("/api/v1/subcapitols/check-quiz/questions/generate/adaptive", json=payload)
        assert response.status_code == 500
        assert "invalid JSON" in response.json()["detail"]
    finally:
        clear_db_override()


@patch("ai_service.api.ai_endpoints.generate_pop_quiz")
def test_db_pop_quiz_api_key_error(mock_ai):
    mock_ai.return_value = '{"error": "GEMINI_API_KEY missing"}'
    apply_db_override(0.5)
    try:
        payload = {"user_id": str(uuid.uuid4()), "topic_name": "Math", "lesson_text": "Text"}
        response = client.post("/api/v1/subcapitols/check-quiz/questions/generate/adaptive", json=payload)
        assert response.status_code == 400
    finally:
        clear_db_override()


@patch("ai_service.api.ai_endpoints.generate_pop_quiz")
def test_db_pop_quiz_generic_ai_error(mock_ai):
    mock_ai.return_value = '{"error": "Internal model error"}'
    apply_db_override(0.5)
    try:
        payload = {"user_id": str(uuid.uuid4()), "topic_name": "Math", "lesson_text": "Text"}
        response = client.post("/api/v1/subcapitols/check-quiz/questions/generate/adaptive", json=payload)
        assert response.status_code == 500
    finally:
        clear_db_override()


# ==========================================
# 3. POP QUIZ — EXPLAIN
# ==========================================

@patch("ai_service.api.ai_endpoints.generate_answer_explanations")
def test_pop_quiz_explanation_success_string_input(mock_ai):
    """quiz_json trimis ca string JSON."""
    mock_ai.return_value = '[{"question": "Q1", "correct": true}]'
    payload = {
        "lesson_text": "Lesson",
        "quiz_json": '[{"q": "Q1"}]',
        "user_answers": [["A"]]
    }
    response = client.post("/api/v1/subcapitols/check-quiz/explain", json=payload)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@patch("ai_service.api.ai_endpoints.generate_answer_explanations")
def test_pop_quiz_explanation_success_list_input(mock_ai):
    """quiz_json trimis ca list → ramura json.dumps din endpoint."""
    mock_ai.return_value = '[{"explanation": "ok"}]'
    payload = {
        "lesson_text": "Lesson",
        "quiz_json": [{"q": "Q1", "answers": ["A", "B"]}],
        "user_answers": [["A"]]
    }
    response = client.post("/api/v1/subcapitols/check-quiz/explain", json=payload)
    assert response.status_code == 200


@patch("ai_service.api.ai_endpoints.generate_answer_explanations")
def test_pop_quiz_explanation_invalid_json(mock_ai):
    mock_ai.return_value = "not json at all"
    payload = {"lesson_text": "T", "quiz_json": [], "user_answers": []}
    response = client.post("/api/v1/subcapitols/check-quiz/explain", json=payload)
    assert response.status_code == 500
    assert "invalid JSON" in response.json()["detail"]


@patch("ai_service.api.ai_endpoints.generate_answer_explanations")
def test_pop_quiz_explanation_mismatch_error(mock_ai):
    mock_ai.return_value = '{"error": "mismatch between answers"}'
    payload = {"lesson_text": "T", "quiz_json": [], "user_answers": []}
    response = client.post("/api/v1/subcapitols/check-quiz/explain", json=payload)
    assert response.status_code == 400


@patch("ai_service.api.ai_endpoints.generate_answer_explanations")
def test_pop_quiz_explanation_invalid_quiz_json_error(mock_ai):
    mock_ai.return_value = '{"error": "invalid quiz_json format"}'
    payload = {"lesson_text": "T", "quiz_json": [], "user_answers": []}
    response = client.post("/api/v1/subcapitols/check-quiz/explain", json=payload)
    assert response.status_code == 400


@patch("ai_service.api.ai_endpoints.generate_answer_explanations")
def test_pop_quiz_explanation_api_key_error(mock_ai):
    mock_ai.return_value = '{"error": "GEMINI_API_KEY not set"}'
    payload = {"lesson_text": "T", "quiz_json": [], "user_answers": []}
    response = client.post("/api/v1/subcapitols/check-quiz/explain", json=payload)
    assert response.status_code == 400


@patch("ai_service.api.ai_endpoints.generate_answer_explanations")
def test_pop_quiz_explanation_generic_500(mock_ai):
    mock_ai.return_value = '{"error": "Unknown service error"}'
    payload = {"lesson_text": "T", "quiz_json": [], "user_answers": []}
    response = client.post("/api/v1/subcapitols/check-quiz/explain", json=payload)
    assert response.status_code == 500


# ==========================================
# 4. FINAL TEST — ENDPOINT NORMAL
# ==========================================

@patch("ai_service.api.ai_endpoints.generate_final_mcq_test")
def test_final_test_success(mock_ai):
    mock_ai.return_value = json.dumps([{"id": i} for i in range(1, 11)])
    payload = {"topic_name": "IT", "lesson_text": "Text", "difficulty": "medium"}
    response = client.post("/api/v1/lessons/final-quiz/questions/generate", json=payload)
    assert response.status_code == 200
    assert len(response.json()) == 10


@patch("ai_service.api.ai_endpoints.generate_final_mcq_test")
def test_final_test_invalid_json(mock_ai):
    mock_ai.return_value = "broken json {"
    payload = {"topic_name": "IT", "lesson_text": "Text", "difficulty": "easy"}
    response = client.post("/api/v1/lessons/final-quiz/questions/generate", json=payload)
    assert response.status_code == 500
    assert "invalid JSON" in response.json()["detail"]


@patch("ai_service.api.ai_endpoints.generate_final_mcq_test")
def test_final_test_api_key_error(mock_ai):
    mock_ai.return_value = '{"error": "google_api_key not configured"}'
    payload = {"topic_name": "IT", "lesson_text": "Text", "difficulty": "easy"}
    response = client.post("/api/v1/lessons/final-quiz/questions/generate", json=payload)
    assert response.status_code == 400


@patch("ai_service.api.ai_endpoints.generate_final_mcq_test")
def test_final_test_generic_error(mock_ai):
    mock_ai.return_value = '{"error": "Something went wrong"}'
    payload = {"topic_name": "IT", "lesson_text": "Text", "difficulty": "easy"}
    response = client.post("/api/v1/lessons/final-quiz/questions/generate", json=payload)
    assert response.status_code == 500


# ==========================================
# 5. FINAL TEST — ENDPOINT ADAPTIV (DB)
# ==========================================

@patch("ai_service.api.ai_endpoints.generate_final_mcq_test")
def test_db_final_test_easy(mock_ai):
    """Scor 0.2 → easy."""
    mock_ai.return_value = '[]'
    apply_db_override(0.2)
    try:
        payload = {"user_id": str(uuid.uuid4()), "topic_name": "History", "lesson_text": "Text"}
        response = client.post("/api/v1/lessons/final-quiz/questions/generate/adaptive", json=payload)
        assert response.status_code == 200
        mock_ai.assert_called_once_with(topic_name="History", lesson_text="Text", difficulty="easy")
    finally:
        clear_db_override()


@patch("ai_service.api.ai_endpoints.generate_final_mcq_test")
def test_db_final_test_medium(mock_ai):
    """Scor 0.5 → medium."""
    mock_ai.return_value = '[]'
    apply_db_override(0.5)
    try:
        payload = {"user_id": str(uuid.uuid4()), "topic_name": "History", "lesson_text": "Text"}
        response = client.post("/api/v1/lessons/final-quiz/questions/generate/adaptive", json=payload)
        assert response.status_code == 200
        mock_ai.assert_called_once_with(topic_name="History", lesson_text="Text", difficulty="medium")
    finally:
        clear_db_override()


@patch("ai_service.api.ai_endpoints.generate_final_mcq_test")
def test_db_final_test_hard(mock_ai):
    """Scor 0.8 → hard."""
    mock_ai.return_value = '{"questions": []}'
    apply_db_override(0.8)
    try:
        payload = {"user_id": str(uuid.uuid4()), "topic_name": "History", "lesson_text": "Text"}
        response = client.post("/api/v1/lessons/final-quiz/questions/generate/adaptive", json=payload)
        assert response.status_code == 200
        mock_ai.assert_called_once_with(topic_name="History", lesson_text="Text", difficulty="hard")
    finally:
        clear_db_override()


@patch("ai_service.api.ai_endpoints.generate_final_mcq_test")
def test_db_final_test_no_mastery_defaults_medium(mock_ai):
    """Niciun rand in DB (None) → default 0.5 → medium."""
    mock_ai.return_value = '[]'
    apply_db_override(None)
    try:
        payload = {"user_id": str(uuid.uuid4()), "topic_name": "History", "lesson_text": "Text"}
        response = client.post("/api/v1/lessons/final-quiz/questions/generate/adaptive", json=payload)
        assert response.status_code == 200
        mock_ai.assert_called_once_with(topic_name="History", lesson_text="Text", difficulty="medium")
    finally:
        clear_db_override()


def test_db_final_test_invalid_uuid():
    payload = {"user_id": "bad-uuid", "topic_name": "History", "lesson_text": "Text"}
    response = client.post("/api/v1/lessons/final-quiz/questions/generate/adaptive", json=payload)
    assert response.status_code == 400
    assert "Invalid UUID" in response.json()["detail"]


@patch("ai_service.api.ai_endpoints.generate_final_mcq_test")
def test_db_final_test_ai_invalid_json(mock_ai):
    mock_ai.return_value = "not json"
    apply_db_override(0.5)
    try:
        payload = {"user_id": str(uuid.uuid4()), "topic_name": "History", "lesson_text": "Text"}
        response = client.post("/api/v1/lessons/final-quiz/questions/generate/adaptive", json=payload)
        assert response.status_code == 500
    finally:
        clear_db_override()


@patch("ai_service.api.ai_endpoints.generate_final_mcq_test")
def test_db_final_test_api_key_error(mock_ai):
    mock_ai.return_value = '{"error": "GEMINI_API_KEY not set"}'
    apply_db_override(0.5)
    try:
        payload = {"user_id": str(uuid.uuid4()), "topic_name": "History", "lesson_text": "Text"}
        response = client.post("/api/v1/lessons/final-quiz/questions/generate/adaptive", json=payload)
        assert response.status_code == 400
    finally:
        clear_db_override()


@patch("ai_service.api.ai_endpoints.generate_final_mcq_test")
def test_db_final_test_generic_error(mock_ai):
    mock_ai.return_value = '{"error": "Service unavailable"}'
    apply_db_override(0.5)
    try:
        payload = {"user_id": str(uuid.uuid4()), "topic_name": "History", "lesson_text": "Text"}
        response = client.post("/api/v1/lessons/final-quiz/questions/generate/adaptive", json=payload)
        assert response.status_code == 500
    finally:
        clear_db_override()


# ==========================================
# 6. FINAL TEST — EXPLAIN
# ==========================================

@patch("ai_service.api.ai_endpoints.grade_and_explain_mcq_test")
def test_final_test_explanation_success_string_input(mock_ai):
    mock_ai.return_value = '[{"question": "Q1", "correct": true, "explanation": "E1"}]'
    payload = {
        "lesson_text": "Lesson",
        "test_json": '[{"q": "Q1"}]',
        "user_answers": [["A"]]
    }
    response = client.post("/api/v1/lessons/final-quiz/explain", json=payload)
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@patch("ai_service.api.ai_endpoints.grade_and_explain_mcq_test")
def test_final_test_explanation_list_input(mock_ai):
    """test_json ca list → ramura json.dumps."""
    mock_ai.return_value = '[{"explanation": "ok"}]'
    payload = {
        "lesson_text": "Lesson",
        "test_json": [{"q": "Q1"}],
        "user_answers": [["A"]]
    }
    response = client.post("/api/v1/lessons/final-quiz/explain", json=payload)
    assert response.status_code == 200


@patch("ai_service.api.ai_endpoints.grade_and_explain_mcq_test")
def test_final_test_explanation_invalid_json(mock_ai):
    mock_ai.return_value = "not json"
    payload = {"lesson_text": "T", "test_json": [], "user_answers": []}
    response = client.post("/api/v1/lessons/final-quiz/explain", json=payload)
    assert response.status_code == 500
    assert "invalid JSON" in response.json()["detail"]


@patch("ai_service.api.ai_endpoints.grade_and_explain_mcq_test")
def test_final_test_explanation_api_key_error(mock_ai):
    mock_ai.return_value = '{"error": "GEMINI_API_KEY missing"}'
    payload = {"lesson_text": "T", "test_json": [], "user_answers": []}
    response = client.post("/api/v1/lessons/final-quiz/explain", json=payload)
    assert response.status_code == 400


@patch("ai_service.api.ai_endpoints.grade_and_explain_mcq_test")
def test_final_test_explanation_mismatch_error(mock_ai):
    mock_ai.return_value = '{"error": "mismatch between test answers"}'
    payload = {"lesson_text": "T", "test_json": [], "user_answers": []}
    response = client.post("/api/v1/lessons/final-quiz/explain", json=payload)
    assert response.status_code == 400


@patch("ai_service.api.ai_endpoints.grade_and_explain_mcq_test")
def test_final_test_explanation_invalid_test_json_error(mock_ai):
    mock_ai.return_value = '{"error": "invalid test_json provided"}'
    payload = {"lesson_text": "T", "test_json": [], "user_answers": []}
    response = client.post("/api/v1/lessons/final-quiz/explain", json=payload)
    assert response.status_code == 400


@patch("ai_service.api.ai_endpoints.grade_and_explain_mcq_test")
def test_final_test_explanation_generic_500(mock_ai):
    mock_ai.return_value = '{"error": "Model timeout"}'
    payload = {"lesson_text": "T", "test_json": [], "user_answers": []}
    response = client.post("/api/v1/lessons/final-quiz/explain", json=payload)
    assert response.status_code == 500


# ==========================================
# 7. PARAGRAPH EXPLANATION
#
# FIX CRITIC: generate_paragraph_explanation este async (apelata cu await
# in endpoint). Cu @patch normal primesti MagicMock care nu poate fi
# await-at → TypeError → testul pica cu 500 si nu acopera codul.
# Solutia: new_callable=AsyncMock
# ==========================================

@patch(
    "ai_service.api.ai_endpoints.generate_paragraph_explanation",
    new_callable=AsyncMock,
)
def test_paragraph_explanation_success_dict(mock_ai):
    """Serviciul returneaza dict → json.dumps(result) → content e string JSON."""
    mock_ai.return_value = {"explanation": "Aceasta este o explicatie"}
    null_db_override()
    try:
        payload = {"topic_name": "X", "confusing_paragraph": "Y", "education_level": "Z"}
        response = client.post("/api/v1/blocks/explain", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "explanation" in data["content"]
    finally:
        clear_db_override()


@patch(
    "ai_service.api.ai_endpoints.generate_paragraph_explanation",
    new_callable=AsyncMock,
)
def test_paragraph_explanation_success_string(mock_ai):
    """Serviciul returneaza string → ramura else → content e str(result)."""
    mock_ai.return_value = "Explicatie simpla ca string"
    null_db_override()
    try:
        payload = {"topic_name": "X", "confusing_paragraph": "Y", "education_level": "Z"}
        response = client.post("/api/v1/blocks/explain", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "Explicatie simpla" in data["content"]
    finally:
        clear_db_override()


@patch(
    "ai_service.api.ai_endpoints.generate_paragraph_explanation",
    new_callable=AsyncMock,
)
def test_paragraph_explanation_service_returns_error(mock_ai):
    """Serviciul returneaza dict cu camp error → HTTPException 500."""
    mock_ai.return_value = {"error": "AI service failed internally"}
    null_db_override()
    try:
        payload = {"topic_name": "X", "confusing_paragraph": "Y", "education_level": "Z"}
        response = client.post("/api/v1/blocks/explain", json=payload)
        assert response.status_code == 500
        assert "AI service failed internally" in response.json()["detail"]
    finally:
        clear_db_override()


@patch(
    "ai_service.api.ai_endpoints.generate_paragraph_explanation",
    new_callable=AsyncMock,
)
def test_paragraph_explanation_unexpected_exception(mock_ai):
    """Exceptie neasteptata → prinsa de except general → 500."""
    mock_ai.side_effect = RuntimeError("Unexpected crash in service")
    null_db_override()
    try:
        payload = {"topic_name": "X", "confusing_paragraph": "Y", "education_level": "Z"}
        response = client.post("/api/v1/blocks/explain", json=payload)
        assert response.status_code == 500
        assert "Unexpected crash in service" in response.json()["detail"]
    finally:
        clear_db_override()


# ==========================================
# 8. REFORMAT PROFESSOR
# ==========================================

@patch("ai_service.api.ai_endpoints.refine_academic_text")
def test_reformat_professor_success(mock_ai):
    mock_ai.return_value = '{"rewritten": "Text academic clar si precis."}'
    payload = {"topic_name": "Physics", "ambiguous_text": "nu stiu cum sa explic"}
    response = client.post("/api/v1/content-blocks/rewrite", json=payload)
    assert response.status_code == 200
    assert "rewritten" in response.json()


@patch("ai_service.api.ai_endpoints.refine_academic_text")
def test_reformat_professor_invalid_json(mock_ai):
    mock_ai.return_value = "Invalid JSON"
    payload = {"topic_name": "T", "ambiguous_text": "A"}
    response = client.post("/api/v1/content-blocks/rewrite", json=payload)
    assert response.status_code == 500
    assert "invalid JSON" in response.json()["detail"]


@patch("ai_service.api.ai_endpoints.refine_academic_text")
def test_reformat_professor_gemini_api_key_error(mock_ai):
    mock_ai.return_value = '{"error": "GEMINI_API_KEY not configured"}'
    payload = {"topic_name": "T", "ambiguous_text": "A"}
    response = client.post("/api/v1/content-blocks/rewrite", json=payload)
    assert response.status_code == 400


@patch("ai_service.api.ai_endpoints.refine_academic_text")
def test_reformat_professor_google_api_key_error(mock_ai):
    mock_ai.return_value = '{"error": "google_api_key invalid"}'
    payload = {"topic_name": "T", "ambiguous_text": "A"}
    response = client.post("/api/v1/content-blocks/rewrite", json=payload)
    assert response.status_code == 400


@patch("ai_service.api.ai_endpoints.refine_academic_text")
def test_reformat_professor_generic_error(mock_ai):
    mock_ai.return_value = '{"error": "Rate limit exceeded"}'
    payload = {"topic_name": "T", "ambiguous_text": "A"}
    response = client.post("/api/v1/content-blocks/rewrite", json=payload)
    assert response.status_code == 500