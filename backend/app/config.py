"""Environment-driven settings, validated once at import."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


def _int(name: str, default: int) -> int:
    try:
        return int(os.environ.get(name, default))
    except ValueError:
        return default


@dataclass(frozen=True)
class Settings:
    api_key: str = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    model: str = os.environ.get("RAKSHALENS_MODEL", "claude-haiku-4-5-20251001")
    llm_timeout: float = float(os.environ.get("RAKSHALENS_LLM_TIMEOUT", "10"))
    max_upload_mb: int = _int("RAKSHALENS_MAX_UPLOAD_MB", 6)
    rate_limit_per_min: int = _int("RAKSHALENS_RATE_LIMIT", 30)
    web_dir: Path = Path(os.environ.get("WEB_DIR", Path(__file__).resolve().parents[2] / "web"))

    @property
    def llm_available(self) -> bool:
        return bool(self.api_key)


settings = Settings()
