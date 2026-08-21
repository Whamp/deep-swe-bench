"""Build candidate pools for the verifier pilot.

Pool design (mirrors the paper's trajectory-reward-model protocol):
- each pool = one task, N=4 candidates: exactly 1 passing + 3 failing cells
  (so random selection hits 25% and oracle 100%; verifier hit-rate is the
  headline metric)
- "cross" pools sample cells from distinct model leafs where possible
  (paper's SWE-bench pool is heterogeneous across model families)
- "qwen" pools use only Qwen3.6-27B leafs: same-family self-verification
  with Qwen3.8-27B as the verifier
- cells must have verifier ground truth (reward_binary 0/1) and a session
- failing cells prefer non-timeout failures (timeout fails are too easy to
  spot and would flatter the verifier)

Writes pools/<name>.json with verifier-visible text + held-out metadata.
"""
import collections
import glob
import json
import os
import random
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from render import render_cell

ROOT = os.path.expanduser("~/evals/deep-swe-bench")
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "pools")

QWEN_LEAFS = ("Qwen3.6-27B-AWQ-BF16-INT4", "ThinkingCap-Qwen3.6-27B",
              "thinkingcap-qwen3.6-27b-awq-int4")


def scan_cells():
    cells = collections.defaultdict(list)
    for p in glob.glob(os.path.join(
            ROOT, "results", "*", "*", "*", "*", "rep*", "result.json")):
        try:
            with open(p) as f:
                d = json.load(f)
        except Exception:
            continue
        rb = d.get("reward_binary")
        if rb not in (0, 1) or d.get("verifier_exit") != 0:
            continue
        rep_dir = os.path.dirname(p)
        if not glob.glob(os.path.join(rep_dir, "session", "*.jsonl")):
            continue
        leaf = os.path.relpath(p, os.path.join(ROOT, "results")).split(os.sep)[0]
        cells[d["task"]].append({
            "rep_dir": rep_dir, "reward": rb, "leaf": leaf,
            "turns": d.get("turns") or 0,
            "timed_out": bool(d.get("agent_timed_out")),
        })
    return cells


def pick_pool(task, cells, rng, qwen_only=False):
    pool_cells = [c for c in cells
                  if not qwen_only or c["leaf"] in QWEN_LEAFS]
    passes = [c for c in pool_cells if c["reward"] == 1]
    fails_clean = [c for c in pool_cells
                   if c["reward"] == 0 and not c["timed_out"]]
    fails_to = [c for c in pool_cells if c["reward"] == 0 and c["timed_out"]]
    if not passes or len(fails_clean) + len(fails_to) < 3:
        return None
    pick = [rng.choice(passes)]
    rng.shuffle(fails_clean)
    rng.shuffle(fails_to)
    pick += (fails_clean + fails_to)[:3]
    # distinct leafs preferred for cross pools
    if not qwen_only:
        seen, dedup = set(), []
        for c in pick[1:]:
            if c["leaf"] not in seen:
                seen.add(c["leaf"])
                dedup.append(c)
        rest = [c for c in pick[1:] if c not in dedup]
        pick = pick[:1] + (dedup + rest)[:3]
    rng.shuffle(pick)
    return pick


def main():
    rng = random.Random(42)
    cells = scan_cells()
    mixed = {t: v for t, v in cells.items()
             if len(v) >= 4 and 0 < sum(c["reward"] for c in v) < len(v)}

    # cross-model tasks: moderate length (median turns <= 130), most leafs first
    def n_leafs(v):
        return len({c["leaf"] for c in v})

    def med_turns(v):
        ts = sorted(c["turns"] for c in v)
        return ts[len(ts) // 2]

    cross_tasks = [t for t, v in mixed.items() if med_turns(v) <= 130]
    cross_tasks.sort(key=lambda t: (-n_leafs(mixed[t]), t))
    qwen_tasks = [t for t, v in mixed.items()
                  if sum(1 for c in v if c["leaf"] in QWEN_LEAFS) >= 4
                  and any(c["leaf"] in QWEN_LEAFS and c["reward"] == 1
                          for c in v)]

    manifest = []
    os.makedirs(OUT, exist_ok=True)
    wanted = [("cross", cross_tasks, 8, False), ("qwen", qwen_tasks, 2, True)]
    for kind, tasks, n_wanted, qwen_only in wanted:
        made = 0
        for task in tasks:
            if made >= n_wanted:
                break
            pool = pick_pool(task, cells[task], rng, qwen_only=qwen_only)
            if not pool:
                continue
            cands = []
            try:
                for c in pool:
                    rendered = render_cell(c["rep_dir"])
                    cands.append({"problem": rendered["problem"],
                                  "trace": rendered["trace"],
                                  "meta": rendered["meta"]})
            except Exception as e:
                print(f"skip {task}: render failed: {e}", file=sys.stderr)
                continue
            problems = {c["problem"] for c in cands}
            if len(problems) != 1:
                print(f"skip {task}: problem text differs across cells",
                      file=sys.stderr)
                continue
            name = f"{kind}-{task}"
            with open(os.path.join(OUT, f"{name}.json"), "w") as f:
                json.dump({"task": task, "kind": kind,
                           "problem": cands[0]["problem"],
                           "candidates": cands}, f, indent=1)
            n_pass = sum(c["meta"]["reward_binary"] for c in cands)
            manifest.append({
                "pool": name, "kind": kind, "n_pass": n_pass,
                "leafs": [c["meta"]["model"] for c in cands],
                "turns": [c["meta"]["turns"] for c in cands],
                "trace_chars": [len(c["trace"]) for c in cands],
            })
            made += 1
    with open(os.path.join(OUT, "manifest.json"), "w") as f:
        json.dump(manifest, f, indent=1)
    print(json.dumps(manifest, indent=1))


if __name__ == "__main__":
    main()
