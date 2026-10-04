"""Voice-call prototype (IVR) - for people with a basic phone and no smartphone.

PROTOTYPE STATUS: this speaks Twilio-style TwiML (<Gather>/<Say>/<Hangup>), which
several Indian telephony providers can also relay. It has been tested here with
simulated webhook requests only, NOT against a live phone number. The spoken
voices and Tamil/Hindi speech-recognition quality depend on the provider.

Flow:  /api/ivr/start  ->  press 1/2/3 for English/Tamil/Hindi
       /api/ivr/lang   ->  "say or read out the message"  (speech input)
       /api/ivr/result ->  spoken verdict, top reasons, first safe action
The spoken text is analysed with the same rules engine and is not stored.
Set IVR_TOKEN and put ?token=... on the webhook URLs so strangers cannot use it.
"""
from __future__ import annotations

import os
from xml.sax.saxutils import escape

from fastapi import APIRouter, Form, HTTPException, Query
from fastapi.responses import Response

from ..explain.composer import compose, template_for
from ..rules.engine import analyze_text

router = APIRouter(prefix="/api/ivr")

_VOICE = {"en": ("en-IN", "Polly.Aditi"), "hi": ("hi-IN", "Polly.Aditi"), "ta": ("ta-IN", None)}
_PROMPT = {
    "menu": {
        "en": "Welcome to RakshaLens. For English press 1.",
        "hi": "हिंदी के लिए 2 दबाएँ।",
        "ta": "தமிழுக்கு 3 ஐ அழுத்தவும்.",
    },
    "ask": {
        "en": "Please say or read out the message you received, after the beep. Do not say your OTP or bank details.",
        "ta": "உங்களுக்கு வந்த செய்தியை பீப் ஒலிக்குப் பிறகு சொல்லவும். உங்கள் OTP அல்லது வங்கி விவரங்களைச் சொல்ல வேண்டாம்.",
        "hi": "बीप के बाद आपको मिला संदेश बोलकर बताएँ। अपना OTP या बैंक की जानकारी न बोलें।",
    },
    "noinput": {
        "en": "We did not hear anything. Goodbye.",
        "ta": "எதுவும் கேட்கவில்லை. நன்றி.",
        "hi": "कुछ सुनाई नहीं दिया। धन्यवाद।",
    },
    "bye": {
        "en": "Do not pay anything until you have checked. Report at 1930. Goodbye.",
        "ta": "சரிபார்க்கும் வரை பணம் செலுத்த வேண்டாம். 1930 இல் புகாரளிக்கவும். நன்றி.",
        "hi": "जाँच करने तक कोई पैसा न भेजें। 1930 पर शिकायत करें। धन्यवाद।",
    },
}
_DIGIT_LANG = {"1": "en", "2": "hi", "3": "ta"}


def _check_token(token: str | None) -> None:
    expected = os.environ.get("IVR_TOKEN", "")
    if expected and token != expected:
        raise HTTPException(403, "forbidden")


def _say(text: str, lang: str) -> str:
    code, voice = _VOICE.get(lang, _VOICE["en"])
    attrs = f' language="{code}"' + (f' voice="{voice}"' if voice else "")
    return f"<Say{attrs}>{escape(text)}</Say>"


def _twiml(*parts: str) -> Response:
    return Response('<?xml version="1.0" encoding="UTF-8"?><Response>' + "".join(parts) + "</Response>", media_type="application/xml")


def _q(path: str, token: str | None, **kw: str) -> str:
    params = "&amp;".join(f"{k}={v}" for k, v in {**kw, **({"token": token} if token else {})}.items())
    return f"{path}?{params}" if params else path


@router.post("/start")
def start(token: str | None = Query(None)) -> Response:
    _check_token(token)
    return _twiml(
        f'<Gather input="dtmf" numDigits="1" timeout="6" action="{_q("/api/ivr/lang", token)}" method="POST">',
        _say(_PROMPT["menu"]["en"], "en"),
        _say(_PROMPT["menu"]["hi"], "hi"),
        _say(_PROMPT["menu"]["ta"], "ta"),
        "</Gather>",
        _say(_PROMPT["noinput"]["en"], "en"),
        "<Hangup/>",
    )


@router.post("/lang")
def pick_language(Digits: str = Form(""), token: str | None = Query(None)) -> Response:
    _check_token(token)
    lang = _DIGIT_LANG.get(Digits.strip())
    if not lang:
        return _twiml(f'<Redirect method="POST">{_q("/api/ivr/start", token)}</Redirect>')
    code = _VOICE[lang][0]
    return _twiml(
        f'<Gather input="speech" language="{code}" speechTimeout="auto" timeout="8" '
        f'action="{_q("/api/ivr/result", token, lang=lang)}" method="POST">',
        _say(_PROMPT["ask"][lang], lang),
        "</Gather>",
        _say(_PROMPT["noinput"][lang], lang),
        "<Hangup/>",
    )


@router.post("/result")
def result(
    SpeechResult: str = Form(""),
    lang: str = Query("en"),
    token: str | None = Query(None),
) -> Response:
    _check_token(token)
    lang = lang if lang in _VOICE else "en"
    text = SpeechResult.strip()[:2000]
    if len(text) < 8:
        return _twiml(_say(_PROMPT["noinput"][lang], lang), "<Hangup/>")
    res = compose(analyze_text(text), lang)
    t = template_for(lang)
    spoken = [res["headline"]]
    top = [f["title"] for f in res["findings"][:2]]
    if top:
        spoken.append(t["reasons_prefix"] + " " + "; ".join(top) + ".")
    if res["actions"]:
        spoken.append(res["actions"][0]["text"])
    return _twiml(_say(" ".join(spoken), lang), _say(_PROMPT["bye"][lang], lang), "<Hangup/>")
