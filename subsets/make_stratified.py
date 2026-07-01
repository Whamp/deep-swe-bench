#!/usr/bin/env python3
"""Build arm-independent, nested, stratified DeepSWE subsamples.

Selection uses ONLY task-intrinsic properties: language + cross-model pass-rate
tercile from data/deepswe-v1.1-task-difficulty.tsv. No arm outcomes are ever
consulted, so the resulting subsamples are a neutral substrate for comparing
the very arms they were not selected on (no selection-on-the-dependent-variable
bias).

Produces a nested pair: 12_v2 ⊂ 36_v2  (the full 113 set is subsets/113_v0.txt).

Nesting is guaranteed BY CONSTRUCTION: the 12-task per-cell allocations are
drawn as subsets of the 36-task per-cell allocations (which are subsets of each
cell's full membership). So a 12-task run's cells are a strict prefix of the
36-task run's cells under the same harness --run-name.

Within-cell order is a pure function of the slug (sha256), so the sample is
fully deterministic and reproducible regardless of Python dict ordering.
"""
from __future__ import annotations
import argparse
import csv
import hashlib
import sys
from collections import defaultdict
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
DIFF = REPO / "data" / "deepswe-v1.1-task-difficulty.tsv"
OUT_DIR = REPO / "subsets"

DEFAULT_SEED = "deepswe-v1.1-stratified"


def tercile(pr: int) -> str:
    return "hard" if pr < 33 else ("medium" if pr < 66 else "easy")


def load_tasks() -> list[dict]:
    rows = []
    with open(DIFF) as f:
        for r in csv.DictReader(f, delimiter="\t"):
            rows.append({
                "slug": r["slug"],
                "language": r["language"],
                "repository": r["repository"],
                "title": r["title"],
                "pass_rate": int(r["pass_rate"]),
                "tercile": tercile(int(r["pass_rate"])),
            })
    return rows


def cell_order_key(task: dict, seed: str) -> str:
    """Deterministic within-cell rank: pure function of (seed, slug)."""
    return hashlib.sha256(f"{seed}|{task['slug']}".encode()).hexdigest()


def largest_remainder(quota_by_key: dict, total: int) -> dict:
    """Allocate `total` integer slots proportional to quota values (Hamilton method)."""
    s = float(sum(quota_by_key.values()))
    if s == 0 or total <= 0:
        return {k: 0 for k in quota_by_key}
    alloc, frac = {}, {}
    for k, q in quota_by_key.items():
        exact = total * q / s
        alloc[k] = int(exact)  # floor (values are non-negative)
        frac[k] = exact - alloc[k]
    need = total - sum(alloc.values())
    # hand remaining slots to largest fractions; deterministic tiebreak by key
    for k in sorted(quota_by_key, key=lambda k: (-frac[k], k))[:need]:
        alloc[k] += 1
    return alloc


def select(rows: list[dict], target_n: int, seed: str,
           allowed: set | None = None) -> list[dict]:
    """Stratified selection of target_n tasks across (tercile, language) cells.

    If `allowed` (a set of slugs) is given, picks are restricted to it; this is
    what guarantees nesting (12's pool = the 36 already chosen)."""
    pool = rows if allowed is None else [r for r in rows if r["slug"] in allowed]
    cells: dict[tuple, list[dict]] = defaultdict(list)
    for r in pool:
        cells[(r["tercile"], r["language"])].append(r)
    # deterministic order within cell
    for key in cells:
        cells[key].sort(key=lambda t: cell_order_key(t, seed))
    # per-cell quota = cell membership (so allocation is proportional to cell size)
    quota = {k: len(v) for k, v in cells.items()}
    alloc = largest_remainder(quota, target_n)
    # cap at cell size (safety; redistribute overflow to largest under-full cells)
    for k in list(alloc):
        if alloc[k] > len(cells[k]):
            alloc[k] = len(cells[k])
    picked = []
    for k in sorted(cells):
        picked.extend(cells[k][:alloc[k]])
    return picked


def write_subset(name: str, tasks: list[dict]) -> Path:
    OUT_DIR.mkdir(exist_ok=True)
    # deterministic line order: by pass_rate then slug (hardest first)
    ordered = sorted(tasks, key=lambda t: (t["pass_rate"], t["slug"]))
    path = OUT_DIR / f"{name}.txt"
    with open(path, "w") as f:
        for t in ordered:
            f.write(t["slug"] + "\n")
    return path


def verify_nesting(small: list[dict], big: list[dict], small_name: str, big_name: str):
    s = {t["slug"] for t in small}
    b = {t["slug"] for t in big}
    leak = s - b
    if leak:
        sys.exit(f"NESTING VIOLATION: {small_name} not subset of {big_name}; "
                 f"offending slugs: {sorted(leak)}")


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seed", default=DEFAULT_SEED,
                    help="deterministic seed baked into within-cell ordering")
    ap.add_argument("--small", type=int, default=12)
    ap.add_argument("--large", type=int, default=36)
    ap.add_argument("--small-name", default=None)
    ap.add_argument("--large-name", default=None)
    ap.add_argument("--dry-run", action="store_true",
                    help="print allocation + members, do not write files")
    args = ap.parse_args()

    rows = load_tasks()
    sn = args.small_name or f"{args.small}_v2"
    ln = args.large_name or f"{args.large}_v2"

    large = select(rows, args.large, args.seed)
    small = select(rows, args.small, args.seed, allowed={t["slug"] for t in large})
    verify_nesting(small, large, sn, ln)

    if not args.dry_run:
        p_small = write_subset(sn, small)
        p_large = write_subset(ln, large)
        print(f"wrote {p_small} ({len(small)} tasks)")
        print(f"wrote {p_large} ({len(large)} tasks)")
    print(f"\nnesting OK: {sn} ({len(small)}) ⊂ {ln} ({len(large)}) ⊂ 113")

    for name, tasks in [(sn, small), (ln, large)]:
        print(f"\n=== {name} ({len(tasks)} tasks) ===")
        tert = defaultdict(int)
        lang = defaultdict(int)
        for t in tasks:
            tert[t["tercile"]] += 1
            lang[t["language"]] += 1
        pr = [t["pass_rate"] for t in tasks]
        print(f"  terciles: hard={tert['hard']} medium={tert['medium']} easy={tert['easy']}")
        print(f"  languages: {dict(sorted(lang.items(), key=lambda x:-x[1]))}")
        print(f"  pass_rate: mean={sum(pr)/len(pr):.1f} min={min(pr)} max={max(pr)}")


if __name__ == "__main__":
    main()
