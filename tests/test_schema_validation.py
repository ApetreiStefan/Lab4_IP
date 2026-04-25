import pytest
import json


def test_final_test_schema_is_valid():
    mock_ai_final_test_response = """
    [
        {
            "id": 1,
            "question": "Ce este fotosinteza?",
            "options": ["Procesul de hrănire a plantelor", "Eliminarea oxigenului", "Plânsul plantelor", "Mersul pe jos"],
            "num_correct": 2
        },
        {
            "id": 2,
            "question": "Care este formula apei?",
            "options": ["H2O", "CO2", "O2"],
            "num_correct": 1
        }
    ]
    """

    data = json.loads(mock_ai_final_test_response)

    assert isinstance(data, list), "Răspunsul trebuie să fie un Array (Listă)"

    for question_obj in data:
        assert "id" in question_obj
        assert "question" in question_obj
        assert "options" in question_obj
        assert "num_correct" in question_obj

        assert type(question_obj["id"]) == int
        assert type(question_obj["options"]) == list
        assert type(question_obj["num_correct"]) == int

        assert question_obj["num_correct"] <= len(question_obj["options"])


def test_final_test_explanation_schema_is_valid():
    mock_ai_explanation_response = """
    [
        {
            "question": "Ce este gravitația?",
            "is_fully_correct": false,
            "explanation": "Ai ales varianta B, dar gravitația este forța de atracție...",
            "key_takeaway": "Gravitația ține planetele pe orbită."
        }
    ]
    """

    data = json.loads(mock_ai_explanation_response)

    assert isinstance(data, list)

    for feedback_obj in data:
        assert "question" in feedback_obj
        assert "is_fully_correct" in feedback_obj
        assert "explanation" in feedback_obj
        assert "key_takeaway" in feedback_obj

        assert type(feedback_obj["is_fully_correct"]) == bool