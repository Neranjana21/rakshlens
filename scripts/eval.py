"""Run the labelled datasets and print real, unrounded results.

    python scripts/eval.py            # summary + every failure
    python scripts/eval.py --all      # every case

devset.json  - written alongside the rules and tuned against: optimistic by construction.
evasion.json - written once and run untuned: the honest number. Do not tune to it silently.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "backend"))
from app.rules.engine import analyze_text  # noqa: E402

SCAM_BANDS = {"high", "critical"}


def run(name: str, show_all: bool):
    rows = json.loads((ROOT / "backend/tests/data" / f"{name}.json").read_text(encoding="utf-8"))
    ok = 0
    scam_total = scam_hit = safe_total = safe_fp = 0
    fails = []
    for r in rows:
        a = analyze_text(r["text"])
        passed = a.band in r["ok_bands"]
        ok += passed
        expects_scam = set(r["ok_bands"]) <= SCAM_BANDS
        expects_low = r["ok_bands"] == ["low"]
        if expects_scam:
            scam_total += 1
            scam_hit += a.band in SCAM_BANDS
        if expects_low:
            safe_total += 1
            safe_fp += a.band != "low"
        if show_all or not passed:
            fails.append(f"  {'PASS' if passed else 'FAIL'} {r['id']} [{r['note']}] got={a.band}({a.score}) want={r['ok_bands']} signals={[f.id for f in a.findings]}")
    print(f"\n{name}: {ok}/{len(rows)} within the expected band")
    print(f"  scam messages flagged High/Critical: {scam_hit}/{scam_total}")
    print(f"  clearly-safe messages kept Low:      {safe_total - safe_fp}/{safe_total}")
    print("\n".join(fails))


if __name__ == "__main__":
    for n in ("devset", "evasion", "holdout", "holdout2"):
        run(n, "--all" in sys.argv)
