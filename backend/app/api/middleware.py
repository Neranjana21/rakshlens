"""Security headers, request size limit and a small in-memory rate limiter.

Nothing here logs request bodies. Rate-limit state is a per-process dict of
timestamps keyed by client address and is lost on restart, by design.
"""
from __future__ import annotations

import time
from collections import defaultdict, deque

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse, Response

from ..config import settings

_CSP = (
    "default-src 'self'; img-src 'self' data: blob:; style-src 'self'; script-src 'self'; "
    "connect-src 'self'; media-src 'self' blob:; manifest-src 'self'; worker-src 'self'; "
    "frame-ancestors 'none'; base-uri 'none'; form-action 'self'"
)
_WINDOW = 60.0
_hits: dict[str, deque[float]] = defaultdict(deque)


_MAX_KEYS = 10_000


def client_key(request: Request) -> str:
    # The proxy appends the real peer address last; earlier entries are client-supplied and spoofable.
    fwd = request.headers.get("x-forwarded-for", "")
    return (fwd.split(",")[-1].strip() if fwd else (request.client.host if request.client else "unknown")) or "unknown"


def _prune(now: float) -> None:
    if len(_hits) < _MAX_KEYS:
        return
    for key in [k for k, q in _hits.items() if not q or now - q[-1] > _WINDOW]:
        del _hits[key]


class Guard(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        path = request.url.path
        if path.startswith(("/api/analyze", "/api/report", "/api/ivr")):
            if "content-length" not in request.headers and "chunked" in request.headers.get("transfer-encoding", "").lower():
                # A chunked body has no declared size, so it would bypass the size check below.
                return JSONResponse({"error": "length_required"}, status_code=411)
            try:
                length = int(request.headers.get("content-length") or 0)
            except ValueError:
                return JSONResponse({"error": "bad_request"}, status_code=400)
            if length > settings.max_upload_mb * 1024 * 1024 + 4096:
                return JSONResponse({"error": "too_large"}, status_code=413)
            now = time.monotonic()
            _prune(now)
            q = _hits[client_key(request)]
            while q and now - q[0] > _WINDOW:
                q.popleft()
            if len(q) >= settings.rate_limit_per_min:
                return JSONResponse({"error": "rate_limited"}, status_code=429, headers={"Retry-After": "30"})
            q.append(now)

        response: Response = await call_next(request)
        h = response.headers
        h.setdefault("Content-Security-Policy", _CSP)
        h["X-Content-Type-Options"] = "nosniff"
        h["Referrer-Policy"] = "no-referrer"
        h["Permissions-Policy"] = "camera=(self), microphone=(self), geolocation=()"
        h["X-Frame-Options"] = "DENY"
        if path.startswith("/api"):
            h["Cache-Control"] = "no-store"
        return response
