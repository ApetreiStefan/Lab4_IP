"""
Utilitare comune pentru serviciile AI cu fallback și retry selectiv.
"""

import os
import json
import importlib
import logging
from typing import Optional

from google import genai
from google.genai import errors as genai_errors
from tenacity import (
    retry, stop_after_attempt, wait_exponential,
    retry_if_exception_type, RetryError,
)

logger = logging.getLogger(__name__)

# Cascade: primary → fallback. Adaugă mai multe dacă vrei.
MODEL_CASCADE = ["gemini-2.5-flash", "gemini-2.5-flash-lite"]


def _load_dotenv() -> None:
    try:
        dotenv = importlib.import_module("dotenv")
        loader = getattr(dotenv, "load_dotenv", None)
        if callable(loader):
            loader()
    except ImportError:
        pass


def get_api_key() -> Optional[str]:
    _load_dotenv()
    return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")


def missing_key_error() -> str:
    return json.dumps({
        "error": "No API key. Set GEMINI_API_KEY or GOOGLE_API_KEY."
    })


def _is_transient(exc: BaseException) -> bool:
    """Retry doar pe erori tranzitorii: rate limit, server overload, network."""
    if isinstance(exc, genai_errors.APIError):
        # 429 = rate limit, 503 = overloaded, 500/502/504 = server-side
        return exc.code in {429, 500, 502, 503, 504}
    # Network errors (timeout, connection reset) — also transient
    return isinstance(exc, (TimeoutError, ConnectionError))


def _is_quota_exhausted(exc: BaseException) -> bool:
    """Distincție: 429 RPM (retry ajută) vs 429 RPD (doar fallback ajută)."""
    if isinstance(exc, genai_errors.APIError) and exc.code == 429:
        # Quota epuizată pe zi → mesajul conține "quota" sau "RESOURCE_EXHAUSTED"
        msg = (exc.message or "").lower()
        return "quota" in msg or "exhausted" in msg
    return False


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    retry=retry_if_exception_type(genai_errors.APIError),
    reraise=True,
)
def _execute_with_retry(client: genai.Client, model: str, prompt: str) -> str:
    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config={"response_mime_type": "application/json"},
    )
    return response.text


def _call_with_fallback(client: genai.Client, prompt: str) -> str:
    last_exc: Optional[BaseException] = None

    for i, model in enumerate(MODEL_CASCADE):
        try:
            return _execute_with_retry(client, model, prompt)
        except RetryError as re_exc:
            exc = re_exc.last_attempt.exception()
            last_exc = exc
            if not _is_transient(exc):
                raise exc  # Permanent error (400/401/404) — nu mai încerca
            # Quota exhausted sau overload persistent → fallback
            logger.warning(
                "Model %s failed after retries (transient). Trying next.",
                model,
            )
        except genai_errors.APIError as exc:
            last_exc = exc
            if not _is_transient(exc):
                raise
            logger.warning("Model %s: transient APIError, fallback.", model)

    # Toate modelele exhausted
    raise last_exc if last_exc else RuntimeError("All models failed.")


def call_gemini(prompt: str) -> str:
    api_key = get_api_key()
    if not api_key:
        return missing_key_error()

    client = genai.Client(api_key=api_key)

    try:
        raw = _call_with_fallback(client, prompt)
    except genai_errors.APIError as e:
        # Distincție între tipuri de 429 — RPD vs RPM
        if e.code == 429:
            msg = (getattr(e, "message", "") or "").lower()
            # Indicatori pentru cotă zilnică epuizată (RPD)
            # Google folosește "quota", "exhausted", "RESOURCE_EXHAUSTED",
            # "per day", "daily" în mesaje pentru limita zilnică.
            is_daily = any(kw in msg for kw in [
                "per day", "daily", "rpd",
                "quota exceeded", "resource_exhausted", "exhausted"
            ])
            error_type = "rate_limit_daily" if is_daily else "rate_limit_minute"
            return json.dumps({
                "error": f"API error: HTTP 429",
                "error_type": error_type,
            })
        return json.dumps({"error": f"API error: HTTP {e.code}"})
    except Exception as e:
        return json.dumps({"error": f"Unexpected error: {type(e).__name__}"})

    try:
        json.loads(raw)
        return raw
    except json.JSONDecodeError:
        return json.dumps({"error": "Model returned invalid JSON."})
