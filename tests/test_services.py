import json
from unittest.mock import patch, MagicMock
from ai_service.services.gen_popquiz import generate_pop_quiz


@patch("ai_service.services.gen_popquiz.genai.Client")
@patch("ai_service.services.gen_popquiz.os.getenv")
def test_generate_pop_quiz_happy(mock_getenv, mock_client):
    mock_getenv.return_value = "fake_key"
    mock_response = MagicMock()
    mock_response.text = 'Aici este testul tau: {"quiz_type": "pop_quiz"} Succes!'
    mock_client.return_value.models.generate_content.return_value = mock_response

    res = generate_pop_quiz("Math", "1+1", "easy")
    assert json.loads(res) == {"quiz_type": "pop_quiz"}


@patch("ai_service.services.gen_popquiz.genai.Client")
@patch("ai_service.services.gen_popquiz.os.getenv")
def test_generate_pop_quiz_invalid_json(mock_getenv, mock_client):
    mock_getenv.return_value = "fake_key"
    mock_response = MagicMock()
    mock_response.text = 'Eroare: text simplu fara formatare'
    mock_client.return_value.models.generate_content.return_value = mock_response

    res = generate_pop_quiz("Math", "1+1", "easy")
    assert "error" in json.loads(res)


@patch("ai_service.services.gen_popquiz.os.getenv")
def test_generate_pop_quiz_no_api_key(mock_getenv):
    mock_getenv.return_value = None
    res = generate_pop_quiz("Math", "1+1", "easy")
    assert "error" in json.loads(res)
