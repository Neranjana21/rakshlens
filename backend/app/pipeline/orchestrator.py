"""Runs the pipeline end to end. Nothing here persists anything."""
from __future__ import annotations

from typing import Any

from ..explain.composer import compose, template_for
from ..explain.llm import rewrite_summary
from ..rules.engine import analyze_text
from .ocr import ImageError, read_image
from .source import detect_source


class InputError(ValueError):
    def __init__(self, code: str):
        super().__init__(code)
        self.code = code


async def run(
    *,
    text: str,
    image: bytes | None,
    media_type: str,
    lang: str,
    allow_cloud: bool,
) -> dict[str, Any]:
    ocr_info: dict[str, Any] | None = None
    combined = (text or "").strip()

    if image:
        try:
            res = await read_image(image, media_type, allow_cloud)
        except ImageError as exc:
            raise InputError(str(exc)) from exc
        ocr_info = {"engine": res.engine, "cloud_used": res.cloud_used, "readable": res.quality >= 0.6}
        combined = (combined + "\n" + res.text).strip()

    if len(combined) < 8:
        raise InputError("no_text_found" if image else "text_too_short")

    analysis = analyze_text(combined)

    llm_summary = None
    cloud_text_used = False
    if allow_cloud and analysis.findings:
        t = template_for(lang)
        reasons = [t["rules"][f.id] for f in analysis.findings[:4]]
        llm_summary = await rewrite_summary(t["bands"][analysis.band]["label"], t["bands"][analysis.band]["headline"], reasons, t["code"])
        cloud_text_used = llm_summary is not None

    result = compose(analysis, lang, llm_summary, detect_source(combined, image))
    result["input"] = {
        "chars": len(combined),
        "from_image": bool(image),
        "ocr": ocr_info,
        "cloud_used": bool((ocr_info or {}).get("cloud_used")) or cloud_text_used,
        "extracted_text": combined[:2000] if image else None,
    }
    return result
