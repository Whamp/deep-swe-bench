"""Aggregate pilot results from run outputs + score caches.

Reports, per pool and overall:
- verifier (G=20 expectation) PPT pick vs judge (argmax letter) PPT pick
  against the held-out passing candidate; chance = 25%, oracle = 100%
- pairwise discrimination on informative (pass vs fail) directed pairs
- judge tie rate (argmax letters equal)
- robustness: nudges needed, missing distributions
- cost: latency, prompt/completion tokens
"""
import glob
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))


def load_results():
    out = {}
    for f in glob.glob(os.path.join(HERE, "results_*.json")):
        for r in json.load(open(f)):
            out[r["pool"]] = r
    return out


def main():
    results = load_results()
    if not results:
        print("no results yet")
        return
    rows = []
    pair_stats = {"pass_higher": 0, "tie": 0, "fail_higher": 0,
                  "judge_ties": 0, "informative": 0, "nudges": 0,
                  "missing_dist": 0, "calls": 0, "latency": 0.0,
                  "prompt_toks": 0, "completion_toks": 0}
    for pool_name, r in sorted(results.items()):
        pool_file = os.path.join(HERE, "pools", pool_name + ".json")
        cache_file = os.path.join(HERE, "cache", pool_name + ".json")
        pool = json.load(open(pool_file))
        cache = json.load(open(cache_file))
        truth = [c["meta"]["reward_binary"] for c in pool["candidates"]]
        for key, v in cache.items():
            a, b = (int(x) for x in key.split(","))
            d = v["detail"]
            pair_stats["calls"] += 1
            pair_stats["nudges"] += d["nudges"]
            pair_stats["latency"] += d["latency_s"]
            pair_stats["prompt_toks"] += d["usage"].get("prompt_tokens", 0)
            pair_stats["completion_toks"] += \
                d["usage"].get("completion_tokens", 0)
            if d["dist_A"] is None or d["dist_B"] is None:
                pair_stats["missing_dist"] += 1
            if truth[a] != truth[b]:  # informative pass/fail pair
                pair_stats["informative"] += 1
                sa, sb = v["score_A"], v["score_B"]
                pass_score, fail_score = (sa, sb) if truth[a] == 1 else (sb, sa)
                if abs(pass_score - fail_score) < 1e-9:
                    pair_stats["tie"] += 1
                elif pass_score > fail_score:
                    pair_stats["pass_higher"] += 1
                else:
                    pair_stats["fail_higher"] += 1
                ja, jb = d["argmax_A"], d["argmax_B"]
                if ja == jb:
                    pair_stats["judge_ties"] += 1
        rows.append((pool_name, r["hit_verifier"], r["hit_judge"],
                     r["pick_verifier"], r["pick_judge"], r["pass_index"],
                     r["comparisons"]))

    print(f"{'pool':<58s} ver judge  (picks v/j, pass)")
    for name, hv, hj, pv, pj, pi, ncmp in rows:
        print(f"{name:<58s}  {hv}     {hj}    ({pv}/{pj}/{pi})  {ncmp} pairs")
    hv = sum(r["hit_verifier"] for r in results.values())
    hj = sum(r["hit_judge"] for r in results.values())
    n = len(results)
    print(f"\nPPT pick hits: verifier {hv}/{n} ({100*hv/n:.0f}%), "
          f"judge {hj}/{n} ({100*hj/n:.0f}%), chance 25%, oracle 100%")
    ps = pair_stats
    if ps["informative"]:
        acc = ps["pass_higher"] / ps["informative"]
        print(f"pairwise pass-vs-fail (expectation): "
              f"{ps['pass_higher']}/{ps['informative']} correct "
              f"({100*acc:.0f}%), {ps['tie']} ties, "
              f"{ps['fail_higher']} wrong")
        print(f"judge (argmax) tie rate on informative pairs: "
              f"{ps['judge_ties']}/{ps['informative']} "
              f"({100*ps['judge_ties']/ps['informative']:.0f}%)")
    if ps["calls"]:
        print(f"robustness: {ps['nudges']} nudges, "
              f"{ps['missing_dist']} missing distributions / {ps['calls']} calls")
        print(f"cost/call: {ps['latency']/ps['calls']:.0f}s, "
              f"{ps['prompt_toks']/ps['calls']:.0f} prompt toks, "
              f"{ps['completion_toks']/ps['calls']:.0f} completion toks; "
              f"total {ps['latency']/3600:.2f} GPU-hours")


if __name__ == "__main__":
    main()
