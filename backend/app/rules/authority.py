"""Authority signals: borrowed credibility and impersonation.

Important: a SEBI registration number is only checked for *format* here. A
well-formed number is not proof of registration, and a missing lookup is not
proof of fraud, so those cases are reported as "could not verify".
"""
from __future__ import annotations

import re

from ..knowledge import patterns as P
from .base import Ctx, Rule, scan

_ADVICE = re.compile(P.ADVICE_BEFORE, re.IGNORECASE)


def _claims(ctx: Ctx) -> list[str]:
    return scan(ctx.text, P.SEBI_CLAIM, before_blocker=_ADVICE)


def detect_claim_no_number(ctx: Ctx) -> list[str]:
    claims = _claims(ctx)
    return claims if claims and not ctx.ent.sebi_numbers else []


def detect_number_unverified(ctx: Ctx) -> list[str]:
    return [s.raw for s in ctx.ent.sebi_numbers if s.well_formed][:2]


def detect_number_bad_format(ctx: Ctx) -> list[str]:
    return [s.raw for s in ctx.ent.sebi_numbers if not s.well_formed][:2]


def detect_insider(ctx: Ctx) -> list[str]:
    return scan(ctx.text, P.INSIDER)


def detect_impersonation(ctx: Ctx) -> list[str]:
    return scan(ctx.text, P.AUTHORITY_IMPERSONATION)


_KYC_DONE = re.compile(r"kyc[^.!?\n]{0,40}\b(?:successfully|completed|approved|verified)\b|\b(?:successfully|completed)\b[^.!?\n]{0,25}kyc")


def detect_kyc(ctx: Ctx) -> list[str]:
    # "Your KYC has been successfully updated" is a confirmation, not pressure.
    if _KYC_DONE.search(ctx.text):
        return []
    return scan(ctx.text, P.KYC_PRESSURE)


RULES = [
    Rule("SEBI_CLAIM_NO_NUMBER", "authority", 15, "unverified", detect_claim_no_number, forces="verify"),
    Rule("SEBI_NUMBER_UNVERIFIED", "authority", 5, "unverified", detect_number_unverified, forces="verify"),
    Rule("SEBI_NUMBER_BAD_FORMAT", "authority", 25, "strong", detect_number_bad_format, forces="verify"),
    Rule("INSIDER_OR_OPERATOR_CLAIM", "authority", 25, "strong", detect_insider),
    Rule("AUTHORITY_IMPERSONATION", "authority", 30, "strong", detect_impersonation, forces="high", quote_prone=True),
    Rule("KYC_PRESSURE", "authority", 20, "warning", detect_kyc, quote_prone=True),
]
