"""Payment signals: money requested before anything of value is delivered."""
from __future__ import annotations

import re

from ..knowledge import patterns as P
from ..pipeline.masking import mask_account, mask_upi
from .base import Ctx, Rule, scan

_PAY_CONTEXT = re.compile(
    r"\b(?:pay|send|transfer|deposit|remit|upi|gpay|phonepe|paytm|scan|qr|bhejo|bhej)\b|भेज|जमा|ट्रांसफर|அனுப்ப|செலுத்த|பணம்",
    re.IGNORECASE,
)


_PAY_AMOUNT = re.compile(r"\bpay\s+(?:rs\.?\s?|₹\s?)[\d,]+\s+(?:on|to|via|at|through)\b")


def detect_upfront_fee(ctx: Ctx) -> list[str]:
    out = scan(ctx.text, P.UPFRONT_FEE)
    # "Pay 999 on <upi id>": an amount asked into a personal UPI id in a chat.
    if not out and ctx.ent.upi_ids and _PAY_AMOUNT.search(ctx.text):
        out = ["payment requested to a personal UPI id"]
    return out


_FUNDS_HELD = re.compile(P.FUNDS_HELD, re.IGNORECASE)
_HELD_LEGIT = re.compile(P.FUNDS_HELD_LEGIT_CONTEXT, re.IGNORECASE)
_FEE_DEMAND = re.compile(P.FEE_DEMAND, re.IGNORECASE)


def detect_withdrawal_fee(ctx: Ctx) -> list[str]:
    out = scan(ctx.text, P.WITHDRAWAL_FEE)
    if out:
        return out
    # "funds are blocked" on its own is how a normal IPO application (ASBA) is described.
    # Count it only if a fee is demanded, or there is no sign of that kind of context.
    held = scan(ctx.text, [P.FUNDS_HELD])
    if held and (_FEE_DEMAND.search(ctx.text) or not _HELD_LEGIT.search(ctx.text)):
        return held
    return []


def detect_personal_payee(ctx: Ctx) -> list[str]:
    """A UPI id or bank account in a chat message, in a payment context."""
    if not _PAY_CONTEXT.search(ctx.text):
        return []
    out = [mask_upi(u) for u in ctx.ent.upi_ids]
    if ctx.ent.ifsc or (ctx.ent.accounts and re.search(r"\b(?:a/?c|account|acc)\b|खाता|கணக்கு", ctx.text)):
        out += [mask_account(a) for a in ctx.ent.accounts[:1]] or ["bank account details"]
    return out[:3]


def detect_mule(ctx: Ctx) -> list[str]:
    return scan(ctx.text, P.MULE_ACCOUNT)


RULES = [
    Rule("UPFRONT_FEE", "payment", 30, "strong", detect_upfront_fee),
    Rule("WITHDRAWAL_BLOCKED_FEE", "payment", 35, "strong", detect_withdrawal_fee, forces="high"),
    Rule("MULE_ACCOUNT_REQUEST", "payment", 35, "strong", detect_mule, forces="high", quote_prone=True),
    Rule("PERSONAL_PAYEE", "payment", 20, "warning", detect_personal_payee),
]
