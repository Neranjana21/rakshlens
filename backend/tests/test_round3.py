"""Regression tests for gaps found with the persona messages (Praveen, Kavita, Babulal).

Each case is a *kind* of message, not one sentence: the fixes are general patterns.
"""
import pytest

from app.rules.engine import analyze_text


def band(text: str) -> str:
    return analyze_text(text).band


def ids(text: str) -> set[str]:
    return {f.id for f in analyze_text(text).findings}


# --- false alarm: a normal IPO application holds funds under ASBA -------------------------------
@pytest.mark.parametrize(
    "text",
    [
        "Your IPO application for XYZ Ltd has been received. Allotment status will be available on the registrar website on 12-Oct. Funds are blocked in your bank account under ASBA.",
        "IPO allotment status: funds blocked under ASBA will be unblocked on 12-Oct if you are not allotted.",
    ],
)
def test_genuine_ipo_hold_is_not_a_withdrawal_scam(text):
    assert "WITHDRAWAL_BLOCKED_FEE" not in ids(text)
    assert band(text) == "low"


@pytest.mark.parametrize(
    "text",
    [
        "Your funds are frozen. Contact our manager on Telegram to unfreeze.",
        "IPO funds are blocked. Pay Rs 5000 tax to release your money.",
    ],
)
def test_blocked_funds_with_a_demand_still_flagged(text):
    assert "WITHDRAWAL_BLOCKED_FEE" in ids(text)
    assert band(text) in ("high", "critical")


# --- "pay a fee to withdraw", either word order -------------------------------------------------
@pytest.mark.parametrize(
    "text",
    [
        "Your trading balance is ready. To withdraw, pay 10% tax Rs 18,500 to account 5678901234.",
        "Before you can withdraw you must pay a service fee of Rs 3000.",
        "Pay tax of Rs 4000 to withdraw your profit.",
    ],
)
def test_pay_to_withdraw_both_orders(text):
    assert "WITHDRAWAL_BLOCKED_FEE" in ids(text)


def test_free_withdrawal_message_is_not_flagged():
    assert band("Withdrawals are free of charge. To withdraw, open the app and tap Withdraw.") == "low"


# --- upfront payment wording --------------------------------------------------------------------
def test_join_fee_with_guaranteed_returns_is_high_or_critical():
    assert band("Join fee 999. Guaranteed returns.") in ("high", "critical")


@pytest.mark.parametrize(
    "text",
    [
        "Deposit 5000 to activate your trading account",
        "Daily profit 5000 pakka, pehle 999 bharo",
    ],
)
def test_pay_first_without_rupee_symbol_is_noticed(text):
    assert "UPFRONT_FEE" in ids(text)


# --- Hindi / Tamil -----------------------------------------------------------------------------
def test_hindi_ipo_double_money_scam():
    text = "शानदार मौका! नए IPO में अलॉटमेंट पक्का। आज ही 3000 रुपये भेजें और 2 दिन में पैसे दोगुने पाएं।"
    found = ids(text)
    assert {"GUARANTEED_RETURNS", "UPFRONT_FEE", "UNREALISTIC_RETURN_RATE"} <= found
    assert band(text) in ("high", "critical")


def test_tamil_pay_now_and_double():
    text = "பெண்களுக்கான சிறப்பு முதலீடு! பணம் இரட்டிப்பு. இன்றே 5000 ரூபாய் செலுத்துங்கள்."
    assert "UPFRONT_FEE" in ids(text) and band(text) in ("high", "critical")


@pytest.mark.parametrize(
    "text",
    [
        "आपका SIP 5000 रुपये आज कट गया है। म्यूचुअल फंड निवेश बाज़ार जोखिमों के अधीन हैं।",
        "पक्का मकान बनवाने के लिए होम लोन 8.5% ब्याज पर उपलब्ध। नियम व शर्तें लागू।",
        "Deposit 5000 to your own savings account at any SBI branch. No fee.",
    ],
)
def test_ordinary_messages_stay_low(text):
    assert band(text) == "low"


# --- OCR: a SEBI number whose zeros were read as the letter O is still a number --------------------
def test_ocr_misread_sebi_number_is_still_found():
    a = analyze_text("Rakesh Sharma, SEBI registered research analyst (INHO00012345). Join our channel.")
    assert [n.raw for n in a.entities.sebi_numbers] == ["INH000012345"]
    found = {f.id for f in a.findings}
    assert "SEBI_NUMBER_UNVERIFIED" in found and "SEBI_CLAIM_NO_NUMBER" not in found


def test_ordinary_words_are_not_read_as_sebi_numbers():
    a = analyze_text("INDIA OILLOILLO INFLATION data INBOOLLIIL is not a number. Interest rates stay.")
    assert a.entities.sebi_numbers == []


# --- phone / speech-to-text wording: no symbols, numbers spelt as words -----------------------------
def test_spoken_percent_and_fee_wording_is_noticed():
    text = "Guaranteed 30 percent returns, pay 5000 fee to ravi at okaxis"
    assert {"GUARANTEED_RETURNS", "UPFRONT_FEE"} <= ids(text)
    assert band(text) in ("high", "critical")


def test_percent_word_is_read_as_a_rate():
    assert "UNREALISTIC_RETURN_RATE" in ids("earn 40 percent every month, join now")


def test_body_less_post_is_accepted_but_chunked_upload_is_not():
    from fastapi.testclient import TestClient

    from app.api import middleware
    from app.main import app

    middleware._hits.clear()
    c = TestClient(app)
    # A phone provider's webhook or `curl -X POST` may send no Content-Length at all.
    assert c.post("/api/ivr/start").status_code == 200
    # A chunked body has no declared size and must be refused.
    r = c.post("/api/analyze", content=iter([b"abc", b"def"]), headers={"content-type": "multipart/form-data; boundary=x"})
    assert r.status_code == 411


# --- pay-to-join wording, and a UPI id that OCR cut short ---------------------------------------
@pytest.mark.parametrize(
    "text",
    [
        "Join premium group for Rs 2999 UPI 9876543210.",
        "Join our VIP tips channel for \u20b9999 today",
        "Enter the trading club for Rs 5,000 only",
    ],
)
def test_pay_to_join_a_group_counts_as_an_upfront_fee(text):
    assert "UPFRONT_FEE" in ids(text)


def test_screenshot_of_a_tips_post_stays_high_even_if_ocr_drops_the_upi_suffix():
    text = ("Telegram VIP F&O calls: Nifty 24500 CE buy today, target 180, stoploss 90. 90% accuracy. "
            "Last month members made 4 lakh from 20k capital. Join premium group for Rs 2999 UPI 9876543210.")
    assert band(text) in ("high", "critical")


@pytest.mark.parametrize(
    "text",
    [
        "Join our free webinar on saving tax. Register on the official website, no fee.",
        "You can join the group chat for the school picnic. Rs 200 per child is collected by the teacher.",
        "Subscribe to the news app for Rs 199 a month",
    ],
)
def test_ordinary_join_or_subscribe_messages_are_not_flagged_as_upfront_fee(text):
    assert "UPFRONT_FEE" not in ids(text)


def test_pay_to_join_survives_line_wrapping_from_a_screenshot():
    wrapped = "Last month members made 4\nlakh from 20k capital. Join premium\ngroup for Rs 2999 UPI 9876543210."
    assert "UPFRONT_FEE" in ids(wrapped)
