"""
Utilitare comune pentru serviciile AI cu fallback și retry selectiv.
"""

import importlib
import json
import logging
import os
import re
from typing import Optional

from google import genai
from google.genai import errors as genai_errors
from tenacity import (
    RetryError,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger(__name__)

# Cascade: primary → fallback. Ordine de la cota cea mai mică/calitate cea mai bună
# la cota mai mare/calitate mai slabă.
MODEL_CASCADE = [
    "gemini-3.1-flash-lite",  # 500 RPD, calitate Gemini, JSON mode
    "gemini-2.5-flash",  # 20 RPD,
    "gemini-2.5-flash-lite",  # 20 RPD,
    "gemma-4-26b-a4b-it",  # 1500 RPD, TPM unlimited
    "gemma-4-31b-it",  # 1500 RPD, TPM unlimited
]

# Câte încercări per model dacă JSON-ul e invalid (LLM non-determinism)
JSON_RETRY_ATTEMPTS = 2


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
    return json.dumps({"error": "No API key. Set GEMINI_API_KEY or GOOGLE_API_KEY."})


def _is_transient(exc: BaseException) -> bool:
    """Retry doar pe erori tranzitorii: rate limit, server overload, network."""
    if isinstance(exc, genai_errors.APIError):
        return exc.code in {429, 500, 502, 503, 504}
    return isinstance(exc, (TimeoutError, ConnectionError))


def _is_quota_exhausted(exc: BaseException) -> bool:
    """Distincție: 429 RPM (retry ajută) vs 429 RPD (doar fallback ajută)."""
    if isinstance(exc, genai_errors.APIError) and exc.code == 429:
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
    """Single API call cu retry pe erori tranzitorii (429, 5xx)."""
    # Gemma nu suportă response_mime_type — feature specific Gemini
    config = {}
    if model.startswith("gemini"):
        config["response_mime_type"] = "application/json"

    response = client.models.generate_content(
        model=model,
        contents=prompt,
        config=config,
    )
    raw = response.text or ""

    # Defensive cleanup pentru Gemma — poate returna markdown fences ```json ... ```
    # sau text adițional în jurul JSON-ului
    if not model.startswith("gemini") and raw:
        raw = raw.strip()
        # Strip markdown fences
        if raw.startswith("```"):
            raw = re.sub(r"^```(?:json)?\s*\n?", "", raw)
            raw = re.sub(r"\n?```\s*$", "", raw)
            raw = raw.strip()
        # Extrage doar JSON-ul (între prima [/{ și ultima ]/}) dacă există text adițional
        match = re.search(r"(\[.*\]|\{.*\})", raw, re.DOTALL)
        if match:
            raw = match.group(1)

    return raw


def _call_with_fallback(client: genai.Client, prompt: str) -> str:
    """
    Încearcă fiecare model din cascade. Pentru fiecare model:
    - retry-uri pe erori API (gestionate de @retry intern)
    - retry-uri pe JSON invalid (LLM non-determinism)
    - fallback la următorul model dacă tot eșuează
    """
    last_exc: Optional[BaseException] = None

    for i, model in enumerate(MODEL_CASCADE):
        # Pentru fiecare model, încercăm de JSON_RETRY_ATTEMPTS ori
        # dacă output-ul nu e JSON valid (model non-determinism)
        for json_attempt in range(JSON_RETRY_ATTEMPTS):
            print(
                f"[CASCADE] Position {i}/{len(MODEL_CASCADE) - 1} → {model} "
                f"(json_attempt {json_attempt + 1}/{JSON_RETRY_ATTEMPTS})",
                flush=True,
            )
            try:
                result = _execute_with_retry(client, model, prompt)
                # Validare inline că rezultatul e JSON valid
                json.loads(result)
                print(f"[CASCADE] ✅ {model} succeeded", flush=True)
                return result
            except json.JSONDecodeError as e:
                # JSON invalid — model non-determinism, retry pe același model
                print(
                    f"[CASCADE] ⚠ {model} returned invalid JSON "
                    f"(line {e.lineno}, col {e.colno}, msg: {e.msg[:100]})",
                    flush=True,
                )
                if json_attempt + 1 < JSON_RETRY_ATTEMPTS:
                    print(f"[CASCADE] ↻ Retrying same model", flush=True)
                    continue
                print(
                    f"[CASCADE] ↪ JSON failures exhausted on {model}, falling back",
                    flush=True,
                )
                # Salvăm o excepție generică ca să propagăm dacă toate modelele cad
                last_exc = RuntimeError(
                    f"{model}: invalid JSON after {JSON_RETRY_ATTEMPTS} attempts"
                )
                break  # ies din loop-ul json_attempt, trec la următorul model
            except RetryError as re_exc:
                exc = re_exc.last_attempt.exception()
                code = getattr(exc, "code", "?")
                msg = (getattr(exc, "message", str(exc)) or "")[:200]
                print(f"[CASCADE] ❌ {model}: code={code}, msg={msg}", flush=True)
                last_exc = exc
                if not _is_transient(exc):
                    raise exc
                if _is_quota_exhausted(exc):
                    print(
                        f"[CASCADE] ⚠ Daily quota exhausted on {model}, skipping retries",
                        flush=True,
                    )
                break  # fallback la următorul model
            except genai_errors.APIError as exc:
                code = getattr(exc, "code", "?")
                msg = (getattr(exc, "message", "") or "")[:200]
                print(
                    f"[CASCADE] ❌ {model} APIError: code={code}, msg={msg}", flush=True
                )
                last_exc = exc
                if not _is_transient(exc):
                    raise
                break

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
            is_daily = any(
                kw in msg
                for kw in [
                    "per day",
                    "daily",
                    "rpd",
                    "quota exceeded",
                    "resource_exhausted",
                    "exhausted",
                ]
            )
            error_type = "rate_limit_daily" if is_daily else "rate_limit_minute"
            return json.dumps(
                {
                    "error": "API error: HTTP 429",
                    "error_type": error_type,
                }
            )
        return json.dumps({"error": f"API error: HTTP {e.code}"})
    except Exception as e:
        # Acoperă inclusiv RuntimeError din _call_with_fallback (toate modelele eșuate)
        msg = str(e)[:200]
        print(f"[ERROR] call_gemini failed: {type(e).__name__}: {msg}", flush=True)
        return json.dumps({"error": f"All models failed: {msg}"})

    # Validare finală (defensive — _call_with_fallback ar trebui să garanteze JSON valid)
    try:
        json.loads(raw)
        return raw
    except json.JSONDecodeError:
        return json.dumps({"error": "Model returned invalid JSON."})
