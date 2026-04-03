import json
import re
from google import genai

def grade_and_explain_mcq_test(lesson_text: str, test_json: str, user_answers: list) -> str:
    """
    Takes the lesson text, the generated 10-question MCQ test, and the user's answers.
    Calls Gemma-3-27B to evaluate the answers and generate a JSON array of explanations.
    
    :param lesson_text: The original lesson text.
    :param test_json: The JSON string returned by `generate_final_mcq_test`.
    :param user_answers: A list of lists containing the user's selected strings. 
                         (e.g., [["Oxygen"], ["Plants", "Algae"], ...])
    """
    client = genai.Client()

    # 1. Parse the original test JSON
    try:
        test_data = json.loads(test_json)
    except json.JSONDecodeError:
        return json.dumps({"error": "Invalid test_json provided. Must be a valid JSON string."})

    if len(test_data) != len(user_answers):
        return json.dumps({"error": f"Mismatch: Expected 10 answers, but received {len(user_answers)}."})

    # 2. Build the evaluation context for MCQs only
    evaluation_context = ""
    for i, (q_item, user_ans) in enumerate(zip(test_data, user_answers)):
        question = q_item.get("question", "Unknown Question")
        num_correct = q_item.get("num_correct", 1)
        
        # Extract correct answers based on the num_correct index rule
        correct_answers = q_item.get("options", [])[:num_correct]
        
        evaluation_context += f"--- Question {i+1} ---\n"
        evaluation_context += f"Question: {question}\n"
        evaluation_context += f"Actual Correct Answer(s): {correct_answers}\n"
        evaluation_context += f"User's Selected Answer(s): {user_ans}\n\n"

    # 3. Construct the prompt
    prompt = f"""You are an expert, empathetic educational tutor grading a 10-question multiple-choice test. 
Review the original lesson text and the evaluation context showing the user's selections versus the correct answers.

CRITICAL REQUIREMENTS:
1. Output ONLY valid JSON. No conversational text, no explanations outside the JSON, and no markdown formatting blocks.
2. The JSON must be an array of exactly 10 objects, maintaining the order of the questions.
3. Each object must have four fields:
   - "question" (string): The text of the question.
   - "is_fully_correct" (boolean): true ONLY if the user's selected answers perfectly match all correct answers, otherwise false.
   - "explanation" (string): A highly educational and encouraging explanation. If correct, reinforce why. If incorrect or partially correct, address the specific misconception based on what they selected, and explain the correct reasoning using facts from the lesson.
   - "key_takeaway" (string): A short, memorable one-sentence summary of the core concept.

Lesson Text:
{lesson_text}

Evaluation Context:
{evaluation_context}
"""

    # 4. Call the API
    try:
        response = client.models.generate_content(
            model='gemma-3-27b-it', 
            contents=prompt,
        )
        
        raw_text = response.text

        # 5. Extract JSON
        match = re.search(r'(\{.*\}|\[.*\])', raw_text, re.DOTALL)

        if match:
            json_string = match.group(0)
            json.loads(json_string) 
            return json_string
        else:
            return json.dumps({"error": "Failed to extract valid JSON from the AI response."})

    except json.JSONDecodeError:
        return json.dumps({"error": "The AI generated invalid JSON that could not be parsed."})
    except Exception as e:
        return json.dumps({"error": f"API or execution error: {str(e)}"})