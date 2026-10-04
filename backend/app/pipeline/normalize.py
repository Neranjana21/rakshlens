"""Text normalisation.

Scam messages are often written to dodge keyword filters: spaced-out letters
("g u a r a n t e e d"), zero-width characters, look-alike Unicode, native
digits. We produce two views of the text:

* ``display`` - cleaned for showing back to the user (keeps Indic joiners).
* ``match``   - aggressively normalised for rule matching only.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

# Removed from both views: invisible, carry no meaning in any script we support.
_ALWAYS_STRIP = dict.fromkeys(map(ord, "​⁠﻿­‪‫‬‭‮"), None)
# ZWJ / ZWNJ matter for Indic rendering, so they are removed from the match view only.
_MATCH_STRIP = dict.fromkeys(map(ord, "‌‍"), None)

# Common Cyrillic/Greek look-alikes used to disguise Latin words.
_HOMOGLYPHS = str.maketrans(
    {
        "а": "a", "е": "e", "о": "o", "р": "p", "с": "c", "х": "x", "у": "y",
        "і": "i", "ј": "j", "ѕ": "s", "һ": "h", "ԁ": "d", "ɡ": "g", "ո": "n",
        "ο": "o", "α": "a", "ε": "e", "ι": "i", "ν": "v", "ρ": "p", "τ": "t",
    }
)

# Letters separated by single separators: "g.u.a.r.a.n.t.e.e.d", "s e b i".
_SPACED = re.compile(r"(?<![A-Za-z])(?:[A-Za-z][ \t.\-_*•·]){3,}[A-Za-z](?![A-Za-z])")
_WS = re.compile(r"[ \t ]+")
# Speech-to-text writes "30 percent" or "30 per cent"; the rules look for "30%".
_PERCENT_WORD = re.compile(r"(\d)\s*(?:percent|per\s*cent)\b")


@dataclass(frozen=True)
class Normalized:
    display: str
    match: str
    changed: bool  # True if we undid an obfuscation attempt (spaced letters, homoglyphs)
    original: str = ""  # the text as received (capped), for the "how we read it" view
    # What was undone, in order: (step id, example before, example after). Informational only.
    steps: tuple[tuple[str, str, str], ...] = ()


def _ascii_digits(s: str) -> str:
    out = []
    for ch in s:
        if ch.isdigit() and not ch.isascii():
            try:
                out.append(str(unicodedata.decimal(ch)))
                continue
            except ValueError:
                pass
        out.append(ch)
    return "".join(out)


def _despace(m: re.Match[str]) -> str:
    return re.sub(r"[ \t.\-_*•·]", "", m.group(0))


_ALWAYS_STRIP_CHARS = "".join(map(chr, _ALWAYS_STRIP))


def _is_styled(ch: str) -> bool:
    """Full-width Latin, mathematical bold/italic letters, circled letters: look like text, are not ASCII."""
    o = ord(ch)
    return 0xFF01 <= o <= 0xFF5E or 0x1D400 <= o <= 0x1D7FF or 0x2460 <= o <= 0x24FF


def _first_token(text: str, pred) -> str | None:
    for tok in text.split():
        if pred(tok):
            return tok
    return None


def _steps(raw: str, before_collapse: str) -> tuple[tuple[str, str, str], ...]:
    """Describe the clean-ups that actually changed this text, with one example each."""
    out: list[tuple[str, str, str]] = []
    if any(c in raw for c in _ALWAYS_STRIP_CHARS):
        out.append(("hidden", "", ""))
    tok = _first_token(raw, lambda t: any(_is_styled(c) for c in t))
    if tok:
        out.append(("width", tok[:30], unicodedata.normalize("NFKC", tok)[:30]))
    base = unicodedata.normalize("NFKC", raw).translate(_ALWAYS_STRIP)
    tok = _first_token(base, lambda t: any(c.isascii() and c.isalpha() for c in t) and t.translate(_HOMOGLYPHS) != t)
    if tok:
        out.append(("lookalike", tok[:30], tok.translate(_HOMOGLYPHS)[:30]))
    m = _SPACED.search(before_collapse.translate(_HOMOGLYPHS))
    if m:
        out.append(("spaced", m.group(0)[:40], _despace(m)[:40]))
    run = _first_token(base, lambda t: any(c.isdigit() and not c.isascii() for c in t))
    if run:
        out.append(("digits", run[:20], _ascii_digits(run)[:20]))
    return tuple(out)


def normalize(raw: str, max_chars: int = 8000) -> Normalized:
    raw = (raw or "")[:max_chars]
    text = unicodedata.normalize("NFKC", raw).translate(_ALWAYS_STRIP)
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    display = _WS.sub(" ", text).strip()

    # The match view is built from the text BEFORE whitespace is collapsed, so a
    # double space still separates two spaced-out words ("G U A R  R E T U R N S").
    match = text.translate(_MATCH_STRIP).replace("\u2019", "'").replace("\u2018", "'")
    translated = match.translate(_HOMOGLYPHS)
    homoglyph_hit = translated != match
    match = translated
    despaced = _SPACED.sub(_despace, match)
    spaced_hit = despaced != match
    match = _PERCENT_WORD.sub(r"\1%", _WS.sub(" ", _ascii_digits(despaced).lower()).strip())
    return Normalized(display=display, match=match, changed=homoglyph_hit or spaced_hit,
                      original=raw, steps=_steps(raw, text.translate(_MATCH_STRIP)))
