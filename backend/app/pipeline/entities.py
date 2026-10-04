"""Entity extraction: the concrete things a message asks you to trust or use."""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import urlparse

URL_RE = re.compile(
    r"""(?ix)
    (?:https?://|www\.)[^\s<>"'()\[\]]+
    |
    \b(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+
      (?:com|in|net|org|xyz|top|live|co|info|site|online|app|club|vip|link|me|io|icu|buzz|shop|click|store|pro|fun|ly|gl|gd|to|cc|ink)
      (?:/[^\s<>"'()\[\]]*)?
    """
)
PHONE_RE = re.compile(r"(?<![\d.])(?:\+?91[\s-]?)?[6-9]\d{4}[\s-]?\d{5}(?!\d)")
# name@bank - but not name@domain.tld (an e-mail address)
UPI_RE = re.compile(r"(?<![\w.])[a-zA-Z0-9][a-zA-Z0-9._\-]{1,40}@[a-zA-Z][a-zA-Z0-9]{1,20}\b(?!\.[a-zA-Z])")
HANDLE_RE = re.compile(r"(?<![\w@./])@[A-Za-z][A-Za-z0-9_]{4,31}\b")
AMOUNT_RE = re.compile(
    r"(?i)(?:₹|rs\.?|inr|rupees?)\s?([\d,]+(?:\.\d+)?)|([\d,]+(?:\.\d+)?)\s?(?:rupees|rs\b|/-)"
)
PERCENT_RE = re.compile(r"(\d{1,4}(?:\.\d+)?)\s?%")
SEBI_NO_RE = re.compile(r"(?i)\bIN[A-Z]\s?[-]?\s?(\d{9})\b")
SEBI_NO_OCR_RE = re.compile(r"\b(IN[A-Z])\s?-?\s?([0-9OIL]{9})\b")
_OCR_DIGITS = str.maketrans("OIL", "011")
SEBI_NO_LOOSE_RE =re.compile(r"(?i)\b(?:sebi\s*)?reg(?:istration|\.)?\s*(?:no\.?|number|#)?\s*[:\-]?\s*(IN[A-Z]?[\s-]?[\dA-Z]{4,12})")
IFSC_RE = re.compile(r"\b[A-Z]{4}0[A-Z0-9]{6}\b")
ACCOUNT_RE = re.compile(r"(?<![\d.])\d{9,18}(?!\d)")

# Known SEBI registration-number families. Format only - never proof of registration.
SEBI_PREFIX_MEANING = {
    "INH": "research analyst",
    "INA": "investment adviser",
    "INZ": "stock broker",
    "INB": "stock broker (cash)",
    "INF": "stock broker (F&O)",
    "INP": "portfolio manager",
    "INM": "merchant banker",
    "IND": "depository participant",
}


@dataclass
class SebiNumber:
    raw: str
    well_formed: bool
    kind: str | None


@dataclass
class Entities:
    urls: list[str] = field(default_factory=list)
    domains: list[str] = field(default_factory=list)
    phones: list[str] = field(default_factory=list)
    upi_ids: list[str] = field(default_factory=list)
    handles: list[str] = field(default_factory=list)
    amounts: list[float] = field(default_factory=list)
    percents: list[float] = field(default_factory=list)
    sebi_numbers: list[SebiNumber] = field(default_factory=list)
    ifsc: list[str] = field(default_factory=list)
    accounts: list[str] = field(default_factory=list)


def _clean_url(u: str) -> str:
    return u.rstrip(".,;:!?)]}\"'")


def host_of(url: str) -> str:
    u = url if "://" in url else "http://" + url
    try:
        host = urlparse(u).hostname or ""
    except ValueError:
        host = ""
    return host.lower().lstrip(".")


def extract(display_text: str, match_text: str) -> Entities:
    """Extract from the display text (original case) and the match text (normalised)."""
    e = Entities()
    seen: set[str] = set()

    upis = [m.group(0) for m in UPI_RE.finditer(display_text)]
    e.upi_ids = list(dict.fromkeys(upis))

    for m in URL_RE.finditer(display_text):
        u = _clean_url(m.group(0))
        # Skip the bank part of a UPI id (name@oksbi) and plain file names.
        if any(u in up or up in u for up in e.upi_ids):
            continue
        if u.lower() in seen:
            continue
        seen.add(u.lower())
        e.urls.append(u)
        h = host_of(u)
        if h and h not in e.domains:
            e.domains.append(h)

    e.phones = list(dict.fromkeys(re.sub(r"[\s-]", "", m.group(0)) for m in PHONE_RE.finditer(display_text)))
    e.handles = list(dict.fromkeys(m.group(0) for m in HANDLE_RE.finditer(display_text)))

    for m in AMOUNT_RE.finditer(match_text):
        raw = (m.group(1) or m.group(2) or "").replace(",", "")
        try:
            e.amounts.append(float(raw))
        except ValueError:
            pass
    for m in PERCENT_RE.finditer(match_text):
        try:
            e.percents.append(float(m.group(1)))
        except ValueError:
            pass

    for m in SEBI_NO_RE.finditer(display_text.upper()):
        raw = re.sub(r"[\s-]", "", m.group(0))
        prefix = raw[:3]
        e.sebi_numbers.append(SebiNumber(raw=raw, well_formed=True, kind=SEBI_PREFIX_MEANING.get(prefix)))
    # Screenshots: OCR often reads 0 as O and 1 as I/L ("INHO00012345"). Accept 9 digit-like characters
    # when at least 6 are real digits, and repair them, so a number that is on screen is not reported missing.
    for m in SEBI_NO_OCR_RE.finditer(display_text.upper()):
        digits = m.group(2)
        if sum(c.isdigit() for c in digits) < 6:
            continue
        raw = m.group(1) + digits.translate(_OCR_DIGITS)
        if any(s.raw == raw for s in e.sebi_numbers):
            continue
        e.sebi_numbers.append(SebiNumber(raw=raw, well_formed=True, kind=SEBI_PREFIX_MEANING.get(raw[:3])))
    for m in SEBI_NO_LOOSE_RE.finditer(display_text):
        raw = re.sub(r"[\s-]", "", m.group(1).upper())
        if any(s.raw == raw for s in e.sebi_numbers):
            continue
        ok = bool(re.fullmatch(r"IN[A-Z]\d{9}", raw))
        e.sebi_numbers.append(SebiNumber(raw=raw, well_formed=ok, kind=SEBI_PREFIX_MEANING.get(raw[:3]) if ok else None))

    e.ifsc = list(dict.fromkeys(IFSC_RE.findall(display_text.upper())))
    phone_digits = {re.sub(r"\D", "", p)[-10:] for p in e.phones}
    accounts = []
    for m in ACCOUNT_RE.finditer(display_text):
        digits = m.group(0)
        if digits[-10:] in phone_digits and len(digits) <= 12:
            continue
        accounts.append(digits)
    e.accounts = list(dict.fromkeys(accounts))
    return e
