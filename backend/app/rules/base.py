"""Shared rule machinery: context, Rule type and the phrase scanner."""
from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import Callable

from ..pipeline.entities import Entities
from ..pipeline.normalize import Normalized

_KB_DIR = Path(__file__).resolve().parent.parent / "knowledge"


@lru_cache(maxsize=1)
def load_brands() -> dict[str, list[str]]:
    data = json.loads((_KB_DIR / "brands.json").read_text(encoding="utf-8"))
    return {k: v for k, v in data.items() if not k.startswith("_")}


@dataclass
class Ctx:
    n: Normalized
    ent: Entities
    brands: dict[str, list[str]] = field(default_factory=load_brands)

    @property
    def text(self) -> str:
        return self.n.match


@dataclass(frozen=True)
class Rule:
    id: str
    group: str  # returns | authority | payment | channel | technical | pressure | recovery
    weight: int
    severity: str  # strong | warning | unverified
    detect: Callable[[Ctx], list[str]]
    forces: str | None = None  # None | "verify" | "high": minimum band when this fires
    quote_prone: bool = False  # phrase is often quoted in warnings -> halved in awareness messages


# --- negation handling -------------------------------------------------------

_NEG_PRE = re.compile(
    r"(?:\b(?:not|no|never|cannot|can't|don't|dont|do\s+not|doesn't|won't|without|nahi|nahin|mat|kabhi\s+nahi)\s+"
    r"(?:(?:be|is|are|been|ever|a|an|any|the|to|really|at\s+all)\s+)*"
    r"|(?:कभी\s*नहीं|नहीं|मत)\s+"
    r"|(?:வேண்டாம்|இல்லை)\s*)$"
)
_NEG_POST = re.compile(r"^\s*(?:नहीं|नही|नहि|nahi|nahin|illai|இல்லை|மாட்டார்|வேண்டாம்)")


def _negated(text: str, m: re.Match[str]) -> bool:
    pre = text[max(0, m.start() - 30) : m.start()]
    post = text[m.end() : m.end() + 14]
    return bool(_NEG_PRE.search(pre) or _NEG_POST.match(post))


@lru_cache(maxsize=512)
def _compile(p: str) -> tuple[re.Pattern[str], bool]:
    non_negatable = p.startswith("~")
    return re.compile(p[1:] if non_negatable else p, re.IGNORECASE | re.UNICODE), non_negatable


def scan(
    text: str,
    patterns: list[str],
    *,
    negatable: bool = True,
    limit: int = 3,
    before_blocker: re.Pattern[str] | None = None,
) -> list[str]:
    """Return short evidence snippets for every pattern hit, skipping negated ones."""
    out: list[str] = []
    for p in patterns:
        rx, non_neg = _compile(p)
        for m in rx.finditer(text):
            if negatable and not non_neg and _negated(text, m):
                continue
            if before_blocker and before_blocker.search(text[max(0, m.start() - 45) : m.start()]):
                continue
            snippet = re.sub(r"\s+", " ", m.group(0)).strip()[:70]
            if snippet and snippet not in out:
                out.append(snippet)
            if len(out) >= limit:
                return out
    return out


def redact_digits(snips: list[str]) -> list[str]:
    return [re.sub(r"\d+", "…", s) for s in snips]
