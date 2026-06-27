#!/usr/bin/env python3
"""Run a paired DeepSWE/pi comparison over configs × tasks × reps.

Examples:
  python harness/run_batch.py --configs baseline,ponytail-full --tasks adaptix-name-mapping-aliases --agent-timeout 150
  python harness/run_batch.py --configs baseline,ponytail-full --range 0:10 --workers 2
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
TRANSIENT_EXIT = 75


def all_task_ids() -> list[str]:
    return sorted(p.name for p in TASKS.iterdir() if p.is_dir() and (p / "task.toml").exists())


def parse_range(s: str | None, ids: list[str]) -> list[str]:
    if not s:
        return ids
    a, b = s.split(":", 1)
    return ids[int(a or 0): int(b or len(ids))]


def model_leaf_of(model: str) -> str:
    return model.rstrip("/").split("/")[-1]


def run_one(spec, args):
    task, config, rep = spec
    mleaf = model_leaf_of(args.model)
    result = REPO / "results" / mleaf / args.thinking / config / task / f"rep{rep}" / "result.json"
    if result.exists() and not args.force:
        return {"task": task, "config": config, "rep": rep, "skipped": True, "result": str(result)}
    cmd = [sys.executable, str(HERE / "run.py"), "--config", config, "--task", task,
           "--model", args.model,
           "--thinking", args.thinking, "--rep", str(rep)]
    if args.agent_timeout:
        cmd += ["--agent-timeout", str(args.agent_timeout)]
    if args.pass_openai_codex_oauth:
        cmd += ["--pass-openai-codex-oauth"]
    p = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True)
    logdir = REPO / "results" / mleaf / args.thinking / "logs"
    logdir.mkdir(parents=True, exist_ok=True)
    log = logdir / f"{task}__{config}__rep{rep}.log"
    log.write_text(p.stdout + p.stderr)
    return {"task": task, "config": config, "rep": rep, "exit": p.returncode, "log": str(log)}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--configs", required=True, help="comma list, e.g. baseline,ponytail-full")
    ap.add_argument("--tasks", help="comma list of task ids")
    ap.add_argument("--range", help="range over sorted task ids, e.g. 0:10")
    ap.add_argument("--subset", help="named subset in subsets/<name>.txt (one task id per line)")
    ap.add_argument("--model", default="openrouter/deepseek/deepseek-v4-flash")
    ap.add_argument("--thinking", default="high",
                    choices=["off", "minimal", "low", "medium", "high", "xhigh"])
    ap.add_argument("--runs", type=int, default=1)
    ap.add_argument("--workers", type=int, default=1)
    ap.add_argument("--agent-timeout", type=float)
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--pass-openai-codex-oauth", action="store_true",
                    help="copy only the host openai-codex OAuth entry into each agent container")
    args = ap.parse_args()

    ids = all_task_ids()
    if args.tasks and args.subset:
        ap.error("pass only one of --tasks / --subset")
    if args.tasks:
        ids = [t.strip() for t in args.tasks.split(",") if t.strip()]
    elif args.subset:
        sf = REPO / "subsets" / f"{args.subset}.txt"
        if not sf.exists():
            ap.error(f"subset file not found: {sf}")
        ids = [t.strip() for t in sf.read_text().splitlines() if t.strip()]
    ids = parse_range(args.range, ids)
    configs = [a.strip() for a in args.configs.split(",") if a.strip()]
    specs = [(t, c, r) for t in ids for r in range(args.runs) for c in configs]
    print(f"running {len(specs)} cells: {len(ids)} tasks × {len(configs)} configs × {args.runs} reps; workers={args.workers}", flush=True)

    done = 0
    paused = False
    with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as ex:
        futs = {ex.submit(run_one, s, args): s for s in specs}
        for fut in concurrent.futures.as_completed(futs):
            if fut.cancelled():
                continue
            res = fut.result()
            done += 1
            status = "skip" if res.get("skipped") else ("ok" if res.get("exit") == 0 else f"exit={res.get('exit')}")
            print(f"[{done}/{len(specs)}] {res['task']} / {res['config']} / rep{res['rep']}  {status}", flush=True)
            if res.get("exit") == TRANSIENT_EXIT:
                paused = True
                for other in futs:
                    if other is not fut and not other.done():
                        other.cancel()
                print("[pause] transient model/subscription limit detected; resume this same command after the reset", flush=True)
                break
    if paused:
        raise SystemExit(TRANSIENT_EXIT)


if __name__ == "__main__":
    main()
