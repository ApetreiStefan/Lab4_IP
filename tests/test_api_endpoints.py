import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import patch
from ai_service.main import app

client = TestClient(app)


@patch("ai_service.api.endpoints.generate_pop_quiz")
def test_pop_quiz_endpoint_success(mock_ai):
    mock_ai.return_value = '{"questions": []}'

    payload = {
        "lesson_type": "Science",
        "lesson_text": "Test content",
        "difficulty": "easy"
    }

    response = client.post("/get-pop-quiz", json=payload)

    assert response.status_code == 200
    mock_ai.assert_called_once()


def test_pop_quiz_endpoint_respinge_date_invalide():
    payload_invalid = {
        "lesson_type": "Science"
    }

    response = client.post("/get-pop-quiz", json=payload_invalid)

    assert response.status_code == 422


@patch("ai_service.api.endpoints.generate_final_mcq_test")
def test_get_final_test_success(mock_ai):
    mock_questions = [
        {"id": i, "question": f"Q{i}", "options": ["A", "B"], "num_correct": 1}
        for i in range(1, 11)
    ]
    mock_ai.return_value = json.dumps(mock_questions)

    payload = {
        "topic_name": "Python Arrays",
        "lesson_text": "Arrays are used to store multiple values...",
        "difficulty": "medium"
    }

    response = client.post("/get-final-test", json=payload)

    assert response.status_code == 200
    data = response.json()
    assert len(data) == 10  # Verificăm cerința ta critică de 10 întrebări
    assert data[0]["id"] == 1


@patch("ai_service.api.endpoints.generate_answer_explanations")
def test_get_pop_quiz_explanation_success(mock_ai):
    mock_ai.return_value = json.dumps({"explanations": ["Corect", "Greșit"]})

    payload = {
        "lesson_text": "Textul lectiei",
        "quiz_json": [{"question": "Q1", "answer": "A"}],
        "user_answers": [["A"]]
    }

    response = client.post("/get-pop-quiz-explanation", json=payload)
    assert response.status_code == 200
    assert "explanations" in response.json()


@patch("ai_service.api.endpoints.generate_final_mcq_test")
def test_get_final_test_success(mock_ai):
    mock_questions = [{"id": i, "q": f"Q{i}"} for i in range(1, 11)]
    mock_ai.return_value = json.dumps(mock_questions)

    payload = {
        "topic_name": "Matematica",
        "lesson_text": "Adunarea...",
        "difficulty": "medium"
    }

    response = client.post("/get-final-test", json=payload)
    assert response.status_code == 200
    assert len(response.json()) == 10


@patch("ai_service.api.endpoints.grade_and_explain_mcq_test")
def test_get_final_test_explanation_success(mock_ai):
    mock_ai.return_value = json.dumps({"score": 10, "feedback": "Excelent"})

    payload = {
        "lesson_text": "Lectie finala",
        "test_json": [{"q": "Q1"}],
        "user_answers": [["B"]]
    }

    response = client.post("/get-final-test-explanation", json=payload)
    assert response.status_code == 200
    assert response.json()["score"] == 10


@patch("ai_service.api.endpoints.refine_academic_text")
def test_reformat_professor_success(mock_ai):
    mock_ai.return_value = json.dumps({"refined_text": "Acesta este un text academic."})

    payload = {
        "topic_name": "Istorie",
        "ambiguous_text": "A fost odata ca niciodata"
    }

    response = client.post("/reformat-professor", json=payload)
    assert response.status_code == 200
    assert "refined_text" in response.json()


@pytest.mark.asyncio
@patch("ai_service.api.endpoints.generate_paragraph_explanation")
async def test_get_paragraph_explanation_success(mock_ai):
    mock_ai.return_value = {"explanation": "Paragraful explicat"}

    payload = {
        "topic_name": "Biologie",
        "confusing_paragraph": "Celulele sunt...",
        "education_level": "High School"
    }

    response = client.post("/get-paragraph-explanation", json=payload)
    assert response.status_code == 200
    assert response.json()["explanation"] == "Paragraful explicat"
