import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch, AsyncMock, MagicMock
from ai_service.main import app
from ai_service.db.database import get_db

client = TestClient(app)


@patch("ai_service.api.ai_endpoints.generate_pop_quiz")
def test_get_pop_quiz_success(mock_ai):
    mock_ai.return_value = json.dumps({"questions": [{"q": "Q1"}]})
    payload = {"lesson_type": "Science", "lesson_text": "Text", "difficulty": "easy"}
    response = client.post("/v1/pop-quiz", json=payload)
    assert response.status_code == 200
    assert "questions" in response.json()


def test_pop_quiz_invalid_data():
    payload_invalid = {"lesson_type": "Science"}  # Lipseste lesson_text
    response = client.post("/v1/pop-quiz", json=payload_invalid)
    assert response.status_code == 422  # Pydantic respinge automat


@patch("ai_service.api.ai_endpoints.generate_answer_explanations")
def test_get_pop_quiz_explanation_success(mock_ai):
    mock_ai.return_value = json.dumps({"explanations": ["Corect", "Greșit"]})
    payload = {"lesson_text": "Text", "quiz_json": [{"q": "Q1"}], "user_answers": [["A"]]}
    response = client.post("/v1/pop-quiz-explanation", json=payload)
    assert response.status_code == 200
    assert "explanations" in response.json()


@patch("ai_service.api.ai_endpoints.generate_final_mcq_test")
def test_get_final_test_success(mock_ai):
    mock_questions = [{"id": i, "q": f"Q{i}"} for i in range(1, 11)]
    mock_ai.return_value = json.dumps(mock_questions)
    payload = {"topic_name": "Math", "lesson_text": "Adunarea...", "difficulty": "medium"}
    response = client.post("/v1/final-test", json=payload)
    assert response.status_code == 200
    assert len(response.json()) == 10


@patch("ai_service.api.ai_endpoints.grade_and_explain_mcq_test")
def test_get_final_test_explanation_success(mock_ai):
    mock_ai.return_value = json.dumps({"score": 10, "feedback": "Excelent"})
    payload = {"lesson_text": "Lectie finala", "test_json": [{"q": "Q1"}], "user_answers": [["B"]]}
    response = client.post("/v1/final-test-explanation", json=payload)
    assert response.status_code == 200
    assert response.json()["score"] == 10


@patch("ai_service.api.ai_endpoints.refine_academic_text")
def test_reformat_professor_success(mock_ai):
    mock_ai.return_value = json.dumps({"refined_text": "Acesta este un text academic."})
    payload = {"topic_name": "Istorie", "ambiguous_text": "A fost odata"}
    response = client.post("/v1/reformat-professor", json=payload)
    assert response.status_code == 200
    assert "refined_text" in response.json()


@patch("ai_service.api.ai_endpoints.generate_paragraph_explanation")
def test_paragraph_explanation_success(mock_ai):
    mock_ai.return_value = {"explanation": "Paragraful explicat"}
    payload = {"topic_name": "Biologie", "confusing_paragraph": "Celulele...", "education_level": "High School"}

    async def override_get_db():
        yield None

    app.dependency_overrides[get_db] = override_get_db
    response = client.post("/v1/paragraph-explanation", json=payload)
    assert response.status_code == 200
    assert response.json()["explanation"] == "Paragraful explicat"
    app.dependency_overrides.clear()  # Curățăm override-ul


@patch("ai_service.api.ai_endpoints.generate_pop_quiz")
def test_db_pop_quiz_success(mock_ai):
    # Simulăm că AI-ul a primit dificultatea 'hard'
    mock_ai.return_value = json.dumps({"questions": [{"q": "Hard Q1"}]})
    payload = {"user_id": "123", "lesson_type": "Science", "lesson_text": "Text"}

    async def override_get_db_high_score():
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = 0.85  # Scorul mare (> 0.7) forțează test HARD
        mock_session.execute.return_value = mock_result
        yield mock_session

    app.dependency_overrides[get_db] = override_get_db_high_score
    response = client.post("/v1/db-pop-quiz", json=payload)

    assert response.status_code == 200
    mock_ai.assert_called_once_with(lesson_type="Science", lesson_text="Text", difficulty="hard")
    app.dependency_overrides.clear()


@patch("ai_service.api.ai_endpoints.generate_final_mcq_test")
def test_db_final_test_success(mock_ai):
    mock_ai.return_value = json.dumps({"questions": [{"q": "Easy Q1"}]})
    payload = {"user_id": "123", "topic_name": "Math", "lesson_text": "Text"}

    async def override_get_db_low_score():
        mock_session = AsyncMock()
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = 0.2  # Scorul mic (< 0.4) forțează test EASY
        mock_session.execute.return_value = mock_result
        yield mock_session

    app.dependency_overrides[get_db] = override_get_db_low_score
    response = client.post("/v1/db-final-test", json=payload)

    assert response.status_code == 200
    mock_ai.assert_called_once_with(topic_name="Math", lesson_text="Text", difficulty="easy")
    app.dependency_overrides.clear()


@patch("ai_service.api.ai_endpoints.generate_pop_quiz")
def test_pop_quiz_invalid_json(mock_ai):
    mock_ai.return_value = "Acesta este un simplu text, nu un JSON valid"
    payload = {"lesson_type": "Science", "lesson_text": "Text", "difficulty": "easy"}

    response = client.post("/v1/pop-quiz", json=payload)

    assert response.status_code == 500
    assert response.json()["detail"] == "Generator returned invalid JSON"


@patch("ai_service.api.ai_endpoints.generate_pop_quiz")
def test_pop_quiz_api_key_error(mock_ai):
    mock_ai.return_value = json.dumps({"error": "Invalid Google API Key provided"})
    payload = {"lesson_type": "Science", "lesson_text": "Text", "difficulty": "easy"}

    response = client.post("/v1/pop-quiz", json=payload)

    assert response.status_code == 400
    assert "API Key" in response.json()["detail"]
