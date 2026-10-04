"""Privacy masking.

Two uses:
1. The evidence report and the masked excerpt shown to the user never carry full
   phone numbers, UPI ids or account numbers.
2. Anything sent to a cloud model is built from *findings*, not from the raw
   message; masking is the second line of defence if raw text is ever used.
"""
from __future__ import annotations

import re

from .entities import ACCOUNT_RE, IFSC_RE, PHONE_RE, UPI_RE


def mask_phone(p: str) -> str:
    d = re.sub(r"\D", "", p)
    return f"+91 ******{d[-4:]}" if len(d) >= 4 else "******"


def mask_upi(u: str) -> str:
    name, _, bank = u.partition("@")
    keep = name[:2] if len(name) > 3 else name[:1]
    return f"{keep}***@{bank}"


def mask_account(a: str) -> str:
    return "*" * max(len(a) - 4, 4) + a[-4:]


def mask_text(text: str) -> str:
    """Mask phones, UPI ids, IFSC-qualified and bare long account numbers."""
    out = UPI_RE.sub(lambda m: mask_upi(m.group(0)), text)
    out = PHONE_RE.sub(lambda m: mask_phone(m.group(0)), out)
    out = IFSC_RE.sub("****0******", out)
    out = ACCOUNT_RE.sub(lambda m: mask_account(m.group(0)), out)
    return out
