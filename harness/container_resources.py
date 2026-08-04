"""Enforce confirmed memory limits on DeepSWE Docker containers."""

from __future__ import annotations

import fcntl
import json
import math
import subprocess
from collections.abc import Iterator, Mapping
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from types import MappingProxyType

_GIB_BYTES = 1024**3
VERIFIER_MEMORY_EVENTS_SHELL_COMMAND = (
    "status=0; bash /tests/test.sh || status=$?; "
    "cat /sys/fs/cgroup/memory.events > "
    '/logs/verifier/memory-events.txt; exit "$status"'
)
_LABEL_PREFIX = "deep-swe-bench"
_CONTAINER_START_LOCK = "container-start.lock"
_CONTAINER_MEMORY_RESULT_FIELDS = frozenset(
    {
        "agent_resource_exhausted",
        "subject_memory_events",
        "verifier_memory_events",
        "verifier_resource_diagnostic",
        "verifier_resource_evidence_unavailable",
        "verifier_resource_exhausted",
    }
)
_DEFAULT_RESOURCE_POLICY: Mapping[str, object] = MappingProxyType(
    {
        "additional_swap_gib": 0.0,
        "host_reserve_gib": 12.0,
        "subject_memory_gib": 12.0,
        "verifier_memory_gib": 12.0,
    }
)


class ContainerStartHaltedError(RuntimeError):
    """Stop Docker creation after the resource supervisor halts a run."""


def read_resource_halt_reason(state_path: Path) -> str | None:
    """Read and validate the durable halt reason for one managed run."""
    halt_path = state_path / "resource-halt.json"
    if not halt_path.is_file():
        return None
    try:
        raw_document: object = json.loads(halt_path.read_text())
    except (json.JSONDecodeError, OSError) as error:
        raise ValueError(
            f"Container resource halt unreadable: {type(error).__name__}: {error}"
        ) from error
    if not isinstance(raw_document, Mapping):
        raise TypeError("Container resource halt invalid: expected an object")
    reason = raw_document.get("reason")
    if not isinstance(reason, str) or not reason:
        raise ValueError("Container resource halt invalid: reason is missing")
    return reason


@contextmanager
def managed_container_start_guard(
    container_labels: Mapping[str, str] | None,
) -> Iterator[None]:
    """Serialize managed container creation against run-level containment."""
    labels = container_labels or {}
    if labels.get(f"{_LABEL_PREFIX}.managed") != "true":
        yield
        return
    raw_state_path = labels.get(f"{_LABEL_PREFIX}.state-path")
    if not raw_state_path:
        raise TypeError(
            "Container resource labels invalid: managed container lacks state path"
        )
    state_path = Path(raw_state_path)
    state_path.mkdir(parents=True, exist_ok=True)
    with (state_path / _CONTAINER_START_LOCK).open("a+") as lock_file:
        fcntl.flock(lock_file.fileno(), fcntl.LOCK_SH)
        reason = read_resource_halt_reason(state_path)
        if reason is not None:
            raise ContainerStartHaltedError(reason)
        yield


def _require_container_role(role: str) -> None:
    """Require one of the two managed DeepSWE container roles."""
    if role not in {"subject", "verifier"}:
        raise ValueError(
            "Container resource role invalid: expected subject or verifier; "
            f"got {role!r}"
        )


def confirmed_container_labels(
    *,
    cell_identity: str,
    host_reserve_gib: float,
    launch_plan_identity: str,
    role: str,
    run_key: str,
    state_path: str,
) -> dict[str, str]:
    """Identify one managed container and its owning confirmed launch."""
    _require_container_role(role)
    host_reserve_bytes = _resource_gib_to_bytes(
        host_reserve_gib,
        "host reserve",
    )
    if host_reserve_bytes == 0:
        raise ValueError(
            "Container resource limit invalid: host reserve must be greater than zero"
        )
    return {
        f"{_LABEL_PREFIX}.cell-id": cell_identity,
        f"{_LABEL_PREFIX}.host-reserve-bytes": str(host_reserve_bytes),
        f"{_LABEL_PREFIX}.managed": "true",
        f"{_LABEL_PREFIX}.plan-identity": launch_plan_identity,
        f"{_LABEL_PREFIX}.role": role,
        f"{_LABEL_PREFIX}.run-key": run_key,
        f"{_LABEL_PREFIX}.state-path": state_path,
    }


def _resource_gib_to_bytes(value: float, resource_name: str) -> int:
    """Convert a finite non-negative GiB value to Docker's byte unit."""
    if not math.isfinite(value) or value < 0:
        raise ValueError(
            "Container resource limit invalid: expected finite non-negative "
            f"GiB for {resource_name}; got {value!r}"
        )
    return int(value * _GIB_BYTES)


def parse_cgroup_memory_events(content: str) -> dict[str, int]:
    """Parse Linux cgroup-v2 memory event counters by their kernel names."""
    events: dict[str, int] = {}
    for line_number, line in enumerate(content.splitlines(), start=1):
        fields = line.split()
        if len(fields) != 2:
            raise ValueError(
                "Container memory events invalid: expected name and count at "
                f"line {line_number}; got {line!r}"
            )
        event_name, raw_count = fields
        if event_name in events:
            raise ValueError(
                f"Container memory events invalid: duplicate event {event_name!r}"
            )
        try:
            count = int(raw_count)
        except ValueError as error:
            raise ValueError(
                "Container memory events invalid: expected integer count for "
                f"{event_name!r}; got {raw_count!r}"
            ) from error
        if count < 0:
            raise ValueError(
                "Container memory events invalid: count cannot be negative for "
                f"{event_name!r}"
            )
        events[event_name] = count
    return events


@dataclass(frozen=True, slots=True)
class DockerContainerOomEvidence:
    """Represent Docker OOM state without conflating unknown with false."""

    oom_killed: bool | None
    diagnostic: str | None


def inspect_docker_container_oom(
    container_name: str,
) -> DockerContainerOomEvidence:
    """Inspect Docker's init-process OOM state before container removal."""
    command = [
        "docker",
        "inspect",
        "--format",
        "{{.State.OOMKilled}}",
        container_name,
    ]
    try:
        completed = subprocess.run(
            command,
            capture_output=True,
            check=False,
            text=True,
            timeout=10,
        )
    except (OSError, subprocess.SubprocessError) as error:
        return DockerContainerOomEvidence(
            oom_killed=None,
            diagnostic=f"docker inspect failed: {error}",
        )
    output = completed.stdout.strip()
    if completed.returncode != 0:
        diagnostic = (completed.stdout + completed.stderr).strip()
        return DockerContainerOomEvidence(
            oom_killed=None,
            diagnostic=(
                "docker inspect returned "
                f"{completed.returncode}: {diagnostic or 'no diagnostic'}"
            ),
        )
    if output not in {"false", "true"}:
        return DockerContainerOomEvidence(
            oom_killed=None,
            diagnostic=f"docker inspect returned invalid OOM state: {output!r}",
        )
    return DockerContainerOomEvidence(
        oom_killed=output == "true",
        diagnostic=None,
    )


def run_managed_container_and_wait(
    command: list[str],
    *,
    container_labels: Mapping[str, str] | None,
    container_name: str,
    timeout: float,
) -> subprocess.CompletedProcess[str]:
    """Start a managed container under the lock, then wait without it."""
    with managed_container_start_guard(container_labels):
        started = subprocess.run(
            command,
            capture_output=True,
            check=False,
            text=True,
        )
    if started.returncode != 0:
        return started
    waited = subprocess.run(
        ["docker", "wait", container_name],
        capture_output=True,
        check=False,
        text=True,
        timeout=timeout,
    )
    try:
        logs = subprocess.run(
            ["docker", "logs", container_name],
            capture_output=True,
            check=False,
            text=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError) as error:
        logs = subprocess.CompletedProcess(
            args=["docker", "logs", container_name],
            returncode=1,
            stdout="",
            stderr=f"Docker logs unavailable: {error}",
        )
    if waited.returncode != 0:
        return subprocess.CompletedProcess(
            args=command,
            returncode=waited.returncode,
            stdout=logs.stdout,
            stderr=logs.stderr + waited.stdout + waited.stderr,
        )
    try:
        container_exit = int(waited.stdout.strip())
    except ValueError:
        return subprocess.CompletedProcess(
            args=command,
            returncode=1,
            stdout=logs.stdout,
            stderr=(
                logs.stderr
                + "Docker wait returned invalid container exit status: "
                + repr(waited.stdout.strip())
            ),
        )
    return subprocess.CompletedProcess(
        args=command,
        returncode=container_exit,
        stdout=logs.stdout,
        stderr=logs.stderr,
    )


def read_container_memory_events(container_name: str) -> dict[str, int]:
    """Read cgroup-v2 memory event counters from a running Docker container."""
    completed = subprocess.run(
        [
            "docker",
            "exec",
            container_name,
            "cat",
            "/sys/fs/cgroup/memory.events",
        ],
        capture_output=True,
        check=False,
        text=True,
        timeout=10,
    )
    if completed.returncode != 0:
        diagnostic = (completed.stdout + completed.stderr).strip()
        raise RuntimeError(
            "Container memory events unavailable: "
            f"container={container_name!r}; diagnostic={diagnostic!r}"
        )
    return parse_cgroup_memory_events(completed.stdout)


def record_subject_container_memory_status(
    container_name: str,
    memory_events_path: Path,
) -> dict[str, object]:
    """Persist and classify cgroup memory events before subject teardown."""
    events = read_container_memory_events(container_name)
    memory_events_path.write_text(json.dumps(events, sort_keys=True) + "\n")
    return classify_container_memory_events("subject", events)


def verifier_container_memory_status(
    memory_events_path: Path,
    *,
    oom_evidence: DockerContainerOomEvidence,
) -> dict[str, object]:
    """Classify verifier memory evidence without accepting unknown state."""
    if oom_evidence.oom_killed is True:
        return classify_container_memory_events("verifier", {"oom_kill": 1})
    if memory_events_path.is_file():
        try:
            events = parse_cgroup_memory_events(memory_events_path.read_text())
        except (OSError, ValueError) as error:
            return {
                "verifier_exit": "resource_evidence_unavailable",
                "verifier_resource_diagnostic": (
                    "verifier memory-events sidecar invalid: "
                    f"{type(error).__name__}: {error}"
                ),
                "verifier_resource_evidence_unavailable": True,
            }
        return classify_container_memory_events("verifier", events)
    diagnostic = oom_evidence.diagnostic or (
        "verifier memory-events sidecar is missing"
    )
    return {
        "verifier_exit": "resource_evidence_unavailable",
        "verifier_resource_diagnostic": diagnostic,
        "verifier_resource_evidence_unavailable": True,
    }


def container_memory_result_fields(
    status: Mapping[str, object],
) -> dict[str, object]:
    """Project cgroup exhaustion evidence into a canonical result record."""
    return {
        field_name: status[field_name]
        for field_name in _CONTAINER_MEMORY_RESULT_FIELDS
        if field_name in status
    }


def classify_container_memory_events(
    role: str,
    events: Mapping[str, int],
) -> dict[str, object]:
    """Classify cgroup OOM kills as subject or verifier exhaustion evidence."""
    _require_container_role(role)
    result: dict[str, object] = {f"{role}_memory_events": dict(events)}
    if events.get("oom_kill", 0) > 0 or events.get("oom_group_kill", 0) > 0:
        exhaustion_field = (
            "agent_resource_exhausted"
            if role == "subject"
            else "verifier_resource_exhausted"
        )
        result[exhaustion_field] = True
        if role == "verifier":
            result["verifier_exit"] = "memory_limit"
    return result


def planned_container_resource_docker_args(
    resource_policy: Mapping[str, object] | None,
    container_labels: Mapping[str, str] | None,
    *,
    role: str,
) -> list[str]:
    """Build role-specific Docker limits from one confirmed resource policy."""
    _require_container_role(role)
    policy = resource_policy or _DEFAULT_RESOURCE_POLICY
    memory_value = policy.get(f"{role}_memory_gib")
    additional_swap_value = policy.get("additional_swap_gib")
    if (
        isinstance(memory_value, bool)
        or not isinstance(memory_value, int | float)
        or isinstance(additional_swap_value, bool)
        or not isinstance(additional_swap_value, int | float)
    ):
        raise TypeError(
            "Container resource policy invalid: memory and additional swap "
            "must be numbers"
        )
    labels = dict(container_labels or {})
    if labels:
        labels[f"{_LABEL_PREFIX}.role"] = role
    return container_resource_docker_args(
        memory_gib=float(memory_value),
        additional_swap_gib=float(additional_swap_value),
        labels=labels,
    )


def container_resource_docker_args(
    *,
    memory_gib: float,
    additional_swap_gib: float,
    labels: Mapping[str, str],
) -> list[str]:
    """Build Docker arguments enforcing aggregate memory and ownership labels."""
    memory_bytes = _resource_gib_to_bytes(memory_gib, "memory")
    if memory_bytes == 0:
        raise ValueError(
            "Container resource limit invalid: memory must be greater than zero"
        )
    additional_swap_bytes = _resource_gib_to_bytes(
        additional_swap_gib,
        "additional swap",
    )
    arguments = [
        "--memory",
        str(memory_bytes),
        "--memory-swap",
        str(memory_bytes + additional_swap_bytes),
    ]
    for label_name, label_value in sorted(labels.items()):
        arguments.extend(["--label", f"{label_name}={label_value}"])
    return arguments
