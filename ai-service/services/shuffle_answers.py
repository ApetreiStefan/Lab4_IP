import json
import random

def travel_json_text():
    with open("quiz.json", "r") as file:
        file_content = file.read()
        json_data = json.loads(file_content)
        for q in json_data["questions"]:
            correct_answer_text = q["options"][q["correctAnswerIndex"]]
            print(correct_answer_text)
        
            random.shuffle(q["options"])
        
            q["correctAnswerIndex"] = q["options"].index(correct_answer_text)

if __name__ == "__maikn__":
    travel_json_text()