from ai_service.core.prompt_engine import prompt_reformat_professor
from ai_service.services.gemini_utils import call_gemini


def refine_academic_text(topic_name: str, ambiguous_text: str) -> str:
    """
    Apelează Gemini să corecteze gramatica, să rezolve ambiguitățile
    și să îmbunătățească tonul academic al textului dat.
    Returnează un JSON string valid.
    """
    prompt = prompt_reformat_professor(topic_name, ambiguous_text)
    return call_gemini(prompt)


if __name__ == "__main__":
    sample_topic = "Physics: Thermodynamics"
    sample_messy_text = (
        "Heat is like going from the hot thing to the cold thing and it dont stop "
        "until they is the same hotness. this is called equilibrium i think."
    )
    print(refine_academic_text(sample_topic, sample_messy_text))