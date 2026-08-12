#!/usr/bin/env python3
"""Serve the deep-swe-bench dashboard JSON API.

The frontend is a React+Vite SPA in dashboard/. This server provides:
  GET /api/runs              — list all discovered runs (structured + legacy)
  GET /api/runs/<id>         — detailed projection of a single run
  GET /api/runs/<id>/events  — events.ndjson tail
  GET /api/compare           — aggregated cross-run benchmark metrics for charts
  GET /api/subsets           — list available task subsets
  GET /api/cell-trajectory   — paginated full trajectory for one result cell
  GET /api/file?path=&tail=  — tail a file from the repo (allowlisted)

Usage:
    python3 scripts/run_dashboard.py --host 0.0.0.0 --port 8789
"""

from __future__ import annotations

import argparse
import json
import math
import statistics
import sys
import urllib.parse
from http import HTTPStatus
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from harness.cell_trajectory import build_cell_trajectory_page
from harness.run_state import (
    DETAIL_LEVELS,
    RunStateWriter,
    discover_runs,
    load_json,
    parse_timestamp,
    project_legacy_track,
    project_structured_run,
    read_events,
    sanitize_run_id,
)

DEFAULT_STATE_ROOT = ROOT / "results" / "_runs"
DEFAULT_LEGACY_ROOT = ROOT / "runs"
DEFAULT_RESULTS_ROOT = ROOT / "results"
DEFAULT_SUBSETS_ROOT = ROOT / "subsets"
DIFFICULTY_TSV = ROOT / "data" / "deepswe-v1.1-task-difficulty.tsv"


# ---------------------------------------------------------------------------
# Run discovery (existing API)
# ---------------------------------------------------------------------------


def _launch_plan_structured_state_target(
    wrapper_dir: Path,
    state_root: Path,
) -> Path | None:
    """Return a wrapper's declared structured state when it is safe and attributable."""
    plan = load_json(wrapper_dir / "launch-plan.json") or {}
    plan_run_id = plan.get("runId")
    raw_paths = plan.get("paths")
    paths = raw_paths if isinstance(raw_paths, dict) else {}
    raw_state_path = paths.get("statePath")
    if not isinstance(plan_run_id, str) or not plan_run_id:
        return None
    if not isinstance(raw_state_path, str) or not raw_state_path:
        return None
    candidate = Path(raw_state_path)
    if not candidate.is_absolute():
        return None
    try:
        resolved = candidate.resolve()
        resolved.relative_to(state_root.resolve().parent)
    except (OSError, ValueError):
        return None
    manifest = load_json(resolved / "manifest.json")
    if not manifest or manifest.get("run_id") != plan_run_id:
        return None
    return resolved


def resolve_dashboard_run_state_dir(
    run_id: str,
    state_root: str | Path = DEFAULT_STATE_ROOT,
) -> Path:
    """Resolve a dashboard run ID or immutable run key to its structured state."""
    safe_id = sanitize_run_id(run_id)
    root = Path(state_root)
    direct_dir = root / safe_id
    if direct_dir.is_dir():
        if any((direct_dir / name).exists() for name in ("manifest.json", "status.json")):
            return direct_dir
        target = _launch_plan_structured_state_target(direct_dir, root)
        return target if target is not None else direct_dir

    if root.is_dir():
        for wrapper_dir in root.iterdir():
            if not wrapper_dir.is_dir():
                continue
            target = _launch_plan_structured_state_target(wrapper_dir, root)
            if target is None:
                continue
            manifest = load_json(target / "manifest.json") or {}
            if manifest.get("run_key") == run_id:
                return target
    return direct_dir


def load_dashboard_runs(
    state_root: str | Path = DEFAULT_STATE_ROOT,
    *,
    detail: str = "summary",
    include_legacy: bool = True,
    legacy_root: str | Path | None = DEFAULT_LEGACY_ROOT,
) -> list[dict[str, Any]]:
    rows = discover_runs(
        state_root,
        detail=detail,
        include_legacy=include_legacy,
        legacy_root=legacy_root,
    )
    known_ids = {str(row.get("run_id") or "") for row in rows}
    root = Path(state_root)
    if root.is_dir():
        for wrapper_dir in sorted(root.iterdir()):
            if not wrapper_dir.is_dir() or wrapper_dir.name in known_ids:
                continue
            try:
                resolved = resolve_dashboard_run_state_dir(wrapper_dir.name, root)
            except ValueError:
                continue
            if resolved != wrapper_dir:
                rows.append(project_structured_run(resolved, detail=detail))
    rows.sort(
        key=lambda row: row.get("updated_at") or row.get("created_at") or "",
        reverse=True,
    )
    return rows


def load_dashboard_run(
    run_id: str,
    state_root: str | Path = DEFAULT_STATE_ROOT,
    *,
    detail: str = "operational",
    legacy_root: str | Path | None = DEFAULT_LEGACY_ROOT,
    repo_root: Path = ROOT,
) -> dict[str, Any] | None:
    if detail not in DETAIL_LEVELS:
        detail = "summary"
    if run_id.startswith("legacy-"):
        legacy_name = run_id.removeprefix("legacy-")
        if not legacy_name or "/" in legacy_name or "\\" in legacy_name:
            return None
        root = Path(legacy_root) if legacy_root is not None else DEFAULT_LEGACY_ROOT
        track = root / legacy_name / "track.out"
        if not track.exists():
            return None
        return project_legacy_track(track, detail=detail)
    try:
        run_dir = resolve_dashboard_run_state_dir(run_id, state_root)
    except ValueError:
        return None
    if not run_dir.exists():
        return None
    run = project_structured_run(run_dir, detail=detail)
    if detail != "summary":
        _attach_finished_cell_session_metrics(
            run,
            repo_root=repo_root,
            state_root=Path(state_root),
        )
    return run


def _attach_finished_cell_session_metrics(
    run: dict[str, Any],
    *,
    repo_root: Path,
    state_root: Path,
) -> None:
    """Add compact transcript-derived tool telemetry to finished cell summaries."""
    for cell in run.get("finished_cells") or []:
        session = load_cell_session(
            str(cell.get("result_path") or ""),
            tail_turns=1,
            repo_root=repo_root,
            state_root=state_root,
        )
        if not session.get("found"):
            continue
        summary = cell.get("summary")
        if not isinstance(summary, dict):
            summary = {}
            cell["summary"] = summary
        for key in ("tool_calls", "tool_call_errors", "tool_call_error_rate"):
            summary[key] = session.get(key)


# ---------------------------------------------------------------------------
# Comparison data (new /api/compare endpoint)
# ---------------------------------------------------------------------------


def load_subsets(subsets_dir: Path = DEFAULT_SUBSETS_ROOT) -> list[dict[str, Any]]:
    """List available task subsets (.txt files, one task slug per line)."""
    out: list[dict[str, Any]] = []
    if not subsets_dir.is_dir():
        return out
    for txt in sorted(subsets_dir.glob("*.txt")):
        try:
            tasks = [t.strip() for t in txt.read_text().splitlines() if t.strip()]
        except OSError:
            continue
        out.append({"name": txt.stem, "task_count": len(tasks), "tasks": tasks})
    return out


def load_subset_tasks(path: Path) -> set[str] | None:
    """Load a subset file into a set of task slugs, or None if unreadable."""
    try:
        return {t.strip() for t in path.read_text().splitlines() if t.strip()}
    except OSError:
        return None


def _load_difficulty_map() -> dict[str, dict[str, str]]:
    """Load task slug -> {pass_rate, language} from the difficulty TSV."""
    mapping: dict[str, dict[str, str]] = {}
    if not DIFFICULTY_TSV.exists():
        return mapping
    try:
        lines = DIFFICULTY_TSV.read_text().splitlines()
        for line in lines[1:]:  # skip header
            parts = line.split("\t")
            if len(parts) < 5:
                continue
            pass_rate, language, slug = parts[0], parts[1], parts[2]
            mapping[slug] = {"pass_rate": pass_rate, "language": language}
    except OSError:
        pass
    return mapping


def _difficulty_bucket(pass_rate_str: str) -> str:
    try:
        pr = float(pass_rate_str)
    except (ValueError, TypeError):
        return "unknown"
    if pr < 33:
        return "hard"
    if pr < 66:
        return "medium"
    return "easy"


def _median(values: list[float]) -> float:
    valid = [v for v in values if v is not None and isinstance(v, (int, float))]
    if not valid:
        return 0.0
    return float(statistics.median(valid))


def _mean(values: list[float]) -> float:
    valid = [v for v in values if v is not None and isinstance(v, (int, float))]
    if not valid:
        return 0.0
    return float(statistics.fmean(valid))


def _rep_from_parts(parts: tuple[str, ...]) -> int:
    """Best-effort integer rep number from a result path (e.g. 'rep2' -> 2)."""
    raw = parts[-2]
    digits = "".join(ch for ch in raw if ch.isdigit())
    try:
        return int(digits) if digits else 0
    except ValueError:
        return 0


def load_comparison_data(
    results_root: str | Path = DEFAULT_RESULTS_ROOT,
    *,
    subset_tasks: set[str] | None = None,
    max_reps: int | None = None,
) -> list[dict[str, Any]]:
    """Scan results/ for result.json files and aggregate by model/thinking/config path.

    Args:
        results_root: Directory containing <model>/<thinking>/<config>/<task>/<rep>/result.json.
        subset_tasks: If set, only include cells whose task slug is in this set.
        max_reps: If set, keep at most this many lowest-numbered reps per task per config.

    Returns a list of comparison run dicts with per-cell data and aggregates.
    """
    results_root = Path(results_root)
    difficulty = _load_difficulty_map()

    # Collect all result.json files, grouped by the path model/thinking/config
    groups: dict[str, list[dict[str, Any]]] = {}
    # Segment the canonical layout so config directories projected from benchmark
    # worktrees are entered; Path.rglob() skips directory symlinks.
    for result_file in results_root.glob("*/*/*/*/*/result.json"):
        # Skip contaminated runs
        if "_contaminated" in result_file.parts:
            continue
        try:
            data = json.loads(result_file.read_text())
        except (OSError, json.JSONDecodeError):
            continue
        # Determine the group key from path: results/<model>/<thinking>/<config>/...
        parts = result_file.relative_to(results_root).parts
        if len(parts) < 5:  # need at least model/thinking/config/task/rep/result.json
            continue
        model, thinking, config = parts[0], parts[1], parts[2]
        task = data.get("task") or parts[-3]
        # Subset filter: only keep cells whose task is in the chosen subset
        if subset_tasks is not None and task not in subset_tasks:
            continue
        data["_group_key"] = f"{model}/{thinking}/{config}"
        data["_model"] = model
        data["_thinking"] = thinking
        data["_config"] = config
        data["_task"] = task
        data["_rep"] = (
            data.get("rep")
            if isinstance(data.get("rep"), int)
            else _rep_from_parts(parts)
        )
        data["_result_path"] = str(result_file.absolute())
        groups.setdefault(data["_group_key"], []).append(data)

    runs: list[dict[str, Any]] = []
    for group_key, cells_raw in sorted(groups.items()):
        if not cells_raw:
            continue
        # Optional rep cap: keep the lowest-numbered N reps per task
        if max_reps is not None:
            kept: list[dict[str, Any]] = []
            by_task: dict[str, list[dict[str, Any]]] = {}
            for c in cells_raw:
                by_task.setdefault(c["_task"], []).append(c)
            for task_cells in by_task.values():
                task_cells.sort(key=lambda c: c.get("_rep", 0))
                kept.extend(task_cells[:max_reps])
            cells_raw = kept
        model = cells_raw[0]["_model"]
        thinking = cells_raw[0]["_thinking"]
        config = cells_raw[0]["_config"]

        binaries = [c.get("reward_binary") or 0 for c in cells_raw]
        partials = [c.get("reward_partial") or 0.0 for c in cells_raw]
        costs = [c.get("cost_usd") or 0.0 for c in cells_raw]
        tokens = [c.get("total_tokens") or 0 for c in cells_raw]
        walls = [c.get("agent_wall_s") or 0.0 for c in cells_raw]

        solved = sum(1 for b in binaries if b >= 1)
        total = len(binaries)

        cells_out = []
        for c in cells_raw:
            task = c.get("_task") or c.get("task", "")
            diff_info = difficulty.get(task, {})
            diff_bucket = _difficulty_bucket(diff_info.get("pass_rate", ""))
            cells_out.append(
                {
                    "task": task,
                    "config": c.get("config", config),
                    "rep": c.get("_rep", c.get("rep", 0)),
                    "result_path": c.get("_result_path", ""),
                    "reward_binary": c.get("reward_binary") or 0,
                    "reward_partial": c.get("reward_partial") or 0.0,
                    "total_tokens": c.get("total_tokens") or 0,
                    "cost_usd": c.get("cost_usd") or 0.0,
                    "agent_wall_s": c.get("agent_wall_s") or 0.0,
                    "patch_bytes": c.get("patch_bytes") or 0,
                    "difficulty": diff_bucket,
                    "language": diff_info.get("language", c.get("language", "")),
                }
            )

        runs.append(
            {
                "run_id": group_key,
                "model": model,
                "thinking": thinking,
                "config": config,
                "state": "completed",
                "total_cells": total,
                "distinct_tasks": len({c.get("_task") for c in cells_raw}),
                "solved": solved,
                "solve_rate": (solved / total * 100) if total > 0 else 0.0,
                "mean_partial": _mean(partials),
                "median_cost": _median(costs),
                "median_tokens": int(_median(tokens)),
                "median_wall_s": _median(walls),
                "total_cost": sum(c for c in costs if isinstance(c, (int, float))),
                "cells": cells_out,
            }
        )

    return runs


# ---------------------------------------------------------------------------
# File serving (allowlisted)
# ---------------------------------------------------------------------------


def resolve_dashboard_path(
    raw_path: str, *, repo_root: Path = ROOT, state_root: Path = DEFAULT_STATE_ROOT
) -> Path:
    if not raw_path:
        raise ValueError("missing path")
    candidate = Path(raw_path)
    if not candidate.is_absolute():
        candidate = repo_root / candidate
    resolved = candidate.resolve()
    allowed_roots = [repo_root.resolve(), state_root.resolve()]
    for allowed in allowed_roots:
        try:
            resolved.relative_to(allowed)
            return resolved
        except ValueError:
            continue
    raise ValueError("path is outside the dashboard allowlist")


def head_file(path: Path, *, lines: int = 200, max_bytes: int = 256_000) -> str:
    """Return the first bounded lines of an allowlisted text file."""
    lines = max(1, min(lines, 2000))
    if not path.is_file():
        raise FileNotFoundError(path)
    with path.open("rb") as fh:
        data = fh.read(max_bytes).decode("utf-8", errors="replace")
    return "\n".join(data.splitlines()[:lines]) + ("\n" if data else "")


def tail_file(path: Path, *, lines: int = 200, max_bytes: int = 256_000) -> str:
    lines = max(1, min(lines, 2000))
    if not path.is_file():
        raise FileNotFoundError(path)
    chunks: list[bytes] = []
    size = path.stat().st_size
    remaining = min(size, max_bytes)
    with path.open("rb") as fh:
        while remaining > 0:
            step = min(8192, remaining)
            remaining -= step
            fh.seek(size - sum(len(c) for c in chunks) - step)
            chunk = fh.read(step)
            chunks.append(chunk)
            if b"\n".join(reversed(chunks)).count(b"\n") > lines:
                break
    data = b"".join(reversed(chunks)).decode("utf-8", errors="replace")
    return "\n".join(data.splitlines()[-lines:]) + ("\n" if data else "")


# ---------------------------------------------------------------------------
# Live run scoring (from events.ndjson) and session activity (from JSONL)
# ---------------------------------------------------------------------------

# Module-level cache for cell-session summaries, keyed by session file path.
# Invalidated when the file's mtime or size changes (sessions are appended to
# live during a run). Bounded so a long-lived API process never grows unbounded.
_SESSION_CACHE: dict[tuple[str, int], tuple[float, int, dict[str, Any]]] = {}
_SESSION_CACHE_LIMIT = 512


def _num(value: Any) -> float:
    """Coerce a JSON value to a finite float, else 0.0."""
    try:
        f = float(value)
    except (TypeError, ValueError):
        return 0.0
    return f if math.isfinite(f) else 0.0


def _span_seconds(start_ts: str | None, end_ts: str | None) -> float | None:
    """Seconds between two ISO timestamps, or None if either is unparseable."""
    if not start_ts or not end_ts:
        return None
    start = parse_timestamp(start_ts)
    end = parse_timestamp(end_ts)
    if start is None or end is None:
        return None
    span = (end - start).total_seconds()
    return span if span > 0 else None


def _status_batch_total(run_dir: Path) -> int | None:
    """Best-effort batch_total from status.json (the event log has no total)."""
    status = load_json(run_dir / "status.json")
    if not status:
        return None
    counts = RunStateWriter._counts(status) if status else {}
    total = counts.get("batch_total")
    return int(total) if isinstance(total, int) and total > 0 else None


def load_run_score(
    run_dir: Path,
    *,
    timeline_limit: int = 400,
    repo_root: Path = ROOT,
    state_root: Path = DEFAULT_STATE_ROOT,
) -> dict[str, Any]:
    """Replay a run's events.ndjson into a live score projection.

    Reads only the append-only event log (no transcript parsing), so it works
    for in-flight runs and is cheap to recompute on every poll. Returns running
    solve rate, partial/cost aggregates, a failure breakdown, a throughput/ETA
    estimate, a cumulative timeline for sparklines, and per-task best results.
    """
    events = read_events(run_dir, limit=10000)
    started: set[str] = set()
    finished_ids: set[str] = set()
    done_cells = 0  # finished + skipped: counts toward progress/outcome
    processed_cells = 0  # cell_finished only: real processing (cost/throughput)
    solved_cells = 0  # reward_binary>=1 over all done cells
    partials: list[float] = []
    costs: list[float] = []
    tool_calls = 0
    tool_call_errors = 0
    failures: dict[str, int] = {}
    timeline: list[dict[str, Any]] = []
    tasks: dict[str, dict[str, Any]] = {}
    first_finish_ts: str | None = None
    last_finish_ts: str | None = None

    for ev in events:
        kind = ev.get("kind")
        if kind != "batch":
            continue
        cid = str(ev.get("cell_id") or "")
        name = ev.get("event")
        if name == "cell_started":
            started.add(cid)
            continue
        if name not in ("cell_finished", "cell_skipped"):
            continue
        finished_ids.add(cid)
        is_skip = name == "cell_skipped"
        task = str(ev.get("task") or "")
        outcome = str(ev.get("outcome") or "")
        summary = ev.get("summary") or {}
        binary = _num(summary.get("reward_binary"))
        partial = _num(summary.get("reward_partial"))
        # A skipped cell reuses a PRIOR run's result. Its cost is not this run's
        # spend and it required zero processing, so it is excluded from the
        # cost sum and the throughput/timeline (but still counts as done and
        # contributes its outcome to the task-level solve rate).
        cost = (
            0.0
            if is_skip
            else (
                _num(summary.get("combined_cost_usd")) or _num(summary.get("cost_usd"))
            )
        )
        done_cells += 1
        partials.append(partial)
        if binary >= 1:
            solved_cells += 1
        if outcome and outcome not in ("ok", "skipped"):
            failures[outcome] = failures.get(outcome, 0) + 1
        # Per-task best result across reps in this run (both fresh + reused).
        best = tasks.setdefault(
            task,
            {
                "task": task,
                "best_reward_binary": 0,
                "best_reward_partial": 0.0,
                "reps": 0,
                "solved": False,
                "last_outcome": outcome,
            },
        )
        best["reps"] += 1
        best["best_reward_binary"] = max(best["best_reward_binary"], int(binary >= 1))
        best["best_reward_partial"] = round(
            max(best["best_reward_partial"], partial), 4
        )
        best["solved"] = bool(best["best_reward_binary"])
        best["last_outcome"] = outcome
        if is_skip:
            continue
        # Real finish (this-run processing): feed cost, throughput, timeline,
        # and compact tool-result telemetry from the cell's native session.
        processed_cells += 1
        costs.append(cost)
        session = load_cell_session(
            str(ev.get("result_path") or ""),
            repo_root=repo_root,
            state_root=state_root,
        )
        tool_calls += int(session.get("tool_calls") or 0)
        tool_call_errors += int(session.get("tool_call_errors") or 0)
        tool_call_error_rate = (
            round(tool_call_errors / tool_calls, 4) if tool_calls else None
        )
        ts = ev.get("ts")
        if ts:
            if first_finish_ts is None:
                first_finish_ts = ts
            last_finish_ts = ts
        timeline.append(
            {
                "ts": ts,
                "finished": processed_cells,
                "solved": sum(1 for t in tasks.values() if t["solved"]),
                "cost": round(sum(costs), 4),
                "mean_partial": round(_mean(partials), 4),
                "tool_calls": tool_calls,
                "tool_call_errors": tool_call_errors,
                "tool_call_error_rate": tool_call_error_rate,
            }
        )

    active = len(started - finished_ids)
    cumulative_cost = round(sum(costs), 4)
    tasks_total = len(tasks)
    tasks_solved = sum(1 for t in tasks.values() if t["solved"])
    # Solve rate is TASK-LEVEL (distinct tasks solved / distinct tasks) so it is
    # directly comparable to the baseline's any-rep task-level rate.
    solve_rate = round(tasks_solved / tasks_total * 100, 2) if tasks_total else 0.0
    mean_partial = round(_mean(partials), 4)
    tool_call_error_rate = (
        round(tool_call_errors / tool_calls, 4) if tool_calls else None
    )
    cost_per_solve = round(cumulative_cost / tasks_solved, 4) if tasks_solved else 0.0

    # Throughput (cells/hr) from the REAL finish-time span (skips excluded),
    # then project ETA from the remaining cell count.
    throughput_cph = 0.0
    eta_s: float | None = None
    span_s = _span_seconds(first_finish_ts, last_finish_ts)
    if span_s and processed_cells > 1:
        throughput_cph = round((processed_cells - 1) / span_s * 3600, 2)
    batch_total = _status_batch_total(run_dir)
    if throughput_cph > 0 and batch_total and batch_total > done_cells:
        remaining = batch_total - done_cells
        eta_s = round(remaining / throughput_cph * 3600, 1)
    # Projected cost uses THIS-RUN per-processed-cell spend, not the
    # lineage-blended figure that reused results would produce.
    cost_per_processed = cumulative_cost / processed_cells if processed_cells else 0.0
    projected_total_cost = (
        round(cost_per_processed * batch_total, 2) if batch_total else 0.0
    )

    return {
        "finished": done_cells,
        "processed": processed_cells,
        "solved": solved_cells,
        "tasks_total": tasks_total,
        "tasks_solved": tasks_solved,
        "solve_rate": solve_rate,
        "mean_partial": mean_partial,
        "tool_calls": tool_calls,
        "tool_call_errors": tool_call_errors,
        "tool_call_error_rate": tool_call_error_rate,
        "active": active,
        "cumulative_cost": cumulative_cost,
        "cost_per_solve": cost_per_solve,
        "projected_total_cost": projected_total_cost,
        "throughput_cells_per_hr": throughput_cph,
        "eta_s": eta_s,
        "failure_breakdown": failures,
        "timeline": timeline[-timeline_limit:],
        "tasks": list(tasks.values()),
    }


# Tolerant regex for tool targets inside a pi-fabric `fabric_exec` code blob.
# Captures the tool name and the first path/cmd/pattern/file value it sees.
import re as _re

_FABRIC_TOOL_RE = _re.compile(r"pi\.(\w+)\s*\(")
_FABRIC_TARGET_RE = _re.compile(
    r"(?:path|file|cmd|command|pattern)\s*:\s*['\"]([^'\"]{0,80})"
)
# Target keys for native pi tool arguments, in preference order.
_NATIVE_TARGET_KEYS = ("path", "file", "command", "cmd", "pattern")


def _intent_from_thinking(text: str | None) -> str | None:
    """First non-empty line of a thinking/text block, with markdown bold stripped."""
    if not text:
        return None
    for line in text.splitlines():
        line = line.strip().lstrip("#").replace("**", "").strip()
        if line:
            # Keep it short so a turn row stays one line in the UI.
            return line[:160]
    return None


def _tools_from_content(blocks: list[Any]) -> tuple[list[str], list[str]]:
    """Extract (tool_names, targets) from an assistant message's content blocks.

    Handles both dialects:
    - native pi: toolCall blocks carry name + a small arguments dict.
    - pi-fabric: one fabric_exec block whose arguments.code is a JS blob of
      many pi.<tool>({...}) calls; the inner calls are the real tools.
    Returns de-duplicated, order-preserving lists.
    """
    names: list[str] = []
    targets: list[str] = []
    seen_names: set[str] = set()
    seen_targets: set[str] = set()

    def push_name(n: str) -> None:
        if n and n not in seen_names:
            seen_names.add(n)
            names.append(n)

    def push_target(t: str) -> None:
        t = t.strip()
        if t and t not in seen_targets:
            seen_targets.add(t)
            targets.append(t[:100])

    for block in blocks or []:
        if not isinstance(block, dict):
            continue
        btype = block.get("type")
        if btype not in ("toolCall", "tool_use", "function_call"):
            continue
        outer_name = str(block.get("name") or "")
        args = block.get("arguments")
        if outer_name == "fabric_exec" and isinstance(args, dict):
            code = str(args.get("code") or "")
            if code:
                for m in _FABRIC_TOOL_RE.finditer(code):
                    push_name(m.group(1))
                for m in _FABRIC_TARGET_RE.finditer(code):
                    push_target(m.group(1))
        elif isinstance(args, dict):
            push_name(outer_name)
            for key in _NATIVE_TARGET_KEYS:
                val = args.get(key)
                if isinstance(val, str):
                    push_target(val)
                    break
        elif outer_name:
            push_name(outer_name)
    return names, targets


def _newest_session_file(session_dir: Path) -> Path | None:
    """Newest *.jsonl under a session dir by mtime, or None."""
    if not session_dir.is_dir():
        return None
    candidates = list(session_dir.glob("*.jsonl"))
    if not candidates:
        return None
    return max(candidates, key=lambda p: p.stat().st_mtime)


_TOOL_ERROR_OUTCOMES = {"failed", "aborted", "timed_out"}


def _tool_result_counts(message: dict[str, Any]) -> tuple[int, int]:
    """Return (tool calls, errors) from one native or Fabric tool result.

    Native Pi emits one result per call and marks failures with `isError`.
    Fabric emits one outer result for multiple inner trace operations; those
    operations are the meaningful denominator when telemetry is available.
    """
    if message.get("toolName") == "fabric_exec":
        details = message.get("details")
        trace = details.get("trace") if isinstance(details, dict) else None
        operations = trace.get("operations") if isinstance(trace, dict) else None
        if isinstance(operations, list):
            calls = [
                operation
                for operation in operations
                if isinstance(operation, dict) and operation.get("type") == "call"
            ]
            if calls:
                errors = sum(
                    str(call.get("outcome") or "") in _TOOL_ERROR_OUTCOMES
                    for call in calls
                )
                return len(calls), errors
    return 1, int(bool(message.get("isError")))


def _summarize_session(
    path: Path, *, tail_turns: int = 30, now_ts: float | None = None
) -> dict[str, Any]:
    """Parse one session JSONL into an aggregated turn timeline + summary.

    Cached by (mtime, size). Returns <=a few KB: a summary and the most recent
    `tail_turns` turns, never raw transcript lines.
    """
    try:
        st = path.stat()
    except OSError:
        return {"found": False}
    cache_key = (str(path), tail_turns)
    cached = _SESSION_CACHE.get(cache_key)
    if cached and cached[0] == st.st_mtime and cached[1] == st.st_size:
        result = cached[2]
        # Refresh live-ness against the current wall clock each call.
        return {**result, "is_live": _is_live(st.st_mtime, now_ts)}

    turns: list[dict[str, Any]] = []
    distinct_tools: set[str] = set()
    total_tokens = 0.0
    total_cost = 0.0
    tool_calls = 0
    tool_call_errors = 0
    started_at: str | None = None
    last_intent: str | None = None
    try:
        with path.open(encoding="utf-8", errors="replace") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if rec.get("type") != "message":
                    continue
                msg = rec.get("message") or {}
                role = msg.get("role")
                if role == "toolResult":
                    calls, errors = _tool_result_counts(msg)
                    tool_calls += calls
                    tool_call_errors += errors
                    continue
                if role != "assistant":
                    continue
                content = msg.get("content")
                if not isinstance(content, list):
                    continue
                intent = None
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "thinking":
                        intent = _intent_from_thinking(block.get("thinking"))
                        if intent:
                            break
                if intent is None:
                    for block in content:
                        if isinstance(block, dict) and block.get("type") == "text":
                            intent = _intent_from_thinking(block.get("text"))
                            if intent:
                                break
                tool_names, targets = _tools_from_content(content)
                distinct_tools.update(tool_names)
                usage = msg.get("usage") or {}
                token_delta = int(_num(usage.get("totalTokens")))
                cost_obj = usage.get("cost")
                cost_delta = (
                    _num(cost_obj.get("total"))
                    if isinstance(cost_obj, dict)
                    else _num(usage.get("cost"))
                )
                total_tokens += token_delta
                total_cost += cost_delta
                ts = rec.get("timestamp") or msg.get("timestamp")
                if ts and started_at is None:
                    started_at = ts
                if intent:
                    last_intent = intent
                turns.append(
                    {
                        "idx": len(turns) + 1,
                        "ts": ts,
                        "intent": intent,
                        "tools": tool_names[:8],
                        "targets": targets[:8],
                        "token_delta": token_delta,
                        "cost_delta": round(cost_delta, 5),
                        "cumulative_tokens": int(total_tokens),
                        "cumulative_cost": round(total_cost, 5),
                    }
                )
    except OSError:
        return {"found": False}

    summary = {
        "found": True,
        "path": str(path),
        "turns": len(turns),
        "total_tokens": int(total_tokens),
        "total_cost": round(total_cost, 5),
        "tool_calls": tool_calls,
        "tool_call_errors": tool_call_errors,
        "tool_call_error_rate": (
            round(tool_call_errors / tool_calls, 4) if tool_calls else None
        ),
        "distinct_tools": sorted(distinct_tools),
        "last_intent": last_intent,
        "started_at": started_at,
        "updated_at": st.st_mtime,
        "is_live": _is_live(st.st_mtime, now_ts),
    }
    result = {
        **summary,
        "turns_list": turns[-tail_turns:],
        "truncated": len(turns) > tail_turns,
    }

    # Bound the cache (FIFO eviction for a long-lived API process).
    if len(_SESSION_CACHE) >= _SESSION_CACHE_LIMIT:
        _SESSION_CACHE.pop(next(iter(_SESSION_CACHE)))
    _SESSION_CACHE[cache_key] = (st.st_mtime, st.st_size, result)
    return result


def _is_live(mtime: float, now_ts: float | None) -> bool:
    """A session is "live" if its file was modified within the last 3 minutes."""
    import time as _time

    now = now_ts if now_ts is not None else _time.time()
    return (now - mtime) < 180


def load_cell_session(
    result_path_str: str,
    *,
    tail_turns: int = 30,
    repo_root: Path = ROOT,
    state_root: Path = DEFAULT_STATE_ROOT,
    now_ts: float | None = None,
) -> dict[str, Any]:
    """Resolve a cell's result_path to its session JSONL and summarize it."""
    try:
        resolved = resolve_dashboard_path(
            result_path_str, repo_root=repo_root, state_root=state_root
        )
    except ValueError:
        return {"found": False, "error": "path outside dashboard allowlist"}
    session_dir = resolved.parent / "session"
    session_file = _newest_session_file(session_dir)
    if session_file is None:
        return {"found": False}
    return _summarize_session(session_file, tail_turns=tail_turns, now_ts=now_ts)


def load_cell_trajectory(
    result_path_str: str,
    *,
    offset: int = 0,
    limit: int = 20,
    repo_root: Path = ROOT,
    state_root: Path = DEFAULT_STATE_ROOT,
    now_ts: float | None = None,
) -> dict[str, Any]:
    """Resolve and return one complete, paginated cell trajectory page."""
    try:
        result_path = resolve_dashboard_path(
            result_path_str, repo_root=repo_root, state_root=state_root
        )
    except ValueError:
        return {"found": False, "error": "path outside dashboard allowlist"}
    session_path = _newest_session_file(result_path.parent / "session")
    if session_path is None:
        return {"found": False}
    return build_cell_trajectory_page(
        result_path,
        session_path,
        offset=max(0, offset),
        limit=max(1, min(limit, 50)),
        now_ts=now_ts,
    )


# ---------------------------------------------------------------------------
# HTTP server
# ---------------------------------------------------------------------------


class DashboardHTTPServer(ThreadingHTTPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(
        self,
        server_address: tuple[str, int],
        handler_class: type[BaseHTTPRequestHandler],
        *,
        state_root: Path,
        detail: str,
        repo_root: Path = ROOT,
        legacy_root: Path | None = DEFAULT_LEGACY_ROOT,
        results_root: Path = DEFAULT_RESULTS_ROOT,
        subsets_root: Path | None = None,
    ):
        super().__init__(server_address, handler_class)
        self.state_root = state_root
        self.detail = detail
        self.repo_root = repo_root
        self.legacy_root = legacy_root
        self.results_root = results_root
        self.subsets_root = (
            subsets_root if subsets_root is not None else repo_root / "subsets"
        )


class DashboardHandler(BaseHTTPRequestHandler):
    server: DashboardHTTPServer

    def log_message(self, format: str, *args: Any) -> None:
        return

    def do_GET(self) -> None:
        parsed = urllib.parse.urlparse(self.path)
        try:
            if parsed.path == "/api/runs":
                qs = urllib.parse.parse_qs(parsed.query)
                detail = qs.get("detail", [self.server.detail])[0]
                runs = load_dashboard_runs(
                    self.server.state_root,
                    detail=detail,
                    include_legacy=True,
                    legacy_root=self.server.legacy_root,
                )
                self._send_json({"runs": runs})
                return
            if parsed.path == "/api/subsets":
                subs = load_subsets(self.server.subsets_root)
                self._send_json({"subsets": subs})
                return
            if parsed.path == "/api/compare":
                qs = urllib.parse.parse_qs(parsed.query)
                subset = qs.get("subset", [None])[0]
                subset_tasks = None
                if subset:
                    subset_tasks = load_subset_tasks(
                        self.server.subsets_root / f"{subset}.txt"
                    )
                    if subset_tasks is None:
                        self._send_error(
                            HTTPStatus.NOT_FOUND, f"unknown subset: {subset}"
                        )
                        return
                try:
                    max_reps = int(qs.get("reps", ["0"])[0])
                except ValueError:
                    max_reps = 0
                runs = load_comparison_data(
                    self.server.results_root,
                    subset_tasks=subset_tasks,
                    max_reps=max_reps or None,
                )
                self._send_json({"runs": runs, "subset": subset})
                return
            if parsed.path.startswith("/api/runs/"):
                parts = [urllib.parse.unquote(p) for p in parsed.path.split("/") if p]
                if len(parts) < 3:
                    self._send_error(HTTPStatus.NOT_FOUND, "missing run_id")
                    return
                run_id = parts[2]
                qs = urllib.parse.parse_qs(parsed.query)
                detail = qs.get("detail", [self.server.detail])[0]
                if len(parts) == 4 and parts[3] == "events":
                    after = qs.get("after", [None])[0]
                    limit = int(qs.get("limit", [100])[0])
                    if run_id.startswith("legacy-"):
                        self._send_json({"events": []})
                        return
                    try:
                        run_dir = resolve_dashboard_run_state_dir(
                            run_id, self.server.state_root
                        )
                    except ValueError:
                        self._send_error(HTTPStatus.BAD_REQUEST, "invalid run_id")
                        return
                    events = read_events(
                        run_dir,
                        after=int(after) if after else None,
                        limit=limit,
                    )
                    self._send_json({"events": events})
                    return
                if len(parts) == 4 and parts[3] == "score":
                    if run_id.startswith("legacy-"):
                        self._send_json({"score": {}})
                        return
                    try:
                        run_dir = resolve_dashboard_run_state_dir(
                            run_id, self.server.state_root
                        )
                    except ValueError:
                        self._send_error(HTTPStatus.BAD_REQUEST, "invalid run_id")
                        return
                    score = load_run_score(
                        run_dir,
                        repo_root=self.server.repo_root,
                        state_root=self.server.state_root,
                    )
                    self._send_json({"score": score})
                    return
                if len(parts) == 3:
                    run = load_dashboard_run(
                        run_id,
                        self.server.state_root,
                        detail=detail,
                        legacy_root=self.server.legacy_root,
                        repo_root=self.server.repo_root,
                    )
                    if run is None:
                        self._send_error(HTTPStatus.NOT_FOUND, "run not found")
                        return
                    self._send_json(run)
                    return
            if parsed.path == "/api/cell-trajectory":
                qs = urllib.parse.parse_qs(parsed.query)
                raw = qs.get("path", [""])[0]
                if not raw:
                    self._send_error(HTTPStatus.BAD_REQUEST, "missing path")
                    return
                try:
                    offset = int(qs.get("offset", ["0"])[0])
                    limit = int(qs.get("limit", ["20"])[0])
                except ValueError:
                    self._send_error(
                        HTTPStatus.BAD_REQUEST, "offset and limit must be integers"
                    )
                    return
                trajectory = load_cell_trajectory(
                    raw,
                    offset=offset,
                    limit=limit,
                    repo_root=self.server.repo_root,
                    state_root=self.server.state_root,
                )
                self._send_json({"trajectory": trajectory})
                return
            if parsed.path == "/api/cell-session":
                qs = urllib.parse.parse_qs(parsed.query)
                raw = qs.get("path", [""])[0]
                try:
                    tail_turns = int(qs.get("tail", ["30"])[0])
                except ValueError:
                    tail_turns = 30
                if not raw:
                    self._send_error(HTTPStatus.BAD_REQUEST, "missing path")
                    return
                session = load_cell_session(
                    raw,
                    tail_turns=max(1, min(tail_turns, 200)),
                    repo_root=self.server.repo_root,
                    state_root=self.server.state_root,
                )
                self._send_json({"session": session})
                return
            if parsed.path == "/api/file":
                qs = urllib.parse.parse_qs(parsed.query)
                raw = qs.get("path", [""])[0]
                path = resolve_dashboard_path(
                    raw,
                    repo_root=self.server.repo_root,
                    state_root=self.server.state_root,
                )
                if qs.get("download", [""])[0] == "1":
                    self._send_file(path)
                    return
                if "head" in qs:
                    text = head_file(path, lines=int(qs["head"][0]))
                else:
                    text = tail_file(path, lines=int(qs.get("tail", [200])[0]))
                self._send_text(text)
                return
            self._send_error(HTTPStatus.NOT_FOUND, "not found")
        except FileNotFoundError as exc:
            self._send_error(HTTPStatus.NOT_FOUND, str(exc))
        except ValueError as exc:
            self._send_error(HTTPStatus.BAD_REQUEST, str(exc))
        except Exception as exc:  # noqa: BLE001  # pragma: no cover - HTTP boundary
            self._send_error(HTTPStatus.INTERNAL_SERVER_ERROR, repr(exc))

    def _send_json(self, payload: dict[str, Any]) -> None:
        data = json.dumps(payload, sort_keys=True).encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_text(self, text: str) -> None:
        data = text.encode("utf-8")
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "text/plain; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def _send_file(self, path: Path) -> None:
        if not path.is_file():
            raise FileNotFoundError(path)
        self.send_response(HTTPStatus.OK)
        self.send_header("Content-Type", "application/octet-stream")
        self.send_header("Content-Length", str(path.stat().st_size))
        filename = urllib.parse.quote(path.name)
        self.send_header(
            "Content-Disposition", f"attachment; filename*=UTF-8''{filename}"
        )
        self.end_headers()
        with path.open("rb") as fh:
            while chunk := fh.read(64 * 1024):
                self.wfile.write(chunk)

    def _send_error(self, status: HTTPStatus, message: str) -> None:
        data = json.dumps({"error": message}).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)


def make_server(
    *,
    host: str,
    port: int,
    state_root: str | Path = DEFAULT_STATE_ROOT,
    detail: str = "operational",
    repo_root: str | Path = ROOT,
    legacy_root: str | Path | None = DEFAULT_LEGACY_ROOT,
    results_root: str | Path = DEFAULT_RESULTS_ROOT,
) -> DashboardHTTPServer:
    if detail not in DETAIL_LEVELS:
        raise ValueError(f"detail must be one of {sorted(DETAIL_LEVELS)}")
    legacy = Path(legacy_root) if legacy_root is not None else None
    return DashboardHTTPServer(
        (host, port),
        DashboardHandler,
        state_root=Path(state_root),
        detail=detail,
        repo_root=Path(repo_root),
        legacy_root=legacy,
        results_root=Path(results_root),
    )


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument(
        "--state-root", default=str(DEFAULT_STATE_ROOT), help="default: results/_runs"
    )
    ap.add_argument(
        "--results-root", default=str(DEFAULT_RESULTS_ROOT), help="default: results/"
    )
    ap.add_argument("--detail", choices=sorted(DETAIL_LEVELS), default="operational")
    args = ap.parse_args(argv)

    server = make_server(
        host=args.host,
        port=args.port,
        state_root=args.state_root,
        detail=args.detail,
        results_root=args.results_root,
    )
    url = f"http://{args.host}:{server.server_address[1]}/"
    print(f"serving deep-swe-bench dashboard API at {url}", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
