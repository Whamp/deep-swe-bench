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
import subprocess
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from harness import quota

try:
    from harness.run_state import (
        RunStateWriter,
        base_manifest,
        default_run_id,
        make_cell,
        sanitize_run_id,
    )
except ModuleNotFoundError:  # ``python harness/run_batch.py`` puts harness/ on sys.path.
    from run_state import (  # type: ignore[no-redef]
        RunStateWriter,
        base_manifest,
        default_run_id,
        make_cell,
        sanitize_run_id,
    )

HERE = Path(__file__).resolve().parent
REPO = HERE.parent
TASKS = Path.home() / "evals" / "deep-swe" / "tasks"
TRANSIENT_EXIT = 75
SMOKE_SUBSET = REPO / "subsets" / "12_v0.txt"
STATE_ROOT = REPO / "results" / "_runs"


def all_task_ids() -> list[str]:
    return sorted(p.name for p in TASKS.iterdir() if p.is_dir() and (p / "task.toml").exists())


def parse_range(s: str | None, ids: list[str]) -> list[str]:
    if not s:
        return ids
    a, b = s.split(":", 1)
    return ids[int(a or 0): int(b or len(ids))]


def model_leaf_of(model: str) -> str:
    return model.rstrip("/").split("/")[-1]


def repo_rel(path: Path | None) -> str | None:
    if path is None:
        return None
    try:
        return str(path.relative_to(REPO))
    except ValueError:
        return str(path)


def result_path(model: str, thinking: str, config: str, task: str, rep: int) -> Path:
    return REPO / "results" / model_leaf_of(model) / thinking / config / task / f"rep{rep}" / "result.json"


def log_path(model: str, thinking: str, config: str, task: str, rep: int) -> Path:
    return REPO / "results" / model_leaf_of(model) / thinking / "logs" / f"{task}__{config}__rep{rep}.log"


def config_has_results(model: str, thinking: str, config: str) -> bool:
    base = REPO / "results" / model_leaf_of(model) / thinking / config
    return base.exists() and any(base.glob("*/rep*/result.json"))


def smoke_task(requested_ids: list[str]) -> str:
    """Pick a reusable smoke task from the requested batch.

    Prefer the stable 12_v0 smoke subset when it overlaps the requested tasks;
    otherwise use the first requested task so subset-specific launches do not
    create throwaway cells outside the comparison.
    """
    smoke_ids = [t.strip() for t in SMOKE_SUBSET.read_text().splitlines() if t.strip()]
    requested = set(requested_ids)
    for task in smoke_ids:
        if task in requested:
            return task
    if requested_ids:
        return requested_ids[0]
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
    runner_log = path.parent / "logs" / "pi-rpc-runner.jsonl"
    if not runner_log.exists():
        errors.append("RPC runner log missing")
    else:
        runner_text = runner_log.read_text(errors="replace")
        if '"event":"prompt_sent"' not in runner_text:
            errors.append("RPC runner prompt_sent event missing")
        if '"event":"quiescent"' not in runner_text:
            errors.append("RPC runner quiescent event missing")
        if '"transport":"rpc"' not in runner_text:
            errors.append("RPC runner transport=rpc evidence missing")
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
    result = result_path(args.model, args.thinking, config, task, rep)
    log = log_path(args.model, args.thinking, config, task, rep)
    if result.exists() and not args.force:
        return {"task": task, "config": config, "rep": rep, "skipped": True, "result": str(result), "log": str(log)}
    cmd = [sys.executable, str(HERE / "run.py"), "--config", config, "--task", task,
           "--model", args.model,
           "--thinking", args.thinking, "--rep", str(rep)]
    if args.agent_timeout:
        cmd += ["--agent-timeout", str(args.agent_timeout)]
    rpc_quiescence = getattr(args, "rpc_quiescence", None)
    if rpc_quiescence is not None:
        cmd += ["--rpc-quiescence", str(rpc_quiescence)]
    if args.pass_openai_codex_oauth:
        cmd += ["--pass-openai-codex-oauth"]
    p = subprocess.run(cmd, cwd=str(REPO), capture_output=True, text=True)
    log.parent.mkdir(parents=True, exist_ok=True)
    log.write_text(p.stdout + p.stderr)
    return {"task": task, "config": config, "rep": rep, "exit": p.returncode, "result": str(result), "log": str(log)}


def batch_cell_for_spec(spec, args) -> dict:
    task, config, rep = spec
    return make_cell(
        task=task,
        config=config,
        rep=rep,
        result_path=repo_rel(result_path(args.model, args.thinking, config, task, rep)),
        log_path=repo_rel(log_path(args.model, args.thinking, config, task, rep)),
    )


def run_one_with_state(spec, args, state: RunStateWriter, cell: dict):
    task, config, rep = spec
    result = result_path(args.model, args.thinking, config, task, rep)
    if result.exists() and not args.force:
        skipped_cell = dict(cell)
        skipped_cell["result_path"] = str(result)
        skipped_cell["log_path"] = str(log_path(args.model, args.thinking, config, task, rep))
        state.cell_skipped(skipped_cell, reason="existing_result")
        return run_one(spec, args)
    state.cell_started(cell)
    try:
        res = run_one(spec, args)
    except BaseException:
        state.cell_finished(cell, exit_code="exception")
        raise
    state.cell_finished(
        cell,
        result_path=res.get("result"),
        log_path=res.get("log"),
        exit_code=res.get("exit"),
        transient_exit=TRANSIENT_EXIT,
    )
    return res


def selection_metadata(args, ids: list[str]) -> dict:
    if args.subset:
        mode = "subset"
    elif args.tasks:
        mode = "tasks"
    elif args.range:
        mode = "range"
    else:
        mode = "all"
    data = {"mode": mode, "tasks": ids}
    if args.subset:
        data["subset"] = args.subset
    if args.range:
        data["range"] = args.range
    return data


def preflight_plan(args, configs: list[str], ids: list[str]) -> list[dict]:
    decisions = []
    needs_smoke = False
    for config in configs:
        if args.no_smoke_new_configs:
            decision = {"config": config, "run": False, "reason": "disabled"}
        elif config_has_results(args.model, args.thinking, config):
            decision = {"config": config, "run": False, "reason": "existing_results"}
        else:
            decision = {"config": config, "run": True, "reason": None}
            needs_smoke = True
        decisions.append(decision)

    task = smoke_task(ids) if needs_smoke else (ids[0] if ids else "preflight")
    plan = []
    for decision in decisions:
        config = decision["config"]
        contract = smoke_contract_path(args.model, args.thinking, config)
        cell = make_cell(
            task=task,
            config=config,
            rep=0,
            result_path=repo_rel(result_path(args.model, args.thinking, config, task, 0)),
            log_path=repo_rel(log_path(args.model, args.thinking, config, task, 0)),
            contract_path=repo_rel(contract),
        )
        plan.append({"cell": cell, "run": decision["run"], "reason": decision["reason"]})
    return plan


RESULTS_ROOT = REPO / "results"


def _latest_transient_error_msg() -> str | None:
    """Read ``transient_model_error`` from the most recently written sentinel."""
    try:
        files = sorted(
            RESULTS_ROOT.rglob("transient_error.json"),
            key=lambda p: p.stat().st_mtime,
            reverse=True,
        )
    except OSError:
        return None
    for f in files:
        try:
            data = json.loads(f.read_text())
        except (json.JSONDecodeError, OSError):
            continue
        msg = data.get("transient_model_error")
        if msg:
            return str(msg)
    return None


class QuotaResumer:
    """Decide whether to wait for a subscription quota reset and resume the batch.

    On a transient (exit 75) pause, this inspects the underlying error, queries
    the provider usage API (via :mod:`harness.quota`) for the reset time, sleeps
    until the window resets, then tells the caller to re-launch the batch. Cells
    with completed ``result.json`` are skipped on re-launch, so only the
    interrupted work re-runs.
    """

    def __init__(self, args):
        self.args = args
        self.attempt = 0

    def on_transient_pause(self, state) -> dict:
        """Inspect the pause and optionally block until the quota resets.

        Returns ``{"retry": bool, "reason": str}``. When ``retry`` is true the
        caller re-launches the batch; otherwise it exits 75.
        """
        self.attempt += 1
        msg = _latest_transient_error_msg()
        kind = quota.classify_transient(msg)

        if kind == "rate_limit":
            backoff = self.args.rate_limit_backoff_s
            print(f"[resume] rate-limit transient ({msg!r}); backing off {backoff:.0f}s", flush=True)
            time.sleep(backoff)
            return {"retry": True, "reason": f"rate-limit backoff {backoff:.0f}s"}

        if kind == "quota":
            return self._wait_for_quota_reset(state, msg)

        reason = f"unclassified transient (cannot auto-resume): {msg!r}"
        print(f"[resume] {reason}", flush=True)
        return {"retry": False, "reason": reason}

    def _wait_for_quota_reset(self, state, msg) -> dict:
        windows, source = quota.codex_windows(self.args.model)
        if not windows:
            reason = f"quota limit but no usage data available (source={source}): {msg!r}"
            print(f"[resume] {reason}", flush=True)
            return {"retry": False, "reason": reason}

        now = datetime.now(timezone.utc)
        reset = quota.next_reset(windows)
        desc = quota.describe_pause(windows, now=now)

        if not quota.exhausted_windows(windows):
            # Quota is already available (manual reset, or the window rolled over
            # between the pause firing and this check). Resume immediately instead
            # of polling. Without this guard, next_reset()==None makes wait_seconds
            # return None, which the ``wait is None`` branch below misreads as
            # "reset time unknown" and pointlessly polls for quota_poll_s.
            print(f"[resume] quota no longer exhausted ({desc}); resuming immediately "
                  f"[attempt {self.attempt}]", flush=True)
            return {"retry": True, "reason": f"quota available ({desc})"}

        wait = quota.wait_seconds(reset, now=now)

        if wait is None:
            # Exhausted but reset time unknown: poll and retry so a later check catches it.
            poll = self.args.quota_poll_s
            print(f"[resume] quota exhausted ({desc}) but reset time unknown; polling every {poll:.0f}s", flush=True)
            state.set_stage("quota_wait")
            time.sleep(poll)
            return {"retry": True, "reason": f"quota unknown-reset poll {poll:.0f}s ({desc})"}

        if wait > self.args.max_quota_wait_s:
            reason = (f"quota reset too far away ({desc}); {wait:.0f}s exceeds max "
                      f"{self.args.max_quota_wait_s:.0f}s — resume manually after the reset")
            print(f"[resume] {reason}", flush=True)
            return {"retry": False, "reason": reason}

        state.set_stage("quota_wait")
        print(f"[resume] quota exhausted ({desc}); sleeping ~{wait:.0f}s until reset, then resuming "
              f"[attempt {self.attempt}]", flush=True)
        self._sleep_until_reset(reset)
        return {"retry": True, "reason": f"quota reset waited ({desc})"}

    def _sleep_until_reset(self, reset: datetime) -> None:
        """Sleep in chunks, re-checking the API so early resets or status changes surface."""
        deadline = reset + timedelta(seconds=60)  # small safety buffer
        poll = self.args.quota_poll_s
        while True:
            now = datetime.now(timezone.utc)
            remaining = (deadline - now).total_seconds()
            if remaining <= 0:
                break
            chunk = min(remaining, poll)
            mins = int(remaining // 60)
            print(f"[resume] waiting for quota reset: {mins}m remaining (re-check in {int(chunk)}s)", flush=True)
            time.sleep(chunk)
            # Re-check: the window may reset early or the plan may change.
            windows, _ = quota.codex_windows(self.args.model)
            if not quota.exhausted_windows(windows):
                print("[resume] quota windows no longer exhausted; resuming early", flush=True)
                break


def _execute_batch(args, state, configs, ids, specs, batch_cells_by_spec, smoke_plan):
    """Run smoke preflight + batch cells once. Returns a process exit code.

    0 = all scheduled cells finished; TRANSIENT_EXIT (75) = paused on a
    transient model/subscription limit; anything else = a hard failure whose
    state transition was already recorded here.
    """
    paused = False
    try:
        if smoke_plan:
            state.set_stage("preflight")
        for item in smoke_plan:
            config = item["cell"]["config"]
            task = item["cell"]["task"]
            if not item["run"]:
                state.preflight_skipped(item["cell"], reason=item["reason"] or "skipped")
                continue
            print(f"[smoke] {config} has no existing results for {model_leaf_of(args.model)}/{args.thinking}; "
                  f"running {task}/rep0 before batch fan-out", flush=True)
            state.preflight_started(item["cell"])
            res = run_one((task, config, 0), args)
            status = "ok" if res.get("exit") == 0 else f"exit={res.get('exit')}"
            print(f"[smoke] {task} / {config} / rep0  {status}", flush=True)
            state.preflight_finished(
                item["cell"],
                result_path=res.get("result"),
                log_path=res.get("log"),
                exit_code=res.get("exit"),
                transient_exit=TRANSIENT_EXIT,
            )
            if res.get("exit") == TRANSIENT_EXIT:
                state.run_paused(reason="transient model/subscription limit during preflight")
                return TRANSIENT_EXIT
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

        print(f"running {len(specs)} cells: {len(ids)} tasks × {len(configs)} configs × {args.runs} reps; workers={args.workers}", flush=True)
        state.set_stage("batch")

        done = 0
        with concurrent.futures.ThreadPoolExecutor(max_workers=args.workers) as ex:
            futs = {
                ex.submit(run_one_with_state, s, args, state, batch_cells_by_spec[s]): s
                for s in specs
            }
            for fut in concurrent.futures.as_completed(futs):
                if fut.cancelled():
                    continue
                res = fut.result()
                done += 1
                status = "skip" if res.get("skipped") else ("ok" if res.get("exit") == 0 else f"exit={res.get('exit')}")
                print(f"[{done}/{len(specs)}] {res['task']} / {res['config']} / rep{res['rep']}  {status}", flush=True)
                if res.get("exit") == TRANSIENT_EXIT:
                    paused = True
                    state.run_paused(reason="transient model/subscription limit detected")
                    for other in futs:
                        if other is not fut and not other.done():
                            other.cancel()
                    print("[pause] transient model/subscription limit detected; "
                          "waiting for the window reset before auto-resume", flush=True)
                    break
        if paused:
            return TRANSIENT_EXIT
        return 0
    except SystemExit as exc:
        code = exc.code
        if code == TRANSIENT_EXIT and not paused:
            state.run_paused(reason="transient model/subscription limit detected")
            return TRANSIENT_EXIT
        state.run_failed(reason=str(code), exit_code=code)
        return code if isinstance(code, int) else 1
    except BaseException as exc:
        state.run_failed(reason=repr(exc))
        return 1


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
    ap.add_argument("--rpc-quiescence", type=float,
                    help="seconds Pi RPC must remain idle with no pending messages before each cell stops")
    ap.add_argument("--run-id", help="structured state id under results/_runs/<run-id> (auto-generated by default)")
    ap.add_argument("--progress-interval", type=float, default=15.0,
                    help="seconds between structured status heartbeats (default 15; <=0 disables heartbeat thread)")
    ap.add_argument("--force", action="store_true")
    ap.add_argument("--pass-openai-codex-oauth", action="store_true",
                    help="copy only the host openai-codex OAuth entry into each agent container")
    ap.add_argument("--no-smoke-new-configs", action="store_true",
                    help="skip the one-cell 12_v0 smoke gate for configs with no existing results")
    ap.add_argument("--no-auto-resume", action="store_true",
                    help="disable automatic wait-and-resume on subscription quota limits; "
                         "exit 75 immediately like the old behavior")
    ap.add_argument("--max-quota-wait", type=float, default=21600.0, dest="max_quota_wait_s",
                    help="max seconds to sleep waiting for a quota window to reset before giving up (default 21600 = 6h)")
    ap.add_argument("--quota-poll", type=float, default=300.0, dest="quota_poll_s",
                    help="seconds between quota re-checks while waiting for a reset (default 300 = 5m)")
    ap.add_argument("--rate-limit-backoff", type=float, default=60.0, dest="rate_limit_backoff_s",
                    help="seconds to back off before retrying after a short rate-limit transient (default 60)")
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
    batch_cells_by_spec = {spec: batch_cell_for_spec(spec, args) for spec in specs}
    smoke_plan = preflight_plan(args, configs, ids)
    run_id = args.run_id or default_run_id()
    try:
        sanitize_run_id(run_id)
    except ValueError as exc:
        ap.error(str(exc))
    manifest = base_manifest(
        run_id=run_id,
        command=[sys.executable, str(Path(__file__)), *sys.argv[1:]],
        cwd=REPO,
        model=args.model,
        thinking=args.thinking,
        configs=configs,
        selection=selection_metadata(args, ids),
        runs=args.runs,
        workers=args.workers,
        agent_timeout_s=args.agent_timeout,
        rpc_quiescence_s=args.rpc_quiescence,
        progress_interval_s=args.progress_interval,
        batch_cells=list(batch_cells_by_spec.values()),
        preflight=[item["cell"] | {"reason": item.get("reason")} for item in smoke_plan],
    )
    state = RunStateWriter(STATE_ROOT, manifest)
    state.start()
    state.start_heartbeat(args.progress_interval)
    try:
        resumer = QuotaResumer(args)
        while True:
            code = _execute_batch(args, state, configs, ids, specs, batch_cells_by_spec, smoke_plan)
            if code == TRANSIENT_EXIT and not args.no_auto_resume:
                decision = resumer.on_transient_pause(state)
                if decision.get("retry"):
                    print(f"[resume] re-launching batch (attempt {resumer.attempt})", flush=True)
                    continue
                print(f"[resume] not auto-resuming: {decision.get('reason')}", flush=True)
            break
        if code == 0:
            state.run_completed()
            return
        raise SystemExit(code if isinstance(code, int) else 1)
    finally:
        state.stop_heartbeat()


if __name__ == "__main__":
    main()
