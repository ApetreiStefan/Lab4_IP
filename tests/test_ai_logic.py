# tests/test_ai_logic.py

import pytest
import json
from ai_service.shuffle_answers import shuffle_options


def test_shuffle_keeps_all_elements_and_updates_index():
    mock_string = """
    {
        "questions": [
            {
                "questionText": "Care este capitala Franței?",
                "options": ["Paris", "Londra", "Berlin", "Madrid"],
                "correctAnswerIndex": 0
            }
        ]
    }
    """

    shuffled_string = shuffle_options(mock_string)

    result_dict = json.loads(shuffled_string)
    prima_intrebare = result_dict["questions"][0]

    assert len(prima_intrebare["options"]) == 4
    assert "Paris" in prima_intrebare["options"]

    noul_index = prima_intrebare["correctAnswerIndex"]
    assert prima_intrebare["options"][noul_index] == "Paris"
