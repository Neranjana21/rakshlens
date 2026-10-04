"""Pressure signals: urgency, exclusivity, and specific price-level calls."""
from __future__ import annotations

from ..knowledge import patterns as P
from .base import Ctx, Rule, redact_digits, scan


def detect_urgency(ctx: Ctx) -> list[str]:
    return scan(ctx.text, P.URGENCY)


def detect_exclusivity(ctx: Ctx) -> list[str]:
    return scan(ctx.text, P.EXCLUSIVITY)


def detect_referral(ctx: Ctx) -> list[str]:
    return scan(ctx.text, P.REFERRAL_SCHEME)


def detect_target_call(ctx: Ctx) -> list[str]:
    # Evidence is shown with numbers removed: we describe the pattern, never the call.
    return redact_digits(scan(ctx.text, P.TARGET_CALL))


RULES = [
    Rule("URGENCY", "pressure", 15, "warning", detect_urgency, quote_prone=True),
    Rule("EXCLUSIVITY_VIP", "pressure", 10, "warning", detect_exclusivity, quote_prone=True),
    Rule("REFERRAL_SCHEME", "pressure", 25, "strong", detect_referral, quote_prone=True),
    Rule("TARGET_PRICE_CALL", "pressure", 20, "warning", detect_target_call),
]
