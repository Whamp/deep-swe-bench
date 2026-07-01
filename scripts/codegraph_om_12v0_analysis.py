#!/usr/bin/env python3
"""8-arm factorial: {none/skill/auto/impact} x {no-OM/+OM} on gpt-5.5/low, 12_v0 x3.

Reads only the 12_v0 subset. Paired on (task, rep). The 8 arms:
  baseline                          (none, no-OM)
  observational-memory-gpt54mini-low (none, +OM)        <-- OM alone
  codegraph-skill                   (skill, no-OM)
  codegraph-auto                    (counts, no-OM)
  codegraph-impact                  (names, no-OM)
  codegraph-skill-om                (skill, +OM)
  codegraph-auto-om                 (counts, +OM)
  codegraph-impact-om               (names, +OM)

Decomposition: marginal +OM effect at each codegraph level, and marginal
codegraph-level effect at each OM level. Bootstrap 95% CI on every delta.
"""
from __future__ import annotations
import json, glob, sys, statistics as st
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "harness"))
import numpy as np  # noqa: E402

SUBSET = (ROOT / "subsets" / "12_v0.txt").read_text().split()
MODEL, THINK = "gpt-5.5", "low"

# (codegraph level, OM flag) -> config name
CELLS = {
    ("none",   False): "baseline",
    ("none",   True):  "observational-memory-gpt54mini-low",
    ("skill",  False): "codegraph-skill",
    ("counts", False): "codegraph-auto",
    ("names",  False): "codegraph-impact",
    ("skill",  True):  "codegraph-skill-om",
    ("counts", True):  "codegraph-auto-om",
    ("names",  True):  "codegraph-impact-om",
}
CG_LEVELS = ["none", "skill", "counts", "names"]
ALL_ARMS = [CELLS[(cg, om)] for cg in CG_LEVELS for om in (False, True)]


def load():
    rows = defaultdict(dict)  # (task, rep) -> {arm: rec}
    for arm in ALL_ARMS:
        for rj in glob.glob(f"results/{MODEL}/{THINK}/{arm}/*/rep*/result.json"):
            p = rj.split("/")
            task, rep = p[-3], p[-2]
            if task not in SUBSET:
                continue
            r = json.load(open(rj))
            rows[(task, rep)][arm] = {
                "arm": arm,
                "partial": r.get("reward_partial", 0.0),
                "binary": int(r.get("reward_binary", 0)),
                "tokens": r.get("total_tokens", 0),
                "cost": r.get("combined_cost_usd") or r.get("cost_usd") or 0.0,
                "turns": r.get("turns", 0),
                "timeout": bool(r.get("agent_timed_out")),
            }
    return rows


def boot_ci(treated, base, B=20000, seed=0):
    """Bootstrap 95% CI on mean(treated - base) over paired reps."""
    rng = np.random.default_rng(seed)
    diffs = np.array([t - b for t, b in zip(treated, base)], dtype=float)
    if len(diffs) == 0:
        return float("nan"), (float("nan"), float("nan"))
    n = len(diffs)
    boots = rng.choice(diffs, size=(B, n), replace=True).mean(axis=1)
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return float(diffs.mean()), (float(lo), float(hi))


def sig(ci):
    return "*" if (ci[0] > 0 or ci[1] < 0) else " "


def main():
    rows = load()
    keys = sorted(k for k in rows if all(a in rows[k] for a in ALL_ARMS))
    if not keys:
        sys.exit("no task+rep present in all 8 arms")
    print(f"# codegraph x OM factorial — {MODEL}/{THINK}, subset 12_v0, n={len(keys)} paired reps\n")

    # ---- per-arm table ----
    print(f"{'arm':<38}{'OM':>4}{'solve':>7}{'partial':>9}{'med_tok(k)':>12}{'med_$':>7}{'med_trn':>8}")
    summary = {}
    for arm in ALL_ARMS:
        rs = [rows[k][arm] for k in keys]
        om = "+OM" if any(arm == CELLS[(cg, True)] for cg in CG_LEVELS) else "—"
        s = st.mean(r["binary"] for r in rs)
        p = st.mean(r["partial"] for r in rs)
        tok = st.median(r["tokens"] for r in rs) / 1000
        cost = st.median(r["cost"] for r in rs)
        tr = st.median(r["turns"] for r in rs)
        summary[arm] = {"solve": s, "partial": p, "tok": tok, "cost": cost, "turns": tr}
        print(f"{arm:<38}{om:>4}{s:>7.3f}{p:>9.3f}{tok:>12.0f}{cost:>7.2f}{tr:>8.0f}")

    # ---- marginal effect of +OM at each codegraph level ----
    print(f"\n# marginal effect of adding OM (paired, +OM minus no-OM)")
    print(f"{'cg level':<12}{'Δpartial':>10}{'  95% CI':>22}{'Δsolve':>9}{'  95% CI':>22}")
    for cg in CG_LEVELS:
        no, yes = CELLS[(cg, False)], CELLS[(cg, True)]
        yp = [rows[k][yes]["partial"] for k in keys]
        np_ = [rows[k][no]["partial"] for k in keys]
        yb = [rows[k][yes]["binary"] for k in keys]
        nb = [rows[k][no]["binary"] for k in keys]
        dp, cp = boot_ci(yp, np_)
        db, cb = boot_ci(yb, nb)
        print(f"{cg:<12}{dp:>+10.3f}  [{cp[0]:+.3f},{cp[1]:+.3f}]{db:>+9.3f}  [{cb[0]:+.3f},{cb[1]:+.3f}] {sig(cp)}{sig(cb)}")

    # ---- marginal effect of codegraph level vs none, at each OM level ----
    print(f"\n# marginal effect of each codegraph level vs none (paired)")
    for om in (False, True):
        tag = "+OM" if om else "no-OM"
        base = CELLS[("none", om)]
        bp = [rows[k][base]["partial"] for k in keys]
        bb = [rows[k][base]["binary"] for k in keys]
        print(f"\n  [{tag}] vs {base}:")
        print(f"  {'cg level':<12}{'Δpartial':>10}{'  95% CI':>22}{'Δsolve':>9}{'  95% CI':>22}")
        for cg in CG_LEVELS[1:]:
            arm = CELLS[(cg, om)]
            ap = [rows[k][arm]["partial"] for k in keys]
            ab = [rows[k][arm]["binary"] for k in keys]
            dp, cp = boot_ci(ap, bp)
            db, cb = boot_ci(ab, bb)
            print(f"  {cg:<12}{dp:>+10.3f}  [{cp[0]:+.3f},{cp[1]:+.3f}]{db:>+9.3f}  [{cb[0]:+.3f},{cb[1]:+.3f}] {sig(cp)}{sig(cb)}")

    # ---- head-to-head: stacked vs OM-alone ----
    print(f"\n# stacked vs OM-alone (does codegraph add to OM?)")
    om_only = "observational-memory-gpt54mini-low"
    op = [rows[k][om_only]["partial"] for k in keys]
    ob = [rows[k][om_only]["binary"] for k in keys]
    print(f"{'stacked':<24}{'Δpartial':>10}{'  95% CI':>22}{'Δsolve':>9}{'  95% CI':>22}")
    for cg in ["skill", "counts", "names"]:
        arm = CELLS[(cg, True)]
        ap = [rows[k][arm]["partial"] for k in keys]
        ab = [rows[k][arm]["binary"] for k in keys]
        dp, cp = boot_ci(ap, op)
        db, cb = boot_ci(ab, ob)
        print(f"{arm:<24}{dp:>+10.3f}  [{cp[0]:+.3f},{cp[1]:+.3f}]{db:>+9.3f}  [{cb[0]:+.3f},{cb[1]:+.3f}] {sig(cp)}{sig(cb)}")

    # ---- OM rescuing codegraph-auto's regression? (auto+OM vs auto) ----
    print(f"\n# does OM rescue the counts regression? (auto+OM vs auto, and vs auto-impact)")
    auto, auto_om = "codegraph-auto", "codegraph-auto-om"
    ap = [rows[k][auto]["partial"] for k in keys]
    yp = [rows[k][auto_om]["partial"] for k in keys]
    ab = [rows[k][auto]["binary"] for k in keys]
    yb = [rows[k][auto_om]["binary"] for k in keys]
    dp, cp = boot_ci(yp, ap)
    db, cb = boot_ci(yb, ab)
    print(f"  auto+OM vs auto: Δpartial={dp:+.3f} CI[{cp[0]:+.3f},{cp[1]:+.3f}] {sig(cp)}  Δsolve={db:+.3f} CI[{cb[0]:+.3f},{cb[1]:+.3f}] {sig(cb)}")
    # per-task auto regression rescue
    print(f"  per-task (auto -> auto+OM) on the 3 known v1-catastrophic tasks:")
    for t in ["fastapi-implicit-head-options", "ts-pattern-match-each", "boa-hierarchical-evaluation-cancellation"]:
        if t in {k[0] for k in keys}:
            line = f"    {t}:"
            for rep in sorted({k[1] for k in keys if k[0] == t}):
                a = rows[(t, rep)].get(auto, {}).get("partial")
                y = rows[(t, rep)].get(auto_om, {}).get("partial")
                if a is not None and y is not None:
                    line += f"  rep{rep} {a:.2f}->{y:.2f}"
            print(line)

    # ---- best overall ----
    print(f"\n# ranking by mean partial")
    for arm in sorted(ALL_ARMS, key=lambda a: -summary[a]["partial"]):
        s = summary[arm]
        print(f"  {arm:<38} partial={s['partial']:.3f} solve={s['solve']:.3f}  ${s['cost']:.2f} {s['tok']:.0f}k tok")

    # ---- per-task across 8 arms (the catastrophic-regression audit) ----
    print(f"\n# per-task mean partial (8 arms); flag where any stacked cell regressed >0.3 vs its non-OM twin")
    print(f"{'task':<42}{'none':>6}{'OM':>6}{'skl':>6}{'skl+OM':>8}{'cnt':>6}{'cnt+OM':>8}{'nm':>6}{'nm+OM':>8}")
    tasks = sorted({k[0] for k in keys})
    for t in tasks:
        rks = sorted({k[1] for k in keys if k[0] == t})
        means = {}
        for arm in ALL_ARMS:
            means[arm] = st.mean(rows[(t, r)][arm]["partial"] for r in rks if (t, r) in rows and arm in rows[(t, r)])
        flag = ""
        for cg in ["skill", "counts", "names"]:
            if means[CELLS[(cg, True)]] < means[CELLS[(cg, False)]] - 0.3:
                flag += f" {cg}↓"
        print(f"{t:<42}{means[CELLS[('none',False)]]:>6.2f}{means[CELLS[('none',True)]]:>6.2f}"
              f"{means[CELLS[('skill',False)]]:>6.2f}{means[CELLS[('skill',True)]]:>8.2f}"
              f"{means[CELLS[('counts',False)]]:>6.2f}{means[CELLS[('counts',True)]]:>8.2f}"
              f"{means[CELLS[('names',False)]]:>6.2f}{means[CELLS[('names',True)]]:>8.2f}{flag}")


if __name__ == "__main__":
    main()
