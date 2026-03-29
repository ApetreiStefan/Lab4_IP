import json
import ollama


# =========================
# PROMPT BUILDER
# =========================
class PromptBuilder:

    @staticmethod
    def build_quiz_prompt(lesson, num_questions, difficulty):
        return f"""
    You are an expert instructional designer and university-level professor.

    Your task is to generate a high-quality quiz that tests deep understanding, not just memorization.

    =====================
    QUIZ REQUIREMENTS
    =====================

    - Number of questions: {num_questions}
    - Difficulty level: {difficulty}

    Difficulty guidelines:
    - easy → basic recall, definitions
    - medium → understanding, relationships, cause-effect
    - hard → reasoning, multi-step thinking, subtle distinctions

    =====================
    QUESTION QUALITY RULES
    =====================

    - Avoid trivial or obvious questions
    - Avoid repeating the same question pattern
    - Ensure conceptual diversity across questions
    - Include a mix of:
    • factual questions
    • cause-effect reasoning
    • conceptual understanding
    • interpretation

    - At least 30% of questions MUST require reasoning (not direct lookup)

    =====================
    ANSWER OPTIONS RULES
    =====================

    - Each question MUST have exactly 4 options
    - Only ONE correct answer
    - Incorrect answers (distractors) must be:
    • plausible
    • same domain/topic
    • not obviously wrong
    • not jokes or unrelated facts

    BAD example:
    - "The moon exploded"
    GOOD example:
    - historically plausible but incorrect

    =====================
    EXPLANATION RULES
    =====================

    - Each question MUST include a clear explanation
    - Explanation must:
    • justify the correct answer
    • briefly explain why others are incorrect (optional but preferred)
    • be concise but informative

    =====================
    STRICT OUTPUT FORMAT
    =====================

    Return ONLY valid JSON. No markdown, no text outside JSON.

    Schema:
    {{
    "questions": [
        {{
        "question": "string",
        "options": ["string", "string", "string", "string"],
        "correct_answer": "string",
        "explanation": "string",
        "difficulty": "{difficulty}",
        "type": "factual | reasoning | conceptual"
        }}
    ]
    }}

    =====================
    LESSON CONTENT
    =====================

    {lesson}

    =====================
    FINAL INSTRUCTION
    =====================

    Double-check:
    - JSON is valid
    - All fields exist
    - Exactly 4 options per question
    - No extra text outside JSON

    Now generate the quiz.
    """


# =========================
# MODEL WRAPPER (OLLAMA)
# =========================
def ask_model(prompt, model="qwen2.5:7b"):
    try:
        response = ollama.chat(
            model=model,
            messages=[{"role": "user", "content": prompt}],
        )
        return response["message"]["content"]
    except Exception as e:
        print("❌ Error calling model:", e)
        return None


# =========================
# PARSER + VALIDATOR
# =========================
def parse_json(text):
    try:
        return json.loads(text)
    except Exception:
        return None


def fix_json(bad_json, model="qwen2.5:7b"):
    fix_prompt = f"""
Fix the following JSON and return ONLY valid JSON:

{bad_json}
"""
    return ask_model(fix_prompt, model)


def validate_quiz(data):
    if not data or "questions" not in data:
        return False

    for q in data["questions"]:
        if not all(k in q for k in ["question", "options", "correct_answer", "explanation"]):
            return False
        if len(q["options"]) != 4:
            return False

    return True


# =========================
# GENERATION ENGINE
# =========================
class GenerationEngine:

    def __init__(self, model="qwen2.5:7b"):
        self.model = model

    def generate_quiz(self, lesson, num_questions=5, difficulty="easy"):
        print("⚙️ Generating quiz...")

        prompt = PromptBuilder.build_quiz_prompt(
            lesson, num_questions, difficulty
        )

        raw = ask_model(prompt, self.model)

        if raw is None:
            print("❌ Model failed.")
            return None

        parsed = parse_json(raw)

        # retry dacă JSON invalid
        if parsed is None:
            print("⚠️ Invalid JSON, attempting fix...")
            fixed = fix_json(raw, self.model)
            parsed = parse_json(fixed)

        # validare finală
        if not validate_quiz(parsed):
            print("❌ Invalid quiz structure.")
            return None

        print("✅ Quiz generated successfully!")
        return parsed


# =========================
# TEST LOCAL
# =========================
if __name__ == "__main__":

    lesson_history = """
World War I began in 1914 after the assassination of Archduke Franz Ferdinand.
It involved major world powers divided into the Allies and the Central Powers.
The war ended in 1918 with the Treaty of Versailles.
"""
    lesson_biology = """
Photosynthesis is the process by which green plants convert sunlight into chemical energy.
It takes place in the chloroplasts using chlorophyll.
Carbon dioxide and water are used to produce glucose and oxygen.
The process has two main stages: light-dependent reactions and the Calvin cycle.
"""
    lesson_economics = """
Supply and demand is a fundamental concept in economics.
When demand increases and supply remains constant, prices tend to rise.
When supply increases and demand remains constant, prices tend to fall.
Market equilibrium occurs when supply equals demand.
External factors like government policies and global events can shift supply and demand curves.
"""
    lesson_psychology = """
Cognitive dissonance is a psychological theory that refers to the discomfort experienced when holding conflicting beliefs.
People are motivated to reduce this discomfort by changing their beliefs or behaviors.
This concept explains why individuals justify decisions even when evidence contradicts them.
"""
    lesson_cs = """
A stack is a data structure that follows the Last In, First Out (LIFO) principle.
Elements can be added using the push operation and removed using the pop operation.
Stacks are used in function calls, recursion, and expression evaluation.
"""
    lesson_physics = """
Newton's First Law states that an object will remain at rest or in uniform motion unless acted upon by an external force.
This is also known as the law of inertia.
Mass is a measure of an object's resistance to acceleration.
"""
    # edge cases:
    # 1: lectie prea vaga
    lesson_edge_short = """
Energy is important in physics.
"""

    # 2: lectie ambigua
    lesson_edge_ambiguous = """
Systems can change over time depending on internal and external factors.
"""
    # 3: lectie incompleta
    lesson_edge_incomplete = """
World War I began in 1914 and involved several major powers.
"""

    engine = GenerationEngine(model="qwen2.5:7b")

    quiz = engine.generate_quiz(
        lesson=lesson_biology,
        num_questions=5,
        difficulty="medium"
    )

    print("\n📦 FINAL OUTPUT:\n")
    print(json.dumps(quiz, indent=2, ensure_ascii=False))
