#!/usr/bin/env python3
"""Migrate runs/ -> results/ per RENAME-PLAN §19.

The old layout runs/<run>/<arm>/<task>/rep<N>/ drops the run-name axis into the
new results/<model-leaf>/<thinking>/<config>/<task>/rep<N>/ tree (model-leaf is
EXECUTOR-ONLY; +advisor is configs-leaf-only). Reps accumulate under a config
regardless of which subset/run produced them.

Provenance & safety rules (all verified against live data):
  - Walker uses os.walk(followlinks=False) so the 3 symlinked baseline/ dirs
    (-> ponytail-full-pilot-w2/baseline) are NOT double-migrated.
  - (config, model-leaf, thinking) derived from result.json; thinking_level
    missing -> DEFAULT_THINKING=high, logged (never fail-loud).
  - Collision policies (renumber to rep1): advisor-glm52-reliability-rerun
    (40 cells), codex-spark-baseline-sub (36 cells). Any OTHER collision fails
    loud (would silently overwrite).
  - In-file rewrite: arm -> config (§11 map); rep -> effective rep on
    renumbered cells. Post-migrate assertion: rec['rep']==N and rec has 'config'
    matching the path segment (analyze.py keys on in-file task/rep/config).
  - COPY (not move): result.json, verifier/, artifacts/, logs/, session/.
    pi.jsonl is NOT migrated (retired, ADR-0002); runs/ stays intact as fallback.

Usage: python3 scripts/migrate_results.py --dry-run   (report; writes nothing)
       python3 scripts/migrate_results.py             (migrate)
"""
from __future__ import annotations
import argparse, json, os, shutil, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "harness"))
from lib import model_leaf

REPO = Path(__file__).resolve().parent.parent
RUNS = REPO / "runs"
RESULTS = REPO / "results"

ARM_TO_CONFIG = {
    "baseline": "baseline", "baseline-codex": "baseline", "baseline-codex-wf": "baseline-wf",
    "pi-advisor-glm52": "advisor",
    "pi-observational-memory": "observational-memory",
    "pi-observational-memory-codex54mini": "observational-memory",
    "ponytail-full": "ponytail-full", "ponytail-lite": "ponytail-lite",
    "ponytail-pi-extension": "ponytail-extension", "ponytail-ultra": "ponytail-ultra",
}
EXCLUDED_RUNS = {
    "diag", "validate", "validate-fixed",           # throwaways (collide at adaptix)
    "codex54mini-high-wf-sub", "codex54mini-xhigh-wf-sub", "ponytail-full-pilot",  # empty
    "_phase05-validate",                            # phase 0.5 validation cell
}
DEFAULT_THINKING = "high"
# Rep-renumber collision policies: run_name -> rep offset added to base rep.
REP_RENUMBER = {"advisor-glm52-reliability-rerun": 1, "codex-spark-baseline-sub": 1}
COPY_FILES = {"result.json"}
COPY_DIRS = {"verifier", "artifacts", "logs", "session"}
AUDIT = REPO / "migrate-thinking-audit.jsonl"


def iter_cells():
    """Yield (cell_dir, run_name) for every real (non-symlinked) result.json."""
    for root, dirs, files in os.walk(RUNS, followlinks=False):
        if "result.json" in files:
            cell = Path(root)
            run = cell.relative_to(RUNS).parts[0]
            yield cell, run


def derive(cell: Path, run: str):
    """Return (config, mleaf, thinking, task, eff_rep, rj, backfilled_thinking)."""
    rj = json.loads((cell / "result.json").read_text())
    arm = rj.get("arm")
    model = rj.get("model")
    if arm not in ARM_TO_CONFIG:
        raise ValueError(f"unmapped arm {arm!r} in {cell}")
    if not model:
        raise ValueError(f"missing model in {cell}")
    config = ARM_TO_CONFIG[arm]
    mleaf = model_leaf(model)  # executor-only
    thinking = rj.get("thinking_level")
    backfilled = False
    if not thinking:
        thinking = DEFAULT_THINKING
        backfilled = True
    task = rj["task"]
    base_rep = int(rj.get("rep", 0))
    eff_rep = base_rep + REP_RENUMBER.get(run, 0)
    return config, mleaf, thinking, task, eff_rep, rj, backfilled


def dest_for(config, mleaf, thinking, task, eff_rep) -> Path:
    return RESULTS / mleaf / thinking / config / task / f"rep{eff_rep}"


def plan():
    """Collect destinations, detect collisions, count backfills. Returns
    (cells, collisions, backfill_count, by_tuple) where by_tuple maps
    dest->list of source cells."""
    cells = []
    by_tuple = {}
    backfill = 0
    for cell, run in iter_cells():
        if run in EXCLUDED_RUNS:
            continue
        config, mleaf, thinking, task, eff_rep, rj, bf = derive(cell, run)
        if bf:
            backfill += 1
        dst = dest_for(config, mleaf, thinking, task, eff_rep)
        cells.append((cell, dst, config, mleaf, thinking, task, eff_rep, run, bf, rj))
        by_tuple.setdefault(str(dst.relative_to(REPO)), []).append(cell)
    collisions = {k: v for k, v in by_tuple.items() if len(v) > 1}
    return cells, collisions, backfill, by_tuple


def report():
    cells, collisions, backfill, _ = plan()
    # destination breakdown by (config, mleaf, thinking)
    leaves = {}
    for cell, dst, config, mleaf, thinking, task, eff_rep, run, bf, rj in cells:
        leaves.setdefault((config, mleaf, thinking, eff_rep), 0)
        leaves[(config, mleaf, thinking, eff_rep)] += 1
    print(f"=== MIGRATION DRY-RUN ===")
    print(f"cells to migrate: {len(cells)}")
    print(f"thinking backfilled (missing->high): {backfill}")
    print(f"distinct destinations: {len({str(c[1]) for c in cells})}")
    print()
    print(f"{'config':<22}{'model-leaf':<28}{'think':<8}{'rep':<5}{'cells':<6}")
    for (cfg, ml, th, rep), n in sorted(leaves.items()):
        print(f"  {cfg:<20}{ml:<28}{th:<8}rep{rep:<3}{n}")
    print()
    if collisions:
        print(f"!! {len(collisions)} UNRESOLVED COLLISIONS (would fail-loud):")
        for dst, srcs in sorted(collisions.items()):
            print(f"   {dst}:")
            for s in srcs:
                print(f"      <- {s.relative_to(REPO)}")
    else:
        print("collisions: 0 (all covered by renumber policies or unique)")
    renumbered = {r: 0 for r in REP_RENUMBER}
    for cell, dst, config, mleaf, thinking, task, eff_rep, run, bf, rj in cells:
        if run in REP_RENUMBER:
            renumbered[run] += 1
    print()
    print("rep-renumber policy application:")
    for r, n in renumbered.items():
        print(f"  {r}: {n} cells -> rep+1")
    print()
    print(f"(dry-run: nothing written. {len(cells)} cells would migrate.)")


def rewrite_infile(rj: dict, config: str, eff_rep: int, backfilled: bool) -> dict:
    """arm->config, rep->eff_rep; set thinking_level if backfilled. Keeps 'arm'
    removed (analyze reads 'config'); preserves all other fields."""
    rj["config"] = config
    rj.pop("arm", None)
    rj["rep"] = eff_rep
    if backfilled and not rj.get("thinking_level"):
        rj["thinking_level"] = DEFAULT_THINKING
    return rj


def migrate():
    cells, collisions, backfill, _ = plan()
    if collisions:
        sys.exit(f"ABORT: {len(collisions)} unresolved collisions — see --dry-run")
    AUDIT.unlink(missing_ok=True)
    moved = 0
    for cell, dst, config, mleaf, thinking, task, eff_rep, run, bf, rj in cells:
        dst.mkdir(parents=True, exist_ok=True)
        # rewrite result.json in-place content at the destination
        rj2 = rewrite_infile(dict(rj), config, eff_rep, bf)
        (dst / "result.json").write_text(json.dumps(rj2, indent=2))
        if bf:
            with open(AUDIT, "a") as f:
                f.write(json.dumps({"src": str(cell.relative_to(REPO)),
                                    "dst": str(dst.relative_to(REPO))}) + "\n")
        for name in COPY_DIRS:
            src = cell / name
            if src.exists() and not (dst / name).exists():
                try:
                    shutil.copytree(src, dst / name, symlinks=False)
                except Exception as e:
                    print(f"  warn: copy {src} -> {dst/name}: {e}")
        moved += 1
    # post-migrate assertion: rec['rep']==N, rec has 'config' matching path.
    # dst = results/<mleaf>/<thinking>/<config>/<task>/rep<N>
    #   -> dst.name=rep<N>, dst.parent=<task>, dst.parent.parent=<config>
    fails = 0
    for cell, dst, config, mleaf, thinking, task, eff_rep, run, bf, rj in cells:
        rj2 = json.loads((dst / "result.json").read_text())
        rep_in_path = int(dst.name.removeprefix("rep"))
        cfg_in_path = dst.parent.parent.name
        task_in_path = dst.parent.name
        if (rj2.get("rep") != rep_in_path
                or rj2.get("config") != cfg_in_path
                or rj2.get("task") != task_in_path
                or "arm" in rj2):
            fails += 1
            print(f"  ASSERT FAIL: {dst.relative_to(REPO)} "
                  f"rep={rj2.get('rep')} config={rj2.get('config')} task={rj2.get('task')}")
    if fails:
        sys.exit(f"ABORT: {fails} cells failed post-migrate assertion")
    print(f"migrated {moved} cells to results/ (backfilled {backfill} thinking; audit -> {AUDIT.name})")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()
    if args.dry_run:
        report()
    else:
        migrate()


if __name__ == "__main__":
    main()
