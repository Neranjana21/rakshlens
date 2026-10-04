"""Regression: every labelled message stays within its expected band.

These sets were tuned against (devset, evasion) or used once for the honest
first-run number and then fixed against (holdout). They guard regressions; they
are NOT an estimate of real-world accuracy. See docs/evaluation.md.
"""
import json
from pathlib import Path

import pytest

from app.rules.engine import analyze_text

DATA = Path(__file__).parent / "data"
CASES = [(f, c) for f in ("devset", "evasion", "holdout", "holdout2") for c in json.loads((DATA / f"{f}.json").read_text(encoding="utf-8"))]


@pytest.mark.parametrize("name,case", CASES, ids=[f"{n}-{c['id']}" for n, c in CASES])
def test_case(name, case):
    a = analyze_text(case["text"])
    assert a.band in case["ok_bands"], f"{case['note']}: got {a.band} ({a.score}); signals {[f.id for f in a.findings]}"
