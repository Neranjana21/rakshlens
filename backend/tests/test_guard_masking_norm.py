import json

import pytest

from app.explain import guard
from app.explain.composer import TEMPLATES, compose
from app.pipeline.masking import mask_account, mask_phone, mask_text, mask_upi
from app.pipeline.normalize import normalize
from app.rules.engine import RULES_BY_ID, analyze_text


# ---- guard ---------------------------------------------------------------
@pytest.mark.parametrize("bad", [
    "You should buy this stock now.",
    "I recommend you sell the shares.",
    "The target price is clearly higher.",
    "This is a great investment.",
    "It will double soon.",
    "இதை வாங்குங்கள்",
    "यह शेयर खरीदें",
])
def test_guard_blocks_advice(bad):
    assert guard.violates(bad)


def test_guard_allows_plain_warning():
    assert guard.is_safe("Do not pay anything until you have checked the sender.", "Do not pay")


def test_guard_blocks_invented_numbers_and_links():
    assert not guard.is_safe("Call 1930 now.", "no numbers here")
    assert guard.is_safe("Call 1930 now.", "helpline 1930")
    assert not guard.is_safe("Visit http://x.example", "nothing")


# ---- templates: every rule explained in every language ---------------------
@pytest.mark.parametrize("lang", sorted(TEMPLATES))
def test_every_rule_has_wording(lang):
    t = TEMPLATES[lang]
    missing = [r for r in list(RULES_BY_ID) + ["COMBO_PROMISE_PLUS_PAYMENT"] if r not in t["rules"]]
    assert not missing, f"{lang} missing {missing}"
    for k in ("sender", "registration", "scope", "links", "verdict"):
        assert t["uncertainty"][k]
    for k in ("stop", "verify", "preserve", "report", "paid", "recovery", "talk", "low_general"):
        assert t["actions"][k]
    assert {"low", "verify", "high", "critical"} == set(t["bands"])


def test_templates_never_contain_advice_language_about_stocks():
    # Templates describe scams; they must not instruct anyone to buy/sell/hold.
    for t in TEMPLATES.values():
        for title, detail in t["rules"].values():
            for text in (title, detail):
                assert not guard._ADVICE_RX[0].search(text) and not guard._ADVICE_RX[1].search(text)


# ---- masking -------------------------------------------------------------
def test_masking_helpers():
    assert mask_phone("+919876543210").endswith("3210") and "98765" not in mask_phone("+919876543210")
    assert mask_upi("trader99@ybl") == "tr***@ybl"
    assert mask_account("123456789012").endswith("9012") and "12345" not in mask_account("123456789012")


def test_no_raw_pii_leaves_the_service():
    msg = "Pay on trader99@ybl or call 9876543210, a/c 123456789012 IFSC HDFC0001234 for the registration fee"
    out = json.dumps(compose(analyze_text(msg), "en"), ensure_ascii=False)
    for raw in ("trader99", "9876543210", "123456789012", "HDFC0001234"):
        assert raw not in out, f"{raw} leaked into the response"


def test_email_is_not_treated_as_upi():
    assert not analyze_text("Contact info@company.in").entities.upi_ids


# ---- normalisation ---------------------------------------------------------
def test_spaced_letters_and_word_gaps():
    n = normalize("G U A R A N T E E D  R E T U R N S")
    assert "guaranteed returns" in n.match and n.changed


def test_zero_width_and_homoglyphs():
    assert "guaranteed" in normalize("Guar​anteed").match
    assert "guaranteed" in normalize("Guаrаnteed").match  # Cyrillic a


def test_native_digits():
    assert "5000" in normalize("₹५०००").match
