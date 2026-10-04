"""The 'how we read this message' view: which clean-ups are reported, and that normal text reports none."""
import pytest
from fastapi.testclient import TestClient

from app.api import middleware
from app.main import app
from app.pipeline.normalize import normalize


def step_ids(text: str) -> list[str]:
    return [sid for sid, _, _ in normalize(text).steps]


def test_plain_message_has_no_steps():
    assert step_ids("Guaranteed returns, pay registration fee now") == []


@pytest.mark.parametrize(
    "text,expected",
    [
        ("G.U.A.R.A.N.T.E.E.D returns", "spaced"),
        ("g u a r a n t e e d returns", "spaced"),
        ("ＧＵＡＲＡＮＴＥＥＤ returns", "width"),
        ("𝐆𝐮𝐚𝐫𝐚𝐧𝐭𝐞𝐞𝐝 returns", "width"),
        ("Gu​aran​teed returns", "hidden"),
        ("gаrаntееd returns pay fee", "lookalike"),  # Cyrillic а / е
        ("Pay Rs ५००० to activate", "digits"),
        ("செலுத்துங்கள் ௫௦௦௦ ரூபாய்", "digits"),
    ],
)
def test_each_disguise_is_reported(text, expected):
    assert expected in step_ids(text)


def test_examples_show_before_and_after():
    steps = {sid: (b, a) for sid, b, a in normalize("G.U.A.R.A.N.T.E.E.D returns. Pay ₹ ५०००").steps}
    assert steps["spaced"] == ("G.U.A.R.A.N.T.E.E.D", "GUARANTEED")
    assert steps["digits"] == ("५०००", "5000")


@pytest.mark.parametrize(
    "text",
    [
        "आपका SIP 5000 रुपये आज कट गया है। क़ीमत और फ़ायदा देखें।",  # nukta letters are not a disguise
        "வணக்கம், உங்கள் கணக்கில் பணம் வரவு வைக்கப்பட்டுள்ளது.",
        "Pure Cyrillic: привет мир",  # not mixed into a Latin word
    ],
)
def test_ordinary_non_english_text_reports_no_disguise(text):
    assert not [s for s in step_ids(text) if s in ("lookalike", "width", "hidden", "spaced")]


@pytest.fixture()
def client():
    middleware._hits.clear()
    return TestClient(app)


def test_api_returns_the_view_only_when_something_was_undone(client):
    plain = client.post("/api/analyze/text", json={"text": "Guaranteed returns, pay registration fee now", "lang": "en"}).json()
    assert plain["normalization"] is None
    dressed = client.post("/api/analyze/text", json={"text": "G.U.A.R.A.N.T.E.E.D returns, pay registration fee now", "lang": "en"}).json()
    nz = dressed["normalization"]
    assert nz and nz["steps"][0]["id"] == "spaced" and "guaranteed" in nz["cleaned"]
    assert nz["original"].startswith("G.U.A.R")


@pytest.mark.parametrize("lang", ["en", "ta", "hi"])
def test_view_is_localised(client, lang):
    r = client.post("/api/analyze/text", json={"text": "Pay Rs ५००० to activate guaranteed returns", "lang": lang}).json()
    nz = r["normalization"]
    assert nz and nz["title"] and nz["steps"][0]["label"] and nz["original_label"] and nz["cleaned_label"]


def test_view_masks_phone_numbers(client):
    r = client.post("/api/analyze/text", json={"text": "G.U.A.R.A.N.T.E.E.D returns call 9876543210 now", "lang": "en"}).json()
    assert "9876543210" not in r["normalization"]["original"] + r["normalization"]["cleaned"]
