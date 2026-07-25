"""Structured state snapshots for ``harness/run_batch.py`` and its dashboard.

The batch runner still prints its historical progress lines to stdout.  This
module adds a side-channel under ``results/_runs/<run_id>/`` so tools can poll a
small status file instead of tailing stdout or per-cell logs.
"""
from __future__ import annotations

import json
import os
import re
import socket
import threading
import time
from collections import deque
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


SCHEMA_VERSION = 1
RUN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_.-]{0,127}$")

BASE_SUMMARY_FIELDS = {
    "reward_partial",
    "reward_binary",
    "patch_bytes",
    "agent_wall_s",
    "agent_exit",
    "agent_timed_out",
    "verifier_exit",
    "total_tokens",
    "input_tokens",
    "output_tokens",
    "cache_read_tokens",
    "cache_write_tokens",
    "cost_usd",
    "combined_total_tokens",
    "combined_cost_usd",
    "transient_model_error",
    "f2p",
    "p2p",
}
SUMMARY_PREFIXES = (
    "advisor_",
    "om_worker_",
    "combined_",
    "recursive_child_",
    "arm_",  # historical result.json diagnostic fields
)
TERMINAL_STATES = {"done", "skipped", "failed", "passed"}
DETAIL_LEVELS = {"summary", "operational", "diagnostic"}


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def parse_timestamp(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def seconds_since(value: str | None, *, now: datetime | None = None) -> float | None:
    ts = parse_timestamp(value)
    if ts is None:
        return None
    now = now or datetime.now(timezone.utc)
    return max(0.0, (now - ts).total_seconds())


def sanitize_run_id(run_id: str) -> str:
    if not RUN_ID_RE.fullmatch(run_id):
        raise ValueError("run_id must match [A-Za-z0-9][A-Za-z0-9_.-]{0,127}")
    return run_id


def default_run_id(*, pid: int | None = None) -> str:
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return f"{stamp}-{pid or os.getpid()}"


def atomic_write_json(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(f".{path.name}.{os.getpid()}.{threading.get_ident()}.tmp")
    tmp.write_text(json.dumps(data, indent=2, sort_keys=True) + "\n")
    os.replace(tmp, path)


def append_ndjson(path: Path, record: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record, sort_keys=True) + "\n")


def load_json(path: Path) -> dict[str, Any] | None:
    try:
        document = json.loads(path.read_text())
    except (FileNotFoundError, json.JSONDecodeError, OSError):
        return None
    return document if isinstance(document, dict) else None


def cell_id(task: str, config: str, rep: int) -> str:
    return f"{task}/{config}/rep{rep}"


def make_cell(
    *,
    task: str,
    config: str,
    rep: int,
    result_path: str | Path | None = None,
    log_path: str | Path | None = None,
    **extra: Any,
) -> dict[str, Any]:
    cell = {
        "cell_id": cell_id(task, config, rep),
        "task": task,
        "config": config,
        "rep": rep,
    }
    if result_path is not None:
        cell["result_path"] = str(result_path)
    if log_path is not None:
        cell["log_path"] = str(log_path)
    cell.update({k: v for k, v in extra.items() if v is not None})
    return cell


def classify_result(record: dict[str, Any]) -> str:
    """Classify a completed cell using the same labels as track_run.py."""
    if record.get("transient_model_error"):
        return "transient"
    if record.get("agent_timed_out") or record.get("agent_exit") == "timeout":
        return "timeout"
    agent_exit = record.get("agent_exit")
    verifier_exit = record.get("verifier_exit")
    if agent_exit in (0, "0") and verifier_exit in (0, "0", "skipped_empty_patch"):
        return "empty" if verifier_exit == "skipped_empty_patch" else "ok"
    return f"exit={agent_exit}"


def compact_result_summary(record: dict[str, Any]) -> dict[str, Any]:
    """Return scalar result fields useful on a live dashboard, not raw logs."""
    summary: dict[str, Any] = {}
    for key, value in record.items():
        if key not in BASE_SUMMARY_FIELDS and not key.startswith(SUMMARY_PREFIXES):
            continue
        if isinstance(value, (str, int, float, bool)) or value is None:
            summary[key] = value
    return summary


def summarize_result_path(
    path: str | Path | None,
    *,
    exit_code: int | str | None = None,
    transient_exit: int | None = None,
) -> tuple[str, dict[str, Any]]:
    """Return ``(outcome, summary)`` for a result path or subprocess exit."""
    if path:
        rec = load_json(Path(path))
        if rec is not None:
            return classify_result(rec), compact_result_summary(rec)
    if transient_exit is not None and exit_code == transient_exit:
        return "transient", {"agent_exit": exit_code, "transient_model_error": True}
    if exit_code is None:
        return "skipped", {}
    return f"exit={exit_code}", {"agent_exit": exit_code}


class RunStateWriter:
    """Thread-safe writer for one ``results/_runs/<run_id>`` state directory."""

    def __init__(self, state_root: str | Path, manifest: dict[str, Any]):
        run_id = sanitize_run_id(str(manifest["run_id"]))
        run_key = sanitize_run_id(str(manifest.get("run_key") or run_id))
        self.state_root = Path(state_root)
        self.run_dir = self.state_root / run_key
        self.manifest_path = self.run_dir / "manifest.json"
        self.status_path = self.run_dir / "status.json"
        self.events_path = self.run_dir / "events.ndjson"
        self.manifest = dict(manifest)
        self.manifest.setdefault("schema_version", SCHEMA_VERSION)
        self.manifest["run_id"] = run_id
        self.manifest["run_key"] = run_key
        self._lock = threading.Lock()
        self._seq = 0
        self._stop_heartbeat = threading.Event()
        self._heartbeat_thread: threading.Thread | None = None
        self.status = self._initial_status()

    def _initial_status(self) -> dict[str, Any]:
        now = utc_now()
        cells = {
            cell["cell_id"]: self._initial_cell(cell, kind="batch")
            for cell in self.manifest.get("batch_cells", [])
        }
        preflight = {
            cell["cell_id"]: self._initial_cell(cell, kind="preflight")
            for cell in self.manifest.get("preflight", [])
        }
        status = {
            "schema_version": SCHEMA_VERSION,
            "run_id": self.manifest["run_id"],
            "state": "running",
            "stage": "starting",
            "started_at": now,
            "updated_at": now,
            "heartbeat_at": now,
            "counts": {},
            "active_cell_ids": [],
            "active_preflight_ids": [],
            "cells": cells,
            "preflight": preflight,
            "recent_finished": [],
        }
        status["counts"] = self._counts(status)
        return status

    @staticmethod
    def _initial_cell(cell: dict[str, Any], *, kind: str) -> dict[str, Any]:
        keys = ("cell_id", "task", "config", "rep", "result_path", "log_path", "contract_path", "reason")
        entry = {k: cell[k] for k in keys if k in cell}
        entry.update({"kind": kind, "state": "pending"})
        return entry

    def start(self) -> None:
        with self._lock:
            self.run_dir.mkdir(parents=True, exist_ok=True)
            self.events_path.write_text("")
            atomic_write_json(self.manifest_path, self.manifest)
            self._save_status_locked()
            self._append_event_locked("run_started", kind="run")

    def start_heartbeat(self, interval_s: float | None) -> None:
        if not interval_s or interval_s <= 0:
            return
        if self._heartbeat_thread and self._heartbeat_thread.is_alive():
            return

        def loop() -> None:
            while not self._stop_heartbeat.wait(interval_s):
                self.heartbeat()

        self._heartbeat_thread = threading.Thread(target=loop, name="run-state-heartbeat", daemon=True)
        self._heartbeat_thread.start()

    def stop_heartbeat(self) -> None:
        self._stop_heartbeat.set()
        if self._heartbeat_thread:
            self._heartbeat_thread.join(timeout=1.0)

    def heartbeat(self) -> None:
        with self._lock:
            self._save_status_locked()

    def set_stage(self, stage: str) -> None:
        with self._lock:
            self.status["stage"] = stage
            self._save_status_locked()

    def preflight_skipped(self, cell: dict[str, Any], *, reason: str) -> None:
        self._finish_cell("preflight", cell, event="preflight_skipped", state="skipped", reason=reason)

    def preflight_started(self, cell: dict[str, Any]) -> None:
        self._start_cell("preflight", cell, event="preflight_started")

    def preflight_finished(
        self,
        cell: dict[str, Any],
        *,
        result_path: str | Path | None = None,
        log_path: str | Path | None = None,
        exit_code: int | str | None = None,
        transient_exit: int | None = None,
        diagnostics: list[dict[str, object]] | None = None,
    ) -> None:
        outcome, summary = summarize_result_path(
            result_path,
            exit_code=exit_code,
            transient_exit=transient_exit,
        )
        state = (
            "passed"
            if outcome in {"ok", "empty"} and not diagnostics
            else "failed"
        )
        self._finish_cell(
            "preflight",
            cell,
            event="preflight_finished",
            state=state,
            outcome=outcome,
            summary=summary,
            result_path=result_path,
            log_path=log_path,
            exit_code=exit_code,
            diagnostics=diagnostics,
        )

    def cell_started(self, cell: dict[str, Any]) -> None:
        self._start_cell("batch", cell, event="cell_started")

    def cell_skipped(self, cell: dict[str, Any], *, reason: str = "existing_result") -> None:
        result_path = cell.get("result_path")
        # A skipped cell already has a result on disk. Classify it so the batch
        # counts reflect the existing outcome (a valid prior result counts as
        # "ok"), instead of masking every skip as a generic "skipped" outcome.
        # The cell STATE stays "skipped" so batch_skipped still increments.
        outcome, summary = summarize_result_path(result_path)
        self._finish_cell(
            "batch",
            cell,
            event="cell_skipped",
            state="skipped",
            outcome=outcome,
            summary=summary,
            reason=reason,
        )

    def cell_finished(
        self,
        cell: dict[str, Any],
        *,
        result_path: str | Path | None = None,
        log_path: str | Path | None = None,
        exit_code: int | str | None = None,
        transient_exit: int | None = None,
    ) -> None:
        outcome, summary = summarize_result_path(result_path, exit_code=exit_code, transient_exit=transient_exit)
        self._finish_cell(
            "batch",
            cell,
            event="cell_finished",
            state="done",
            outcome=outcome,
            summary=summary,
            result_path=result_path,
            log_path=log_path,
            exit_code=exit_code,
        )

    def run_paused(self, *, reason: str) -> None:
        with self._lock:
            self.status["state"] = "paused"
            self.status["stage"] = "paused"
            self.status["paused_at"] = utc_now()
            self._save_status_locked()
            self._append_event_locked("run_paused", kind="run", reason=reason)

    def launch_input_drift(
        self,
        *,
        pending_cell_id: str,
        changes: list[dict[str, object]],
    ) -> None:
        """Fail a run and record every changed approved launch input."""
        with self._lock:
            active_cell_ids = list(self.status["active_cell_ids"])
            active_preflight_ids = list(self.status["active_preflight_ids"])
            drift = {
                "pending_cell_id": pending_cell_id,
                "active_cell_ids": active_cell_ids,
                "active_preflight_ids": active_preflight_ids,
                "changes": [dict(change) for change in changes],
            }
            self.status["state"] = "failed"
            self.status["stage"] = "failed"
            self.status["failed_at"] = utc_now()
            self.status["launch_input_drift"] = drift
            self._save_status_locked()
            self._append_event_locked(
                "launch_input_drift",
                kind="run",
                **drift,
            )

    def run_completed(self) -> None:
        with self._lock:
            self.status["state"] = "completed"
            self.status["stage"] = "done"
            self.status["completed_at"] = utc_now()
            self._save_status_locked()
            self._append_event_locked("run_completed", kind="run")

    def run_failed(self, *, reason: str, exit_code: int | str | None = None) -> None:
        with self._lock:
            if self.status.get("state") in {"completed", "paused"}:
                return
            self.status["state"] = "failed"
            self.status["stage"] = "failed"
            self.status["failed_at"] = utc_now()
            self._save_status_locked()
            self._append_event_locked("run_failed", kind="run", reason=reason, exit_code=exit_code)

    def _start_cell(self, collection: str, cell: dict[str, Any], *, event: str) -> None:
        cid = cell["cell_id"]
        now = utc_now()
        with self._lock:
            entry = self._cell_collection(collection).setdefault(cid, self._initial_cell(cell, kind=collection))
            entry.update({"state": "running", "started_at": now})
            self.status["stage"] = "preflight" if collection == "preflight" else "batch"
            self._refresh_active_locked()
            self._save_status_locked()
            self._append_event_locked(event, kind=collection, cell_id=cid, **self._event_cell_fields(entry))

    def _finish_cell(
        self,
        collection: str,
        cell: dict[str, Any],
        *,
        event: str,
        state: str,
        outcome: str | None = None,
        summary: dict[str, Any] | None = None,
        result_path: str | Path | None = None,
        log_path: str | Path | None = None,
        reason: str | None = None,
        exit_code: int | str | None = None,
        diagnostics: list[dict[str, object]] | None = None,
    ) -> None:
        cid = cell["cell_id"]
        now = utc_now()
        result_path = str(result_path or cell.get("result_path") or "") or None
        log_path = str(log_path or cell.get("log_path") or "") or None
        with self._lock:
            entry = self._cell_collection(collection).setdefault(cid, self._initial_cell(cell, kind=collection))
            entry.update({"state": state, "finished_at": now})
            if outcome is not None:
                entry["outcome"] = outcome
            if summary is not None:
                entry["summary"] = summary
            if result_path:
                entry["result_path"] = result_path
            if log_path:
                entry["log_path"] = log_path
            if reason:
                entry["reason"] = reason
            if exit_code is not None:
                entry["exit_code"] = exit_code
            if diagnostics is not None:
                entry["diagnostics"] = diagnostics
            self._add_recent_locked(entry)
            self._refresh_active_locked()
            self._save_status_locked()
            payload = {
                "kind": collection,
                "cell_id": cid,
                **self._event_cell_fields(entry),
                "outcome": outcome,
                "summary": summary,
                "result_path": result_path,
                "log_path": log_path,
                "reason": reason,
                "exit_code": exit_code,
                "diagnostics": diagnostics,
            }
            self._append_event_locked(event, **{k: v for k, v in payload.items() if v is not None})

    def _cell_collection(self, collection: str) -> dict[str, Any]:
        return self.status["preflight" if collection == "preflight" else "cells"]

    @staticmethod
    def _event_cell_fields(entry: dict[str, Any]) -> dict[str, Any]:
        return {k: entry[k] for k in ("task", "config", "rep") if k in entry}

    def _refresh_active_locked(self) -> None:
        self.status["active_cell_ids"] = [
            cid for cid, cell in self.status.get("cells", {}).items() if cell.get("state") == "running"
        ]
        self.status["active_preflight_ids"] = [
            cid for cid, cell in self.status.get("preflight", {}).items() if cell.get("state") == "running"
        ]

    def _add_recent_locked(self, entry: dict[str, Any]) -> None:
        item = {
            k: entry[k]
            for k in (
                "kind",
                "cell_id",
                "task",
                "config",
                "rep",
                "state",
                "outcome",
                "finished_at",
                "summary",
                "result_path",
                "log_path",
                "reason",
            )
            if k in entry
        }
        recent = list(self.status.get("recent_finished") or [])
        recent.append(item)
        self.status["recent_finished"] = recent[-30:]

    def _save_status_locked(self) -> None:
        now = utc_now()
        self.status["updated_at"] = now
        self.status["heartbeat_at"] = now
        self.status["counts"] = self._counts(self.status)
        atomic_write_json(self.status_path, self.status)

    def _append_event_locked(self, event: str, **payload: Any) -> None:
        self._seq += 1
        record = {"schema_version": SCHEMA_VERSION, "seq": self._seq, "ts": utc_now(), "event": event}
        record.update({k: v for k, v in payload.items() if v is not None})
        append_ndjson(self.events_path, record)

    @staticmethod
    def _counts(status: dict[str, Any]) -> dict[str, int]:
        batch = status.get("cells") or {}
        preflight = status.get("preflight") or {}
        counts = {
            "batch_total": len(batch),
            "batch_done": 0,
            "batch_running": 0,
            "batch_skipped": 0,
            "ok": 0,
            "empty": 0,
            "timeout": 0,
            "transient": 0,
            "failed": 0,
            "preflight_total": len(preflight),
            "preflight_done": 0,
            "preflight_running": 0,
            "preflight_skipped": 0,
            "preflight_failed": 0,
        }
        for cell in batch.values():
            state = cell.get("state")
            if state == "running":
                counts["batch_running"] += 1
            if state == "skipped":
                counts["batch_skipped"] += 1
            if state in TERMINAL_STATES:
                counts["batch_done"] += 1
            outcome = cell.get("outcome")
            # Only count outcomes for cells that actually ran in THIS run.
            # Skipped cells (existing result reused) must not inflate ok/failed
            # buckets; their outcome is preserved on the cell for detail views.
            if state in TERMINAL_STATES and outcome and state != "skipped":
                if outcome in {"ok", "empty", "timeout", "transient"}:
                    counts[outcome] += 1
                else:
                    counts["failed"] += 1
        for cell in preflight.values():
            state = cell.get("state")
            if state == "running":
                counts["preflight_running"] += 1
            if state == "skipped":
                counts["preflight_skipped"] += 1
            if state in TERMINAL_STATES:
                counts["preflight_done"] += 1
            if state == "failed":
                counts["preflight_failed"] += 1
        return counts


def base_manifest(
    *,
    run_id: str,
    command: list[str],
    cwd: str | Path,
    model: str,
    thinking: str,
    configs: list[str],
    selection: dict[str, Any],
    runs: int,
    workers: int,
    agent: str = "pi",
    agent_timeout_s: float | None = None,
    rpc_quiescence_s: float | None,
    initial_context_capture_enabled: bool = True,
    progress_interval_s: float | None,
    batch_cells: list[dict[str, Any]],
    preflight: list[dict[str, Any]],
) -> dict[str, Any]:
    return {
        "schema_version": SCHEMA_VERSION,
        "run_id": sanitize_run_id(run_id),
        "created_at": utc_now(),
        "command": command,
        "cwd": str(cwd),
        "host": socket.gethostname(),
        "pid": os.getpid(),
        "model": model,
        "thinking": thinking,
        "configs": configs,
        "selection": selection,
        "runs": runs,
        "workers": workers,
        "agent": agent,
        "agent_timeout_s": agent_timeout_s,
        "rpc_quiescence_s": rpc_quiescence_s,
        "initial_context_capture_enabled": initial_context_capture_enabled,
        "progress_interval_s": progress_interval_s,
        "batch_cells": batch_cells,
        "preflight": preflight,
    }


def read_events(run_dir: Path, *, after: int | None = None, limit: int = 100) -> list[dict[str, Any]]:
    path = run_dir / "events.ndjson"
    limit = max(1, min(limit, 1000))
    rows: deque[dict[str, Any]] | list[dict[str, Any]]
    rows = [] if after is not None else deque(maxlen=limit)
    try:
        with path.open(encoding="utf-8") as fh:
            for line in fh:
                line = line.strip()
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if after is not None:
                    if int(rec.get("seq") or 0) <= after:
                        continue
                    rows.append(rec)  # type: ignore[union-attr]
                    if len(rows) >= limit:  # type: ignore[arg-type]
                        break
                else:
                    rows.append(rec)  # type: ignore[union-attr]
    except OSError:
        return []
    return list(rows)


def _estimate_eta_s(status: dict[str, Any]) -> float | None:
    counts = status.get("counts") or {}
    total = counts.get("batch_total") or 0
    done = counts.get("batch_done") or 0
    if total <= 0 or done <= 0 or done >= total:
        return None
    started = parse_timestamp(status.get("started_at"))
    if not started:
        return None
    elapsed = max(0.0, (datetime.now(timezone.utc) - started).total_seconds())
    rate = done / elapsed if elapsed > 0 else 0
    if rate <= 0:
        return None
    return (total - done) / rate


def _failure_buckets(status: dict[str, Any]) -> dict[str, int]:
    buckets: dict[str, int] = {}
    for cell in (status.get("cells") or {}).values():
        outcome = cell.get("outcome")
        if not outcome or outcome in {"ok", "empty", "skipped"}:
            continue
        buckets[outcome] = buckets.get(outcome, 0) + 1
    return buckets


# Threshold for flagging an active cell as potentially stuck. Cells running
# longer than this without finishing may be hung on a provider request.
STALE_CELL_THRESHOLD_S = 1800  # 30 minutes


def _enrich_active_cells(active_cells: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], float | None, int]:
    """Add cell_age_s to each active cell and return (cells, max_age_s, stale_count)."""
    now = datetime.now(timezone.utc)
    max_age: float | None = None
    stale = 0
    enriched = []
    for cell in active_cells:
        cell = dict(cell)  # shallow copy so we don't mutate the source
        started = parse_timestamp(cell.get("started_at"))
        if started:
            age = max(0.0, (now - started).total_seconds())
            cell["cell_age_s"] = round(age, 1)
            if max_age is None or age > max_age:
                max_age = age
            if age > STALE_CELL_THRESHOLD_S:
                cell["potentially_stale"] = True
                stale += 1
        enriched.append(cell)
    return enriched, max_age, stale


def project_atomic_preflight_state(status: dict[str, Any]) -> str:
    """Project the truthful run-level state of the complete preflight gate.

    Args:
        status: Durable structured-run status with per-config preflight cells.

    Returns:
        One aggregate state that cannot pass before every preflight passes.
    """
    preflight = status.get("preflight")
    if not isinstance(preflight, dict) or not preflight:
        return "not_required"
    states = {
        cell.get("state")
        for cell in preflight.values()
        if isinstance(cell, dict)
    }
    if "failed" in states:
        return "failed"
    if "running" in states:
        return "running"
    if states == {"passed"}:
        return "passed"
    if states == {"skipped"}:
        return "skipped"
    if states == {"pending"}:
        return "pending"
    if "pending" in states and states <= {"pending", "passed", "skipped"}:
        return "running"
    if states <= {"passed", "skipped"}:
        return "incomplete"
    return "unknown"


def project_structured_run(run_dir: Path, *, detail: str = "summary") -> dict[str, Any]:
    if detail not in DETAIL_LEVELS:
        detail = "summary"
    manifest = load_json(run_dir / "manifest.json") or {}
    status = load_json(run_dir / "status.json") or {}
    run_id = str(manifest.get("run_id") or status.get("run_id") or run_dir.name)
    # Recompute counts from cells on read so the dashboard always reflects the
    # current _counts logic, even for runs whose batch process cached an older
    # version of this module.
    counts = RunStateWriter._counts(status) if status else {}
    active_ids = status.get("active_cell_ids") or []
    all_cells = status.get("cells") or {}
    raw_active = [all_cells[cid] for cid in active_ids if cid in all_cells]
    active_cells, max_cell_age_s, stale_cell_count = _enrich_active_cells(raw_active)
    preflight = status.get("preflight") or {}
    # run_key is the unique directory name — always unique even when two runs
    # share the same manifest run_id (e.g. a smoke-failed rerun).  The frontend
    # routes on run_key so every discovered run is individually addressable.
    launch_plan_identity = manifest.get("launch_plan_identity")
    launch_metadata = (
        "confirmed_plan"
        if isinstance(launch_plan_identity, str)
        else "legacy_structured"
    )
    projected = {
        "kind": "structured",
        "run_id": run_id,
        "run_key": run_dir.name,
        "state": status.get("state", "unknown"),
        "stage": status.get("stage"),
        "created_at": manifest.get("created_at") or status.get("started_at"),
        "updated_at": status.get("updated_at"),
        "heartbeat_at": status.get("heartbeat_at"),
        "heartbeat_age_s": seconds_since(status.get("heartbeat_at")),
        "eta_s": _estimate_eta_s(status),
        "model": manifest.get("model"),
        "thinking": manifest.get("thinking"),
        "configs": manifest.get("config_identities")
        or manifest.get("configs")
        or [],
        "launch_metadata": launch_metadata,
        "launch_plan_identity": launch_plan_identity,
        "preflight_state": project_atomic_preflight_state(status),
        "results_root": manifest.get("results_root"),
        "selection": manifest.get("selection") or {},
        "state_root": manifest.get("state_root"),
        "workers": manifest.get("workers"),
        "workspace": manifest.get("workspace") or manifest.get("cwd"),
        "counts": counts,
        "active_count": len(active_cells),
        "max_cell_age_s": round(max_cell_age_s, 1) if max_cell_age_s is not None else None,
        "stale_cell_count": stale_cell_count,
        "failure_buckets": _failure_buckets(status),
        "paths": {
            "run_dir": str(run_dir),
            "manifest": str(run_dir / "manifest.json"),
            "status": str(run_dir / "status.json"),
            "events": str(run_dir / "events.ndjson"),
        },
    }
    if detail in {"operational", "diagnostic"}:
        projected.update(
            {
                "active_cells": active_cells,
                "recent_finished": status.get("recent_finished") or [],
                "preflight": preflight,
            }
        )
    if detail == "diagnostic":
        projected.update(
            {
                "manifest": manifest,
                "status": status,
                "events_tail": read_events(run_dir, limit=100),
            }
        )
    return projected


def _legacy_status_of(record: dict[str, Any]) -> str:
    return classify_result(record)


def project_legacy_track(track_path: Path, *, detail: str = "summary") -> dict[str, Any]:
    run_name = track_path.parent.name
    lines: list[str] = []
    try:
        lines = track_path.read_text(errors="replace").splitlines()
    except OSError:
        pass
    total = 0
    done = 0
    buckets = {"ok": 0, "empty": 0, "timeout": 0, "transient": 0, "failed": 0}
    recent: list[dict[str, Any]] = []
    line_re = re.compile(r"^\[(?P<done>\d+)/(?:\?|(?P<total>\d+))\]\s+(?P<task>.*?)\s+/\s+(?P<config>.*?)\s+/\s+rep(?P<rep>\d+)\s+(?P<outcome>\S+)")
    done_re = re.compile(r"^done:\s+(?P<done>\d+)/(?:\?|(?P<total>\d+))")
    for line in lines:
        m = line_re.match(line)
        if m:
            done = max(done, int(m.group("done")))
            if m.group("total"):
                total = max(total, int(m.group("total")))
            outcome = m.group("outcome")
            if outcome in {"ok", "empty", "timeout", "transient"}:
                buckets[outcome] += 1
            elif outcome != "skip":
                buckets["failed"] += 1
            recent.append(
                {
                    "cell_id": cell_id(m.group("task"), m.group("config"), int(m.group("rep"))),
                    "task": m.group("task"),
                    "config": m.group("config"),
                    "rep": int(m.group("rep")),
                    "outcome": outcome,
                }
            )
            continue
        m = done_re.match(line)
        if m:
            done = max(done, int(m.group("done")))
            total = max(total, int(m.group("total")))
    state = "completed" if total and done >= total else "legacy"
    try:
        updated_at = datetime.fromtimestamp(track_path.stat().st_mtime, timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")
    except OSError:
        updated_at = None
    counts = {
        "batch_total": total,
        "batch_done": done,
        "batch_running": 0,
        "batch_skipped": 0,
        **buckets,
        "preflight_total": 0,
        "preflight_done": 0,
    }
    projected = {
        "kind": "legacy_track",
        "run_id": f"legacy-{run_name}",
        "run_key": f"legacy-{run_name}",
        "legacy_name": run_name,
        "state": state,
        "stage": "track.out",
        "created_at": updated_at,
        "updated_at": updated_at,
        "heartbeat_at": updated_at,
        "heartbeat_age_s": seconds_since(updated_at),
        "eta_s": None,
        "model": None,
        "thinking": None,
        "configs": [],
        "launch_metadata": "legacy_track",
        "launch_plan_identity": None,
        "preflight_state": "not_required",
        "results_root": None,
        "selection": {},
        "state_root": None,
        "workers": None,
        "workspace": None,
        "counts": counts,
        "active_count": 0,
        "failure_buckets": {k: v for k, v in buckets.items() if k not in {"ok", "empty"} and v},
        "paths": {"track": str(track_path)},
    }
    if detail in {"operational", "diagnostic"}:
        projected["recent_finished"] = recent[-30:]
        projected["active_cells"] = []
        projected["preflight"] = {}
    if detail == "diagnostic":
        projected["track_tail"] = lines[-100:]
    return projected


def discover_runs(
    state_root: str | Path,
    *,
    detail: str = "summary",
    include_legacy: bool = True,
    legacy_root: str | Path | None = None,
) -> list[dict[str, Any]]:
    root = Path(state_root)
    rows: list[dict[str, Any]] = []
    if root.exists():
        for child in sorted(root.iterdir()):
            if child.is_dir() and ((child / "manifest.json").exists() or (child / "status.json").exists()):
                rows.append(project_structured_run(child, detail=detail))
    if include_legacy:
        legacy = Path(legacy_root) if legacy_root is not None else root.parent.parent / "runs"
        if legacy.exists():
            for track in sorted(legacy.glob("*/track.out")):
                rows.append(project_legacy_track(track, detail=detail))
    rows.sort(key=lambda row: row.get("updated_at") or row.get("created_at") or "", reverse=True)
    return rows
