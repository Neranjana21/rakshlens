# Small user study: "Does RakshaLens help people judge a message?"

Purpose: give the "Resilience & Safety impact" criterion some real evidence. This is a small, informal test, so report it as such (n = number of people), never as a statistically proven result.

## Who
5 to 10 people who are not on your team: family, neighbours, classmates' parents. Ideally include people who prefer Tamil or Hindi and at least two who are over 45. Get their consent. Do not record names; use P1, P2, ...

## What
Use 6 messages: 4 scams and 2 legitimate. Take them from the sample screenshots in `web/samples/` (the same ones as the app's "Try a sample screenshot" list; include a Tamil or Hindi one for people who prefer those languages). For the legitimate ones use the genuine samples (`babulal-genuine-reminder`, `hindi-genuine-sip-reminder`, `tamil-genuine-bank-credit`) or a real bank alert you write yourself. Show the first message on paper or on a phone before they use the app. Shuffle the order.

## Steps (about 10 minutes per person)
1. Show message 1 on paper or a phone. Ask: "Is this a scam, safe, or not sure?" and "How sure are you, 1 to 5?" Write both down (**before**).
2. Let them paste or upload it into RakshaLens in their preferred language. Read the result with them silently; do not explain.
3. Ask the same two questions again (**after**), plus: "Would you pay or share an OTP?" (yes/no).
4. Repeat for all 6 messages.
5. At the end ask: "Was the language easy? Which part helped most? What confused you?"

## Record
Create `study/responses.csv` with this header line, then add one row per person per message:

`participant,language,message_id,truth,before_judgement,before_confidence,before_would_pay,after_judgement,after_confidence,after_would_pay,comment`

## Summarise
`python scripts/study_summary.py study/responses.csv` prints: share of correct judgments before vs after, share who would have paid/shared before vs after, average confidence, and how many "not sure" became correct. Put these numbers and n on a slide, with the limits: small sample, same people see before and after, scams are synthetic.

## Honest limits to state
Small n; participants may be more careful because they are being observed; messages are synthetic; this measures judgement in a test, not real-world losses avoided.
