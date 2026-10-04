"""Recovery-scam signal: victims are re-targeted by people offering to get money back for a fee."""
from __future__ import annotations

from ..knowledge import patterns as P
from .base import Ctx, Rule, scan


def detect_recovery(ctx: Ctx) -> list[str]:
    return scan(ctx.text, P.RECOVERY)


RULES = [
    Rule("RECOVERY_SCAM", "recovery", 40, "strong", detect_recovery, forces="high", quote_prone=True),
]
