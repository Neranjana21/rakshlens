# Evaluation (read this before quoting any number)

RakshaLens is a rules engine, so every verdict can be traced to a named signal. That makes it explainable, but its coverage is only as good as its rules. These are the measured results, including the misses.

## Method
Four labelled sets of synthetic messages written by the team (in `backend/tests/data/`). Each case lists the bands that are acceptable. "Scam flagged" = High or Critical. "Safe kept Low" = Low.

| Set | Size | Role |
|---|---|---|
| devset | 26 | Written alongside the rules. Tuned against. Optimistic by construction. |
| evasion | 13 | Obfuscation, awareness posts, no-keyword pitches. Run once untuned, then rules were fixed. |
| holdout | 22 | Written after the rules, run untuned. |
| holdout2 | 20 | A second fresh set, run untuned. |

## First-run results (before any fix for that set)
| Set | In expected band | Scams flagged | Safe kept Low |
|---|---|---|---|
| devset | 24/26 | 10/12 | 9/9 |
| evasion | 10/13 | 6/7 | 3/4 |
| holdout | 17/22 | 4/7 | 9/10 |
| holdout2 | 15/20 | 4/8 | 9/10 |

**The honest headline: on messages the rules had never seen, roughly half of the scam messages were caught as High/Critical on the first run, and about nine in ten safe messages were kept Low.** Raw logs: `docs/evidence/`.

## After fixes
Every miss was then fixed with a *general* pattern (not a copy of the test sentence), and all four sets now pass (26/26, 13/13, 22/22, 20/20; pytest: 256 tests). **These post-fix numbers are contaminated: the sets were used to find the bugs, so they do not estimate performance on new messages.** Expect the first-run figures to be closer to reality, and to improve only as more real-world messages are added to the rules.

Later additions (also contaminated): a referral/chain-recruitment rule and Hindi/Hinglish patterns, added after three persona test messages exposed gaps; they are covered by regression tests, not by an unseen set.

## Round 3: persona messages and a fresh set (measured later)
Fifteen messages written for the three personas (Praveen, Kavita, Babulal) found three real gaps on the first run: 10/12 scams flagged High/Critical, but also **one false alarm**, where a genuine IPO status message ("funds are blocked under ASBA") was rated High. All three were fixed with general patterns (fee demands in either word order, an IPO/ASBA hold no longer counts on its own, Hindi/Tamil/Hinglish pay-first wording). Those messages are now regression tests (`tests/test_round3.py`), so their post-fix result (12/12, 3/3) is **contaminated**.

Then 22 new messages (11 scams, 11 genuine) were run once, with no tuning afterwards:

| Set | Scams flagged High/Critical | Genuine kept Low |
|---|---|---|
| fresh set, first run | **4/11** | **11/11** |

Missed: a fake SEBI enforcement notice ("avoid arrest"), a "release your unclaimed dividend, pay stamp duty" message, a Hindi "your demat account will close, enter PAN on this link" message, a Tamil recovery-agent message, a deepfake-finfluencer pitch, a Hinglish grey-market IPO message, and a fake "SEBI registered" adviser promising "assured" 30% a month. Four of the seven scored Low and three scored Needs verification.

**All runs that were untuned when first measured** (evasion, holdout, holdout2 and this fresh set; the devset was tuned alongside the rules, so it is left out): **18 of 33 scams (55%)** reached High/Critical and **32 of 35 genuine messages (91%)** stayed Low. These are small synthetic sets written by the team, so the real figures could differ a lot in either direction.

Read together with the earlier rounds: on unseen messages, expect roughly 35-50% of scams to reach High/Critical, and very few genuine messages to be wrongly alarmed. The tool is a first-pass screen and not a detector.

## Known limitations
- Coverage is keyword/pattern based (English, Hinglish, Hindi, Tamil, Tanglish). A scam in unfamiliar wording, a different language, or one that avoids every pattern is scored Low or Needs verification. **Low means "no strong warning signs found", never "safe".**
- A pitch with no payment ask, link or promise (pure social proof) can score Low.
- Legit-but-promising text, such as a bank FD advert saying "guaranteed returns", gets Needs verification, not Low.
- Quote-stripping works only when the message is detected as a warning/awareness post. An advice message that quotes scam phrases without clear awareness wording can still be flagged.
- Spaced-out letters are rejoined only when separated by a single character; mixed spacing can still evade.
- SEBI numbers are checked for format only. There is no live lookup and the app says "could not verify".
- Weights are hand-set heuristics, not probabilities. The score is shown as a band, never as "% scam".
- Tamil/Hindi OCR needs Tesseract language packs (included in the Docker image). Speech recognition and voices depend on the device and browser.
- The voice-call (IVR) prototype was tested with simulated webhook requests only, not a live phone number.
- The Docker image was built and run locally, and Tamil/Hindi OCR ran inside it on drawn sample screenshots, but it has not been deployed, and real phone screenshots have not been tried. There is no mobile app in this repository. Deploy and test on a real phone before relying on any of this.
