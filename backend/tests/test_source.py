"""Source (WhatsApp / Telegram / SMS ...) guessing: conservative by design."""
import io

import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.api import middleware
from app.main import app
from app.pipeline.source import detect_source


def _png(rgb, size=(120, 200)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, rgb).save(buf, "PNG")
    return buf.getvalue()


@pytest.mark.parametrize(
    "text,expected",
    [
        ("Forwarded many times\nJoin our VIP group, guaranteed returns", "whatsapp"),
        ("Messages and calls are end-to-end encrypted. Guaranteed 25% returns", "whatsapp"),
        ("Forwarded from Stock Kings VIP\nBuy now target 180\n12.4K views", "telegram"),
        ("Praveen\nlast seen recently\nGuaranteed profit", "telegram"),
        ("VM-SBIINB: Your KYC is expiring. Update now http://sbi-kyc.top", "sms"),
        ("Subject: Urgent KYC\nFrom: care@sbi-kyc.top\nTo: you@example.com\nUpdate now", "email"),
        ("Pinned by creator\nGuaranteed returns, DM for tips", "social"),
    ],
)
def test_origin_clues_are_recognised(text, expected):
    got = detect_source(text)
    assert got is not None and got.id == expected and got.basis == "text"


@pytest.mark.parametrize(
    "text",
    [
        # The scam names the app it wants to move you to; that is not where it arrived.
        "Guaranteed 25% returns. Contact our manager on Telegram @prof_raj_vip",
        "Join our WhatsApp group https://chat.whatsapp.com/abc123 for VIP calls",
        "Join https://t.me/vipcalls for daily tips",
        "Pay Rs 5000 registration fee to activate your account",
        "",
    ],
)
def test_mentions_of_an_app_are_not_enough(text):
    assert detect_source(text) is None


def test_conflicting_clues_give_no_answer():
    assert detect_source("Forwarded many times\nForwarded from Stock Kings") is None


def test_screenshot_colours_alone_are_only_possible():
    got = detect_source("some text", _png((0xEF, 0xEA, 0xE2)))  # WhatsApp wallpaper beige
    assert got is not None and got.id == "whatsapp"
    assert got.basis == "look" and got.confidence == "possible"


def test_telegram_blue_screenshot():
    got = detect_source("some text", _png((0x51, 0x7D, 0xA2)))
    assert got is not None and got.id == "telegram"


def test_plain_screenshot_is_unknown():
    assert detect_source("some text", _png((255, 255, 255))) is None


def test_look_plus_text_is_likely_and_both():
    got = detect_source("Forwarded many times", _png((0xEF, 0xEA, 0xE2)))
    assert got is not None and got.id == "whatsapp" and got.basis == "both" and got.confidence == "likely"


def test_corrupt_image_does_not_crash():
    assert detect_source("hello world", b"not an image") is None


@pytest.fixture()
def client():
    middleware._hits.clear()
    return TestClient(app)


def test_api_always_returns_a_source_block(client):
    r = client.post("/api/analyze/text", json={"text": "Guaranteed returns, pay registration fee now", "lang": "en"})
    assert r.status_code == 200
    src = r.json()["source"]
    assert src["id"] == "unknown" and src["tip"] is None and src["label"]


@pytest.mark.parametrize("lang", ["en", "ta", "hi"])
def test_api_source_is_localised(client, lang):
    r = client.post("/api/analyze/text", json={"text": "Forwarded many times\nGuaranteed returns, pay registration fee", "lang": lang})
    src = r.json()["source"]
    assert src["id"] == "whatsapp" and "WhatsApp" in src["label"] and src["tip"] and src["note"]
    assert "{app}" not in src["label"]
