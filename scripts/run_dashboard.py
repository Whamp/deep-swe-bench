#!/usr/bin/env python3
"""Serve the deep-swe-bench dashboard JSON API.

The frontend is a React+Vite SPA in dashboard/. This server provides:
  GET /api/runs              — list all discovered runs (structured + legacy)
  GET /api/runs/<id>         — detailed projection of a single run
  GET /api/runs/<id>/events  — events.ndjson tail
  GET /api/compare           — aggregated cross-run benchmark metrics for charts
  GET /api/subsets            — list available task subsets
  GET /api/file?path=&tail=  — tail a file from the repo (allowlisted)

Usage:
    python3 scripts/run_dashboard.py --host 0.0.0.0 --port 8789
"""
from __future__ import annotations

import argparse
import json
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

from harness.run_state import (  # noqa: E402
    DETAIL_LEVELS,
    discover_runs,
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

def load_dashboard_runs(
    state_root: str | Path = DEFAULT_STATE_ROOT,
    *,
    detail: str = "summary",
    include_legacy: bool = True,
    legacy_root: str | Path | None = DEFAULT_LEGACY_ROOT,
) -> list[dict[str, Any]]:
    return discover_runs(state_root, detail=detail, include_legacy=include_legacy, legacy_root=legacy_root)


def load_dashboard_run(
    run_id: str,
    state_root: str | Path = DEFAULT_STATE_ROOT,
    *,
    detail: str = "operational",
    legacy_root: str | Path | None = DEFAULT_LEGACY_ROOT,
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
        safe_id = sanitize_run_id(run_id)
    except ValueError:
        return None
    run_dir = Path(state_root) / safe_id
    if not run_dir.exists():
        return None
    return project_structured_run(run_dir, detail=detail)


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
        data["_rep"] = data.get("rep") if isinstance(data.get("rep"), int) else _rep_from_parts(parts)
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
            cells_out.append({
                "task": task,
                "config": c.get("config", config),
                "rep": c.get("_rep", c.get("rep", 0)),
                "reward_binary": c.get("reward_binary") or 0,
                "reward_partial": c.get("reward_partial") or 0.0,
                "total_tokens": c.get("total_tokens") or 0,
                "cost_usd": c.get("cost_usd") or 0.0,
                "agent_wall_s": c.get("agent_wall_s") or 0.0,
                "patch_bytes": c.get("patch_bytes") or 0,
                "difficulty": diff_bucket,
                "language": diff_info.get("language", c.get("language", "")),
            })

        runs.append({
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
        })

    return runs


# ---------------------------------------------------------------------------
# File serving (allowlisted)
# ---------------------------------------------------------------------------

def resolve_dashboard_path(raw_path: str, *, repo_root: Path = ROOT, state_root: Path = DEFAULT_STATE_ROOT) -> Path:
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
        self.subsets_root = subsets_root if subsets_root is not None else repo_root / "subsets"


class DashboardHandler(BaseHTTPRequestHandler):
    server: DashboardHTTPServer

    def log_message(self, fmt: str, *args: Any) -> None:
        return

    def do_GET(self) -> None:  # noqa: N802
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
                    subset_tasks = load_subset_tasks(self.server.subsets_root / f"{subset}.txt")
                    if subset_tasks is None:
                        self._send_error(HTTPStatus.NOT_FOUND, f"unknown subset: {subset}")
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
                        safe_id = sanitize_run_id(run_id)
                    except ValueError:
                        self._send_error(HTTPStatus.BAD_REQUEST, "invalid run_id")
                        return
                    events = read_events(self.server.state_root / safe_id, after=int(after) if after else None, limit=limit)
                    self._send_json({"events": events})
                    return
                if len(parts) == 3:
                    run = load_dashboard_run(
                        run_id,
                        self.server.state_root,
                        detail=detail,
                        legacy_root=self.server.legacy_root,
                    )
                    if run is None:
                        self._send_error(HTTPStatus.NOT_FOUND, "run not found")
                        return
                    self._send_json(run)
                    return
            if parsed.path == "/api/file":
                qs = urllib.parse.parse_qs(parsed.query)
                raw = qs.get("path", [""])[0]
                tail = int(qs.get("tail", [200])[0])
                path = resolve_dashboard_path(raw, repo_root=self.server.repo_root, state_root=self.server.state_root)
                text = tail_file(path, lines=tail)
                self._send_text(text)
                return
            self._send_error(HTTPStatus.NOT_FOUND, "not found")
        except FileNotFoundError as exc:
            self._send_error(HTTPStatus.NOT_FOUND, str(exc))
        except ValueError as exc:
            self._send_error(HTTPStatus.BAD_REQUEST, str(exc))
        except Exception as exc:  # pragma: no cover - defensive HTTP boundary
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
    ap.add_argument("--state-root", default=str(DEFAULT_STATE_ROOT), help="default: results/_runs")
    ap.add_argument("--results-root", default=str(DEFAULT_RESULTS_ROOT), help="default: results/")
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
