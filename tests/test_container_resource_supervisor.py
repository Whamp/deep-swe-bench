"""Behavior tests for host-level DeepSWE resource containment."""

from __future__ import annotations

import json
import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest

import scripts.container_resource_supervisor as resource_supervisor
from scripts.container_resource_supervisor import (
    HostResourceSnapshot,
    ManagedContainer,
    ResourcePressureTracker,
    clear_resource_halt,
    contain_resource_decision,
    parse_docker_memory_stats,
    select_resource_containment,
    write_resource_halt,
)


def _container(
    tmp_path: Path,
    *,
    name: str,
    run_key: str,
    usage_gib: float,
    limit_gib: float = 12.0,
) -> ManagedContainer:
    return ManagedContainer(
        name=name,
        run_key=run_key,
        state_path=tmp_path / run_key,
        memory_usage_bytes=int(usage_gib * 1024**3),
        memory_limit_bytes=int(limit_gib * 1024**3),
        host_reserve_bytes=12 * 1024**3,
    )


def _docker_inspection(name: str) -> str:
    return json.dumps(
        [
            {
                "Name": f"/{name}",
                "Config": {
                    "Labels": {
                        "deep-swe-bench.run-key": "run-a",
                        "deep-swe-bench.state-path": "/tmp/run-a",
                        "deep-swe-bench.host-reserve-bytes": str(12 * 1024**3),
                    }
                },
                "HostConfig": {"Memory": 12 * 1024**3},
            }
        ]
    )


def _successful_docker_snapshot(
    name: str,
    *,
    usage_gib: int,
) -> list[subprocess.CompletedProcess[str]]:
    return [
        subprocess.CompletedProcess([], 0, f"{name}\n", ""),
        subprocess.CompletedProcess([], 0, _docker_inspection(name), ""),
        subprocess.CompletedProcess(
            [],
            0,
            f"{name}\t{usage_gib}GiB / 12GiB\n",
            "",
        ),
    ]


def _docker_stats_eof_snapshot(
    name: str,
) -> list[subprocess.CompletedProcess[str]]:
    return [
        subprocess.CompletedProcess([], 0, f"{name}\n", ""),
        subprocess.CompletedProcess([], 0, _docker_inspection(name), ""),
        subprocess.CompletedProcess([], 1, "", "EOF\n"),
    ]


def _mock_subprocess_sequence(
    monkeypatch: pytest.MonkeyPatch,
    responses: list[subprocess.CompletedProcess[str]],
) -> list[list[str]]:
    response_iterator = iter(responses)
    commands: list[list[str]] = []

    def fake_run(
        command: list[str],
        **kwargs: object,
    ) -> subprocess.CompletedProcess[str]:
        del kwargs
        commands.append(command)
        return next(response_iterator)

    monkeypatch.setattr(resource_supervisor.subprocess, "run", fake_run)
    return commands


def test_read_managed_containers_resamples_after_docker_stats_eof(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A container teardown race cannot terminate resource monitoring."""
    commands = _mock_subprocess_sequence(
        monkeypatch,
        [
            subprocess.CompletedProcess([], 0, "tearing-down\n", ""),
            subprocess.CompletedProcess([], 0, _docker_inspection("tearing-down"), ""),
            subprocess.CompletedProcess(
                [],
                1,
                "tearing-down\t1GiB / 12GiB\n",
                "EOF\n",
            ),
            subprocess.CompletedProcess([], 0, "remaining\n", ""),
            subprocess.CompletedProcess([], 0, _docker_inspection("remaining"), ""),
            subprocess.CompletedProcess(
                [],
                0,
                "remaining\t2GiB / 12GiB\n",
                "",
            ),
        ],
    )

    containers = resource_supervisor.read_managed_containers()

    assert containers == [
        ManagedContainer(
            name="remaining",
            run_key="run-a",
            state_path=Path("/tmp/run-a"),
            memory_usage_bytes=2 * 1024**3,
            memory_limit_bytes=12 * 1024**3,
            host_reserve_bytes=12 * 1024**3,
        )
    ]
    assert commands[2][-1] == "tearing-down"
    assert commands[5][-1] == "remaining"


def test_read_managed_containers_raises_after_bounded_stats_eof_resampling(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Persistent Docker stats EOF errors fail hard after one resample."""
    commands = _mock_subprocess_sequence(
        monkeypatch,
        [
            subprocess.CompletedProcess([], 0, "container-a\n", ""),
            subprocess.CompletedProcess([], 0, _docker_inspection("container-a"), ""),
            subprocess.CompletedProcess([], 1, "", "EOF\n"),
            subprocess.CompletedProcess([], 0, "container-a\n", ""),
            subprocess.CompletedProcess([], 0, _docker_inspection("container-a"), ""),
            subprocess.CompletedProcess([], 1, "", "EOF\n"),
        ],
    )

    with pytest.raises(resource_supervisor._DockerStatsSnapshotRace):
        resource_supervisor.read_managed_containers()

    assert len(commands) == 6
    assert sum(command[1] == "stats" for command in commands) == 2


def test_read_managed_containers_does_not_retry_other_docker_errors(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Non-teardown Docker failures remain immediate hard failures."""
    commands = _mock_subprocess_sequence(
        monkeypatch,
        [
            subprocess.CompletedProcess([], 0, "container-a\n", ""),
            subprocess.CompletedProcess([], 0, _docker_inspection("container-a"), ""),
            subprocess.CompletedProcess([], 1, "", "permission denied\n"),
        ],
    )

    with pytest.raises(RuntimeError, match="diagnostic='permission denied'"):
        resource_supervisor.read_managed_containers()

    assert len(commands) == 3
    assert commands[-1][1] == "stats"


def test_read_managed_containers_returns_normal_sample_without_resampling(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A complete Docker snapshot returns its resource accounting directly."""
    commands = _mock_subprocess_sequence(
        monkeypatch,
        [
            subprocess.CompletedProcess([], 0, "container-a\n", ""),
            subprocess.CompletedProcess([], 0, _docker_inspection("container-a"), ""),
            subprocess.CompletedProcess(
                [],
                0,
                "container-a\t3GiB / 12GiB\n",
                "",
            ),
        ],
    )

    containers = resource_supervisor.read_managed_containers()

    assert containers[0].name == "container-a"
    assert containers[0].memory_usage_bytes == 3 * 1024**3
    assert len(commands) == 3


def test_main_continues_polling_after_docker_stats_teardown_eof(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The running supervisor survives teardown and completes another poll."""
    commands = _mock_subprocess_sequence(
        monkeypatch,
        [
            *_docker_stats_eof_snapshot("tearing-down"),
            *_successful_docker_snapshot("remaining", usage_gib=2),
            *_successful_docker_snapshot("remaining", usage_gib=3),
        ],
    )
    monkeypatch.setattr(
        resource_supervisor,
        "read_host_resource_snapshot",
        lambda: HostResourceSnapshot(available_memory_bytes=48 * 1024**3),
    )
    stop_supervisor: Callable[[int, object], None] | None = None
    sleep_intervals: list[float] = []

    def fake_signal(
        signum: int,
        handler: Callable[[int, object], None],
    ) -> None:
        nonlocal stop_supervisor
        if signum == resource_supervisor.signal.SIGTERM:
            stop_supervisor = handler

    def fake_sleep(interval: float) -> None:
        sleep_intervals.append(interval)
        if len(sleep_intervals) == 2:
            assert stop_supervisor is not None
            stop_supervisor(resource_supervisor.signal.SIGTERM, None)

    monkeypatch.setattr(resource_supervisor.signal, "signal", fake_signal)
    monkeypatch.setattr(resource_supervisor.time, "sleep", fake_sleep)
    event_log = tmp_path / "events.ndjson"
    pidfile = tmp_path / "supervisor.pid"

    exit_code = resource_supervisor.main(
        [
            "--interval",
            "0.25",
            "--event-log",
            str(event_log),
            "--pidfile",
            str(pidfile),
        ]
    )

    events = [json.loads(line) for line in event_log.read_text().splitlines()]
    assert exit_code == 0
    assert [event["event"] for event in events] == [
        "resource_supervisor_started",
        "resource_supervisor_stopped",
    ]
    assert sleep_intervals == [0.25, 0.25]
    assert [command[-1] for command in commands if command[1] == "stats"] == [
        "tearing-down",
        "remaining",
        "remaining",
    ]
    assert not pidfile.exists()


def test_main_raises_after_persistent_docker_stats_eof(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The main loop fails closed when both Docker snapshots end in EOF."""
    commands = _mock_subprocess_sequence(
        monkeypatch,
        [
            *_docker_stats_eof_snapshot("container-a"),
            *_docker_stats_eof_snapshot("container-a"),
        ],
    )
    monkeypatch.setattr(
        resource_supervisor,
        "read_host_resource_snapshot",
        lambda: HostResourceSnapshot(available_memory_bytes=48 * 1024**3),
    )
    monkeypatch.setattr(resource_supervisor.signal, "signal", lambda *args: None)
    sleep_intervals: list[float] = []
    monkeypatch.setattr(
        resource_supervisor.time,
        "sleep",
        lambda interval: sleep_intervals.append(interval),
    )
    event_log = tmp_path / "events.ndjson"
    pidfile = tmp_path / "supervisor.pid"

    with pytest.raises(resource_supervisor._DockerStatsSnapshotRace):
        resource_supervisor.main(
            [
                "--interval",
                "0.25",
                "--event-log",
                str(event_log),
                "--pidfile",
                str(pidfile),
            ]
        )

    events = [json.loads(line) for line in event_log.read_text().splitlines()]
    assert [event["event"] for event in events] == ["resource_supervisor_started"]
    assert sleep_intervals == []
    assert len(commands) == 6
    assert not pidfile.exists()


def test_docker_memory_stats_require_every_managed_container() -> None:
    """Missing or malformed usage cannot silently bias run selection."""
    with pytest.raises(
        ValueError,
        match="missing usage for managed containers: run-b",
    ):
        parse_docker_memory_stats(
            "run-a\t1GiB / 12GiB\n",
            expected_names=("run-a", "run-b"),
        )
    malformed_rows = (
        "run-a has no separator\n",
        "run-a\t1GiB\n",
        "run-a\t-1GiB / 12GiB\n",
        "run-a\t1GiB / garbage\n",
        "run-a\t1GiB / 12GiB / 13GiB\n",
        "run-a\tnanGiB / 12GiB\n",
        "run-a\tinfGiB / 12GiB\n",
        "run-a\t1GiB / 0GiB\n",
        "run-a\t1GiB / -12GiB\n",
        "run-a\t1GiB / nanGiB\n",
        "run-a\t1GiB / infGiB\n",
    )
    for row in malformed_rows:
        with pytest.raises(
            ValueError,
            match="(malformed line|size invalid|stats limit invalid)",
        ):
            parse_docker_memory_stats(
                row,
                expected_names=("run-a",),
            )


def test_supervisor_contains_largest_run_under_sustained_host_pressure(
    tmp_path: Path,
) -> None:
    """Distributed memory pressure is contained at run granularity."""
    containers = [
        _container(
            tmp_path,
            name="run-a-1",
            run_key="run-a",
            usage_gib=7.0,
        ),
        _container(
            tmp_path,
            name="run-a-2",
            run_key="run-a",
            usage_gib=6.0,
        ),
        _container(
            tmp_path,
            name="run-b-1",
            run_key="run-b",
            usage_gib=9.0,
        ),
    ]
    snapshot = HostResourceSnapshot(available_memory_bytes=8 * 1024**3)
    tracker = ResourcePressureTracker(consecutive_samples=3)

    assert tracker.observe(snapshot, containers) is None
    assert tracker.observe(snapshot, containers) is None
    decision = tracker.observe(snapshot, containers)

    assert decision == select_resource_containment(snapshot, containers)
    assert decision is not None
    assert decision.run_key == "run-a"
    assert decision.container_names == ("run-a-1", "run-a-2")
    assert decision.reason == "host memory reserve breached"


def test_supervisor_immediately_contains_managed_container_without_hard_limit(
    tmp_path: Path,
) -> None:
    """A managed container without memory.max fails closed immediately."""
    container = _container(
        tmp_path,
        name="uncapped",
        run_key="run-a",
        usage_gib=1.0,
        limit_gib=0.0,
    )
    healthy_host = HostResourceSnapshot(available_memory_bytes=48 * 1024**3)
    tracker = ResourcePressureTracker(consecutive_samples=3)

    decision = tracker.observe(healthy_host, [container])

    assert decision is not None
    assert decision.run_key == "run-a"
    assert decision.reason == "managed container has no hard memory limit"


def test_containment_reenumerates_until_owned_containers_are_gone(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """A container appearing during containment is stopped before unlock."""
    containers = [
        _container(
            tmp_path,
            name="run-a-subject",
            run_key="run-a",
            usage_gib=8.0,
        ),
    ]
    decision = select_resource_containment(
        HostResourceSnapshot(available_memory_bytes=4 * 1024**3),
        containers,
    )
    assert decision is not None
    enumerations = iter(
        [
            ("run-a-subject",),
            ("run-a-verifier",),
            (),
        ]
    )
    stopped: list[str] = []

    monkeypatch.setattr(
        resource_supervisor,
        "_managed_run_container_names",
        lambda run_key: next(enumerations),
    )

    def fake_run(
        command: list[str],
        **kwargs: object,
    ) -> subprocess.CompletedProcess[str]:
        stopped.append(command[-1])
        return subprocess.CompletedProcess(command, 0, "", "")

    monkeypatch.setattr(resource_supervisor.subprocess, "run", fake_run)

    contain_resource_decision(
        decision,
        event_log=tmp_path / "events.ndjson",
        dry_run=False,
    )

    assert stopped == ["run-a-subject", "run-a-verifier"]
    assert (decision.state_path / "resource-halt.json").is_file()


def test_resource_halt_clearance_archives_operator_reason(
    tmp_path: Path,
) -> None:
    """An operator clearance preserves the halt and names why resume is safe."""
    state_path = tmp_path / "run-a"
    state_path.mkdir()
    halt_path = state_path / "resource-halt.json"
    halt_path.write_text(
        json.dumps(
            {
                "observed_at": "2026-08-04T20:00:00Z",
                "reason": "host memory reserve breached",
                "run_key": "run-a",
            }
        )
        + "\n"
    )

    archived = clear_resource_halt(
        state_path,
        cleared_at="2026-08-04T22:00:00Z",
        clearance_reason="hard cgroup limits were lowered",
    )

    assert not halt_path.exists()
    document = json.loads(archived.read_text())
    assert document["clearance"] == {
        "cleared_at": "2026-08-04T22:00:00Z",
        "reason": "hard cgroup limits were lowered",
    }
    assert document["reason"] == "host memory reserve breached"


def test_resource_halt_record_is_durable_and_not_overwritten(
    tmp_path: Path,
) -> None:
    """The first containment record remains the operator recovery authority."""
    decision = select_resource_containment(
        HostResourceSnapshot(available_memory_bytes=1),
        [
            _container(
                tmp_path,
                name="run-a-1",
                run_key="run-a",
                usage_gib=7.0,
            )
        ],
    )
    assert decision is not None

    halt_path = write_resource_halt(decision, observed_at="2026-08-04T20:00:00Z")
    original = halt_path.read_bytes()
    second_path = write_resource_halt(
        decision,
        observed_at="2026-08-04T21:00:00Z",
    )

    assert second_path == halt_path
    assert halt_path.read_bytes() == original
    document = json.loads(halt_path.read_text())
    assert document["reason"] == "host memory reserve breached"
    assert document["container_names"] == ["run-a-1"]
    assert document["run_key"] == "run-a"
