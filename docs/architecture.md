# Architecture

```
 PWA (web/) + share sheet   Chrome ext (extension/)   Phone call (IVR) + browser simulator
      \              |                         |                              /
       +-------------+-----------+-------------+------------------------------+
                                 v
                 FastAPI  (backend/app, one container)
   /api/analyze  /api/analyze/text  /api/report  /api/config  /api/health  /api/ivr/*
                                 |
   middleware: security headers + CSP, size limit, rate limit (no body logging)
                                 |
 input -> OCR (local Tesseract eng+tam+hin; cloud vision only if user opts in AND key set)
       -> normalize (NFKC, zero-width strip, homoglyphs, spaced letters, native digits)
       -> entities (URLs, phones, UPI IDs, amounts, %, SEBI no. format, IFSC, accounts)
       -> rules engine (26 rules + combo; additive score; band; fraud stage)
       -> composer (vetted templates: en / ta / hi; masked entities)
       -> [optional] LLM rewording of the summary only -> output guard
       -> JSON result  (+ printable masked evidence report)
```

**Why rules rather than a model for the verdict:** every flag is traceable to a phrase in the message, nothing is a black box, it works offline with no key, and wording is vetted so it cannot give stock tips. The trade-off is coverage (see evaluation.md).

**Stateless:** no database. The only server state is a per-process rate-limit counter.

**One server, many front ends:** the PWA is served by the same process (`web/`, plain JS, no build). The extension and the phone-call prototype call the same JSON API (CORS is open because no cookies/credentials are used).

**Share targets:** the PWA registers a Web Share Target; the service worker parks the shared payload in a throw-away cache, the page reads and deletes it.
Layout: `backend/app/{pipeline,rules,knowledge,explain,report,api}`, tests in `backend/tests`, labelled data in `backend/tests/data`, `scripts/eval.py`.
