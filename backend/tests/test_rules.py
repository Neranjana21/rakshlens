"""One positive and one negative example per rule, so each signal is tested alone."""
import pytest

from app.rules.engine import RULES_BY_ID, analyze_text

POSITIVE = {
    "GUARANTEED_RETURNS": "We give guaranteed profit every week.",
    "UNREALISTIC_RETURN_RATE": "Earn 20% monthly returns with us.",
    "PROFIT_PROOF": "See our profit screenshots in the group.",
    "SEBI_CLAIM_NO_NUMBER": "We are SEBI registered advisers.",
    "SEBI_NUMBER_UNVERIFIED": "Our registration no INH000012345.",
    "SEBI_NUMBER_BAD_FORMAT": "SEBI reg no INH12345.",
    "INSIDER_OR_OPERATOR_CLAIM": "We have insider information on this stock.",
    "AUTHORITY_IMPERSONATION": "This is a SEBI officer. Your account will be frozen.",
    "KYC_PRESSURE": "Your KYC is expired, update your KYC now.",
    "UPFRONT_FEE": "Pay the registration fee to join.",
    "WITHDRAWAL_BLOCKED_FEE": "Pay withdrawal charges to receive your funds.",
    "PERSONAL_PAYEE": "Send the amount to trader99@ybl today.",
    "PRIVATE_CHANNEL_MOVE": "Join our Telegram: t.me/vipchannel",
    "CREDENTIAL_REQUEST": "Please share your OTP with me.",
    "REMOTE_ACCESS_TOOL": "Install AnyDesk so I can help.",
    "APK_OR_SIDELOAD": "Download the app from http://trade-now.xyz/app.apk",
    "LOOKALIKE_DOMAIN": "Login at http://zerodha-support.com now.",
    "IP_ADDRESS_LINK": "Open http://192.168.4.20/login to start.",
    "SHORTENED_LINK": "Details here: bit.ly/abc123",
    "RISKY_LINK_ENDING": "Visit http://best-stock-ideas.xyz for ideas.",
    "URGENCY": "Hurry, only 5 seats left, join now!",
    "EXCLUSIVITY_VIP": "Our VIP premium group is invite only.",
    "REFERRAL_SCHEME": "Add 5 friends to the group and get a referral bonus.",
    "MULE_ACCOUNT_REQUEST": "Rent your bank account to us and earn commission on every transfer.",
    "TARGET_PRICE_CALL": "Buy above 100, target 130, stoploss 90.",
    "RECOVERY_SCAM": "We are recovery agents and will get back your lost money.",
}
NEGATIVE = {
    "GUARANTEED_RETURNS": "Returns are not guaranteed.",
    "UNREALISTIC_RETURN_RATE": "This fund returned 12% per year over a decade.",
    "PROFIT_PROOF": "Here is our fee schedule.",
    "SEBI_CLAIM_NO_NUMBER": "Always check that your adviser is SEBI registered.",
    "SEBI_NUMBER_UNVERIFIED": "Call me tomorrow.",
    "SEBI_NUMBER_BAD_FORMAT": "Call me tomorrow.",
    "INSIDER_OR_OPERATOR_CLAIM": "The telecom operator changed my plan.",
    "AUTHORITY_IMPERSONATION": "The police station is near the market.",
    "KYC_PRESSURE": "KYC is a regulatory requirement.",
    "UPFRONT_FEE": "There is no registration fee.",
    "WITHDRAWAL_BLOCKED_FEE": "Withdrawals are free of charge.",
    "PERSONAL_PAYEE": "Contact me at info@company.in",
    "PRIVATE_CHANNEL_MOVE": "See you at lunch.",
    "CREDENTIAL_REQUEST": "Never share your OTP with anyone.",
    "REMOTE_ACCESS_TOOL": "We never ask you to share your screen.",
    "APK_OR_SIDELOAD": "Download the app from https://play.google.com/store/apps/details?id=x",
    "LOOKALIKE_DOMAIN": "Login at https://zerodha.com now.",
    "IP_ADDRESS_LINK": "Visit https://example.org",
    "SHORTENED_LINK": "Visit https://www.sebi.gov.in",
    "RISKY_LINK_ENDING": "Visit https://www.sebi.gov.in",
    "URGENCY": "The meeting is on Monday.",
    "EXCLUSIVITY_VIP": "Lunch is at one.",
    "REFERRAL_SCHEME": "Please refer to the offer document before investing.",
    "MULE_ACCOUNT_REQUEST": "I rent a flat near my office and pay by bank transfer.",
    "TARGET_PRICE_CALL": "My target for the year is to save more.",
    "RECOVERY_SCAM": "I want a refund of the cinema tickets.",
}


def test_every_rule_has_examples():
    assert set(POSITIVE) == set(NEGATIVE) == set(RULES_BY_ID) - set()


@pytest.mark.parametrize("rule_id", sorted(POSITIVE))
def test_positive(rule_id):
    ids = {f.id for f in analyze_text(POSITIVE[rule_id]).findings}
    assert rule_id in ids, f"{rule_id} did not fire on {POSITIVE[rule_id]!r}; got {ids}"


@pytest.mark.parametrize("rule_id", sorted(NEGATIVE))
def test_negative(rule_id):
    ids = {f.id for f in analyze_text(NEGATIVE[rule_id]).findings}
    assert rule_id not in ids, f"{rule_id} fired on {NEGATIVE[rule_id]!r}"


def test_band_forcing():
    assert analyze_text("Please share your OTP with me now").band in ("high", "critical")
    assert analyze_text("We are SEBI registered").band == "verify"


def test_combo_is_explained():
    ids = {f.id for f in analyze_text("Guaranteed profit. Pay the registration fee.").findings}
    assert "COMBO_PROMISE_PLUS_PAYMENT" in ids


def test_score_is_capped_and_deterministic():
    msg = "Guaranteed profit 50% monthly, registration fee, share OTP, AnyDesk, t.me/x, hurry only 3 seats"
    a, b = analyze_text(msg), analyze_text(msg)
    assert a.score == b.score == 100 and a.band == "critical"


def test_no_findings_is_low_and_says_not_safe():
    a = analyze_text("Are we meeting for lunch tomorrow at one?")
    assert a.band == "low" and not a.findings


def test_kyc_confirmation_is_not_pressure():
    assert "KYC_PRESSURE" not in {f.id for f in analyze_text("Your KYC has been successfully updated. Thank you.").findings}
    assert "KYC_PRESSURE" in {f.id for f in analyze_text("Your KYC is pending, update it today or the account is blocked.").findings}


def test_safe_account_transfer_is_flagged():
    assert analyze_text("You must transfer your holdings to a safe account for verification.").band in ("high", "critical")


def test_hinglish_operator_apk_anydesk_is_critical():
    a = analyze_text("Operator se pakka tip mila hai, kal stock 40% upar jayega. Is APK ko download karo aur AnyDesk install karke screen share karo. Aaj hi ₹10000 UPI karo rohit.trade@okaxis par.")
    ids = {f.id for f in a.findings}
    assert {"APK_OR_SIDELOAD", "REMOTE_ACCESS_TOOL", "INSIDER_OR_OPERATOR_CLAIM"} <= ids
    assert a.band == "critical"


def test_store_app_mention_stays_low():
    assert analyze_text("Download the Zerodha Kite app from the Play Store to track your portfolio.").band == "low"


@pytest.mark.parametrize("text,band", [
    ("Hamare scheme me 10000 jama karo, har mahine 15% pakka milega, paisa double 6 mahine me. Group me 5 log judo to bonus.", {"high", "critical"}),
    ("बड़ी कंपनी का Pre-IPO शेयर सिर्फ ₹120 में, लिस्टिंग पर ₹400 पक्का मिलेगा। SEBI से मान्य। सिर्फ 50 सीटें बची हैं, आज ही ₹25000 खाता 123456789012 में भेजें। 5 दोस्तों को जोड़ो तो बोनस।", {"high", "critical"}),
    ("Telegram VIP F&O calls: Nifty 24500 CE buy today, target 180, stoploss 90. 90% accuracy. Join premium group for Rs 2999 UPI 9876543210@ybl.", {"high", "critical"}),
])
def test_persona_messages(text, band):
    assert analyze_text(text).band in band
