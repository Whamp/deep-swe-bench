"""Behavior tests for enforceable container resource controls."""

from __future__ import annotations

import fcntl
import subprocess
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from harness import container_resources
from harness.container_resources import (
    ContainerStartHaltedError,
    DockerContainerOomEvidence,
    classify_container_memory_events,
    container_memory_result_fields,
    container_resource_docker_args,
    inspect_docker_container_oom,
    managed_container_start_guard,
    parse_cgroup_memory_events,
    run_managed_container_and_wait,
    verifier_container_memory_status,
)


def test_container_resource_docker_args_enforce_memory_without_extra_swap() -> None:
    """A confirmed memory limit becomes an aggregate Docker cgroup limit."""
    arguments = container_resource_docker_args(
        memory_gib=12.0,
        additional_swap_gib=0.0,
        labels={
            "deep-swe-bench.cell-id": "task-a/config@1.0.0/rep0",
            "deep-swe-bench.managed": "true",
        },
    )

    assert arguments == [
        "--memory",
        "12884901888",
        "--memory-swap",
        "12884901888",
        "--label",
        "deep-swe-bench.cell-id=task-a/config@1.0.0/rep0",
        "--label",
        "deep-swe-bench.managed=true",
    ]


def test_managed_container_start_guard_rejects_recorded_halt(
    tmp_path: Path,
) -> None:
    """No container starts after containment records a run halt."""
    state_path = tmp_path / "run-a"
    state_path.mkdir()
    (state_path / "resource-halt.json").write_text(
        '{"reason":"host memory reserve breached"}\n'
    )

    with (
        pytest.raises(
            ContainerStartHaltedError,
            match="host memory reserve breached",
        ),
        managed_container_start_guard(
            {
                "deep-swe-bench.managed": "true",
                "deep-swe-bench.state-path": str(state_path),
            }
        ),
    ):
        raise AssertionError("guard allowed container start")


def test_managed_container_wait_releases_start_lock(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Containment can take its exclusive lock while a verifier runs."""
    state_path = tmp_path / "state"
    state_path.mkdir()
    lock_path = state_path / "container-start.lock"
    lock_states: list[str] = []

    def fake_run(
        command: list[str], **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        if command[1] == "run":
            with lock_path.open("a+") as lock_file, pytest.raises(BlockingIOError):
                fcntl.flock(
                    lock_file.fileno(),
                    fcntl.LOCK_EX | fcntl.LOCK_NB,
                )
            lock_states.append("start_locked")
            return subprocess.CompletedProcess(command, 0, "container-id\n", "")
        if command[1] == "wait":
            with lock_path.open("a+") as lock_file:
                fcntl.flock(
                    lock_file.fileno(),
                    fcntl.LOCK_EX | fcntl.LOCK_NB,
                )
            lock_states.append("wait_unlocked")
            return subprocess.CompletedProcess(command, 0, "17\n", "")
        return subprocess.CompletedProcess(command, 0, "verifier output\n", "")

    monkeypatch.setattr(container_resources.subprocess, "run", fake_run)

    result = run_managed_container_and_wait(
        ["docker", "run", "-d", "image"],
        container_labels={
            "deep-swe-bench.managed": "true",
            "deep-swe-bench.state-path": str(state_path),
        },
        container_name="verifier",
        timeout=30,
    )

    assert lock_states == ["start_locked", "wait_unlocked"]
    assert result.returncode == 17
    assert result.stdout == "verifier output\n"


def test_docker_oom_inspection_preserves_timeout_as_unknown(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Inspection timeout is unavailable evidence, never a negative OOM."""

    def timeout(*args: object, **kwargs: object) -> object:
        raise subprocess.TimeoutExpired(cmd="docker inspect", timeout=10)

    monkeypatch.setattr(container_resources.subprocess, "run", timeout)

    evidence = inspect_docker_container_oom("verifier")

    assert evidence.oom_killed is None
    assert evidence.diagnostic is not None
    assert "timed out" in evidence.diagnostic


def test_verifier_container_memory_status_falls_back_after_shell_oom(
    tmp_path: Path,
) -> None:
    """Docker OOM state preserves invalid-verifier evidence without a sidecar."""
    missing_events = tmp_path / "memory-events.txt"

    status = verifier_container_memory_status(
        missing_events,
        oom_evidence=DockerContainerOomEvidence(
            oom_killed=True,
            diagnostic=None,
        ),
    )

    assert status == {
        "verifier_exit": "memory_limit",
        "verifier_memory_events": {"oom_kill": 1},
        "verifier_resource_exhausted": True,
    }


def test_verifier_container_oom_overrides_stale_sidecar(tmp_path: Path) -> None:
    """Current Docker OOM state wins over a prior attempt's sidecar."""
    events_path = tmp_path / "memory-events.txt"
    events_path.write_text("oom 0\noom_kill 0\n")

    status = verifier_container_memory_status(
        events_path,
        oom_evidence=DockerContainerOomEvidence(
            oom_killed=True,
            diagnostic=None,
        ),
    )

    assert status["verifier_resource_exhausted"] is True
    assert status["verifier_memory_events"] == {"oom_kill": 1}


def test_verifier_container_memory_status_retries_unavailable_evidence(
    tmp_path: Path,
) -> None:
    """Missing sidecar plus unavailable Docker state cannot become no-OOM."""
    status = verifier_container_memory_status(
        tmp_path / "missing.txt",
        oom_evidence=DockerContainerOomEvidence(
            oom_killed=None,
            diagnostic="docker inspect timed out after 10s",
        ),
    )

    assert status == {
        "verifier_exit": "resource_evidence_unavailable",
        "verifier_resource_diagnostic": "docker inspect timed out after 10s",
        "verifier_resource_evidence_unavailable": True,
    }


def test_container_memory_result_fields_preserve_only_resource_evidence() -> None:
    """Runner result construction keeps role evidence without unrelated status."""
    fields = container_memory_result_fields(
        {
            "agent_resource_exhausted": True,
            "subject_memory_events": {"oom_kill": 1},
            "verifier_exit": "memory_limit",
            "verifier_memory_events": {"oom_kill": 2},
            "verifier_resource_diagnostic": "inspect failed",
            "verifier_resource_evidence_unavailable": True,
            "verifier_resource_exhausted": True,
            "unrelated": "discarded",
        }
    )

    assert fields == {
        "agent_resource_exhausted": True,
        "subject_memory_events": {"oom_kill": 1},
        "verifier_memory_events": {"oom_kill": 2},
        "verifier_resource_diagnostic": "inspect failed",
        "verifier_resource_evidence_unavailable": True,
        "verifier_resource_exhausted": True,
    }


def test_cgroup_memory_events_classify_subject_and_verifier_exhaustion() -> None:
    """Only cgroup OOM kills classify role-specific resource exhaustion."""
    events = parse_cgroup_memory_events(
        "low 4\nhigh 8\nmax 2\noom 3\noom_kill 1\noom_group_kill 0\n"
    )

    assert classify_container_memory_events("subject", events) == {
        "agent_resource_exhausted": True,
        "subject_memory_events": events,
    }
    assert classify_container_memory_events("verifier", events) == {
        "verifier_exit": "memory_limit",
        "verifier_resource_exhausted": True,
        "verifier_memory_events": events,
    }
    assert classify_container_memory_events(
        "subject",
        parse_cgroup_memory_events("low 0\nhigh 0\nmax 0\noom 0\noom_kill 0\n"),
    ) == {
        "subject_memory_events": {
            "high": 0,
            "low": 0,
            "max": 0,
            "oom": 0,
            "oom_kill": 0,
        }
    }


@given(
    memory_gib=st.integers(min_value=1, max_value=128),
    additional_swap_gib=st.integers(min_value=0, max_value=128),
)
def test_container_resource_docker_args_preserve_total_memory_plus_swap(
    memory_gib: int,
    additional_swap_gib: int,
) -> None:
    """Docker's combined memory-and-swap limit includes only approved swap."""
    arguments = container_resource_docker_args(
        memory_gib=float(memory_gib),
        additional_swap_gib=float(additional_swap_gib),
        labels={},
    )

    memory_bytes = int(arguments[1])
    memory_swap_bytes = int(arguments[3])
    assert memory_bytes == memory_gib * 1024**3
    assert memory_swap_bytes - memory_bytes == additional_swap_gib * 1024**3
