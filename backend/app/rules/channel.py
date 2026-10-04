"""Channel signals: being moved to a private chat where nothing can be checked."""
from __future__ import annotations

from ..knowledge import patterns as P
from .base import Ctx, Rule, scan


def detect_private_channel(ctx: Ctx) -> list[str]:
    out = scan(ctx.text, P.PRIVATE_CHANNEL)
    if not out and ctx.ent.handles:
        out = ["a personal handle to contact"]
    return out


RULES = [
    Rule("PRIVATE_CHANNEL_MOVE", "channel", 15, "warning", detect_private_channel, forces="verify"),
]
