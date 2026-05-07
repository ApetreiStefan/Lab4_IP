POST /api/v1/subcapitols/check-quiz/questions/generate

{
  "lesson_type": "Biology",
  "lesson_text": "Photosynthesis is the process by which plants convert sunlight into chemical energy.",
  "difficulty": "easy"
}

----------------------------------------

POST /api/v1/subcapitols/check-quiz/questions/generate/adaptive

{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "topic_name": "Biology",
  "lesson_text": "Photosynthesis is the process by which plants convert sunlight into chemical energy."
}

----------------------------------------

POST /api/v1/subcapitols/check-quiz/explain

{
  "lesson_text": "Photosynthesis is the process by which plants convert sunlight into chemical energy.",
  "quiz_json": [
    {
      "question": "What is the main purpose of photosynthesis?",
      "options": ["To produce oxygen", "To convert light into energy", "To absorb water"],
      "num_correct": 1
    }
  ],
  "user_answers": [
    ["To convert light into energy"]
  ]
}

Variantă cu quiz_json ca string:

{
  "lesson_text": "Photosynthesis is the process by which plants convert sunlight into chemical energy.",
  "quiz_json": "[{\"question\":\"What is the main purpose of photosynthesis?\",\"options\":[\"To produce oxygen\",\"To convert light into energy\",\"To absorb water\"],\"num_correct\":1}]",
  "user_answers": [
    ["To convert light into energy"]
  ]
}

----------------------------------------

POST /api/v1/lessons/final-quiz/questions/generate

{
  "topic_name": "Biology",
  "lesson_text": "Photosynthesis is the process by which plants convert sunlight into chemical energy.",
  "difficulty": "medium"
}

----------------------------------------

POST /api/v1/lessons/final-quiz/questions/generate/adaptive

{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "topic_name": "Biology",
  "lesson_text": "Photosynthesis is the process by which plants convert sunlight into chemical energy."
}

----------------------------------------

POST /api/v1/lessons/final-quiz/explain

{
  "lesson_text": "Photosynthesis is the process by which plants convert sunlight into chemical energy.",
  "test_json": [
    {
      "question": "What is the main purpose of photosynthesis?",
      "options": ["To produce oxygen", "To convert light into energy", "To absorb water"],
      "num_correct": 1
    }
  ],
  "user_answers": [
    ["To convert light into energy"]
  ]
}

Variantă cu test_json ca string:

{
  "lesson_text": "Photosynthesis is the process by which plants convert sunlight into chemical energy.",
  "test_json": "[{\"question\":\"What is the main purpose of photosynthesis?\",\"options\":[\"To produce oxygen\",\"To convert light into energy\",\"To absorb water\"],\"num_correct\":1}]",
  "user_answers": [
    ["To convert light into energy"]
  ]
}

----------------------------------------

POST /api/v1/blocks/explain

{
  "topic_name": "Biology",
  "confusing_paragraph": "In photosynthesis, light-dependent reactions occur in the thylakoid membranes and produce ATP and NADPH.",
  "education_level": "High School"
}

----------------------------------------

POST /api/v1/content-blocks/rewrite

{
  "topic_name": "Biology",
  "ambiguous_text": "Plants use sunlight to make food in a special process."
}