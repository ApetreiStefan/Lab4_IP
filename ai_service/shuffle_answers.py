import json
import random


def shuffle_options(json_string: str) -> str:
    """
    Primește un string JSON, amestecă opțiunile pentru fiecare întrebare
    și returnează un nou string JSON cu indexurile actualizate.
    """
    json_data = json.loads(json_string)

    for q in json_data.get("questions", []):
        correct_answer_text = q["options"][q["correctAnswerIndex"]]

        random.shuffle(q["options"])

        q["correctAnswerIndex"] = q["options"].index(correct_answer_text)

    return json.dumps(json_data, indent=2, ensure_ascii=False)


if __name__ == "__main__":
    mock_json_string = """
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

    rezultat_string = shuffle_options(mock_json_string)
    print("Rezultatul final (String JSON):")
    print(rezultat_string)