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
SMOKE_SUBSET = REPO / "subsets" / "12_v0.txt"


def all_task_ids() -> list[str]:
    return sorted(p.name for p in TASKS.iterdir() if p.is_dir() and (p / "task.toml").exists())


def parse_range(s: str | None, ids: list[str]) -> list[str]:
    if not s:
        return ids
    a, b = s.split(":", 1)
    return ids[int(a or 0): int(b or len(ids))]


def model_leaf_of(model: str) -> str:
    return model.rstrip("/").split("/")[-1]


def result_path(model: str, thinking: str, config: str, task: str, rep: int) -> Path:
    return REPO / "results" / model_leaf_of(model) / thinking / config / task / f"rep{rep}" / "result.json"


def config_has_results(model: str, thinking: str, config: str) -> bool:
    base = REPO / "results" / model_leaf_of(model) / thinking / config
    return base.exists() and any(base.glob("*/rep*/result.json"))


def smoke_task(requested_ids: list[str]) -> str:
    smoke_ids = [t.strip() for t in SMOKE_SUBSET.read_text().splitlines() if t.strip()]
    requested = set(requested_ids)
    for task in smoke_ids:
        if task in requested:
            return task
    return smoke_ids[0]


def smoke_contract_path(model: str, thinking: str, config: str) -> Path | None:
    """Return an optional config-authored smoke contract.

    Contracts are intentionally generic. A new skill/extension can define what
    "working" means without teaching run_batch.py about that feature.
    Leaf-local smoke.json wins over config-level smoke.json.
    """
    cfg_dir = REPO / "configs" / config
    leaf = model_leaf_of(model)
    candidates = sorted(p for p in cfg_dir.glob(f"{leaf}*/{thinking}/smoke.json") if p.is_file())
    if candidates:
        return candidates[0]
    p = cfg_dir / "smoke.json"
    return p if p.is_file() else None


def _result_value(rec: dict, dotted_key: str):
    cur = rec
    for part in dotted_key.split("."):
        if not isinstance(cur, dict) or part not in cur:
            return None
        cur = cur[part]
    return cur


def _cell_text(cell: Path, globs: list[str]) -> str:
    chunks = []
    for pattern in globs:
        for p in cell.glob(pattern):
            if p.is_file():
                chunks.append(p.read_text(errors="replace"))
    return "\n".join(chunks)


def validate_smoke_result(path: Path, contract_path: Path | None = None) -> list[str]:
    """Return smoke-check errors.

    Default checks only prove the harness produced a normal cell. Feature-specific
    expectations belong in optional smoke.json files so future skills/extensions
    can state their own success signals.
    """
    if not path.exists():
        return [f"smoke result missing: {path}"]
    rec = json.loads(path.read_text())
    errors: list[str] = []
    if rec.get("agent_exit") != 0:
        errors.append(f"agent_exit is {rec.get('agent_exit')!r}, expected 0")
    if rec.get("agent_timed_out"):
        errors.append("agent_timed_out is true")
    if (rec.get("total_tokens") or 0) <= 0:
        errors.append("total_tokens is 0/missing")
    if not (path.parent / "session").exists() or not list((path.parent / "session").glob("*.jsonl")):
        errors.append("session jsonl missing")
    if not contract_path:
        return errors

    contract = json.loads(contract_path.read_text())
    cell = path.parent
    for key, minimum in (contract.get("minResultValues") or {}).items():
        value = _result_value(rec, key)
        if value is None or value < minimum:
            errors.append(f"result {key}={value!r}, expected >= {minimum!r}")
    for key, expected in (contract.get("equalsResultValues") or {}).items():
        value = _result_value(rec, key)
        if value != expected:
            errors.append(f"result {key}={value!r}, expected {expected!r}")
    for pattern in contract.get("requireFiles") or []:
        if not list(cell.glob(pattern)):
            errors.append(f"required file/glob missing: {pattern}")
    for pattern in contract.get("requireRepoFiles") or []:
        if not list(REPO.glob(pattern)):
            errors.append(f"required repo file/glob missing: {pattern}")
    text_cache: dict[tuple[str, ...], str] = {}
    for check in contract.get("requireText") or []:
        globs = tuple(check.get("globs") or [])
        text = text_cache.setdefault(globs, _cell_text(cell, list(globs)))
        needle = check.get("text", "")
        if needle not in text:
            errors.append(f"required text not found in {list(globs)}: {needle!r}")
    for check in contract.get("requireRepoText") or []:
        globs = tuple(check.get("globs") or [])
        text = text_cache.setdefault(("repo", *globs), _cell_text(REPO, list(globs)))
        needle = check.get("text", "")
        if needle not in text:
            errors.append(f"required repo text not found in {list(globs)}: {needle!r}")
    for check in contract.get("forbidText") or []:
        globs = tuple(check.get("globs") or [])
        text = text_cache.setdefault(globs, _cell_text(cell, list(globs)))
        needle = check.get("text", "")
        if needle and needle in text:
            errors.append(f"forbidden text found in {list(globs)}: {needle!r}")
    for check in contract.get("forbidRepoText") or []:
        globs = tuple(check.get("globs") or [])
        text = text_cache.setdefault(("repo", *globs), _cell_text(REPO, list(globs)))
        needle = check.get("text", "")
        if needle and needle in text:
            errors.append(f"forbidden repo text found in {list(globs)}: {needle!r}")
    return errors


def run_one(spec, args):
    task, config, rep = spec
    mleaf = model_leaf_of(args.model)
    result = result_path(args.model, args.thinking, config, task, rep)
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
    ap.add_argument("--no-smoke-new-configs", action="store_true",
                    help="skip the one-cell 12_v0 smoke gate for configs with no existing results")
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

    if not args.no_smoke_new_configs:
        for config in configs:
            if config_has_results(args.model, args.thinking, config):
                continue
            task = smoke_task(ids)
            print(f"[smoke] {config} has no existing results for {model_leaf_of(args.model)}/{args.thinking}; "
                  f"running {task}/rep0 before batch fan-out", flush=True)
            res = run_one((task, config, 0), args)
            status = "ok" if res.get("exit") == 0 else f"exit={res.get('exit')}"
            print(f"[smoke] {task} / {config} / rep0  {status}", flush=True)
            if res.get("exit") == TRANSIENT_EXIT:
                raise SystemExit(TRANSIENT_EXIT)
            if res.get("exit") != 0:
                raise SystemExit(f"[smoke] failed for {config}; see {res.get('log')}")
            smoke_result = result_path(args.model, args.thinking, config, task, 0)
            contract = smoke_contract_path(args.model, args.thinking, config)
            if contract:
                print(f"[smoke] using contract {contract.relative_to(REPO)}", flush=True)
            health_errors = validate_smoke_result(smoke_result, contract)
            if health_errors:
                joined = "\n  - ".join(health_errors)
                raise SystemExit(f"[smoke] extension health check failed for {config}:\n  - {joined}")

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
