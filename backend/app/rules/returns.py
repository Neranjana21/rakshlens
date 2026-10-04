"""Return-related signals: promises no legitimate adviser can make."""
from __future__ import annotations

import re

from ..knowledge import patterns as P
from .base import Ctx, Rule, scan

_AVOID = re.compile(P.AVOID_BEFORE, re.IGNORECASE)

# Per-period thresholds above which a stated return is not plausible (percent).
_THRESH = {"day": 0.5, "week": 2.0, "month": 5.0}

_RATE = re.compile(
    r"(?:\d{1,4}(?:\.\d+)?\s?(?:-|–|to)\s?)?(\d{1,4}(?:\.\d+)?)\s?%\s*(?:returns?|profit|income|gain|growth|interest|munafa|लाभ|मुनाफा|லாபம்)?\s*"
    r"(?:/|per|a|every|each|हर|प्रति|ஒரு|ஒவ்வொரு)?\s*" + P.RATE_UNITS
)
_RATE_PREFIX = re.compile(P.RATE_UNITS + r"\s*(?:me|mein|में|ல்)?\s*(?:\d{1,4}(?:\.\d+)?\s?(?:-|–|to)\s?)?(\d{1,4}(?:\.\d+)?)\s?%")
_IN_PERIOD = re.compile(
    r"(\d{2,4})\s?%\s*(?:returns?|profit|gain)?[^.\n]{0,25}?(?:in|within)\s*(\d{1,3})\s*(day|week|month)s?\b"
)


def _unit(u: str) -> str | None:
    u = u.lower().strip()
    if u in {"day", "daily", "din", "roz", "rozana"} or u.startswith(("प्रतिदिन", "रोज", "தினமும்", "தினசரி")):
        return "day"
    if u in {"week", "weekly", "hafte"} or u.startswith(("प्रति सप्ताह", "प्रति\u00a0सप्ताह", "हर हफ्ते", "வார")):
        return "week"
    if u in {"month", "monthly", "mahine", "mahina"} or u.startswith(("प्रति माह", "हर महीने", "महीने", "மாத")):
        return "month"
    return None


def detect_guaranteed(ctx: Ctx) -> list[str]:
    return scan(ctx.text, P.GUARANTEED, before_blocker=_AVOID)


def detect_unrealistic_rate(ctx: Ctx) -> list[str]:
    out: list[str] = []
    for m in _RATE.finditer(ctx.text):
        unit = _unit(m.group(2))
        if unit and float(m.group(1)) >= _THRESH[unit]:
            out.append(f"{m.group(1)}% per {unit}")
    for m in _RATE_PREFIX.finditer(ctx.text):
        unit = _unit(m.group(1))
        if unit and float(m.group(2)) >= _THRESH[unit]:
            out.append(f"{m.group(2)}% per {unit}")
    for m in _IN_PERIOD.finditer(ctx.text):
        pct, n, unit = float(m.group(1)), float(m.group(2)), m.group(3)
        per_month = pct / n if unit == "month" else pct * 4.3 / n if unit == "week" else pct * 30 / n
        if per_month >= _THRESH["month"]:
            out.append(f"{m.group(1)}% in {m.group(2)} {unit}s")
    out += scan(ctx.text, P.DOUBLE_MONEY, before_blocker=_AVOID)
    return list(dict.fromkeys(out))[:3]


def detect_profit_proof(ctx: Ctx) -> list[str]:
    return scan(ctx.text, P.PROFIT_PROOF)


RULES = [
    Rule("GUARANTEED_RETURNS", "returns", 30, "strong", detect_guaranteed, quote_prone=True),
    Rule("UNREALISTIC_RETURN_RATE", "returns", 25, "strong", detect_unrealistic_rate, quote_prone=True),
    Rule("PROFIT_PROOF", "returns", 10, "warning", detect_profit_proof, quote_prone=True),
]
