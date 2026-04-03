import json
import re
from google import genai


def generate_paragraph_explanation(topic_name: str, confusing_paragraph: str,
                                   education_level: str = "Middle School") -> str:
    """
    Calls the AI model to generate a simple, JSON-formatted explanation
    for a specific paragraph a student struggled to understand.
    """
    # parametrul la aceasta functie este cheia
    client = genai.Client()

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

    try:
        response = client.models.generate_content(
            model='gemma-3-27b-it',
            contents=prompt,
        )

        raw_text = response.text

        match = re.search(r'(\{.*\}|\[.*\])', raw_text, re.DOTALL)

        if match:
            json_string = match.group(0)
            json.loads(json_string)  # Validate syntax before returning
            return json_string
        else:
            return json.dumps({"error": "Failed to extract valid JSON from the AI response."})

    except json.JSONDecodeError:
        return json.dumps({"error": "The AI generated invalid JSON that could not be parsed."})
    except Exception as e:
        return json.dumps({"error": f"API or execution error: {str(e)}"})


# --- Example Usage ---
if __name__ == "__main__":
    sample_topic = "Object-Oriented Programming"
    sample_confusing_text = "One of the core pillars of OOP is Encapsulation—the bundling of data and the methods that act on that data, while restricting direct access to some of the object's components. C++ enforces encapsulation using Access Specifiers."

    print(generate_paragraph_explanation(sample_topic, sample_confusing_text, "High School"))
