"""Optional LLM rewording of the summary.

Strict contract: the model receives only the *findings* (already vetted text in
the target language), never the user's message. It may only restate them in
simpler words. It cannot change the band or score. Its output must pass
``guard.is_safe`` or the vetted template summary is used instead.
"""
from __future__ import annotations

import httpx

from ..config import settings
from .guard import is_safe

_LANG_NAMES = {"en": "English", "ta": "Tamil", "hi": "Hindi"}

_SYSTEM = (
    "You rewrite a scam-check result for a first-time investor in India who may be elderly or low-literacy. "
    "Rules: (1) Use ONLY the facts in the provided findings; add no new facts, numbers, names or links. "
    "(2) Write 2 to 3 short, plain sentences in the requested language, no jargon. "
    "(3) Never give investment advice, never mention buying, selling or holding anything, never comment on any stock or on returns. "
    "(4) Do not claim the message is definitely a scam or definitely safe; this is a risk check. "
    "(5) End by telling the reader not to pay or share anything until they have checked, if the risk is high or critical. "
    "Output only the rewritten text."
)


async def rewrite_summary(band_label: str, headline: str, reasons: list[tuple[str, str]], lang: str) -> str | None:
    if not settings.llm_available:
        return None
    source = f"Risk band: {band_label}\nHeadline: {headline}\n" + "\n".join(f"- {t}: {d}" for t, d in reasons[:4])
    payload = {
        "model": settings.model,
        "max_tokens": 300,
        "system": _SYSTEM,
        "messages": [
            {"role": "user", "content": f"Language: {_LANG_NAMES.get(lang, 'English')}\n\nFindings:\n{source}"}
        ],
    }
    try:
        async with httpx.AsyncClient(timeout=settings.llm_timeout) as client:
            r = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": settings.api_key,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json=payload,
            )
        r.raise_for_status()
        text = "".join(b.get("text", "") for b in r.json().get("content", []) if b.get("type") == "text").strip()
    except Exception:  # network, quota, parsing: always fall back to the template
        return None
    return text if is_safe(text, source) else None
