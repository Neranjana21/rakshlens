# Guardrails: how each hackathon constraint is met

| Constraint | What the product does | Where |
|---|---|---|
| No personalised investment advice or stock tips | Output is limited to vetted templates. Optional LLM rewording sees only the already-vetted findings, never the raw message, and its output must pass the guard, which blocks buy/sell/hold/target language, invented numbers and links. If it fails, the template text is used. | `explain/guard.py`, `explain/llm.py` |
| No ads, affiliate links or product promotion | None in the UI or output. Only official helplines are shown: 1930, cybercrime.gov.in, SEBI SCORES, sebi.gov.in. | `explain/composer.py` |
| Honest about uncertainty | Every result has "what we could not check" and "why we are not certain". SEBI numbers are labelled unverifiable. Bands, not percentages. | templates, `rules/authority.py` |
| Privacy | Messages and screenshots are processed in memory and never stored; no content logs (`--no-access-log`); phones, UPI IDs and accounts are masked in output and in the report; no accounts or cookies. Cloud AI (OCR/rewording) only runs if the user ticks consent AND the server has a key. | `pipeline/masking.py`, `api/middleware.py` |
| Security hygiene | Strict CSP (no inline script/style), size limit, in-memory rate limit, non-root container, escaped report HTML. | `api/middleware.py`, `Dockerfile` |
| Regional language / low bandwidth / voice | English, Tamil, Hindi UI and results; speech in and out; no web fonts; small PWA that works as an installed app; IVR prototype for basic phones. | `web/`, `api/ivr.py` |
| Explainable | Every finding shows the exact phrase it matched, why it matters, and its severity. | `rules/`, `explain/` |

What we deliberately did not build: live SEBI lookup (no official API access verified), accounts/logins, Account Aggregator/DigiLocker linking. They are on the roadmap.

## Wording to use (and avoid)
- Say "explainable risk profiler", not "AI scam detector". The numeric score is a hand-weighted heuristic, not a probability; the user sees a band, never a "% scam".
- SEBI: we check the number's format only, show "Official verification: not checked", and link to SEBI's official intermediaries page so the user can verify it themselves. No automatic lookup or scraping.
- Look-alike links are checked against a curated starter list of brands, not all brands.
- Languages: English, Tamil, Hindi with local OCR and browser speech. Bhashini is the production roadmap, not something the prototype uses.
- The web app is same-origin with the API. CORS is open only so the extension and the phone-call prototype can call the same API.
- Obfuscation: we normalize common patterns (spaced letters, look-alike characters), not all of them.
- "Ask someone you trust" builds a note from the band and top reasons only. The original message, phone numbers and UPI IDs are never included.
- The "pause" nudge is advice to wait and talk to someone; it is not a legal or financial judgement.
