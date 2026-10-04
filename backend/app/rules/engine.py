"""Rules engine: pure, deterministic, explainable.

``analyze_text`` returns the set of fired signals with their evidence, a
heuristic score and a band. No I/O, no randomness, no model. The weights are
hand-set heuristics (see docs/rule-catalogue.md); they are NOT calibrated
probabilities and the UI never presents them as such.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field

from ..knowledge import patterns as P
from ..pipeline.entities import Entities, extract
from ..pipeline.normalize import Normalized, normalize
from . import authority, channel, payment, pressure, recovery, returns, technical
from .base import Ctx, Rule, scan

RULES: list[Rule] = [
    *returns.RULES,
    *authority.RULES,
    *payment.RULES,
    *channel.RULES,
    *technical.RULES,
    *pressure.RULES,
    *recovery.RULES,
]
RULES_BY_ID = {r.id: r for r in RULES}

BANDS = ["low", "verify", "high", "critical"]
_BAND_MIN = {"verify": 20, "high": 45, "critical": 70}


@dataclass
class Finding:
    id: str
    group: str
    weight: int
    severity: str  # strong | warning | unverified | info
    evidence: list[str] = field(default_factory=list)


@dataclass
class Analysis:
    band: str
    score: int
    stage: str
    findings: list[Finding]
    entities: Entities
    obfuscation_undone: bool
    awareness_context: bool
    disclaimer_present: bool
    n: Normalized


_QUOTED = re.compile(r"\"[^\"\n]{3,80}\"|“[^”\n]{3,80}”|‘[^’\n]{3,80}’|(?<![A-Za-z])'[^'\n]{3,80}'(?![A-Za-z])")


def _strip_quoted(n: Normalized) -> Normalized:
    """In a warning/awareness message, phrases inside quotes are mentions, not claims."""
    return Normalized(display=n.display, match=_QUOTED.sub(" ", n.match), changed=n.changed)


def band_for(score: int) -> str:
    band = "low"
    for b, floor in _BAND_MIN.items():
        if score >= floor:
            band = b
    return band


def _max_band(a: str, b: str) -> str:
    return a if BANDS.index(a) >= BANDS.index(b) else b


def _stage(ids: set[str], groups: set[str]) -> str:
    if "recovery" in groups or "WITHDRAWAL_BLOCKED_FEE" in ids:
        return "recovery"
    if "payment" in groups or "CREDENTIAL_REQUEST" in ids:
        return "payment_request"
    if groups & {"pressure", "authority", "channel", "technical", "returns"}:
        return "persuasion"
    return "discovery"


def analyze_text(raw: str) -> Analysis:
    n = normalize(raw)
    ent = extract(n.display, n.match)
    awareness = bool(scan(n.match, P.AWARENESS, negatable=False, limit=1))
    disclaimer = bool(scan(n.match, P.RISK_DISCLAIMER, negatable=False, limit=1))
    ctx = Ctx(n=_strip_quoted(n) if awareness else n, ent=ent)

    findings: list[Finding] = []
    forced = "low"
    for rule in RULES:
        evidence = rule.detect(ctx)
        if not evidence:
            continue
        w = rule.weight
        if awareness and rule.quote_prone:
            w = max(1, round(w / 2))
        findings.append(Finding(rule.id, rule.group, w, rule.severity, evidence))
        if rule.forces:
            forced = _max_band(forced, rule.forces)

    ids = {f.id for f in findings}
    groups = {f.group for f in findings}

    # Transparent combination bonus: a profit promise + a payment demand is the
    # classic advance-fee pattern. Shown to the user as its own finding.
    if "payment" in groups and groups & {"returns", "authority"}:
        findings.append(Finding("COMBO_PROMISE_PLUS_PAYMENT", "combo", 10, "strong", []))

    score = min(100, sum(f.weight for f in findings))
    band = _max_band(band_for(score), forced)
    findings.sort(key=lambda f: (-f.weight, f.id))
    return Analysis(
        band=band,
        score=score,
        stage=_stage(ids, groups),
        findings=findings,
        entities=ent,
        obfuscation_undone=n.changed,
        awareness_context=awareness,
        disclaimer_present=disclaimer,
        n=n,
    )
