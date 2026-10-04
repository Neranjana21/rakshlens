"""HTTP API. Stateless: nothing submitted is written anywhere."""
from __future__ import annotations

from typing import Any

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field

from ..config import settings
from ..explain.composer import HELPLINES, LANGS
from ..pipeline.orchestrator import InputError, run
from ..report import builder

router = APIRouter(prefix="/api")

_ALLOWED_IMAGE = {"image/png", "image/jpeg", "image/webp", "image/gif", "image/bmp"}


def _lang(code: str) -> str:
    return code if code in {l["code"] for l in LANGS} else "en"


class TextRequest(BaseModel):
    text: str = Field(min_length=1, max_length=8000)
    lang: str = "en"
    allow_cloud: bool = False


class ReportRequest(BaseModel):
    result: dict[str, Any]
    lang: str = "en"


@router.get("/health")
def health() -> dict[str, Any]:
    return {"ok": True}


@router.get("/config")
def config() -> dict[str, Any]:
    return {
        "langs": LANGS,
        "helplines": HELPLINES,  # same list the result page shows, so the home screen can show it too
        "cloud_available": settings.llm_available,
        "max_upload_mb": settings.max_upload_mb,
        "stores_nothing": True,
    }


@router.post("/analyze")
async def analyze(
    text: str = Form(""),
    lang: str = Form("en"),
    allow_cloud: bool = Form(False),
    image: UploadFile | None = File(None),
) -> dict[str, Any]:
    data: bytes | None = None
    media = ""
    if image is not None and image.filename:
        media = (image.content_type or "").lower()
        if media not in _ALLOWED_IMAGE:
            raise HTTPException(415, {"error": "unsupported_image"})
        data = await image.read(settings.max_upload_mb * 1024 * 1024 + 1)
        if len(data) > settings.max_upload_mb * 1024 * 1024:
            raise HTTPException(413, {"error": "too_large"})
    try:
        return await run(text=text[:8000], image=data, media_type=media, lang=_lang(lang), allow_cloud=allow_cloud)
    except InputError as exc:
        raise HTTPException(422, {"error": exc.code}) from exc


@router.post("/analyze/text")
async def analyze_text_json(req: TextRequest) -> dict[str, Any]:
    """JSON endpoint for the browser extension and the voice-call prototype."""
    try:
        return await run(text=req.text, image=None, media_type="", lang=_lang(req.lang), allow_cloud=req.allow_cloud)
    except InputError as exc:
        raise HTTPException(422, {"error": exc.code}) from exc


@router.post("/report", response_class=HTMLResponse)
def report(req: ReportRequest) -> HTMLResponse:
    html_doc = builder.build(req.result, _lang(req.lang))
    return HTMLResponse(
        html_doc,
        headers={
            "Content-Security-Policy": "default-src 'none'; style-src 'unsafe-inline'",
            "Content-Disposition": 'inline; filename="rakshalens-report.html"',
        },
    )
