"""Printable evidence report (HTML; the browser's Print > Save as PDF makes the PDF).

Built only from the analysis result: phone numbers, UPI ids and account numbers
are already masked. The user should keep the ORIGINAL screenshot themselves,
which is what cybercrime.gov.in and the bank will actually ask for.
"""
from __future__ import annotations

import html
from datetime import datetime, timezone
from typing import Any

L = {
    "en": {
        "title": "RakshaLens evidence report", "risk": "Risk level", "found": "What we found",
        "unverified": "Claims we could not verify", "unchecked": "What we could not check",
        "next": "What to do now", "msg": "Message (phone numbers, UPI ids and account numbers masked)",
        "keep": "Keep your original screenshot and chat. Authorities and your bank will ask for the original, not this report.",
        "gen": "Generated", "helplines": "Where to report", "stage": "Stage",
        "cyber1930": "National Cyber Crime Helpline", "cybercrime": "Cyber crime reporting portal",
        "scores": "SEBI SCORES (investor complaints)", "sebi": "SEBI website",
        "note": "This report is a risk assessment of the message text, not a legal finding.",
    },
    "ta": {
        "title": "RakshaLens ஆதார அறிக்கை", "risk": "ஆபத்து நிலை", "found": "நாங்கள் கண்டவை",
        "unverified": "சரிபார்க்க முடியாத கூற்றுகள்", "unchecked": "சரிபார்க்க முடியாதவை",
        "next": "இப்போது செய்ய வேண்டியவை", "msg": "செய்தி (தொலைபேசி எண்கள், UPI ஐடிகள், கணக்கு எண்கள் மறைக்கப்பட்டுள்ளன)",
        "keep": "உங்கள் அசல் ஸ்கிரீன்ஷாட்டையும் அரட்டையையும் வைத்திருங்கள். அதிகாரிகளும் வங்கியும் இந்த அறிக்கையை அல்ல, அசலையே கேட்பார்கள்.",
        "gen": "உருவாக்கப்பட்டது", "helplines": "எங்கே புகாரளிக்கலாம்", "stage": "நிலை",
        "cyber1930": "தேசிய சைபர் குற்ற உதவி எண்", "cybercrime": "சைபர் குற்றப் புகார் தளம்",
        "scores": "SEBI SCORES (முதலீட்டாளர் புகார்கள்)", "sebi": "SEBI இணையதளம்",
        "note": "இது செய்தியின் உரையைப் பற்றிய ஆபத்து மதிப்பீடு மட்டுமே; சட்டப்படியான முடிவு அல்ல.",
    },
    "hi": {
        "title": "RakshaLens सबूत रिपोर्ट", "risk": "जोखिम स्तर", "found": "हमें क्या मिला",
        "unverified": "ऐसे दावे जिनकी जाँच नहीं हो सकी", "unchecked": "जो हम जाँच नहीं सके",
        "next": "अभी क्या करें", "msg": "संदेश (फ़ोन नंबर, UPI आईडी और खाता नंबर छिपाए गए हैं)",
        "keep": "अपना मूल स्क्रीनशॉट और चैट सुरक्षित रखें। अधिकारी और बैंक इस रिपोर्ट के बजाय मूल माँगेंगे।",
        "gen": "बनाई गई", "helplines": "कहाँ शिकायत करें", "stage": "चरण",
        "cyber1930": "राष्ट्रीय साइबर अपराध हेल्पलाइन", "cybercrime": "साइबर अपराध शिकायत पोर्टल",
        "scores": "SEBI SCORES (निवेशक शिकायतें)", "sebi": "SEBI वेबसाइट",
        "note": "यह संदेश के पाठ का जोखिम आकलन है, कानूनी निष्कर्ष नहीं।",
    },
}

_CSS = """
body{font:16px/1.55 system-ui,-apple-system,'Segoe UI',Roboto,'Noto Sans','Noto Sans Tamil','Noto Sans Devanagari',sans-serif;max-width:760px;margin:24px auto;padding:0 16px;color:#1a1a1a}
h1{font-size:1.4rem;margin:0 0 4px}h2{font-size:1.05rem;margin:22px 0 6px;border-bottom:1px solid #ddd;padding-bottom:4px}
.band{display:inline-block;padding:4px 12px;border-radius:6px;font-weight:700;border:2px solid #1a1a1a}
.f{margin:8px 0;padding:8px 12px;border-left:4px solid #888;background:#f6f6f6}.f b{display:block}
.m{white-space:pre-wrap;background:#f6f6f6;padding:10px;border-radius:6px;font-size:.92rem}
.small{color:#555;font-size:.88rem}li{margin:4px 0}
@media print{body{margin:0}a{color:inherit;text-decoration:none}}
"""


def _s(x: Any, n: int = 600) -> str:
    return html.escape(str(x if x is not None else "")[:n])


def build(result: dict[str, Any], lang: str) -> str:
    lab = L.get(lang, L["en"])
    lang = lang if lang in L else "en"
    now = datetime.now(timezone.utc).strftime("%d %b %Y, %H:%M UTC")

    findings = "".join(
        f'<div class="f"><b>{_s(f.get("title"))} <span class="small">({_s(f.get("severity_label"), 60)})</span></b>'
        f'{_s(f.get("detail"), 700)}'
        + (f'<div class="small">“{" ”, “".join(_s(e, 90) for e in (f.get("evidence") or [])[:3])}”</div>' if f.get("evidence") else "")
        + "</div>"
        for f in (result.get("seen_in_message") or [])[:12]
    )
    unv = "".join(
        f'<div class="f"><b>{_s(f.get("title"))}</b>{_s(f.get("detail"), 700)}</div>'
        for f in (result.get("unverified_claims") or [])[:6]
    )
    unchecked = "".join(f"<li>{_s(x, 400)}</li>" for x in (result.get("could_not_check") or [])[:8])
    actions = "".join(f"<li>{_s(a.get('text'), 500)}</li>" for a in (result.get("actions") or [])[:10] if isinstance(a, dict))
    helplines = "".join(
        f"<li>{_s(lab.get(h.get('id'), h.get('id')), 80)}: <b>{_s(h.get('value'), 60)}</b></li>"
        for h in (result.get("helplines") or [])[:6]
        if isinstance(h, dict)
    )

    return f"""<!doctype html><html lang="{lang}"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1"><title>{_s(lab['title'])}</title>
<style>{_CSS}</style></head><body>
<h1>{_s(lab['title'])}</h1>
<div class="small">{_s(lab['gen'])}: {now}</div>
<h2>{_s(lab['risk'])}</h2>
<span class="band">{_s(result.get('band_label'), 80)}</span>
<span class="small"> · {_s(lab['stage'])}: {_s(result.get('stage_label'), 80)}</span>
<p>{_s(result.get('summary'), 900)}</p>
<h2>{_s(lab['found'])}</h2>{findings or '<p class="small">–</p>'}
{f'<h2>{_s(lab["unverified"])}</h2>{unv}' if unv else ''}
<h2>{_s(lab['unchecked'])}</h2><ul>{unchecked}</ul>
<h2>{_s(lab['next'])}</h2><ul>{actions}</ul>
<h2>{_s(lab['helplines'])}</h2><ul>{helplines}</ul>
<h2>{_s(lab['msg'])}</h2><div class="m">{_s(result.get('masked_text'), 1500)}</div>
<p class="small"><b>{_s(lab['keep'])}</b></p>
<p class="small">{_s(lab['note'])}</p>
</body></html>"""
