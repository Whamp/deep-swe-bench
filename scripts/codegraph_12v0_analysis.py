#!/usr/bin/env python3
"""codegraph 12v0 x3 comparison: baseline vs OM vs codegraph-skill vs codegraph-auto.

Paired on task+rep (deepseek-v4... no — gpt-5.5/low). Reads only the 12_v0
subset so baseline's full-113 coverage is restricted to the same 12 tasks the
codegraph arms ran. Bootstrap CIs on solve-rate delta vs baseline.
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
ARMS = [
    "baseline",
    "observational-memory-gpt54mini-low",
    "codegraph-skill",
    "codegraph-auto",
    "codegraph-impact",
]


def load():
    rows = defaultdict(dict)  # (task) -> {rep: {arm: rec}}
    for arm in ARMS:
        for rj in glob.glob(f"results/{MODEL}/{THINK}/{arm}/*/rep*/result.json"):
            p = rj.split("/")
            task, rep = p[-3], p[-2]
            if task not in SUBSET:
                continue
            r = json.load(open(rj))
            rec = {
                "arm": arm,
                "partial": r.get("reward_partial", 0.0),
                "binary": int(r.get("reward_binary", 0)),
                "tokens": r.get("total_tokens", 0),
                "cost": r.get("combined_cost_usd") or r.get("cost_usd") or 0.0,
                "turns": r.get("turns", 0),
                "timeout": bool(r.get("agent_timed_out")),
            }
            rows[(task, rep)][arm] = rec
    return rows


def boot_delta_ci(treated, base, B=20000, seed=0):
    """Bootstrap 95% CI on (mean treated - mean baseline) over paired reps."""
    rng = np.random.default_rng(seed)
    diffs = np.array([t - b for t, b in zip(treated, base)])
    n = len(diffs)
    if n == 0:
        return float("nan"), (float("nan"), float("nan"))
    boots = rng.choice(diffs, size=(B, n), replace=True).mean(axis=1)
    lo, hi = np.percentile(boots, [2.5, 97.5])
    return float(diffs.mean()), (float(lo), float(hi))


def main():
    rows = load()
    # paired keys = present in ALL four arms
    keys = sorted(k for k in rows if all(a in rows[k] for a in ARMS))
    if not keys:
        sys.exit("no task+rep present in all 4 arms")
    print(f"# codegraph comparison — {MODEL}/{THINK}, subset 12_v0, {len(keys)} paired reps\n")

    # per-arm means over paired reps
    print(f"{'arm':<42}{'solve':>7}{'partial':>9}{'median_tok(k)':>15}{'median_cost':>13}{'med_turns':>11}")
    per_arm = {a: [] for a in ARMS}
    for k in keys:
        for a in ARMS:
            per_arm[a].append(rows[k][a])
    summary = {}
    for a in ARMS:
        rs = per_arm[a]
        solve = st.mean(r["binary"] for r in rs)
        part = st.mean(r["partial"] for r in rs)
        toks = st.median(r["tokens"] for r in rs) / 1000
        cost = st.median(r["cost"] for r in rs)
        turns = st.median(r["turns"] for r in rs)
        summary[a] = (solve, part)
        print(f"{a:<42}{solve:>7.3f}{part:>9.3f}{toks:>15.0f}{cost:>13.2f}{turns:>11.0f}")

    # paired deltas vs baseline
    base_part = [rows[k]["baseline"]["partial"] for k in keys]
    base_bin = [rows[k]["baseline"]["binary"] for k in keys]
    print(f"\n# paired deltas vs baseline (n={len(keys)}, bootstrap 95% CI on mean)")
    print(f"{'arm':<42}{'Δpartial':>9}{'  95% CI':>22}{'Δsolve':>9}{'  95% CI':>22}")
    for a in ARMS[1:]:
        ap = [rows[k][a]["partial"] for k in keys]
        ab = [rows[k][a]["binary"] for k in keys]
        dpart, cip = boot_delta_ci(ap, base_part)
        dsolve, cib = boot_delta_ci(ab, base_bin)
        sgn = "  *" if (cip[0] > 0 or cip[1] < 0) else ""
        print(f"{a:<42}{dpart:>+9.3f}  [{cip[0]:+.3f},{cip[1]:+.3f}]{dsolve:>+9.3f}  [{cib[0]:+.3f},{cib[1]:+.3f}]{sgn}")

    # head-to-head: impact (names) vs auto (counts) — the v1->v2 question
    print(f"\n# head-to-head: codegraph-impact (names) vs codegraph-auto (counts)")
    # impact vs auto (the v2 fix)
    ip = [rows[k]["codegraph-impact"]["partial"] for k in keys]
    ib = [rows[k]["codegraph-impact"]["binary"] for k in keys]
    ap2 = [rows[k]["codegraph-auto"]["partial"] for k in keys]
    ab2 = [rows[k]["codegraph-auto"]["binary"] for k in keys]
    dpart, cip = boot_delta_ci(ip, ap2)
    dsolve, cib = boot_delta_ci(ib, ab2)
    print(f"  Δpartial(impact-auto) = {dpart:+.3f}  CI[{cip[0]:+.3f},{cip[1]:+.3f}]")
    print(f"  Δsolve(impact-auto)   = {dsolve:+.3f}  CI[{cib[0]:+.3f},{cib[1]:+.3f}]")
    # auto vs skill (kept for reference)
    sp2 = [rows[k]["codegraph-skill"]["partial"] for k in keys]
    sb2 = [rows[k]["codegraph-skill"]["binary"] for k in keys]
    dp2, cp2 = boot_delta_ci(ap2, sp2)
    ds2, cs2 = boot_delta_ci(ab2, sb2)
    print(f"  Δpartial(auto-skill)  = {dp2:+.3f}  CI[{cp2[0]:+.3f},{cp2[1]:+.3f}]")
    print(f"  Δsolve(auto-skill)    = {ds2:+.3f}  CI[{cs2[0]:+.3f},{cs2[1]:+.3f}]")

    # per-task: all four codegraph-relevant arms
    print(f"\n# per-task solve rate (base / auto / impact / skill), sorted by |impact-auto|")
    tstat = {}
    for t in sorted({k[0] for k in keys}):
        rows_t = [rows[k] for k in keys if k[0] == t]
        sbt = st.mean(r["baseline"]["binary"] for r in rows_t)
        sa = st.mean(r["codegraph-auto"]["binary"] for r in rows_t)
        si = st.mean(r["codegraph-impact"]["binary"] for r in rows_t)
        ss = st.mean(r["codegraph-skill"]["binary"] for r in rows_t)
        tstat[t] = (si, sa, ss, sbt)
    for t, (si, sa, ss, sbt) in sorted(tstat.items(), key=lambda x: -abs(x[1][0]-x[1][1])):
        print(f"  {t:<45} impact={si:.2f} auto={sa:.2f} skill={ss:.2f} base={sbt:.2f}")


if __name__ == "__main__":
    main()
