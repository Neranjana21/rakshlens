import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw

from app.api import middleware
from app.explain import llm
from app.main import app

client = TestClient(app)
MSG = "Guaranteed 25% monthly returns. Pay ₹5,000 registration fee to activate. Contact our manager on Telegram."


def test_health_and_config():
    assert client.get("/api/health").json() == {"ok": True}
    cfg = client.get("/api/config").json()
    assert cfg["stores_nothing"] is True and {l["code"] for l in cfg["langs"]} == {"en", "ta", "hi"}


def test_config_lists_the_same_helplines_as_a_result():
    # The home screen shows these without a result, so they must match what a result shows.
    cfg = client.get("/api/config").json()
    result = client.post("/api/analyze/text", json={"text": MSG, "lang": "en"}).json()
    assert cfg["helplines"] == result["helplines"]
    assert {h["id"] for h in cfg["helplines"]} == {"cyber1930", "cybercrime", "scores", "sebi"}


@pytest.mark.parametrize("lang", ["en", "ta", "hi"])
def test_analyze_each_language(lang):
    r = client.post("/api/analyze", data={"text": MSG, "lang": lang})
    j = r.json()
    assert r.status_code == 200 and j["band"] in ("high", "critical") and j["lang"] == lang
    assert j["could_not_check"] and j["actions"] and j["disclaimer"]
    assert r.headers["cache-control"] == "no-store"


def test_unknown_language_falls_back_to_english():
    assert client.post("/api/analyze", data={"text": MSG, "lang": "xx"}).json()["lang"] == "en"


def test_json_endpoint():
    assert client.post("/api/analyze/text", json={"text": MSG}).status_code == 200


def test_short_text_rejected():
    assert client.post("/api/analyze", data={"text": "hi"}).status_code == 422


def test_bad_upload_type_rejected():
    assert client.post("/api/analyze", files={"image": ("a.txt", b"abc", "text/plain")}).status_code == 415


def test_corrupt_image_rejected():
    r = client.post("/api/analyze", files={"image": ("a.png", b"not an image", "image/png")})
    assert r.status_code == 422


def test_image_roundtrip():
    img = Image.new("RGB", (900, 200), "white")
    ImageDraw.Draw(img).text((20, 40), "Guaranteed profit. Pay registration fee to join.", fill="black")
    buf = io.BytesIO()
    img.save(buf, "PNG")
    r = client.post("/api/analyze", files={"image": ("s.png", buf.getvalue(), "image/png")})
    assert r.status_code in (200, 422)  # 422 only if the local OCR cannot read the tiny default font


def test_security_headers_and_report_csp():
    h = client.get("/api/health").headers
    assert h["x-content-type-options"] == "nosniff" and "frame-ancestors 'none'" in h["content-security-policy"]
    res = client.post("/api/analyze", data={"text": MSG}).json()
    rep = client.post("/api/report", json={"result": res, "lang": "en"})
    assert rep.status_code == 200 and "<script" not in rep.text.lower()


def test_report_escapes_html():
    res = {"band_label": "<script>alert(1)</script>", "summary": "<img src=x onerror=alert(1)>", "findings": []}
    html = client.post("/api/report", json={"result": res, "lang": "en"}).text
    assert "<script>alert" not in html and "<img src=x" not in html


def test_rate_limit(monkeypatch):
    middleware._hits.clear()
    monkeypatch.setattr(middleware.settings.__class__, "rate_limit_per_min", 3, raising=False)
    object.__setattr__(middleware.settings, "rate_limit_per_min", 3)
    codes = [client.post("/api/analyze", data={"text": MSG}).status_code for _ in range(5)]
    assert 429 in codes
    object.__setattr__(middleware.settings, "rate_limit_per_min", 30)
    middleware._hits.clear()


def test_llm_output_failing_guard_falls_back(monkeypatch):
    async def bad(*a, **k):
        return None  # what rewrite_summary returns when the guard rejects the model text

    monkeypatch.setattr("app.pipeline.orchestrator.rewrite_summary", bad)
    j = client.post("/api/analyze", data={"text": MSG, "allow_cloud": "true"}).json()
    assert j["summary_source"] == "template" and j["input"]["cloud_used"] is False


def test_llm_rewrite_uses_only_guarded_text(monkeypatch):
    class R:
        def raise_for_status(self): ...
        def json(self): return {"content": [{"type": "text", "text": "You should buy this stock."}]}

    class C:
        async def __aenter__(self): return self
        async def __aexit__(self, *a): ...
        async def post(self, *a, **k): return R()

    object.__setattr__(llm.settings, "api_key", "test-key")
    monkeypatch.setattr(llm.httpx, "AsyncClient", lambda **k: C())
    import asyncio
    out = asyncio.run(llm.rewrite_summary("High risk", "Headline", [("Title", "Detail")], "en"))
    assert out is None  # advice language rejected
    object.__setattr__(llm.settings, "api_key", "")
