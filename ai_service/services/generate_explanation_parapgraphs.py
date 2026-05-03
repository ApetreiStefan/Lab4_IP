import os
import json
import re
import importlib
import hashlib

from google import genai
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.dialects.postgresql import insert

from ai_service.core.prompt_engine import (prompt_explanation_paragraphs)
from ai_service.db.database import AICache, get_db
from ai_service.db.repositories import AIRepository


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
    3. Dacă nu → AI → save cache → return
    """

    repo = AIRepository(db)

    # --- Load .env ---
    try:
        dotenv_module = importlib.import_module("dotenv")
        load_dotenv = getattr(dotenv_module, "load_dotenv", None)
        if callable(load_dotenv):
            load_dotenv()
    except Exception:
        pass

    api_key = os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not api_key:
        return {"error": "No API key provided."}

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

    try:
        client = genai.Client(api_key=api_key)

        # Folosim .aio. pentru a face apelul non-blocant!
        response = await client.aio.models.generate_content(
            model='gemma-3-27b-it',
            contents=prompt,
        )

        raw_text = response.text
        match = re.search(r'(\{.*\}|\[.*\])', raw_text, re.DOTALL)

        if not match:
            # Nu mai dăm eroare dacă ratează JSON-ul, îi creăm noi un fallback
            parsed_json = {"explanation": raw_text.strip()}
        else:
            json_string = match.group(0)
            parsed_json = json.loads(json_string)

        # Aici salvăm în cache (O SINGURĂ DATĂ)
        await repo.save_to_cache(confusing_paragraph, parsed_json)

        return parsed_json

    except json.JSONDecodeError:
        return {"error": "Invalid JSON from AI."}
    except Exception as e:
        return {"error": f"API error: {str(e)}"}
