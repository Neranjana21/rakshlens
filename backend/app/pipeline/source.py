"""Guess which app a message was received on (WhatsApp, Telegram, SMS, email, social).

This is a best-effort guess, never a fact. It only uses clues about where a message
was *received*: interface wording ("Forwarded many times"), an SMS sender ID, email
headers, and the look of a screenshot (app colours). A bare mention such as "contact
me on Telegram" is deliberately ignored, because scams name the app they want to move
you to, not the one the message arrived on. With weak or conflicting clues the answer
is None and the UI says it could not tell. Nothing here is stored.
"""
from __future__ import annotations

import io
import re
from dataclasses import dataclass

from PIL import Image

SOURCES = ("whatsapp", "telegram", "sms", "email", "social")

# (source, weight, pattern). Weight 3 = strong interface clue, 1 = weak.
_TEXT_CLUES: list[tuple[str, int, re.Pattern[str]]] = [
    ("whatsapp", 3, re.compile(r"forwarded\s+many\s+times", re.I)),
    ("whatsapp", 3, re.compile(r"messages\s+and\s+calls\s+are\s+end[- ]to[- ]end\s+encrypted", re.I)),
    ("whatsapp", 3, re.compile(r"this\s+message\s+was\s+deleted|you\s+deleted\s+this\s+message", re.I)),
    ("whatsapp", 3, re.compile(r"joined\s+using\s+this\s+group'?s?\s+invite\s+link|added\s+you\s+to\s+(?:the\s+)?group", re.I)),
    ("whatsapp", 2, re.compile(r"(?m)^\s*forwarded\s*$", re.I)),
    ("telegram", 3, re.compile(r"forwarded\s+from\b", re.I)),
    ("telegram", 3, re.compile(r"last\s+seen\s+(?:recently|within\s+a)", re.I)),
    ("telegram", 2, re.compile(r"\b\d[\d.,]*\s?[KM]?\s+views?\b", re.I)),
    ("telegram", 1, re.compile(r"\b\d[\d.,]*\s?[KM]?\s+(?:subscribers|members)\b", re.I)),
    ("sms", 3, re.compile(r"(?m)^\s*[A-Z]{2}-[A-Z][A-Z0-9]{3,8}\b")),
    ("sms", 2, re.compile(r"\btext\s+message\b", re.I)),
    ("sms", 1, re.compile(r"\breply\s+stop\b", re.I)),
    ("email", 3, re.compile(r"(?mi)^\s*(?:subject|from)\s*:[\s\S]{0,400}?^\s*(?:to|cc|date|subject|from)\s*:", re.M)),
    ("email", 2, re.compile(r"view\s+(?:this\s+email\s+)?in\s+(?:your\s+)?browser", re.I)),
    ("email", 1, re.compile(r"\bunsubscribe\b", re.I)),
    ("social", 3, re.compile(r"\bpinned\s+by\b|replied\s+to\s+your\s+story|reply\s+to\s+story", re.I)),
    ("social", 3, re.compile(r"\blike\b\s+\bcomment\b\s+\bshare\b", re.I)),
    ("social", 1, re.compile(r"\b\d[\d.,]*\s?[KM]?\s+followers\b", re.I)),
]

# App colours seen in real screenshots (light and dark themes). RGB, matched with a tolerance.
_PALETTE: dict[str, list[tuple[int, int, int]]] = {
    "whatsapp": [(0xE5, 0xDD, 0xD5), (0xEC, 0xE5, 0xDD), (0xEF, 0xEA, 0xE2), (0xD9, 0xFD, 0xD3),
                 (0xDC, 0xF8, 0xC6), (0x07, 0x5E, 0x54), (0x12, 0x8C, 0x7E), (0x00, 0x5C, 0x4B)],
    "telegram": [(0xEF, 0xFD, 0xDE), (0x51, 0x7D, 0xA2), (0x2A, 0xAB, 0xEE), (0x2B, 0x52, 0x78)],
}
_TOL = 8
_COLOUR_SHARE = 0.18  # share of pixels in an app's palette before it counts as a clue
_MIN_SCORE = 2        # below this the answer is "could not tell"
_MIN_MARGIN = 1       # the best source must beat the runner-up by this much


@dataclass
class Source:
    id: str
    confidence: str  # likely | possible
    basis: str       # text | look | both


def _colour_shares(data: bytes) -> dict[str, float]:
    try:
        img = Image.open(io.BytesIO(data)).convert("RGB")
        img.thumbnail((160, 160))
    except Exception:
        return {}
    raw = img.tobytes()
    px = list(zip(raw[0::3], raw[1::3], raw[2::3]))
    if not px:
        return {}
    shares: dict[str, float] = {}
    for name, colours in _PALETTE.items():
        hit = sum(1 for r, g, b in px if any(abs(r - c[0]) <= _TOL and abs(g - c[1]) <= _TOL and abs(b - c[2]) <= _TOL for c in colours))
        shares[name] = hit / len(px)
    return shares


def detect_source(text: str, image: bytes | None = None) -> Source | None:
    text_score = {s: 0 for s in SOURCES}
    look_score = {s: 0 for s in SOURCES}
    for src, weight, pat in _TEXT_CLUES:
        if pat.search(text or ""):
            text_score[src] += weight
    if image:
        for src, share in _colour_shares(image).items():
            if share >= _COLOUR_SHARE:
                look_score[src] += 2

    total = {s: text_score[s] + look_score[s] for s in SOURCES}
    ranked = sorted(total.items(), key=lambda kv: -kv[1])
    (best, best_score), (_, second_score) = ranked[0], ranked[1]
    if best_score < _MIN_SCORE or best_score - second_score < _MIN_MARGIN:
        return None
    basis = "both" if text_score[best] and look_score[best] else "look" if look_score[best] else "text"
    return Source(best, "likely" if best_score >= 4 else "possible", basis)
