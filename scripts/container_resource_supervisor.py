#!/usr/bin/env python3
"""Contain managed DeepSWE runs before host memory pressure becomes an OOM.

Every managed container must already have a Docker cgroup memory limit. This
supervisor is the second line of defense: it watches host headroom, writes a
durable run halt record, and stops all containers owned by the selected run. It
never kills individual processes and never mutates canonical result artifacts.
"""

from __future__ import annotations

import argparse
import fcntl
import json
import math
import os
import signal
import subprocess
import tempfile
import time
from collections.abc import Iterator, Mapping, Sequence
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import IO, cast

REPO = Path(__file__).resolve().parents[1]
DEFAULT_LOG_DIR = REPO / "runs" / "container-resource-supervisor"
_MANAGED_LABEL = "deep-swe-bench.managed"
_RUN_KEY_LABEL = "deep-swe-bench.run-key"
_STATE_PATH_LABEL = "deep-swe-bench.state-path"
_HOST_RESERVE_LABEL = "deep-swe-bench.host-reserve-bytes"


@dataclass(frozen=True, slots=True)
class HostResourceSnapshot:
    """Report host memory currently available for new allocations."""

    available_memory_bytes: int


@dataclass(frozen=True, slots=True)
class ManagedContainer:
    """Describe one labeled DeepSWE container and its cgroup memory state."""

    name: str
    run_key: str
    state_path: Path
    memory_usage_bytes: int
    memory_limit_bytes: int
    host_reserve_bytes: int


@dataclass(frozen=True, slots=True)
class ResourceContainmentDecision:
    """Identify one complete run that the supervisor must halt."""

    run_key: str
    state_path: Path
    container_names: tuple[str, ...]
    reason: str
    available_memory_bytes: int
    host_reserve_bytes: int


def _run_containment_decision(
    snapshot: HostResourceSnapshot,
    containers: Sequence[ManagedContainer],
    selected: ManagedContainer,
    reason: str,
) -> ResourceContainmentDecision:
    """Build one run-level decision from a selected managed container."""
    owned = sorted(
        (
            container
            for container in containers
            if container.run_key == selected.run_key
        ),
        key=lambda container: container.name,
    )
    return ResourceContainmentDecision(
        run_key=selected.run_key,
        state_path=selected.state_path,
        container_names=tuple(container.name for container in owned),
        reason=reason,
        available_memory_bytes=snapshot.available_memory_bytes,
        host_reserve_bytes=max(container.host_reserve_bytes for container in owned),
    )


def select_resource_containment(
    snapshot: HostResourceSnapshot,
    containers: Sequence[ManagedContainer],
) -> ResourceContainmentDecision | None:
    """Select the run to halt for an invalid limit or host reserve breach."""
    ordered = sorted(containers, key=lambda container: container.name)
    for container in ordered:
        if container.memory_limit_bytes <= 0:
            return _run_containment_decision(
                snapshot,
                ordered,
                container,
                "managed container has no hard memory limit",
            )
        if container.host_reserve_bytes <= 0:
            return _run_containment_decision(
                snapshot,
                ordered,
                container,
                "managed container has no host memory reserve",
            )
    if not ordered:
        return None
    required_reserve = max(container.host_reserve_bytes for container in ordered)
    if snapshot.available_memory_bytes >= required_reserve:
        return None
    usage_by_run: dict[str, int] = {}
    for container in ordered:
        usage_by_run[container.run_key] = (
            usage_by_run.get(container.run_key, 0) + container.memory_usage_bytes
        )
    selected_run = min(
        usage_by_run,
        key=lambda run_key: (-usage_by_run[run_key], run_key),
    )
    selected = next(
        container for container in ordered if container.run_key == selected_run
    )
    return _run_containment_decision(
        snapshot,
        ordered,
        selected,
        "host memory reserve breached",
    )


class ResourcePressureTracker:
    """Require sustained host pressure while failing invalid limits immediately."""

    def __init__(self, *, consecutive_samples: int) -> None:
        """Configure the number of pressure samples required for containment."""
        if consecutive_samples < 1:
            raise ValueError("Resource pressure samples invalid: expected at least one")
        self.consecutive_samples = consecutive_samples
        self._pressure_samples = 0

    def observe(
        self,
        snapshot: HostResourceSnapshot,
        containers: Sequence[ManagedContainer],
    ) -> ResourceContainmentDecision | None:
        """Return a containment decision after invalid or sustained pressure."""
        decision = select_resource_containment(snapshot, containers)
        if decision is None:
            self._pressure_samples = 0
            return None
        if decision.reason != "host memory reserve breached":
            self._pressure_samples = 0
            return decision
        self._pressure_samples += 1
        if self._pressure_samples < self.consecutive_samples:
            return None
        self._pressure_samples = 0
        return decision


def _atomic_create_json(path: Path, document: Mapping[str, object]) -> None:
    """Create one JSON file atomically without replacing prior evidence."""
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists():
        return
    with tempfile.NamedTemporaryFile(
        dir=path.parent,
        mode="w",
        prefix=f".{path.name}.",
        delete=False,
    ) as temporary_file:
        temporary_path = Path(temporary_file.name)
        temporary_file.write(
            json.dumps(document, allow_nan=False, indent=2, sort_keys=True) + "\n"
        )
    try:
        try:
            os.link(temporary_path, path)
        except FileExistsError:
            return
    finally:
        temporary_path.unlink(missing_ok=True)


def write_resource_halt(
    decision: ResourceContainmentDecision,
    *,
    observed_at: str,
) -> Path:
    """Persist the first supervisor containment decision for operator recovery."""
    halt_path = decision.state_path / "resource-halt.json"
    document = {
        **asdict(decision),
        "container_names": list(decision.container_names),
        "observed_at": observed_at,
        "state_path": str(decision.state_path),
    }
    _atomic_create_json(halt_path, document)
    return halt_path


def clear_resource_halt(
    state_path: Path,
    *,
    cleared_at: str,
    clearance_reason: str,
) -> Path:
    """Archive and clear one halt after an operator names why resume is safe."""
    if not clearance_reason.strip():
        raise ValueError("Resource halt clearance invalid: reason cannot be empty")
    halt_path = state_path / "resource-halt.json"
    if not halt_path.is_file():
        raise FileNotFoundError(f"Resource halt clearance missing: {halt_path}")
    raw_document: object = json.loads(halt_path.read_text())
    if not isinstance(raw_document, Mapping) or not all(
        isinstance(key, str) for key in raw_document
    ):
        raise TypeError(
            "Resource halt clearance invalid: halt record must be an object "
            "with string keys"
        )
    halt_document = cast(Mapping[str, object], raw_document)
    archive_document: dict[str, object] = {
        **halt_document,
        "clearance": {
            "cleared_at": cleared_at,
            "reason": clearance_reason.strip(),
        },
    }
    safe_timestamp = "".join(
        character if character.isalnum() else "-" for character in cleared_at
    ).strip("-")
    archive_path = state_path / "resource-halts" / f"cleared-{safe_timestamp}.json"
    if archive_path.exists():
        raise FileExistsError(f"Resource halt clearance archive exists: {archive_path}")
    _atomic_create_json(archive_path, archive_document)
    halt_path.unlink()
    return archive_path


def _run(
    command: Sequence[str], *, timeout: float = 30
) -> subprocess.CompletedProcess[str]:
    """Run one bounded host command and retain diagnostics for fail-closed errors."""
    return subprocess.run(
        list(command),
        capture_output=True,
        check=False,
        text=True,
        timeout=timeout,
    )


def _require_command_output(command: Sequence[str], *, timeout: float = 30) -> str:
    """Return command output or raise a searchable supervisor failure."""
    completed = _run(command, timeout=timeout)
    if completed.returncode != 0:
        diagnostic = (completed.stdout + completed.stderr).strip()
        raise RuntimeError(
            "Container resource supervisor command failed: "
            f"command={list(command)!r}; diagnostic={diagnostic!r}"
        )
    return completed.stdout


def _parse_size_bytes(value: str) -> int:
    """Parse Docker's binary memory sizes into bytes."""
    units = {
        "B": 1,
        "KiB": 1024,
        "MiB": 1024**2,
        "GiB": 1024**3,
        "TiB": 1024**4,
        "kB": 1000,
        "MB": 1000**2,
        "GB": 1000**3,
    }
    for unit in sorted(units, key=len, reverse=True):
        if not value.endswith(unit):
            continue
        raw_number = value[: -len(unit)]
        try:
            number = float(raw_number)
        except ValueError as error:
            raise ValueError(
                f"Container resource supervisor size invalid: {value!r}"
            ) from error
        if not math.isfinite(number) or number < 0:
            raise ValueError(f"Container resource supervisor size invalid: {value!r}")
        return int(number * units[unit])
    raise ValueError(f"Container resource supervisor size invalid: {value!r}")


def parse_docker_memory_stats(
    content: str,
    *,
    expected_names: Sequence[str],
) -> dict[str, int]:
    """Parse aggregate usage and require one Docker stat per managed container."""
    expected = set(expected_names)
    usage_by_name: dict[str, int] = {}
    for line_number, line in enumerate(content.splitlines(), start=1):
        name, separator, usage = line.partition("\t")
        if not separator or not name or not usage:
            raise ValueError(
                "Container resource supervisor stats malformed line "
                f"{line_number}: {line!r}"
            )
        if name not in expected:
            raise ValueError(
                "Container resource supervisor stats included unexpected "
                f"container: {name}"
            )
        if name in usage_by_name:
            raise ValueError(
                f"Container resource supervisor stats duplicated container: {name}"
            )
        size_fields = usage.split("/")
        if len(size_fields) != 2 or not all(
            size_field.strip() for size_field in size_fields
        ):
            raise ValueError(
                "Container resource supervisor stats malformed line "
                f"{line_number}: {line!r}"
            )
        used_bytes = _parse_size_bytes(size_fields[0].strip())
        limit_bytes = _parse_size_bytes(size_fields[1].strip())
        if limit_bytes <= 0:
            raise ValueError(
                "Container resource supervisor stats limit invalid: "
                f"container={name}; limit={size_fields[1].strip()!r}"
            )
        usage_by_name[name] = used_bytes
    missing = sorted(expected - set(usage_by_name))
    if missing:
        raise ValueError(
            "Container resource supervisor stats missing usage for managed "
            f"containers: {', '.join(missing)}"
        )
    return usage_by_name


def read_host_resource_snapshot() -> HostResourceSnapshot:
    """Read available host memory from Linux procfs."""
    fields: dict[str, int] = {}
    for line in Path("/proc/meminfo").read_text().splitlines():
        name, separator, raw_value = line.partition(":")
        if not separator:
            continue
        value_fields = raw_value.split()
        if value_fields:
            fields[name] = int(value_fields[0]) * 1024
    available_memory_bytes = fields.get("MemAvailable", 0)
    if available_memory_bytes <= 0:
        raise RuntimeError(
            "Container resource supervisor host memory unavailable: "
            "MemAvailable is missing"
        )
    return HostResourceSnapshot(available_memory_bytes=available_memory_bytes)


def read_managed_containers() -> list[ManagedContainer]:
    """Read labeled Docker containers, hard limits, and current aggregate usage."""
    names = [
        line
        for line in _require_command_output(
            [
                "docker",
                "ps",
                "--filter",
                f"label={_MANAGED_LABEL}=true",
                "--format",
                "{{.Names}}",
            ]
        ).splitlines()
        if line
    ]
    if not names:
        return []
    raw_inspection: object = json.loads(
        _require_command_output(["docker", "inspect", *names])
    )
    if not isinstance(raw_inspection, list):
        raise TypeError(
            "Container resource supervisor inspection invalid: expected a list"
        )
    stats = _require_command_output(
        [
            "docker",
            "stats",
            "--no-stream",
            "--format",
            "{{.Name}}\\t{{.MemUsage}}",
            *names,
        ],
        timeout=60,
    )
    usage_by_name = parse_docker_memory_stats(
        stats,
        expected_names=names,
    )
    containers: list[ManagedContainer] = []
    for raw_container in raw_inspection:
        if not isinstance(raw_container, Mapping):
            raise TypeError(
                "Container resource supervisor inspection invalid: "
                "container must be an object"
            )
        name = str(raw_container.get("Name", "")).lstrip("/")
        config = raw_container.get("Config")
        host_config = raw_container.get("HostConfig")
        if not isinstance(config, Mapping) or not isinstance(host_config, Mapping):
            raise TypeError(
                "Container resource supervisor inspection invalid: "
                f"container={name!r} lacks config"
            )
        labels = config.get("Labels")
        if not isinstance(labels, Mapping):
            labels = {}
        run_key = labels.get(_RUN_KEY_LABEL)
        state_path = labels.get(_STATE_PATH_LABEL)
        raw_reserve = labels.get(_HOST_RESERVE_LABEL)
        if not isinstance(run_key, str) or not isinstance(state_path, str):
            raise TypeError(
                "Container resource supervisor labels invalid: "
                f"container={name!r} lacks run ownership"
            )
        try:
            host_reserve_bytes = int(str(raw_reserve))
        except (TypeError, ValueError):
            host_reserve_bytes = 0
        memory_limit = host_config.get("Memory", 0)
        if isinstance(memory_limit, bool) or not isinstance(memory_limit, int):
            memory_limit = 0
        containers.append(
            ManagedContainer(
                name=name,
                run_key=run_key,
                state_path=Path(state_path),
                memory_usage_bytes=usage_by_name[name],
                memory_limit_bytes=memory_limit,
                host_reserve_bytes=host_reserve_bytes,
            )
        )
    return sorted(containers, key=lambda container: container.name)


def _append_jsonl(path: Path, document: Mapping[str, object]) -> None:
    """Append one durable supervisor event outside canonical result artifacts."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as output:
        output.write(json.dumps(document, sort_keys=True) + "\n")


def _utc_now() -> str:
    """Return one UTC timestamp for durable supervisor evidence."""
    return datetime.now(UTC).isoformat()


def _managed_run_container_names(run_key: str) -> tuple[str, ...]:
    """List every currently running managed container owned by one run."""
    output = _require_command_output(
        [
            "docker",
            "ps",
            "--filter",
            f"label={_MANAGED_LABEL}=true",
            "--filter",
            f"label={_RUN_KEY_LABEL}={run_key}",
            "--format",
            "{{.Names}}",
        ]
    )
    return tuple(sorted(line for line in output.splitlines() if line))


@contextmanager
def _exclusive_container_start_lock(state_path: Path) -> Iterator[None]:
    """Block run-owned Docker creation for complete containment."""
    state_path.mkdir(parents=True, exist_ok=True)
    with (state_path / "container-start.lock").open("a+") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_EX)
        yield


def contain_resource_decision(
    decision: ResourceContainmentDecision,
    *,
    event_log: Path,
    dry_run: bool,
) -> None:
    """Write a halt record and stop every container owned by the selected run."""
    observed_at = _utc_now()
    event: dict[str, object] = {
        "event": "resource_containment",
        "dry_run": dry_run,
        "observed_at": observed_at,
        **asdict(decision),
        "state_path": str(decision.state_path),
    }
    if not dry_run:
        stop_errors: list[dict[str, str]] = []
        with _exclusive_container_start_lock(decision.state_path):
            halt_path = write_resource_halt(decision, observed_at=observed_at)
            event["halt_path"] = str(halt_path)
            while True:
                container_names = _managed_run_container_names(decision.run_key)
                if not container_names:
                    break
                for container_name in container_names:
                    completed = _run(
                        ["docker", "stop", "--time", "10", container_name],
                        timeout=20,
                    )
                    if completed.returncode != 0:
                        diagnostic = (completed.stdout + completed.stderr).strip()
                        stop_errors.append(
                            {
                                "container": container_name,
                                "diagnostic": diagnostic,
                            }
                        )
                if stop_errors:
                    break
        if stop_errors:
            event["stop_errors"] = stop_errors
    _append_jsonl(event_log, event)


@contextmanager
def _locked_pidfile(path: Path) -> Iterator[IO[str]]:
    """Hold the singleton supervisor lock for the complete process lifetime."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a+", encoding="utf-8") as pidfile:
        try:
            fcntl.flock(pidfile.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError(
                f"Container resource supervisor already running: pidfile={path}"
            ) from error
        pidfile.seek(0)
        pidfile.truncate()
        pidfile.write(str(os.getpid()))
        pidfile.flush()
        try:
            yield pidfile
        finally:
            path.unlink(missing_ok=True)


def _parser() -> argparse.ArgumentParser:
    """Build the persistent resource supervisor command interface."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--interval", type=float, default=2.0)
    parser.add_argument("--consecutive", type=int, default=3)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--once", action="store_true")
    parser.add_argument("--clear-halt", type=Path)
    parser.add_argument("--clearance-reason")
    parser.add_argument(
        "--event-log",
        type=Path,
        default=DEFAULT_LOG_DIR / "events.ndjson",
    )
    parser.add_argument(
        "--pidfile",
        type=Path,
        default=DEFAULT_LOG_DIR / "supervisor.pid",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the singleton host resource supervisor until stopped."""
    arguments = _parser().parse_args(argv)
    if arguments.clear_halt is not None:
        if arguments.clearance_reason is None:
            raise ValueError("Resource halt clearance requires --clearance-reason")
        archive_path = clear_resource_halt(
            arguments.clear_halt,
            cleared_at=_utc_now(),
            clearance_reason=arguments.clearance_reason,
        )
        print(f"Resource halt archived: {archive_path}")
        return 0
    if arguments.clearance_reason is not None:
        raise ValueError("Resource halt clearance requires --clear-halt")
    if arguments.interval <= 0:
        raise ValueError("Resource supervisor interval must be positive")
    tracker = ResourcePressureTracker(consecutive_samples=arguments.consecutive)
    stop_requested = False

    def request_stop(signum: int, frame: object) -> None:
        del signum, frame
        nonlocal stop_requested
        stop_requested = True

    signal.signal(signal.SIGINT, request_stop)
    signal.signal(signal.SIGTERM, request_stop)
    with _locked_pidfile(arguments.pidfile):
        _append_jsonl(
            arguments.event_log,
            {
                "event": "resource_supervisor_started",
                "observed_at": _utc_now(),
                "pid": os.getpid(),
            },
        )
        while not stop_requested:
            snapshot = read_host_resource_snapshot()
            containers = read_managed_containers()
            decision = tracker.observe(snapshot, containers)
            if decision is not None:
                contain_resource_decision(
                    decision,
                    event_log=arguments.event_log,
                    dry_run=arguments.dry_run,
                )
            if arguments.once:
                break
            time.sleep(arguments.interval)
        _append_jsonl(
            arguments.event_log,
            {
                "event": "resource_supervisor_stopped",
                "observed_at": _utc_now(),
                "pid": os.getpid(),
            },
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
