import json
from sqlalchemy.ext.asyncio import AsyncSession

from ai_service.core.prompt_engine import prompt_explanation_paragraphs
from ai_service.db.database import get_db
from ai_service.db.repositories import AIRepository
# Importăm funcția centralizată care știe să facă retries și fallback
from ai_service.services.gemini_utils import call_gemini


async def generate_paragraph_explanation(
        db: AsyncSession,
        topic_name: str,
        confusing_paragraph: str,
        education_level: str = "Middle School"
) -> dict:
    """
    Flow:
    1. Verifică cache (repo)
    2. Dacă există → return
    3. Dacă nu → AI (cu retries & fallback) → save cache → return
    """

    repo = AIRepository(db)

    cached = await repo.get_cached_response(confusing_paragraph)

    # Treat common "not found" payloads (or empty JSON) as a cache miss.
    is_not_found_payload = False
    if isinstance(cached, dict):
        detail = cached.get("detail")
        if isinstance(detail, str) and detail.strip().lower() in {"not found", "not_found"}:
            is_not_found_payload = True

    if cached not in (None, 0, {}, []) and not is_not_found_payload:
        return cached  # deja dict/list

    prompt = prompt_explanation_paragraphs(
        topic_name,
        confusing_paragraph,
        education_level
    )

    # --- APELĂM AI-UL PROTEJAT ---
    json_string = call_gemini(prompt)

    try:
        parsed_json = json.loads(json_string)

        # call_gemini returnează mereu o cheie "error" dacă ceva a picat complet
        if isinstance(parsed_json, dict) and "error" in parsed_json:
            return parsed_json

        # Salvare doar dacă a fost un succes
        await repo.save_to_cache(confusing_paragraph, parsed_json)

        return parsed_json

    except json.JSONDecodeError:
        return {"error": "Invalid JSON from AI."}
    except Exception as e:
        return {"error": f"Internal execution error: {str(e)}"}
