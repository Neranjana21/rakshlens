"""Phrase patterns per signal, in English, Hinglish, Hindi and Tamil (+ Tanglish).

Matched against the *normalised* text (lower-case, ASCII digits, spaced-out
letters re-joined). A leading "~" marks a pattern that already encodes a
negative claim ("no loss") and so must not be skipped by negation handling.

These are heuristics written by hand, not a trained model. Extend by adding
lines here - no code changes needed.
"""

GUARANTEED = [
    r"\bguarantee[ds]?",
    r"\b(?:assured|fixed|sure|certain|confirmed|definite)\s+(?:\w+\s+){0,2}(?:profit|return|income|earning|gain)s?\b",
    r"\b(?:profit|returns?|income|gains?)\s+(?:is\s+|are\s+)?(?:assured|guaranteed|fixed|confirmed)\b",
    r"\b(?:allotment|allocation|admission|selection)\s+(?:is\s+)?(?:assured|guaranteed|confirmed)\b",
    r"\b100\s?%\s*(?:allotment|allocation)\b",
    r"\bsure[\s-]?shot\b",
    r"\bpakka\s+(?:milega|milenge|profit|return|munafa|paisa|income)\b",
    r"\b(?:100\s?%|pakka)\s+(?:profit|munafa|safe)\b",
    r"\bjackpot\b",
    r"100\s?%\s*(?:safe|sure|profit|guarantee|accuracy|success|win)",
    r"~\b(?:no|zero)\s+(?:loss|risk)\b",
    r"~\brisk[\s-]?free\b",
    r"~\bloss[\s-]?free\b",
    r"~\bwithout\s+(?:any\s+)?risk\b",
    r"\bpakka\s+(?:profit|munafa|paisa|return|fayda)",
    # Hindi
    r"गारंटी(?:ड)?",
    r"पक्का\s*(?:मिलेगा|मिलेंगे|मुनाफ़ा|मुनाफा|रिटर्न|लाभ)",
    r"पक्का\s*(?:मुनाफ़ा|मुनाफा|लाभ|रिटर्न|फायदा|फ़ायदा)",
    r"(?:अलॉटमेंट|अलॉटमेन्ट|एलॉटमेंट|मुनाफ़ा|मुनाफा|रिटर्न|कमाई|फायदा|फ़ायदा|लाभ)\s*(?:पक्का|पक्की|तय|निश्चित)",
    r"~बिना\s*(?:किसी\s*)?(?:जोखिम|रिस्क)",
    r"~जोखिम\s*(?:मुक्त|रहित)",
    r"~नुकसान\s*(?:नहीं|नही)",
    # Tamil / Tanglish
    r"உறுதி(?:யான)?\s*(?:லாபம்|வருமானம்|வருவாய்|வட்டி)",
    r"உத்தரவாத",
    r"~நஷ்டம்\s*(?:இல்லை|இல்லாத)",
    r"~ரிஸ்க்\s*இல்லை",
    r"\buru?thi(?:yana)?\s+(?:laabam|labam|profit)",
]

DOUBLE_MONEY = [
    r"\b(?:double|triple|2x|3x|5x|10x|10\s?x)\s+(?:your\s+|my\s+|the\s+)?(?:money|investment|capital|amount|paisa|profit|savings?|funds?|wealth)",
    r"\b(?:money|paisa|amount|investment|savings?)\s+(?:will\s+)?(?:double|triple|multiply)",
    r"पैसा\s*दोगुना|दोगुना|दोगुने|दुगना|दुगुना|दुगुने|तिगुना|तिगुने",
    r"இரட்டிப்பு|மூன்று\s*மடங்கு|பல\s*மடங்கு",
]

RATE_UNITS = (
    r"(day|daily|week|weekly|month|monthly|din|roz|rozana|hafte|mahine|mahina|"
    r"प्रतिदिन|रोज़|रोज|रोजाना|प्रति\s*सप्ताह|हर\s*हफ्ते|प्रति\s*माह|हर\s*महीने|महीने|"
    r"தினமும்|தினசரி|வாரம்|வாரந்தோறும்|மாதம்|மாதாந்திர|மாதந்தோறும்)"
)

PROFIT_PROOF = [
    r"\bprofit\s+(?:screenshots?|proofs?|sheets?|reports?)\b",
    r"\b(?:proofs?|screenshots?)\s+of\s+(?:profit|earnings|withdrawals?|gains)\b",
    r"\b(?:see|check|view|watch)\s+(?:our|my|the)\s+(?:profit|results|track\s+record|testimonials)",
    r"\btestimonials?\b",
    r"\b(?:9\d|100)\s?%\s*(?:accuracy|accurate|success|win(?:ning)?\s*rate|strike\s*rate|hit\s*rate)",
    r"\b(?:members?|clients?|students?)\s+(?:earned|made|booked|got)\s+(?:rs\.?|₹)?\s?[\d,]+",
    r"\b(?:today'?s|yesterday'?s|this\s+week'?s)\s+profit\b",
    r"प्रॉफिट\s*(?:प्रूफ|स्क्रीनशॉट)",
    r"லாப\s*(?:ஆதாரம்|ஸ்கிரீன்ஷாட்)",
]

SEBI_CLAIM = [
    r"\bsebi[\s-]*(?:registered|reg\b\.?|approved|certified|authori[sz]ed|licen[cs]ed|regulated|verified|recogni[sz]ed|compliant)",
    r"\b(?:registered|approved|certified|authori[sz]ed)\s+(?:with|by|under)\s+sebi\b",
    r"\bsebi\s+(?:registration|licen[cs]e|certificate|no\b\.?|number)",
    r"\b(?:nse|bse|rbi|amfi|mca|government|govt\.?)\s*[- ]?(?:approved|registered|certified|authori[sz]ed)\b",
    r"सेबी\s*(?:पंजीकृत|रजिस्टर्ड|रजिस्टर|अप्रूव्ड|से\s*मान्यता|द्वारा\s*(?:पंजीकृत|अनुमोदित|मान्यता))",
    r"(?:\bsebi|सेबी)\s*(?:से|द्वारा)\s*(?:मान्य|मान्यता|पंजीकृत|अनुमोदित|प्रमाणित)",
    r"செபி\s*(?:அங்கீகாரம்|அங்கீகரிக்கப்பட்ட|பதிவு\s*செய்யப்பட்ட|பதிவு|ஒப்புதல்)",
]
# If these appear shortly before a SEBI mention it is advice ("check that your adviser is SEBI registered"), not a claim.
ADVICE_BEFORE = (
    r"(?:check|verify|ensure|make\s+sure|confirm|always|look\s+for|only\s+deal|only\s+invest|how\s+to|"
    r"जांच|सुनिश्चित|देखें|सत्यापित|சரிபார்|உறுதி\s*செய்)"
)

INSIDER = [
    r"\binsider(?:s)?\b",
    r"\boperators?\s*[- ]?(?:backed|calls?|tips?|trades?|se\s+baat|group|connection|news|info)",
    r"\boperators?\s+(?:se|ka|ki|ne)\b",
    r"\binside(?:r)?\s+(?:info|information|tip|news|trade|trading|source)",
    r"\bleaked\s+(?:news|info|tip|data|report)",
    r"\bbig\s+(?:players?|operators?|hands|bulls)\b",
    r"\boperators?\s+(?:are|is)\s+(?:buying|selling|entering|accumulating)\b",
    r"\bbulk\s+deal\s+(?:info|tip|news)",
    r"\bpump\s*(?:and|&|n)?\s*dump\b",
    r"\bpump\s+alert\b",
    r"\bwill\s+hit\s+(?:the\s+)?upper\s+circuit\b",
    r"\b(?:everyone|all)\s+(?:should\s+)?buy\s+(?:at|on)\s+open\b",
    r"ऑपरेटर\s*(?:कॉल|टिप|ट्रेड|से)",
    r"इनसाइडर",
    r"अंदर\s*की\s*(?:खबर|जानकारी)",
    r"உள்\s*(?:தகவல்|செய்தி)",
    r"ஆபரேட்டர்",
]

AUTHORITY_IMPERSONATION = [
    r"\b(?:sebi|nse|bse|rbi|cbi|income\s*tax|cyber\s*(?:cell|crime|police)|police|customs|trai|court|narcotics|enforcement|ed)\s+(?:officer|notice|case|warrant|inspector|department|investigation|inquiry)\b",
    r"\b(?:your|account|sim|aadhaar|aadhar|demat)\s+(?:\w+\s+){0,3}(?:will\s+be|is\s+being|has\s+been|are\s+being)\s+(?:blocked|frozen|suspended|seized|cancelled|arrested)",
    r"\b(?:digital|virtual)\s+arrest\b",
    r"\b(?:transfer|move|shift)\s+(?:\w+\s+){0,4}(?:to|into)\s+(?:a\s+|the\s+|our\s+)?(?:safe|secure|protected|escrow|rbi|government)\s+account\b",
    r"\bcompliance\s+officer\b",
    r"गिरफ्तार",
    r"वारंट",
    r"கைது",
    r"வாரண்ட்",
]

KYC_PRESSURE = [
    r"\bkyc\s+(?:\w+\s+){0,3}(?:update|expired?|expiry|pending|verification|incomplete|suspend|block|lapse)",
    r"\b(?:update|complete|verify)\s+(?:your\s+)?kyc\b",
    r"केवाईसी\s*(?:अपडेट|समाप्त|पेंडिंग)",
    r"கேஒய்சி|கே\.ஒய்\.சி",
]

UPFRONT_FEE = [
    r"\b(?:registration|activation|joining|join|membership|subscription|enrol+ment|processing|verification|account\s+opening|demat\s+opening|security|refundable)\s+(?:fees?|charges?|deposit|amount)\b",
    r"\bpay\s+(?:rs\.?\s?|₹\s?)?[\d,]+\s+(?:to|for)\s+(?:join|activate|start|unlock|enter|register|get\s+access)",
    r"\b(?:fees?|deposit|amount)\s+(?:to|for)\s+(?:join|activate|unlock|get\s+access)",
    r"\b(?:registration|joining|activation|membership)\s*(?:of|:|-|@)?\s*(?:rs\.?|₹)\s?\d",
    r"\bpay\s+(?:rs\.?\s?|₹\s?)?[\d,]+\s+(?:as\s+)?(?:advance|upfront|in\s+advance|first|initially)\b",
    r"\badvance\s+(?:payment|fee|amount|deposit)\b",
    # "Join premium group for Rs 2999": paying to get into a tips group, channel or course
    # (line breaks allowed: text read from a screenshot wraps in the middle of a sentence)
    r"\b(?:join|enter|access)\b[^.!?]{0,40}\b(?:group|channel|club|community|tips|calls|course|webinar|membership)\b[^.!?]{0,30}\bfor\s+(?:rs\.?\s?|₹\s?)[\d,]{3,}",
    # "pay 5000 fee": an amount straight before the word fee/charges (also how speech-to-text writes it)
    r"\b(?:pay|send|transfer|deposit)\s+(?:rs\.?\s?|₹\s?)?[\d,]{3,}\s+(?:fees?|charges?)\b",
    r"\b(?:send|transfer|deposit|pay)\s+(?:rs\.?\s?|₹\s?)[\d,]+\s+(?:as\s+)?(?:initial|starting|seed)\s+(?:capital|investment|amount|deposit)\b",
    r"\b(?:deposit|pay|send|transfer)\s+(?:rs\.?\s?|₹\s?)?[\d,]{3,}\s+(?:now|today|immediately|to\s+(?:confirm|book|secure|reserve|start|join|activate|unlock|get))\b",
    # Hinglish: "pehle 999 bharo", "999 rupaye bhejo"
    r"\b(?:pehle|pahle|abhi|aaj)\s+(?:rs\.?\s?|₹\s?)?[\d,]{3,}\s*(?:rs|rupaye|rupay|rupees)?\s*(?:bharo|bhejo|bhej\s+do|do\b|dena|jama\s*karo|transfer\s*karo)",
    r"\b(?:rs\.?\s?|₹\s?)?[\d,]{3,}\s*(?:rs|rupaye|rupay|rupees)\s*(?:bharo|bhejo|bhej\s+do|jama\s*karo|transfer\s*karo)\b",
    r"(?:रजिस्ट्रेशन|जॉइनिंग|जोइनिंग|सदस्यता|एक्टिवेशन|प्रोसेसिंग)\s*(?:फीस|फ़ीस|शुल्क|चार्ज)",
    r"शुल्क\s*जमा",
    # Hindi: "3000 रुपये भेजें / जमा करें"
    r"[\d,]{3,}\s*(?:रुपये|रुपए|रुपया|रू\.?|₹)\s*(?:अभी\s*|आज\s*ही\s*)?(?:भेजें|भेजिए|भेजो|जमा\s*करें|जमा\s*कीजिए|जमा\s*करो|भरें|ट्रांसफर\s*करें)",
    r"(?:பதிவு|சேர்க்கை|உறுப்பினர்|செயல்படுத்தும்)\s*கட்டணம்",
    r"கட்டணம்\s*செலுத்த",
    # Tamil: "5000 ரூபாய் செலுத்துங்கள் / அனுப்புங்கள்"
    r"[\d,]{3,}\s*(?:ரூபாய்|ரூ\.?)\s*(?:இன்றே\s*|உடனே\s*)?(?:செலுத்து|அனுப்பு|கட்டு|டெபாசிட்)",
]

WITHDRAWAL_FEE = [
    r"\b(?:withdraw(?:al)?|release|unfreeze|unlock)\s+(?:\w+\s+){0,3}(?:fees?|charges?|tax|gst|deposit|commission)\b",
    r"\b(?:pay|deposit)\s+(?:\w+\s+){0,3}(?:tax|gst|fees?|charges?)\s+(?:\w+\s+){0,3}(?:to\s+)?(?:withdraw|release|receive\s+(?:your\s+)?(?:profit|money|funds))",
    # Same demand in the other word order: "To withdraw, pay 10% tax ...", "before you can withdraw you must pay a fee".
    r"\b(?:to|for|before)\s+(?:you\s+(?:can\s+)?)?(?:withdraw(?:al|ing)?|releas(?:e|ing)|receiv(?:e|ing)|unlock(?:ing)?)\b[^.!?\n]{0,50}\b(?:pay|deposit|send|transfer|clear)\b[^.!?\n]{0,40}\b(?:tax|gst|fees?|charges?|commission|penalty)\b",
    r"निकासी\s*(?:शुल्क|फीस|कर)",
    r"पैसे\s*निकालने\s*के\s*लिए\s*(?:टैक्स|शुल्क|फीस)",
    r"பணம்\s*எடுக்க\s*(?:வரி|கட்டணம்)",
]

# "Your funds are frozen/blocked" is a withdrawal scam only when it is not a normal IPO/ASBA/application hold
# and/or a fee is demanded. Used by payment.detect_withdrawal_fee, not as a standalone phrase.
FUNDS_HELD = r"\b(?:profit|funds|amount|balance|account)\s+(?:is\s+|are\s+|has\s+been\s+|will\s+be\s+)?(?:frozen|locked|held|blocked)\b"
FUNDS_HELD_LEGIT_CONTEXT = (
    r"\b(?:asba|ipo|application|allotment|mandate|bid|bidding|unblocked?|refund(?:ed)?|"
    r"will\s+be\s+(?:released|unblocked|debited)|registrar)\b"
)
FEE_DEMAND = (
    r"\b(?:pay|deposit|send|transfer|clear)\b[^.!?\n]{0,60}\b(?:tax|gst|fees?|charges?|commission|penalty)\b"
    r"|\b(?:tax|gst|fees?|charges?|penalty)\b[^.!?\n]{0,40}\b(?:to|for)\s+(?:withdraw|release|unfreeze|unlock|clear)"
)

RECOVERY = [
    r"\b(?:recover(?:y)?|get\s+back|return|refund)\s+(?:of\s+)?(?:your\s+)?(?:lost\s+|stolen\s+|stuck\s+|fraud(?:ed)?\s+)?(?:money|funds|amount|investment|loss(?:es)?)\b",
    r"\b(?:fund|money|loss|fraud|scam)\s+recovery\s+(?:agent|team|service|expert|cell|officer|department)",
    r"\brecovery\s+(?:agent|agency|expert|team|charges?|fees?)\b",
    r"पैसे\s*वापस",
    r"रिकवरी",
    r"रकम\s*वापस",
    r"பணத்தை\s*(?:திரும்ப|மீட்டு)",
    r"பணம்\s*மீட்பு",
]

PRIVATE_CHANNEL = [
    r"\bt\.me/[a-z0-9_+]+",
    r"\btelegram\.me/",
    r"\bwa\.me/\d+",
    r"\bchat\.whatsapp\.com/",
    r"\bwhatsapp\s+group\b",
    r"\b(?:join|contact|message|dm|text|ping|reach)\s+(?:\w+\s+){0,3}(?:on\s+|via\s+)?(?:telegram|whatsapp|signal)\b",
    r"\b(?:contact|message|dm)\s+(?:our\s+|my\s+|the\s+)?(?:manager|admin|assistant|advisor|expert|mentor|analyst|sir|madam)\b",
    r"\b(?:tips?|calls?|signals?|updates?|ideas?)\s+(?:on|via|in|at|through)\s+(?:telegram|whatsapp)\b",
    r"\b(?:message|text|send|type)\s+['\"]?(?:join|vip|start|hi)['\"]?\s+(?:to|on|at)\b",
    r"\bdm\s+me\b",
    r"\binbox\s+me\b",
    r"\btelegram\s+(?:channel|group|id|handle)\b",
    r"टेलीग्राम",
    r"व्हाट्सएप\s*ग्रुप|व्हाट्सऐप",
    r"டெலிகிராம்",
    r"வாட்ஸ்அப்\s*குழு|வாட்ஸ்ஆப்",
]

CREDENTIAL_REQUEST = [
    r"\b(?:share|send|give|tell|provide|enter|submit|forward|read\s+out|batao|bhejo|bata\s+do)\s+(?:\w+\s+){0,3}(?:otp|one[\s-]?time\s+password|pin|password|cvv|upi\s+pin|mpin|aadhaar|aadhar|pan\s+card|pan\s+number|net\s*banking|login|card\s+number|demat\s+(?:login|password))\b",
    r"\b(?:otp|pin|cvv|password)\s+(?:bhejo|batao|share\s+karo|send\s+karo)\b",
    r"\b(?:tell|read|say|give|share|send)\s+(?:me\s+|us\s+)?(?:the\s+|your\s+)?(?:\d+[\s-]?digit|verification|security|confirmation)\s+(?:code|number|pin)\b",
    r"(?:otp|ओटीपी)\s*(?:भेजें|बताएं|बताइए|शेयर|दें)",
    r"(?:ஓடிபி|otp)\s*(?:பகிர|சொல்|அனுப்ப|sollunga|anuppunga)",
    r"கடவுச்சொல்",
]

REMOTE_ACCESS = [
    r"\b(?:anydesk|any\s*desk|teamviewer|team\s*viewer|quick\s*support|quicksupport|rustdesk|airdroid|ammyy|ultraviewer|supremo)\b",
    r"\bscreen\s*(?:share|sharing|mirror)\b",
    r"\bremote\s*(?:access|control|support)\b",
    r"स्क्रीन\s*शेयर",
    r"திரை\s*பகிர்|ஸ்கிரீன்\s*ஷேர்",
]

APP_DOWNLOAD = [
    r"\.apk\b",
    r"\bapk\b[^.!?\n]{0,30}\b(?:download|install)",
    r"\b(?:download|install)\b[^.!?\n]{0,30}\bapk\b",
    r"\b(?:download|install|get)\s+(?:\w+\s+){0,3}(?:apk|app|application)\b",
    r"\b(?:app|apk)\s+(?:link|download)\b",
    r"डाउनलोड\s*(?:करें|ऐप)",
    r"ஆப்?\s*டவுன்லோட்|பதிவிறக்க",
]

URGENCY = [
    r"\b(?:limited|only\s+\d+|few|last)\s+(?:seats?|slots?|spots?|places?|vacanc(?:y|ies)|members?|chance|time|offer|quota|stock)\b",
    r"\b(?:hurry(?:\s+up)?|act\s+now|today\s+only|only\s+today|last\s+(?:day|date|chance)|offer\s+(?:ends|expires|valid)|expires?\s+(?:today|tonight|soon|in)|(?:closes?|ends?)\s+(?:today|tonight|soon|tomorrow)|register\s+now|join\s+now|(?:within|in)\s+\d+\s*(?:hours?|hrs?|minutes?|mins?)|don'?t\s+miss|dont\s+miss|miss\s+(?:out|this)|before\s+it'?s\s+too\s+late)\b",
    r"\burgent(?:ly)?\b",
    r"आज\s*ही",
    r"जल्दी",
    r"सीमित\s*(?:सीट|स्थान)",
    r"अंतिम\s*(?:मौका|तारीख)",
    r"இன்றே",
    r"உடனே",
    r"கடைசி\s*வாய்ப்பு",
    r"குறைந்த\s*(?:இடங்கள்|இடம்)",
]

EXCLUSIVITY = [
    r"\b(?:vip|premium|exclusive|elite|invite[\s-]?only|selected\s+(?:members|few|people)|special\s+(?:offer|group|access)|private\s+(?:group|channel|club)|paid\s+(?:group|channel|calls?|tips?))\b",
    r"वीआईपी|प्रीमियम",
    r"விஐபி|பிரீமியம்",
]

TARGET_CALL = [
    r"\b(?:target|tgt|tp)\s*[:\-=]?\s*(?:rs\.?|₹)?\s*\d{2,6}\b",
    r"\b(?:stop\s*loss|sl)\s*[:\-=]?\s*(?:rs\.?|₹)?\s*\d{2,6}\b",
    r"\bbuy\s+(?:above|at|near|below|on\s+dip)\b",
    r"\bsell\s+(?:below|at|near|above)\b",
    r"\b(?:entry|exit)\s*[:\-=]?\s*(?:rs\.?|₹)?\s*\d{2,6}\b",
    r"टारगेट\s*[:\-]?\s*\d+",
    r"இலக்கு\s*[:\-]?\s*\d+",
]

# Context markers
AWARENESS = [
    r"\b(?:beware|be\s+careful|be\s+aware|fraud\s+alert|scam\s+alert|investor\s+(?:alert|awareness|education|advisory)|do\s+not\s+fall\s+for|don'?t\s+fall\s+for|stay\s+safe|protect\s+yourself|warning\s+signs?|red\s+flags?|how\s+to\s+(?:spot|identify|avoid))\b",
    r"सावधान|सतर्क|जागरूक",
    r"எச்சரிக்கை|ஜாக்கிரதை|விழிப்புணர்வு",
]
RISK_DISCLAIMER = [
    r"subject\s+to\s+market\s+risks?",
    r"read\s+all\s+(?:scheme|offer)\s+related\s+documents",
    r"past\s+performance\s+(?:is\s+)?not",
    r"not\s+an?\s+(?:investment\s+)?(?:advice|recommendation)",
    r"for\s+(?:educational|information(?:al)?)\s+purposes?\s+only",
]

SHORTENERS = {
    "bit.ly", "tinyurl.com", "cutt.ly", "rb.gy", "t.ly", "is.gd", "shorturl.at", "goo.gl",
    "ow.ly", "rebrand.ly", "tiny.cc", "s.id", "v.gd", "lnkd.in", "bl.ink",
}
RISKY_TLDS = {"xyz", "top", "live", "vip", "club", "click", "site", "online", "icu", "buzz", "shop", "fun", "ink"}
STORE_DOMAINS = {"play.google.com", "apps.apple.com", "itunes.apple.com"}

# "avoid anything that promises guaranteed returns" is advice, not a claim.
AVOID_BEFORE = (
    r"(?:\b(?:avoid|beware\s+of|stay\s+away\s+from|never\s+trust|do\s*n[o']t\s+trust)\s+(?:\w+\s+){0,4}"
    r"|\b(?:anything|anyone|those|people|schemes?|ads?|messages?|offers?)\s+(?:that\s+|who\s+|which\s+)?"
    r"(?:promises?|promising|claims?|claiming|offers?|offering|says?|saying)\s+(?:\w+\s+){0,1})$"
)


# Ponzi / chain-recruitment: pay-to-join schemes that pay "bonus" for bringing others.
REFERRAL_SCHEME = [
    r"\b(?:refer|add|invite|bring|get)\s+(?:\d+|two|three|four|five|six|ten)\s+(?:more\s+)?(?:friends?|members?|people|persons?|contacts?)\b",
    r"\b(?:refer\s*(?:and|&|n)\s*earn|referral\s+(?:bonus|income|commission)|team\s+(?:bonus|income)|level\s+income|downline|multi[\s-]?level|chain\s+(?:system|scheme))\b",
    r"\b\d+\s*(?:log|logo|dost|doston|members?)\s+(?:ko\s+)?(?:judo|jodo|jodna|add|refer)\w*",
    r"\b(?:judo|jodo|jodna|refer|add|invite)\b[^.!?\n]{0,30}\bbonus\b",
    r"(?:दोस्तों|लोगों|मित्रों)\s*को\s*जोड़",
    r"रेफरल\s*(?:बोनस|इनकम)?",
    r"நண்பர்களை\s*(?:சேர்|இணை)",
    r"ரெ(?:ஃ|ப)ரல்",
]


# Money-mule recruitment: asking you to lend your account or forward money for a commission.
MULE_ACCOUNT = [
    r"\b(?:rent|lease|lend|hire)\s+(?:out\s+)?(?:your|ur)\s+(?:bank\s+|savings\s+|current\s+)?(?:account|a/c|upi)\b",
    r"\buse\s+your\s+(?:bank\s+)?(?:account|a/c)\s+(?:to|for)\s+(?:receive|receiving|transfer|transferring|collect)",
    r"\b(?:receive|collect)\s+(?:money|payments?|funds?)\s+(?:in|into|on)\s+your\s+(?:bank\s+)?account\b[^.!?\n]{0,60}\b(?:forward|transfer|send|pass)",
    r"\bcommission\s+(?:for|on)\s+(?:each|every)\s+(?:transfer|transaction|payment)",
    r"\b(?:forward|transfer)\s+(?:the\s+)?(?:money|amount|funds?)\b[^.!?\n]{0,40}\bkeep\s+\d+\s*%",
    r"\b(?:khata|account)\s+(?:kiraye|kiraya|rent)\s+(?:pe|par|per)\b",
    r"अपना\s*(?:बैंक\s*)?खाता\s*(?:किराये|किराए|रेंट)",
    r"உங்கள்\s*(?:வங்கி\s*)?கணக்கை\s*(?:வாடகைக்கு|கொடுத்து)",
]
