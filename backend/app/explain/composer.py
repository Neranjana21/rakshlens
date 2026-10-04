"""Turn an Analysis into the JSON the UI renders, in the requested language."""
from __future__ import annotations

from typing import Any

from ..pipeline.masking import mask_phone, mask_text, mask_upi
from ..pipeline.source import Source
from ..rules.engine import Analysis
from .templates import en, hi, ta

TEMPLATES = {"en": en.T, "ta": ta.T, "hi": hi.T}
LANGS = [
    {"code": "en", "name": "English"},
    {"code": "ta", "name": "தமிழ்"},
    {"code": "hi", "name": "हिन्दी"},
]

HELPLINES = [
    {"id": "cyber1930", "value": "1930", "href": "tel:1930"},
    {"id": "cybercrime", "value": "cybercrime.gov.in", "href": "https://cybercrime.gov.in"},
    {"id": "scores", "value": "scores.sebi.gov.in", "href": "https://scores.sebi.gov.in"},
    {"id": "sebi", "value": "sebi.gov.in", "href": "https://www.sebi.gov.in"},
]


def template_for(lang: str) -> dict[str, Any]:
    return TEMPLATES.get(lang, TEMPLATES["en"])


def _entities_view(a: Analysis) -> dict[str, Any]:
    e = a.entities
    return {
        "links": e.urls[:5],
        "phones": [mask_phone(p) for p in e.phones[:3]],
        "upi_ids": [mask_upi(u) for u in e.upi_ids[:3]],
        "handles": e.handles[:3],
        "sebi_numbers": [{"value": s.raw, "format_ok": s.well_formed, "kind": s.kind} for s in e.sebi_numbers[:3]],
    }


def _actions(a: Analysis) -> list[str]:
    ids = {f.id for f in a.findings}
    if a.band in ("high", "critical"):
        keys = ["stop", "verify", "preserve", "report", "paid"]
        if a.stage == "recovery" or ids & {"RECOVERY_SCAM", "WITHDRAWAL_BLOCKED_FEE"}:
            keys.append("recovery")
        keys.append("talk")
        return keys
    if a.band == "verify":
        return ["verify", "stop", "talk"]
    return ["low_general", "verify", "talk"]


def _source_view(source: Source | None, t: dict[str, Any]) -> dict[str, Any]:
    """Where the message seems to come from. Always present; id is "unknown" when we cannot tell."""
    s = t["source"]
    if source is None:
        return {"id": "unknown", "label": s["unclear"], "confidence": None, "basis": None, "basis_label": None, "tip": None, "note": None, "title": s["title"]}
    headline = s["likely" if source.confidence == "likely" else "possible"].replace("{app}", s["names"][source.id])
    return {
        "id": source.id,
        "label": headline,
        "confidence": source.confidence,
        "basis": source.basis,
        "basis_label": s["basis"][source.basis],
        "tip": s["tips"][source.id],
        "note": s["guess_note"],
        "title": s["title"],
    }


def _normalization_view(a: Analysis, t: dict[str, Any]) -> dict[str, Any] | None:
    """What was undone before checking (spaced letters, look-alikes, native digits ...). None if nothing."""
    n = a.n
    if not n.steps:
        return None
    s = t["norm"]
    return {
        "title": s["title"],
        "intro": s["intro"],
        "steps": [
            {"id": sid, "label": s["steps"][sid], "before": mask_text(before), "after": mask_text(after)}
            for sid, before, after in n.steps
        ],
        "original_label": s["original"],
        "original": mask_text(n.original)[:600],
        "cleaned_label": s["cleaned"],
        "cleaned": mask_text(n.match)[:600],
    }


def compose(a: Analysis, lang: str, llm_summary: str | None = None, source: Source | None = None) -> dict[str, Any]:
    t = template_for(lang)
    findings = []
    for f in a.findings:
        title, detail = t["rules"][f.id]
        findings.append(
            {
                "id": f.id,
                "group": f.group,
                "severity": f.severity,
                "severity_label": t["severity"][f.severity],
                "weight": f.weight,
                "title": title,
                "detail": detail,
                "evidence": [mask_text(e) for e in f.evidence][:3],
            }
        )

    notes = []
    for key, present in (
        ("awareness", a.awareness_context),
        ("disclaimer", a.disclaimer_present),
        ("obfuscation", a.obfuscation_undone),
    ):
        if present:
            title, detail = t["notes"][key]
            notes.append({"id": key, "title": title, "detail": detail})
    if not a.findings:
        title, detail = t["notes"]["no_findings"]
        notes.append({"id": "no_findings", "title": title, "detail": detail})

    ids = {f.id for f in a.findings}
    unc_keys = ["sender", "scope"]
    if ids & {"SEBI_CLAIM_NO_NUMBER", "SEBI_NUMBER_UNVERIFIED", "SEBI_NUMBER_BAD_FORMAT"}:
        unc_keys.append("registration")
    if a.entities.urls:
        unc_keys.append("links")
    unc_keys.append("verdict")

    band = t["bands"][a.band]
    top = [f["title"] for f in findings[:3]]
    template_summary = band["headline"] + (f" {t['reasons_prefix']} " + "; ".join(top) + "." if top else "")

    return {
        "band": a.band,
        "band_label": band["label"],
        "headline": band["headline"],
        "score": a.score,
        "score_note": "heuristic",
        "stage": a.stage,
        "stage_label": t["stages"][a.stage],
        "source": _source_view(source, t),
        "normalization": _normalization_view(a, t),
        "summary": llm_summary or template_summary,
        "summary_source": "llm" if llm_summary else "template",
        "findings": findings,
        "notes": notes,
        "seen_in_message": [f for f in findings if f["severity"] in ("strong", "warning")],
        "unverified_claims": [f for f in findings if f["severity"] == "unverified"],
        "could_not_check": [t["uncertainty"][k] for k in unc_keys],
        "actions": [{"id": k, "text": t["actions"][k]} for k in _actions(a)],
        "helplines": HELPLINES,
        "entities": _entities_view(a),
        "masked_text": mask_text(a.n.display)[:1500],
        "disclaimer": t["disclaimer"],
        "lang": t["code"],
        "speech_lang": t["speech_lang"],
    }
