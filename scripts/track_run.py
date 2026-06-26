#!/usr/bin/env python3
"""Emit a tail-able, one-line-per-cell progress log for a harness run.

Mirrors harness/run_batch.py native stdout style:
    [n/N] task / arm / rep0  status
appended live as each cell's result.json appears. Idempotent across restarts
(only appends lines it hasn't already emitted).

Usage:
    scripts/track_run.py <run-name> [--expected N] [--out FILE] [--interval S]

Auto-detects expected cells as (#tasks) * (#distinct arms in first result.json
batch). Pass --expected to force it (e.g. when the run is mid-flight with no
results yet, or to count all arms up front).

Stop with Ctrl-C or kill the pidfile written next to the .out.

Status legend: ok | empty (no patch) | timeout | transient | exit=<n>
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "harness"))


def status_of(d: dict) -> str:
    if d.get("transient_model_error"):
        return "transient"
    ae, ve = d.get("agent_exit"), d.get("verifier_exit")
    if ae in (0, "0") and ve in (0, "0", "skipped_empty_patch"):
        return "empty" if ve == "skipped_empty_patch" else "ok"
    if ae == "timeout":
        return "timeout"
    return f"exit={ae}"


def expected_cells(run_dir: Path, override: int | None) -> int:
    if override:
        return override
    # layout: runs/<run>/<arm>/<task>/<rep>/result.json
    arms: set[str] = set()
    for p in run_dir.glob("*/*/rep*/result.json"):
        arms.add(p.parts[-4])
    if not arms:
        return 0
    try:
        from run_batch import all_task_ids  # noqa: E402
        n_tasks = len(all_task_ids())
    except Exception:
        return 0
    return n_tasks * len(arms)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("run", help="run name, e.g. qwen-local-om-pilot")
    ap.add_argument("--expected", type=int, default=0, help="force expected cell count")
    ap.add_argument("--out", help="output file (default runs/<run>/track.out)")
    ap.add_argument("--interval", type=float, default=15.0, help="poll seconds (default 15)")
    args = ap.parse_args()

    run_dir = ROOT / "runs" / args.run
    if not run_dir.exists():
        sys.exit(f"run dir not found: {run_dir}")

    out = Path(args.out) if args.out else run_dir / "track.out"
    out.parent.mkdir(parents=True, exist_ok=True)
    pidfile = out.with_suffix(".out.pid")
    pidfile.write_text(str(os.getpid()))

    # recover already-emitted lines so a restart never duplicates
    seen: set[str] = set()
    header_emitted = False
    if out.exists():
        text = out.read_text(errors="replace")
        header_emitted = bool(text.strip())
        seen = {ln for ln in text.splitlines() if ln.startswith("[")}

    expected = expected_cells(run_dir, args.expected or None)
    f = out.open("a")
    try:
        if not header_emitted:
            arm_label = ""
            try:
                arms = sorted({p.parts[-4] for p in run_dir.glob("*/*/rep*/result.json")})
                arm_label = ",".join(arms)
            except Exception:
                pass
            label = f"{arm_label} " if arm_label else ""
            f.write(f"running {expected or '?'} cells: {label}\n".rstrip() + "\n")
            f.flush()
        while True:
            results = sorted(run_dir.glob("*/*/rep*/result.json"), key=lambda p: p.stat().st_mtime)
            done = len(results)
            for i, p in enumerate(results, 1):
                try:
                    d = json.loads(p.read_text())
                except Exception:
                    continue
                arm, task = p.parts[-4], p.parts[-3]
                rep = p.parts[-2].replace("rep", "")
                line = f"[{i}/{expected or done}] {task} / {arm} / rep{rep}  {status_of(d)}"
                if line not in seen:
                    f.write(line + "\n")
                    f.flush()
                    seen.add(line)
            if expected and done >= expected:
                f.write(f"done: {done}/{expected}\n")
                f.flush()
                return 0
            time.sleep(args.interval)
    finally:
        f.close()
        pidfile.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
