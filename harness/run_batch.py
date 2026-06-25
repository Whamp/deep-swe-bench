#!/usr/bin/env python3
"""Run a paired DeepSWE/pi study over arms × tasks × reps.

Examples:
  python harness/run_batch.py --arms baseline,ponytail-full --tasks adaptix-name-mapping-aliases --run-name smoke --agent-timeout 150
  python harness/run_batch.py --arms baseline,ponytail-full --slice 0:10 --run-name ponytail-full-pilot --workers 2
"""
from __future__ import annotations

import argparse
import concurrent.futures
import json
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
TASKS = Path.home() / "evals" / "deep-swe" / "tasks"


def all_task_ids() -> list[str]:
    return sorted(p.name for p in TASKS.iterdir() if p.is_dir() and (p / "task.toml").exists())


def parse_slice(s: str | None, ids: list[str]) -> list[str]:
    if not s:
        return ids
    a, b = s.split(":", 1)
    return ids[int(a or 0): int(b or len(ids))]


def run_one(spec, args):
    task, arm, rep = spec
    result = REPO / "runs" / args.run_name / arm / task / f"rep{rep}" / "result.json"
    if result.exists() and not args.force:
        return {"task": task, "arm": arm, "rep": rep, "skipped": True, "result": str(result)}
    cmd = [sys.executable, str(HERE / "run.py"), "--arm", arm, "--task", task,
           "--run-name", args.run_name, "--model", args.model,
           "--thinking", args.thinking, "--rep", str(rep)]
    if args.agent_timeout:
        cmd += ["--agent-timeout", str(args.agent_timeout)]
    p = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True)
    (REPO / "runs" / args.run_name / "batch-logs").mkdir(parents=True, exist_ok=True)
    log = REPO / "runs" / args.run_name / "batch-logs" / f"{task}__{arm}__rep{rep}.log"
    log.write_text(p.stdout + p.stderr)
    return {"task": task, "arm": arm, "rep": rep, "exit": p.returncode, "log": str(log)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--arms", required=True, help="comma list, e.g. baseline,ponytail-full")
    ap.add_argument("--tasks", help="comma list of task ids")
    ap.add_argument("--slice", help="slice over sorted task ids, e.g. 0:10")
    ap.add_argument("--run-name", required=True)
    ap.add_argument("--model", default="openrouter/deepseek/deepseek-v4-flash")
    ap.add_argument("--thinking", default="high",
                    choices=["off", "minimal", "low", "medium", "high", "xhigh"])
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--agent-timeout", type=float)
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    ids = all_task_ids()
    if args.tasks:
        ids = [t.strip() for t in args.tasks.split(",") if t.strip()]
    ids = parse_slice(args.slice, ids)
    arms = [a.strip() for a in args.arms.split(",") if a.strip()]
    specs = [(t, a, r) for t in ids for r in range(args.runs) for a in arms]
    print(f"running {len(specs)} cells: {len(ids)} tasks × {len(arms)} arms × {args.runs} reps; workers={args.workers}", flush=True)

    done = 0
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(run_one, s, args): s for s in specs}
        for fut in concurrent.futures.as_completed(futs):
            res = fut.result()
            done += 1
            status = "skip" if res.get("skipped") else ("ok" if res.get("exit") == 0 else f"exit={res.get('exit')}")
            print(f"[{done}/{len(specs)}] {res['task']} / {res['arm']} / rep{res['rep']}  {status}", flush=True)


if __name__ == "__main__":
    main()
