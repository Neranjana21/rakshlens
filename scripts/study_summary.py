"""Summarise study/responses.csv. truth/judgements: scam | safe | unsure. would_pay: yes | no."""
import csv
import sys
from statistics import mean

path = sys.argv[1] if len(sys.argv) > 1 else "study/responses.csv"
rows = list(csv.DictReader(open(path, encoding="utf-8")))
if not rows:
    sys.exit("No rows yet. Fill study/responses.csv first.")

def correct(r, k):
    return r[f"{k}_judgement"].strip().lower() == r["truth"].strip().lower()

n = len(rows)
people = len({r["participant"] for r in rows})
scam = [r for r in rows if r["truth"].strip().lower() == "scam"]
print(f"{people} participants, {n} judgements ({len(scam)} on scam messages)")
for k in ("before", "after"):
    c = sum(correct(r, k) for r in rows)
    pay = sum(r[f"{k}_would_pay"].strip().lower() == "yes" for r in scam)
    conf = mean(float(r[f"{k}_confidence"]) for r in rows if r[f"{k}_confidence"].strip())
    print(f"{k:>6}: correct {c}/{n} ({100*c/n:.0f}%) | would pay/share on a scam {pay}/{len(scam)} | mean confidence {conf:.1f}")
fixed = sum((not correct(r, "before")) and correct(r, "after") for r in rows)
unsure = [r for r in rows if r["before_judgement"].strip().lower() == "unsure"]
print(f"wrong or unsure before, correct after: {fixed}; of {len(unsure)} 'unsure' answers, {sum(correct(r,'after') for r in unsure)} became correct")
worse = sum(correct(r, "before") and not correct(r, "after") for r in rows)
print(f"correct before, wrong after (report this too): {worse}")
