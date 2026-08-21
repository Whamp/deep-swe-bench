"""Run the PPT best-of-N pilot over pools with the local Qwen verifier.

Per pool: N=4 candidates, ring pass + k pivots (paper's Probabilistic Pivot
Tournament), C=1 criterion, K=1 repetition, G=20 granularity. Every directed
comparison is cached on disk with the raw letter distributions, so judge
(argmax) vs verifier (expectation) selection rules are both computed offline
from identical evidence.

Usage:
  .venv/bin/python run_pilot.py [--pools glob] [--pivots 1] [--limit N]
"""
import argparse
import glob
import json
import os
import random
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from verifier_client import Verifier  # noqa: E402

from llm_verifier import pivot_tournament as ppt  # noqa: E402
from llm_verifier.prompts import load_prompts, select_criteria  # noqa: E402

HERE = os.path.dirname(os.path.abspath(__file__))
CACHE_DIR = os.path.join(HERE, "cache")
REPO = os.path.join(HERE, "vendor", "llm-as-a-verifier")
CRITERIA_FILE = os.path.join(REPO, "criteria", "swe_bench.md")
CRITERION_ID = "verification"  # Empirical Verification: most trace-legible

BASE_URL = os.environ.get("VERIFIER_BASE_URL", "http://127.0.0.1:8388")
MODEL = os.environ.get("VERIFIER_MODEL", "qwen3.8-27b")


def cache_path(pool_name):
    return os.path.join(CACHE_DIR, pool_name + ".json")


def run_pool(pool, verifier, criterion, n_pivots, seed):
    name = pool["task"] + ":" + pool["kind"]
    path = cache_path(pool["kind"] + "-" + pool["task"])
    cache = {}
    if os.path.exists(path):
        cache = json.load(open(path))

    cands = pool["candidates"]
    n = len(cands)
    rng = random.Random(seed)
    ring = ppt.ring_cycle(n, rng)

    def score(a, b):
        key = f"{a},{b}"
        if key not in cache:
            t0 = time.time()
            out = verifier.score_pair(pool["problem"], cands[a]["trace"],
                                      cands[b]["trace"], criterion)
            cache[key] = out
            with open(path, "w") as f:
                json.dump(cache, f, indent=1)
            d = out["detail"]
            print(f"    pair {a}v{b}: R=({out['score_A']:.3f},"
                  f" {out['score_B']:.3f}) argmax=({d['argmax_A']},"
                  f"{d['argmax_B']}) {d['latency_s']}s", flush=True)
        return cache[key]["score_A"], cache[key]["score_B"]

    best, n_cmp = ppt.select_best(n, ring, n_pivots, score)

    # discrete-judge tournament from the same cache (argmax letters, ties
    # split 0.5) — the paper's LM-judge baseline on identical calls
    def score_judge(a, b):
        d = cache[f"{a},{b}"]["detail"]
        va, vb = d["argmax_A"], d["argmax_B"]
        sa = _letter_value(va)
        sb = _letter_value(vb)
        return (sa, sb)

    best_judge, _ = ppt.select_best(n, ring, n_pivots, score_judge)

    truth = [c["meta"]["reward_binary"] for c in cands]
    return {
        "pool": pool["kind"] + "-" + pool["task"], "n": n,
        "pivots": n_pivots, "comparisons": n_cmp,
        "truth": truth,
        "pass_index": truth.index(1) if 1 in truth else None,
        "pick_verifier": best, "pick_judge": best_judge,
        "hit_verifier": int(truth[best] == 1),
        "hit_judge": int(truth[best_judge] == 1),
    }


def _letter_value(letter):
    """A=20 ... T=1, matching the SCALE mapping; None -> 0 (always loses)."""
    if not letter:
        return 0.0
    return float(20 - (ord(letter.upper()) - 65))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pools", default=os.path.join("pools", "*.json"))
    ap.add_argument("--pivots", type=int, default=1)
    ap.add_argument("--limit", type=int, default=0)
    ap.add_argument("--seed", type=int, default=7)
    ap.add_argument("--out", default=os.path.join(HERE, "pilot_results.json"))
    args = ap.parse_args()

    gt_note, criteria = load_prompts(CRITERIA_FILE)
    criterion = select_criteria(criteria, [CRITERION_ID])[0]
    print(f"criterion: {criterion['name']}")

    verifier = Verifier(BASE_URL, MODEL, gt_note)
    pool_files = []
    for part in args.pools.split(","):
        pool_files.extend(sorted(glob.glob(part.strip())))
    pool_files = [p for p in pool_files if "manifest" not in p]
    if args.limit:
        pool_files = pool_files[:args.limit]

    results = []
    for pf in pool_files:
        pool = json.load(open(pf))
        print(f"pool {pool['kind']}-{pool['task']}: "
              f"{len(pool['candidates'])} candidates", flush=True)
        t0 = time.time()
        res = run_pool(pool, verifier, criterion, args.pivots, args.seed)
        res["wall_s"] = round(time.time() - t0, 1)
        results.append(res)
        print(f"  -> verifier pick {res['pick_verifier']} "
              f"(hit={res['hit_verifier']}), judge pick {res['pick_judge']} "
              f"(hit={res['hit_judge']}), pass={res['pass_index']}",
              flush=True)
        with open(args.out, "w") as f:
            json.dump(results, f, indent=1)

    hv = sum(r["hit_verifier"] for r in results)
    hj = sum(r["hit_judge"] for r in results)
    n = len(results)
    print(f"\n=== {n} pools: verifier hits {hv}/{n} "
          f"({100*hv/max(n,1):.0f}%), judge hits {hj}/{n} "
          f"({100*hj/max(n,1):.0f}%), chance 25%, oracle 100% ===")


if __name__ == "__main__":
    main()
