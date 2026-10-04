"""RakshaLens API + PWA host. One process serves both."""
from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .api.middleware import Guard
from .api.ivr import router as ivr_router
from .api.routes import router
from .config import settings

app = FastAPI(title="RakshaLens", docs_url=None, redoc_url=None, openapi_url=None)

# No cookies or credentials are used, so open CORS is safe and lets the browser
# extension and the phone-call prototype call the API.
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["GET", "POST"], allow_headers=["*"], allow_credentials=False)
app.add_middleware(Guard)
app.include_router(router)
app.include_router(ivr_router)

if settings.web_dir.exists():
    app.mount("/", StaticFiles(directory=settings.web_dir, html=True), name="web")
