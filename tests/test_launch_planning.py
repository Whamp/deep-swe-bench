"""Behavior tests for model-free launch planning through its public seam."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest
from hypothesis import given
from hypothesis import strategies as st

from harness import config_lock
from harness.launch import (
    LaunchExecutionPolicies,
    LaunchRequest,
    LaunchRuntimeIdentity,
    LaunchTaskSelection,
    canonical_launch_plan_json,
    compile_launch_request,
    parse_launch_plan_json,
)


class FakeLaunchRuntimeResolver:
    """Return fixed runtime provenance without starting a subject process."""

    def __init__(self, identity: LaunchRuntimeIdentity) -> None:
        """Capture the runtime identity returned by the fake resolver."""
        self.identity = identity
        self.requests: list[tuple[LaunchRequest, tuple[str, ...]]] = []

    def resolve_launch_runtime(
        self,
        request: LaunchRequest,
        tasks: tuple[str, ...],
    ) -> LaunchRuntimeIdentity:
        """Record planning requests and return fixed runtime provenance."""
        self.requests.append((request, tasks))
        return self.identity


def _create_locked_config(
    repository_root: Path,
    config_identity: str,
    *,
    prompt: str,
    secret: str | None = None,
) -> None:
    config_root = repository_root / "configs" / config_identity
    config_leaf = config_root / "model" / "low"
    config_leaf.mkdir(parents=True)
    (config_root / "orchestration.md").write_text(prompt)
    if secret is not None:
        (config_root / "env").write_text(f"OPENAI_API_KEY={secret}\n")
    (config_leaf / "smoke.json").write_text('{"requireFiles":[]}\n')
    config_lock.write_config_lock(
        repository_root,
        config_identity,
        "provider/model",
        "low",
        "rerun",
        {
            "declaredRoles": [
                {
                    "billingCategory": "subscription quota",
                    "credentialRoute": "OPENAI_CODEX_OAUTH",
                    "model": "provider/model",
                    "name": "executor",
                    "provider": "provider",
                    "thinking": "low",
                }
            ],
            "testedSubjectVersions": ["pi@0.81.1"],
            "usageSources": ["session/*.jsonl"],
        },
    )


def _runtime_identity(
    tasks: tuple[str, ...] = ("task-a",),
) -> LaunchRuntimeIdentity:
    return LaunchRuntimeIdentity(
        subject_version="pi@0.81.1",
        harness_revision="git:harness-fixture",
        task_revision="git:tasks-fixture",
        verifier_identities={task: f"sha256:verifier-{task}" for task in tasks},
        immutable_image_identities={
            task: {
                "agent": f"sha256:agent-{task}",
                "environment": f"sha256:environment-{task}",
                "verifier": f"sha256:verifier-image-{task}",
            }
            for task in tasks
        },
    )


def _launch_request(*, run_id: str = "fixture-run") -> LaunchRequest:
    return LaunchRequest(
        subject="pi",
        model="provider/model",
        thinking="low",
        configs=("baseline@1.0.0", "review-assistant@1.0.0"),
        baseline_config="baseline@1.0.0",
        task_selection=LaunchTaskSelection(
            kind="tasks",
            tasks=("task-a",),
        ),
        reps=2,
        concurrency=1,
        run_id=run_id,
        policies=LaunchExecutionPolicies(
            preflight="required",
            existing_results="require-compatible",
            transient_errors="pause",
            cell_retries=1,
        ),
    )


def _write_launch_fixture(tmp_path: Path) -> tuple[Path, Path, Path, Path]:
    repository_root = tmp_path / "repository"
    tasks_root = tmp_path / "tasks"
    results_root = tmp_path / "canonical-results"
    state_root = tmp_path / "central-state"
    task_root = tasks_root / "task-a"
    task_root.mkdir(parents=True)
    harness_root = repository_root / "harness"
    harness_root.mkdir(parents=True)
    (harness_root / "run.py").write_text("# fixture subject runner\n")
    (task_root / "task.toml").write_text("[metadata]\n")
    _create_locked_config(
        repository_root,
        "baseline@1.0.0",
        prompt="Baseline behavior.\n",
    )
    _create_locked_config(
        repository_root,
        "review-assistant@1.0.0",
        prompt="Review behavior.\n",
    )
    return repository_root, tasks_root, results_root, state_root


def test_compile_launch_request_is_deterministic_without_execution(
    tmp_path: Path,
) -> None:
    """Planning freezes inputs without creating canonical result cells."""
    repository_root, tasks_root, results_root, state_root = (
        _write_launch_fixture(tmp_path)
    )
    request = _launch_request()
    runtime_identity = _runtime_identity()
    runtime_resolver = FakeLaunchRuntimeResolver(runtime_identity)

    first = compile_launch_request(
        request,
        repository_root=repository_root,
        tasks_root=tasks_root,
        results_root=results_root,
        state_root=state_root,
        runtime_resolver=runtime_resolver,
    )
    second = compile_launch_request(
        request,
        repository_root=repository_root,
        tasks_root=tasks_root,
        results_root=results_root,
        state_root=state_root,
        runtime_resolver=runtime_resolver,
    )

    plan = first.plan.to_document()
    assert first.plan.identity == second.plan.identity
    assert first.plan.canonical_json == second.plan.canonical_json
    assert plan["subject"] == {
        "name": "pi",
        "runner": str(repository_root / "harness" / "run.py"),
        "version": "pi@0.81.1",
    }
    assert [config["identity"] for config in plan["configs"]] == [
        "baseline@1.0.0",
        "review-assistant@1.0.0",
    ]
    assert all(config["lockIdentity"] for config in plan["configs"])
    assert plan["selection"] == {"kind": "tasks", "tasks": ["task-a"]}
    assert plan["counts"] == {
        "batchCells": 4,
        "configs": 2,
        "preflightCells": 2,
        "reps": 2,
        "tasks": 1,
    }
    assert plan["runtime"] == {
        "harnessRevision": "git:harness-fixture",
        "immutableImageIdentities": runtime_identity.immutable_image_identities,
        "taskRevision": "git:tasks-fixture",
        "verifierIdentities": runtime_identity.verifier_identities,
    }
    assert plan["paths"]["resultsRoot"] == str(results_root.resolve())
    assert plan["paths"]["statePath"] == str(
        (state_root / "fixture-run").resolve()
    )
    assert len(plan["batchCells"]) == 4
    assert len(runtime_resolver.requests) == 2
    assert not results_root.exists()
    assert not state_root.exists()


def test_launch_receipt_shows_review_information_and_baseline_differences(
    tmp_path: Path,
) -> None:
    """The receipt shows run shape, roles, warnings, and behavior drift."""
    repository_root, tasks_root, results_root, state_root = (
        _write_launch_fixture(tmp_path)
    )

    compiled = compile_launch_request(
        _launch_request(),
        repository_root=repository_root,
        tasks_root=tasks_root,
        results_root=results_root,
        state_root=state_root,
        runtime_resolver=FakeLaunchRuntimeResolver(_runtime_identity()),
    )

    receipt = compiled.receipt
    assert receipt.startswith("LAUNCH RECEIPT\nWARNINGS\n- none\n\nSUMMARY\n")
    assert "Subject: pi pi@0.81.1" in receipt
    assert "Model: provider/model (thinking=low)" in receipt
    assert "Tasks: 1; configs: 2; reps: 2; concurrency: 1" in receipt
    assert "Cells: 2 preflight; 4 batch" in receipt
    assert "executor | provider | provider/model | low" in receipt
    assert "OPENAI_CODEX_OAUTH | subscription quota" in receipt
    assert "BEHAVIOR DIFFERENCES FROM baseline@1.0.0" in receipt
    assert "review-assistant@1.0.0" in receipt
    assert "changed prompt: orchestration.md" in receipt
    assert f"Results root: {results_root.resolve()}" in receipt
    assert (
        f"Structured state: {(state_root / 'fixture-run').resolve()}" in receipt
    )


def test_launch_plan_identity_excludes_volatile_run_registration_metadata(
    tmp_path: Path,
) -> None:
    """A run id changes state path but not the behavior identity."""
    repository_root, tasks_root, results_root, state_root = (
        _write_launch_fixture(tmp_path)
    )
    runtime_resolver = FakeLaunchRuntimeResolver(_runtime_identity())

    first = compile_launch_request(
        _launch_request(run_id="first-run"),
        repository_root=repository_root,
        tasks_root=tasks_root,
        results_root=results_root,
        state_root=state_root,
        runtime_resolver=runtime_resolver,
    )
    second = compile_launch_request(
        _launch_request(run_id="second-run"),
        repository_root=repository_root,
        tasks_root=tasks_root,
        results_root=results_root,
        state_root=state_root,
        runtime_resolver=runtime_resolver,
    )

    first_document = first.plan.to_document()
    second_document = second.plan.to_document()
    assert first.plan.identity == second.plan.identity
    assert first_document["runId"] == "first-run"
    assert second_document["runId"] == "second-run"
    assert (
        first_document["paths"]["statePath"]
        != second_document["paths"]["statePath"]
    )
    assert first_document["identityExclusions"] == ["paths.statePath", "runId"]


def test_canonical_launch_plan_serialization_round_trips_and_rejects_tampering(
    tmp_path: Path,
) -> None:
    """A stored plan retains its identity and cannot hide changed behavior."""
    repository_root, tasks_root, results_root, state_root = (
        _write_launch_fixture(tmp_path)
    )
    compiled = compile_launch_request(
        _launch_request(),
        repository_root=repository_root,
        tasks_root=tasks_root,
        results_root=results_root,
        state_root=state_root,
        runtime_resolver=FakeLaunchRuntimeResolver(_runtime_identity()),
    )

    parsed = parse_launch_plan_json(compiled.plan.canonical_json)
    tampered = compiled.plan.canonical_json.replace(
        '"concurrency":1',
        '"concurrency":2',
    )

    assert parsed == compiled.plan
    try:
        parse_launch_plan_json(tampered)
    except ValueError as error:
        assert str(error).startswith("Launch plan identity mismatch:")
    else:
        raise AssertionError("tampered launch plan was accepted")


def test_launch_plan_prefers_selected_task_from_reusable_preflight_subset(
    tmp_path: Path,
) -> None:
    """Preflight uses stable subset order without adding other tasks."""
    repository_root, tasks_root, results_root, state_root = (
        _write_launch_fixture(tmp_path)
    )
    task_b_root = tasks_root / "task-b"
    task_b_root.mkdir()
    (task_b_root / "task.toml").write_text("[metadata]\n")
    subset_path = repository_root / "subsets" / "12_v0.txt"
    subset_path.parent.mkdir()
    subset_path.write_text("task-b\ntask-a\n")
    request = replace(
        _launch_request(),
        task_selection=LaunchTaskSelection(
            kind="tasks",
            tasks=("task-a", "task-b"),
        ),
    )

    compiled = compile_launch_request(
        request,
        repository_root=repository_root,
        tasks_root=tasks_root,
        results_root=results_root,
        state_root=state_root,
        runtime_resolver=FakeLaunchRuntimeResolver(
            _runtime_identity(("task-a", "task-b"))
        ),
    )

    assert {
        cell["task"] for cell in compiled.plan.to_document()["preflightCells"]
    } == {"task-b"}


def test_compile_launch_request_resolves_local_runtime(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Default planning resolves runtime provenance by image inspection."""
    repository_root, tasks_root, results_root, state_root = (
        _write_launch_fixture(tmp_path)
    )
    harness_root = repository_root / "harness"
    harness_root.mkdir(exist_ok=True)
    (harness_root / "run.py").write_text("# fixture subject runner\n")
    (repository_root / "Dockerfile.pi-agent").write_text(
        "ARG PI_VERSION=0.81.1\n"
    )
    task_root = tasks_root / "task-a"
    (task_root / "task.toml").write_text(
        """[metadata]
base_commit_hash = "abc123"
language = "python"
[environment]
docker_image = "fixture/environment:1"
[agent]
timeout_sec = 60
[verifier]
timeout_sec = 60
"""
    )
    tests_root = task_root / "tests"
    tests_root.mkdir()
    (tests_root / "test.sh").write_text("#!/bin/sh\nexit 0\n")
    fake_bin = tmp_path / "fake-bin"
    fake_bin.mkdir()
    fake_docker = fake_bin / "docker"
    fake_docker.write_text("#!/bin/sh\necho sha256:fixture-image\n")
    fake_docker.chmod(0o755)
    monkeypatch.setenv("PATH", f"{fake_bin}:{Path('/usr/bin')}")

    compiled = compile_launch_request(
        _launch_request(),
        repository_root=repository_root,
        tasks_root=tasks_root,
        results_root=results_root,
        state_root=state_root,
    )

    plan = compiled.plan.to_document()
    assert plan["subject"]["version"] == "pi@0.81.1"
    assert plan["runtime"]["harnessRevision"].startswith("sha256:")
    assert plan["runtime"]["taskRevision"].startswith("sha256:")
    assert plan["runtime"]["verifierIdentities"]["task-a"].startswith("sha256:")
    assert plan["runtime"]["immutableImageIdentities"]["task-a"] == {
        "agent": "sha256:fixture-image",
        "environment": "sha256:fixture-image",
        "verifier": "sha256:fixture-image",
    }
    assert not results_root.exists()
    assert not state_root.exists()


def test_launch_planning_rejects_missing_subject_runner(tmp_path: Path) -> None:
    """A runtime identity cannot substitute for a missing subject runner."""
    repository_root, tasks_root, results_root, state_root = (
        _write_launch_fixture(tmp_path)
    )
    (repository_root / "harness" / "run.py").unlink()

    with pytest.raises(ValueError, match=r"^Launch subject runner missing:"):
        compile_launch_request(
            _launch_request(),
            repository_root=repository_root,
            tasks_root=tasks_root,
            results_root=results_root,
            state_root=state_root,
            runtime_resolver=FakeLaunchRuntimeResolver(_runtime_identity()),
        )


def test_launch_planning_rejects_unsafe_run_id(tmp_path: Path) -> None:
    """A run id cannot escape the configured structured-state root."""
    repository_root, tasks_root, results_root, state_root = (
        _write_launch_fixture(tmp_path)
    )
    request = replace(_launch_request(), run_id="../outside-state")

    with pytest.raises(ValueError, match=r"^Launch run id invalid:"):
        compile_launch_request(
            request,
            repository_root=repository_root,
            tasks_root=tasks_root,
            results_root=results_root,
            state_root=state_root,
            runtime_resolver=FakeLaunchRuntimeResolver(_runtime_identity()),
        )


def test_launch_planning_rejects_unresolved_runtime_identity(
    tmp_path: Path,
) -> None:
    """Missing verifier or image provenance stops planning before execution."""
    repository_root, tasks_root, results_root, state_root = (
        _write_launch_fixture(tmp_path)
    )
    unresolved = replace(
        _runtime_identity(),
        verifier_identities={},
        immutable_image_identities={},
    )

    with pytest.raises(
        ValueError, match=r"^Launch runtime identity unresolved:"
    ):
        compile_launch_request(
            _launch_request(),
            repository_root=repository_root,
            tasks_root=tasks_root,
            results_root=results_root,
            state_root=state_root,
            runtime_resolver=FakeLaunchRuntimeResolver(unresolved),
        )

    assert not results_root.exists()
    assert not state_root.exists()


def test_launch_planning_rejects_invalid_task_selection(tmp_path: Path) -> None:
    """A selected task without task metadata cannot enter a launch plan."""
    repository_root, tasks_root, results_root, state_root = (
        _write_launch_fixture(tmp_path)
    )
    request = replace(
        _launch_request(),
        task_selection=LaunchTaskSelection(
            kind="tasks", tasks=("missing-task",)
        ),
    )

    with pytest.raises(ValueError, match=r"^Launch task selection invalid:"):
        compile_launch_request(
            request,
            repository_root=repository_root,
            tasks_root=tasks_root,
            results_root=results_root,
            state_root=state_root,
            runtime_resolver=FakeLaunchRuntimeResolver(_runtime_identity()),
        )


def test_launch_planning_rejects_ambiguous_config_leaf(tmp_path: Path) -> None:
    """Planning never chooses one of multiple matching model leaves by order."""
    repository_root, tasks_root, results_root, state_root = (
        _write_launch_fixture(tmp_path)
    )
    ambiguous_leaf = (
        repository_root
        / "configs"
        / "review-assistant@1.0.0"
        / "model+advisor"
        / "low"
    )
    ambiguous_leaf.mkdir(parents=True)

    with pytest.raises(ValueError, match=r"^Config leaf ambiguous:"):
        compile_launch_request(
            _launch_request(),
            repository_root=repository_root,
            tasks_root=tasks_root,
            results_root=results_root,
            state_root=state_root,
            runtime_resolver=FakeLaunchRuntimeResolver(_runtime_identity()),
        )


def test_launch_planning_rejects_config_lock_drift(tmp_path: Path) -> None:
    """Changed locked behavior prevents plan creation with input diagnostics."""
    repository_root, tasks_root, results_root, state_root = (
        _write_launch_fixture(tmp_path)
    )
    prompt_path = (
        repository_root
        / "configs"
        / "review-assistant@1.0.0"
        / "orchestration.md"
    )
    prompt_path.write_text("Drifted behavior.\n")

    with pytest.raises(ValueError, match=r"^Config lock mismatch:") as raised:
        compile_launch_request(
            _launch_request(),
            repository_root=repository_root,
            tasks_root=tasks_root,
            results_root=results_root,
            state_root=state_root,
            runtime_resolver=FakeLaunchRuntimeResolver(_runtime_identity()),
        )

    assert "changed=['orchestration.md']" in str(raised.value)


def test_launch_plan_and_receipt_exclude_config_secret_values(
    tmp_path: Path,
) -> None:
    """Credential values never enter the canonical plan or human receipt."""
    repository_root, tasks_root, results_root, state_root = (
        _write_launch_fixture(tmp_path)
    )
    secret = "paid-api-secret-value"
    for config_identity in ("baseline@1.0.0", "review-assistant@1.0.0"):
        config_root = repository_root / "configs" / config_identity
        lock_path = config_root / "model" / "low" / "config-lock.json"
        lock_path.unlink()
        (config_root / "env").write_text(f"OPENAI_API_KEY={secret}\n")
        config_lock.write_config_lock(
            repository_root,
            config_identity,
            "provider/model",
            "low",
            "rerun",
            {"credentialRoutes": ["OPENAI_API_KEY"]},
        )

    compiled = compile_launch_request(
        _launch_request(),
        repository_root=repository_root,
        tasks_root=tasks_root,
        results_root=results_root,
        state_root=state_root,
        runtime_resolver=FakeLaunchRuntimeResolver(_runtime_identity()),
    )

    assert secret not in compiled.plan.canonical_json
    assert secret not in compiled.receipt
    assert "OPENAI_API_KEY" in compiled.plan.canonical_json


@given(
    st.dictionaries(
        st.text(
            alphabet=st.characters(min_codepoint=97, max_codepoint=122),
            min_size=1,
            max_size=8,
        ),
        st.one_of(
            st.none(), st.booleans(), st.integers(), st.text(max_size=16)
        ),
        max_size=8,
    )
)
def test_canonical_launch_plan_serialization_ignores_mapping_order(
    document: dict[str, object],
) -> None:
    """Canonical launch-plan serialization is stable across JSON key order."""
    reversed_document = dict(reversed(document.items()))

    serialized = canonical_launch_plan_json(document)

    assert serialized == canonical_launch_plan_json(reversed_document)
    assert json.loads(serialized) == document
