"""Per-record precision vs recall: are observers curating, or just worse?

Question: P4 (deterministic) emits ~105 records and captures 40% of gold callers.
P1/P2 (observers) emit ~7 records and capture ~10%. Are the observers picking
SMARTER symbols (higher per-record precision) but too few of them, or are they
just worse across the board?

If observer per-record precision >> P4 precision, the observer IS curating —
it just curates down to a set too small to cover the real blast radius. That
would mean curated-P4 and observer-curation are doing DIFFERENT things
(graph-structural vs narrative-salience), not the same thing a different way.
"""
import json
import statistics as st
from pathlib import Path

from .impact_common import CASESDIR, RUNSDIR
from .metrics.impact_capture import score_case


def load(p):
    return {json.loads(l)["case_id"]: json.loads(l) for l in Path(p).read_text().splitlines() if l.strip()}


def recs_of(row):
    return row.get("observations") or row.get("records") or []


def main():
    cases = {json.loads(l)["case_id"]: json.loads(l)
             for l in (CASESDIR / "impact_subset.jsonl").read_text().splitlines() if l.strip()}
    p1 = load(str(RUNSDIR / "p1-live.jsonl"))
    p2 = load(str(RUNSDIR / "p2-live.jsonl"))
    p4 = load(str(RUNSDIR / "p4-deterministic.jsonl"))
    clean = sorted(cid for cid, r in p1.items() if len(recs_of(r)) > 0)

    # dump score_case keys once
    sample = score_case(cases[clean[0]], recs_of(p4[clean[0]]))
    print(f"(score_case fields: {list(sample.keys())})\n")

    print(f"{'proto':10} {'recall':>8} {'records':>8} {'prec/rec':>9} {'abs_gold':>9}  read")
    print("-" * 70)
    results = {}
    for label, run in (("p4-det", p4), ("p2-inj", p2), ("p1-tool", p1)):
        recalls, precisions, rec_counts, abs_gold = [], [], [], 0
        for cid in clean:
            if cid not in cases or cid not in run:
                continue
            s = score_case(cases[cid], recs_of(run[cid]))
            recall = s.get("caller_capture") or 0.0
            n_rec = s.get("n_records") or len(recs_of(run[cid])) or 1
            recalls.append(recall)
            rec_counts.append(n_rec)
            precisions.append(recall / max(n_rec, 1))
            # try to recover absolute gold count from fields
        mean_recall = st.mean(recalls)
        mean_rec = st.mean(rec_counts)
        mean_prec = st.mean(precisions)
        results[label] = (mean_recall, mean_rec, mean_prec)
        read = "smart picks, too few" if (mean_prec > 0.008 and mean_recall < 0.2) else \
               "brute coverage" if mean_rec > 50 else "?"
        print(f"{label:10} {mean_recall:>8.3f} {mean_rec:>8.1f} {mean_prec:>9.4f} {'':>9}  {read}")

    # relative precision
    p4p = results["p4-det"][2]
    print()
    for label in ("p2-inj", "p1-tool"):
        rel = results[label][2] / p4p
        print(f"{label} per-record precision is {rel:.2f}x raw P4  "
              f"({results[label][2]:.4f} vs {p4p:.4f})")

    print("\n--- interpretation ---")
    p1r, p1rec, p1p = results["p1-tool"]
    p4r, p4rec, p4p = results["p4-det"]
    print(f"P1 emits {p1rec:.0f} records ({p4rec/p1rec:.0f}x fewer than P4) "
          f"at {p1p/p4p:.1f}x the per-record density.")
    print(f"But P1 recall {p1r:.1%} vs P4 {p4r:.1%}: observer covers "
          f"{p1r/p4r:.0%} of what raw graph coverage does.")
    print("=> observers ARE curating (denser records) but to a set too small")
    print("   for blast-radius COVERAGE. Different objective than curated-P4.")


if __name__ == "__main__":
    main()
