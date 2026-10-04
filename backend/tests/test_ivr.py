import xml.dom.minidom

from fastapi.testclient import TestClient

from app.main import app

c = TestClient(app)


def parse(r):
    assert r.status_code == 200 and r.headers["content-type"].startswith("application/xml")
    return xml.dom.minidom.parseString(r.text)  # must be well-formed XML


def test_menu_offers_three_languages():
    d = parse(c.post("/api/ivr/start"))
    assert d.getElementsByTagName("Gather")[0].getAttribute("input") == "dtmf"
    assert len(d.getElementsByTagName("Say")) >= 4


def test_language_choice_asks_for_speech_in_that_language():
    d = parse(c.post("/api/ivr/lang", data={"Digits": "3"}))
    assert d.getElementsByTagName("Gather")[0].getAttribute("language") == "ta-IN"
    assert "lang=ta" in d.getElementsByTagName("Gather")[0].getAttribute("action")


def test_bad_digit_returns_to_menu():
    d = parse(c.post("/api/ivr/lang", data={"Digits": "9"}))
    assert d.getElementsByTagName("Redirect")


def test_spoken_verdict_for_a_scam():
    d = parse(c.post("/api/ivr/result?lang=en", data={"SpeechResult": "guaranteed profit pay registration fee to join telegram group"}))
    spoken = " ".join(n.firstChild.data for n in d.getElementsByTagName("Say"))
    assert "scam" in spoken.lower() and "1930" in spoken


def test_spoken_verdict_in_hindi_and_xml_escaping():
    d = parse(c.post("/api/ivr/result?lang=hi", data={"SpeechResult": "पक्का मुनाफा <b>रजिस्ट्रेशन फीस</b> & जमा करें"}))
    assert d.getElementsByTagName("Say")[0].getAttribute("language") == "hi-IN"


def test_empty_speech_hangs_up():
    d = parse(c.post("/api/ivr/result?lang=en", data={"SpeechResult": ""}))
    assert d.getElementsByTagName("Hangup")


def test_token_required_when_configured(monkeypatch):
    monkeypatch.setenv("IVR_TOKEN", "s3cret")
    assert c.post("/api/ivr/start").status_code == 403
    assert c.post("/api/ivr/start?token=s3cret").status_code == 200
