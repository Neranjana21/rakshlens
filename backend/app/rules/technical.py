"""Technical signals: links, apps, remote access and credential requests."""
from __future__ import annotations

import difflib
import re

from ..knowledge import patterns as P
from ..pipeline.entities import host_of
from .base import Ctx, Rule, scan

_IP_HOST = re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}$")


def _registered(host: str) -> str:
    parts = host.split(".")
    if len(parts) >= 3 and parts[-2] in {"co", "gov", "org", "ac", "net", "com"} and len(parts[-1]) == 2:
        return ".".join(parts[-3:])
    return ".".join(parts[-2:])


def _is_official(host: str, brand: str, ctx: Ctx) -> bool:
    return any(host == d or host.endswith("." + d) for d in ctx.brands.get(brand, []))


def _imitated_brand(host: str, ctx: Ctx) -> str | None:
    """Return the brand this host appears to imitate, or None."""
    for brand, domains in ctx.brands.items():
        if any(host == d or host.endswith("." + d) for d in domains):
            return None  # genuinely official
    labels = [t for t in re.split(r"[.\-_]", _registered(host).rsplit(".", 1)[0] if "." in host else host) if t]
    whole = "".join(labels)
    for brand in ctx.brands:
        if brand in labels:
            return brand
        if len(brand) >= 5 and brand in whole:
            return brand
        if len(brand) >= 5 and any(difflib.SequenceMatcher(None, brand, t).ratio() >= 0.86 for t in labels + [whole]):
            return brand
    return None


def detect_lookalike(ctx: Ctx) -> list[str]:
    out = []
    for h in ctx.ent.domains:
        if h in P.SHORTENERS or h in P.STORE_DOMAINS or _IP_HOST.match(h):
            continue
        b = _imitated_brand(h, ctx)
        if b:
            out.append(f"{h} (resembles {b})")
    return out[:3]


def detect_shortened(ctx: Ctx) -> list[str]:
    return [h for h in ctx.ent.domains if h in P.SHORTENERS][:3]


def detect_ip_link(ctx: Ctx) -> list[str]:
    return [h for h in ctx.ent.domains if _IP_HOST.match(h)][:2]


def detect_risky_tld(ctx: Ctx) -> list[str]:
    out = []
    for h in ctx.ent.domains:
        if h.rsplit(".", 1)[-1] in P.RISKY_TLDS and _imitated_brand(h, ctx) is None and h not in P.SHORTENERS:
            out.append(h)
    return out[:2]


def detect_apk(ctx: Ctx) -> list[str]:
    hits = scan(ctx.text, P.APP_DOWNLOAD)
    if not hits:
        return []
    if any("apk" in s.lower() for s in hits):
        return hits[:2]
    non_store = [h for h in ctx.ent.domains if h not in P.STORE_DOMAINS]
    return hits[:2] if non_store else []


def detect_credentials(ctx: Ctx) -> list[str]:
    return scan(ctx.text, P.CREDENTIAL_REQUEST)


def detect_remote_access(ctx: Ctx) -> list[str]:
    return scan(ctx.text, P.REMOTE_ACCESS)


RULES = [
    Rule("CREDENTIAL_REQUEST", "technical", 40, "strong", detect_credentials, forces="high"),
    Rule("REMOTE_ACCESS_TOOL", "technical", 40, "strong", detect_remote_access, forces="high"),
    Rule("APK_OR_SIDELOAD", "technical", 35, "strong", detect_apk, forces="high"),
    Rule("LOOKALIKE_DOMAIN", "technical", 35, "strong", detect_lookalike, forces="verify"),
    Rule("IP_ADDRESS_LINK", "technical", 25, "strong", detect_ip_link),
    Rule("SHORTENED_LINK", "technical", 10, "warning", detect_shortened),
    Rule("RISKY_LINK_ENDING", "technical", 8, "warning", detect_risky_tld),
]
