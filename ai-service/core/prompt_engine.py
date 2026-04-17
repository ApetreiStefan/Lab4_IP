

def prompt_popquiz(lesson_type: str, lesson_text: str, difficulty: str):

    # Prompt adaptiv în funcție de nivelul elevului
    difficulty_instructions = {
        "easy": "Focus on basic terminology and simple facts.",
        "medium": "Focus on understanding concepts and relationships.",
        "hard": "Focus on complex application, analysis, and edge cases."
    }

    prompt = f"""You are an expert educational assistant. Create a pop quiz based on the provided {lesson_type} lesson.

    Level: {difficulty.upper()}
    Context: {difficulty_instructions.get(difficulty, "")}

    CRITICAL REQUIREMENTS:
    1. Generate exactly 5 questions. Some can have one correct answer, and some can have multiple correct answers.
    2. Output ONLY valid JSON. No conversational text, no explanations, and no markdown formatting blocks.
    3. The JSON must be an array of objects.
    4. Each object must have three fields: 
    - "question" (string)
    - "options" (array of strings)
    - "num_correct" (integer representing how many correct answers there are).
    5. The correct answer(s) MUST ALWAYS be placed at the very beginning of the "options" array (from index 0 up to `num_correct` - 1). 
    6. All incorrect answers must follow the correct answers in the "options" array.

    Lesson Text:
    {lesson_text}
    """

    return prompt


def prompt_popquiz_explain(lesson_text: str, json_obj_number: int, evaluation_context: str):

    prompt = f"""You are an expert, empathetic educational tutor grading a pop quiz. 
    Review the original lesson text and the evaluation context showing the user's answers versus the correct answers.

    CRITICAL REQUIREMENTS:
    1. Output ONLY valid JSON. No conversational text, no explanations, and no markdown formatting blocks.
    2. The JSON must be an array of exactly {json_obj_number} objects, maintaining the order of the questions.
    3. Each object must have four fields:
    - "question" (string): The text of the question.
    - "is_fully_correct" (boolean): true ONLY if the user's answers perfectly match all correct answers, otherwise false.
    - "explanation" (string): A highly educational and encouraging explanation. If the user is correct, reinforce why. If incorrect or partially correct, gently address the specific misconception based on their choices, and guide them to the correct answer using facts from the lesson. Do not just state the correct answer; explain the reasoning.
    - "key_takeaway" (string): A short, memorable one-sentence summary of the core concept the student should remember for this specific question.

    Lesson Text:
    {lesson_text}

    Evaluation Context:
    {evaluation_context}
    """

    return prompt


def prompt_finaltest(topic_name: str, lesson_text: str, difficulty: str):

    difficulty_instructions = {
        "easy": "Focus on basic terminology and simple facts.",
        "medium": "Focus on understanding concepts and relationships.",
        "hard": "Focus on complex application, analysis, and edge cases."
    }

    prompt = f"""You are an expert curriculum designer creating a multiple-choice final test for the topic: {topic_name}.

    Level: {difficulty.upper()}
    Context: {difficulty_instructions.get(difficulty, "")}

    CRITICAL REQUIREMENTS:
    1. Generate exactly 10 questions based on the provided Lesson Text. Some can have one correct answer, and some can have multiple correct answers.
    2. Output ONLY valid JSON. No conversational text and no markdown formatting blocks.
    3. The JSON must be an array of exactly 10 objects.
    4. Each object must have four fields:
    - "id" (integer 1-10)
    - "question" (string)
    - "options" (array of strings)
    - "num_correct" (integer representing how many correct answers there are)
    5. The correct answer(s) MUST ALWAYS be placed at the very beginning of the "options" array (from index 0 up to `num_correct` - 1). 
    6. All incorrect answers must follow the correct answers in the "options" array.

    Lesson Text:
    {lesson_text}
    """

    return prompt


def prompt_finaltest_explain(lesson_text: str, evaluation_context: str):

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

    return prompt


def prompt_explanation_paragraphs(topic_name: str, confusing_paragraph: str, education_level: str):

    prompt = f"""You are an empathetic, concise, and highly effective AI Tutor. 
    The student is learning about "{topic_name}" at a {education_level} level.
    They are struggling to understand the following paragraph from their course material:

    "{confusing_paragraph}"

    CRITICAL REQUIREMENTS:
    1. Break down the confusing paragraph into simple, easy-to-understand terms appropriate for their education level.
    2. Provide a relatable, everyday analogy to make the concept "click".
    3. Ask one simple, engaging "Socratic" question at the end to check their understanding. Do NOT give them the answer to this closing question.
    4. Output ONLY valid JSON. No conversational text and no markdown formatting blocks (e.g., no ```json).
    5. The JSON must exactly match this structure:
    {{
    "simplified_explanation": "string",
    "analogy": "string",
    "check_for_understanding_question": "string"
    }}
    """

    return prompt


def prompt_reformat_professor(topic_name: str, ambiguous_text: str):

    prompt = f"""You are an expert University Professor specializing in "{topic_name}".
    You are reviewing a text that is ambiguous, poorly phrased, and contains grammatical errors.

    Original Text:
    "{ambiguous_text}"

    CRITICAL REQUIREMENTS:
    1. Rewrite the text to be academically rigorous, perfectly grammatical, and entirely unambiguous.
    2. Maintain the original intent of the text, but elevate the vocabulary and structure.
    3. Output ONLY valid JSON. No conversational text and no markdown formatting blocks (e.g., no ```json).
    4. The JSON must exactly match this structure:
    {{
    "corrected_text": "string (The rewritten, perfect paragraph)",
    "ambiguity_resolution": "string (A brief professor's note explaining what was confusing and how you clarified the meaning)",
    "grammar_fixes": [
        {{
        "error": "string (The specific incorrect word or phrase from the original text)",
        "correction": "string (The corrected word or phrase)",
        "explanation": "string (The grammatical rule or reason why the original was incorrect)"
        }}
    ]
    }}
    """

    return prompt