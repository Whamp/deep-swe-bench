"""Execute confirmed plans through the public batch-launch seam."""

from __future__ import annotations

import hashlib
import json
from collections.abc import Callable, Mapping
from pathlib import Path

import pytest

from harness import config_lock, launch
from harness.launch import (
    CompiledLaunch,
    ConfirmedPiCell,
    LaunchExecutionPolicies,
    LaunchPreflightError,
    LaunchRequest,
    LaunchRuntimeIdentity,
    LaunchTaskSelection,
    compile_launch_request,
    execute_confirmed_launch,
)
from scripts import run_dashboard


class StaticLaunchRuntimeResolver:
    """Return mutable model-free runtime identities for launch fixtures."""

    def __init__(self, identity: LaunchRuntimeIdentity) -> None:
        """Store the runtime identity observed by the next drift check."""
        self.identity = identity

    def resolve_launch_runtime(
        self,
        request: LaunchRequest,
        tasks: tuple[str, ...],
    ) -> LaunchRuntimeIdentity:
        """Return current fixture runtime identity without host inspection."""
        del request, tasks
        return self.identity


class FailingConfirmedPiRunner:
    """Raise a controlled execution error without a subject or model call."""

    def __init__(self) -> None:
        """Track the one attempted confirmed cell."""
        self.calls: list[ConfirmedPiCell] = []

    def run_confirmed_pi_cell(self, cell: ConfirmedPiCell) -> dict[str, object]:
        """Fail after recording the exact plan-resolved cell."""
        self.calls.append(cell)
        raise RuntimeError("fixture runner stopped")


class InvalidPreflightEvidenceRunner:
    """Return deliberately incomplete preflight evidence without model calls."""

    def __init__(self) -> None:
        """Track calls made before the atomic preflight verdict."""
        self.calls: list[ConfirmedPiCell] = []

    def run_confirmed_pi_cell(self, cell: ConfirmedPiCell) -> dict[str, object]:
        """Return a failed subject result and no supporting artifacts."""
        self.calls.append(cell)
        return {
            "agent_exit": 1,
            "agent_timed_out": True,
            "arm_advisor": {},
            "arm_models": {},
            "arm_pi_flags": [],
            "arm_settings": {},
            "reward_binary": 0,
            "total_tokens": 0,
            "verifier_exit": 0,
        }


def _planned_launch_plan_path(compiled: CompiledLaunch) -> Path:
    """Return the launch-plan artifact path declared by the public plan."""
    state_path = compiled.plan.to_document()["paths"]["statePath"]
    return Path(state_path) / "launch-plan.json"


def _registered_state_path(state_root: Path, run_id: str) -> Path:
    """Find one registered state directory by its public manifest run id."""
    matches: list[Path] = []
    for manifest_path in state_root.glob("*/manifest.json"):
        manifest = json.loads(manifest_path.read_text())
        if manifest.get("run_id") == run_id:
            matches.append(manifest_path.parent)
    assert len(matches) == 1
    return matches[0]


class FakeConfirmedPiRunner:
    """Produce controlled Pi results without a subject or model call."""

    def __init__(
        self,
        expected_plan_path: Path,
        after_call: Callable[[ConfirmedPiCell], None] | None = None,
    ) -> None:
        """Record calls and require durable plan state before execution."""
        self.expected_plan_path = expected_plan_path
        self.after_call = after_call
        self.calls: list[ConfirmedPiCell] = []
        self.preflight_was_running = False

    def run_confirmed_pi_cell(self, cell: ConfirmedPiCell) -> dict[str, object]:
        """Return a legacy-compatible result record for one confirmed cell."""
        assert self.expected_plan_path.is_file()
        status = json.loads(
            (self.expected_plan_path.parent / "status.json").read_text()
        )
        preflight = status["preflight"].get(
            f"{cell.task}/{cell.config_identity}/rep{cell.rep}"
        )
        if preflight is not None:
            self.preflight_was_running = preflight["state"] == "running"
        self.calls.append(cell)
        cell_root = cell.result_path.parent
        (cell_root / "artifacts").mkdir(parents=True, exist_ok=True)
        (cell_root / "artifacts" / "model.patch").write_text("fixture patch\n")
        (cell_root / "session").mkdir(exist_ok=True)
        (cell_root / "session" / "fixture.jsonl").write_text(
            '{"message":{"usage":{"total":10}}}\n'
        )
        (cell_root / "logs").mkdir(exist_ok=True)
        (cell_root / "usage").mkdir(exist_ok=True)
        (cell_root / "usage" / "worker-usage.ndjson").write_text(
            '{"event":"assistant_usage","role":"worker"}\n'
        )
        (cell_root / "logs" / "pi-rpc-runner.jsonl").write_text(
            '{"event":"prompt_sent","transport":"rpc"}\n'
            '{"event":"quiescent","transport":"rpc"}\n'
        )
        (cell_root / "logs" / "extension-markers.log").write_text(
            "__FIXTURE_READY__\n"
        )
        if self.after_call is not None:
            self.after_call(cell)
        return {
            "agent_exit": 0,
            "arm_advisor": {"model": "fixture-advisor"},
            "arm_models": {"providers": []},
            "arm_pi_flags": ["--fixture-flag"],
            "arm_settings": {"defaultThinkingLevel": "low"},
            "reward_binary": 1,
            "reward_partial": 1.0,
            "total_tokens": 10,
            "verifier_exit": 0,
            "worker_calls": 1,
        }


def _config_lock_metadata() -> dict[str, object]:
    """Return the fixed secret-free role metadata for launch fixtures."""
    return {
        "credentialRoutes": ["FIXTURE_CREDENTIAL"],
        "declaredRoles": [
            {
                "billingCategory": "subscription quota",
                "callBehavior": {
                    "callsPerRep": 1,
                    "kind": "fixed",
                    "maxConcurrency": 1,
                },
                "credentialRoute": "FIXTURE_CREDENTIAL",
                "modelSelection": {
                    "kind": "fixed",
                    "model": "provider/model",
                    "provider": "provider",
                    "thinking": "low",
                },
                "name": "executor",
                "roleKind": "executor",
                "usageSource": {
                    "format": "native-session",
                    "path": "session/*.jsonl",
                },
            }
        ],
        "launchSurfaces": [
            {
                "modelRoles": ["executor"],
                "path": "extensions/machine-markers.ts",
            }
        ],
        "testedSubjectVersions": ["pi@0.81.1"],
        "usageSources": ["session/*.jsonl"],
    }


def _compile_existing_fixture(
    tmp_path: Path,
    *,
    preflight: str,
    reps: int = 1,
    tasks: tuple[str, ...] = ("task-a",),
    run_id: str = "confirmed-fixture",
    existing_results: str = "rerun",
    reuse_decisions: tuple[launch.ExplicitResultReuseDecision, ...] = (),
    state_root: Path | None = None,
) -> CompiledLaunch:
    """Compile an initialized launch fixture without changing its config."""
    repository_root = tmp_path / "repository"
    tasks_root = tmp_path / "tasks"
    results_root = tmp_path / "canonical-results"
    state_root = state_root or tmp_path / "central-state"
    request = LaunchRequest(
        subject="pi",
        model="provider/model",
        thinking="low",
        configs=("baseline@1.0.0",),
        baseline_config="baseline@1.0.0",
        task_selection=LaunchTaskSelection(kind="tasks", tasks=tasks),
        reps=reps,
        concurrency=1,
        run_id=run_id,
        policies=LaunchExecutionPolicies(
            preflight=preflight,
            existing_results=existing_results,
            transient_errors="stop",
            cell_retries=0,
        ),
        reuse_decisions=reuse_decisions,
    )
    runtime = LaunchRuntimeIdentity(
        subject_version="pi@0.81.1",
        harness_revision="sha256:harness-fixture",
        task_revision="sha256:task-fixture",
        verifier_identities={
            task: (
                "sha256:verifier-fixture"
                if task == "task-a"
                else f"sha256:verifier-fixture-{task}"
            )
            for task in tasks
        },
        immutable_image_identities={
            task: {
                "agent": "sha256:agent-image",
                "environment": "sha256:environment-image",
                "verifier": "sha256:verifier-image",
            }
            for task in tasks
        },
        subject_capabilities=frozenset({"pi-rpc"}),
        available_credential_routes=frozenset({"FIXTURE_CREDENTIAL"}),
    )

    class RuntimeResolver:
        """Return fixed model-free provenance for the temporary fixture."""

        def resolve_launch_runtime(
            self,
            request: LaunchRequest,
            tasks: tuple[str, ...],
        ) -> LaunchRuntimeIdentity:
            """Return the fixture runtime without executing a subject."""
            del request, tasks
            return runtime

    return compile_launch_request(
        request,
        repository_root=repository_root,
        tasks_root=tasks_root,
        results_root=results_root,
        state_root=state_root,
        runtime_resolver=RuntimeResolver(),
    )


def _runtime_resolver_for(
    compiled: CompiledLaunch,
) -> StaticLaunchRuntimeResolver:
    """Build a mutable fake resolver from approved plan runtime fields."""
    document = compiled.plan.to_document()
    runtime = document["runtime"]
    return StaticLaunchRuntimeResolver(
        LaunchRuntimeIdentity(
            subject_version=document["subject"]["version"],
            harness_revision=runtime["harnessRevision"],
            task_revision=runtime["taskRevision"],
            verifier_identities=runtime["verifierIdentities"],
            immutable_image_identities=runtime["immutableImageIdentities"],
            subject_capabilities=frozenset({"pi-rpc"}),
            available_credential_routes=frozenset({"FIXTURE_CREDENTIAL"}),
        )
    )


def _compile_single_cell_launch(
    tmp_path: Path,
    *,
    preflight: str = "disabled",
    reps: int = 1,
    tasks: tuple[str, ...] = ("task-a",),
    smoke_contract_document: dict[str, object] | None = None,
    version_impact: str = "rerun",
    run_id: str = "confirmed-fixture",
    state_root: Path | None = None,
) -> tuple[CompiledLaunch, Path, Path, Path, Path]:
    repository_root = tmp_path / "repository"
    tasks_root = tmp_path / "tasks"
    results_root = tmp_path / "canonical-results"
    state_root = state_root or tmp_path / "central-state"
    config_identity = "baseline@1.0.0"
    config_root = repository_root / "configs" / config_identity
    config_leaf = config_root / "model" / "low"
    config_leaf.mkdir(parents=True)
    extension_owner = config_root / "extensions" / "machine-markers.ts"
    extension_owner.parent.mkdir()
    extension_owner.write_text("export default {};\n")
    (config_root / "orchestration.md").write_text("Fixture behavior.\n")
    (config_leaf / "settings.json").write_text(
        '{"defaultThinkingLevel":"low"}\n'
    )
    smoke_contract = config_leaf / "smoke.json"
    smoke_contract.write_text(
        json.dumps(smoke_contract_document or {"requireFiles": []}) + "\n"
    )
    config_lock.write_config_lock(
        repository_root,
        config_identity,
        "provider/model",
        "low",
        version_impact,
        _config_lock_metadata(),
    )
    subject_runner = repository_root / "harness" / "run.py"
    subject_runner.parent.mkdir(parents=True)
    subject_runner.write_text("# fixture subject runner\n")
    for task_id in tasks:
        task_root = tasks_root / task_id
        task_root.mkdir(parents=True)
        (task_root / "task.toml").write_text("[metadata]\n")
    compiled = _compile_existing_fixture(
        tmp_path,
        preflight=preflight,
        reps=reps,
        tasks=tasks,
        run_id=run_id,
        state_root=state_root,
    )
    return compiled, config_leaf, smoke_contract, results_root, state_root


def test_confirmed_worktree_launches_register_centrally_with_provenance(
    tmp_path: Path,
) -> None:
    """One dashboard discovers confirmed runs from two workspaces."""
    state_root = tmp_path / "central-state"
    compiled_launches = [
        _compile_single_cell_launch(
            tmp_path / workspace,
            preflight="required",
            run_id="shared-run",
            state_root=state_root,
        )[0]
        for workspace in ("worktree-a", "worktree-b")
    ]

    for compiled in compiled_launches:
        execute_confirmed_launch(
            compiled.plan,
            confirmation_identity=compiled.plan.identity,
            runtime_resolver=_runtime_resolver_for(compiled),
            pi_runner=FakeConfirmedPiRunner(
                _planned_launch_plan_path(compiled)
            ),
        )

    runs = run_dashboard.load_dashboard_runs(
        state_root,
        detail="summary",
        include_legacy=False,
        legacy_root=None,
    )

    assert len(runs) == 2
    assert {run["run_id"] for run in runs} == {"shared-run"}
    assert len({run["run_key"] for run in runs}) == 2
    assert {
        run["workspace"] for run in runs
    } == {
        str((tmp_path / workspace / "repository").resolve())
        for workspace in ("worktree-a", "worktree-b")
    }
    assert all(run["configs"] == ["baseline@1.0.0"] for run in runs)
    assert all(run["launch_plan_identity"] for run in runs)
    assert all(run["launch_metadata"] == "confirmed_plan" for run in runs)
    assert all(run["preflight_state"] == "passed" for run in runs)

    for summary in runs:
        detail = run_dashboard.load_dashboard_run(
            summary["run_key"],
            state_root,
            detail="operational",
            legacy_root=None,
        )
        assert detail is not None
        manifest = detail["manifest"] if "manifest" in detail else json.loads(
            Path(detail["paths"]["manifest"]).read_text()
        )
        assert manifest["workspace"] == summary["workspace"]
        assert manifest["results_root"]
        assert manifest["state_root"] == str(state_root.resolve())
        assert manifest["config_identities"] == ["baseline@1.0.0"]
        assert manifest["launch_plan_identity"] == summary[
            "launch_plan_identity"
        ]
        assert detail["preflight_state"] == "passed"


def test_passing_preflight_fans_out_exactly_once_without_second_confirmation(
    tmp_path: Path,
) -> None:
    """One confirmation covers atomic preflight and its conditional batch."""
    compiled, _, _, _, state_root = _compile_single_cell_launch(
        tmp_path,
        preflight="required",
        reps=2,
        tasks=("task-a", "task-b"),
        smoke_contract_document={
            "equalsResultValues": {"reward_binary": 1},
            "minResultValues": {"worker_calls": 1},
            "requireFiles": ["usage/worker-usage.ndjson"],
            "requireUsageRecords": [
                {
                    "equals": {"role": "worker"},
                    "globs": ["usage/worker-usage.ndjson"],
                    "minimum": 1,
                }
            ],
            "requireExtensionMarkers": [
                {
                    "extension": (
                        "configs/baseline@1.0.0/extensions/machine-markers.ts"
                    ),
                    "globs": ["logs/extension-markers.log"],
                    "marker": "__FIXTURE_READY__",
                }
            ],
            "forbidExtensionMarkers": [
                {
                    "extension": (
                        "configs/baseline@1.0.0/extensions/machine-markers.ts"
                    ),
                    "globs": ["logs/extension-markers.log"],
                    "marker": "__FIXTURE_BROKEN__",
                }
            ],
        },
    )
    plan_path = _planned_launch_plan_path(compiled)
    fake_runner = FakeConfirmedPiRunner(plan_path)

    execution = execute_confirmed_launch(
        compiled.plan,
        confirmation_identity=compiled.plan.identity,
        runtime_resolver=_runtime_resolver_for(compiled),
        pi_runner=fake_runner,
    )

    assert fake_runner.preflight_was_running
    assert [(cell.task, cell.rep) for cell in fake_runner.calls] == [
        ("task-a", 0),
        ("task-a", 1),
        ("task-b", 0),
        ("task-b", 1),
    ]
    status = json.loads((execution.state_path / "status.json").read_text())
    preflight = status["preflight"]["task-a/baseline@1.0.0/rep0"]
    assert preflight["state"] == "passed"
    assert preflight["diagnostics"] == []
    assert status["state"] == "completed"
    assert status["counts"]["batch_done"] == 4
    assert status["counts"]["batch_skipped"] == 1
    events = [
        json.loads(line)
        for line in (execution.state_path / "events.ndjson")
        .read_text()
        .splitlines()
    ]
    event_names = [event["event"] for event in events]
    assert event_names.count("preflight_finished") == 1
    assert event_names.index("preflight_finished") < event_names.index(
        "cell_started"
    )
    assert (
        json.loads(execution.result_path.read_text())["preflight_passed"]
        is True
    )


def test_required_preflight_reuses_compatible_result_without_writing(
    tmp_path: Path,
) -> None:
    """Required preflight checks existing evidence without a subject call."""
    first, _, _, _, _ = _compile_single_cell_launch(
        tmp_path,
        preflight="required",
    )
    first_execution = execute_confirmed_launch(
        first.plan,
        confirmation_identity=first.plan.identity,
        runtime_resolver=_runtime_resolver_for(first),
        pi_runner=FakeConfirmedPiRunner(
            _planned_launch_plan_path(first)
        ),
    )
    result_before = first_execution.result_path.read_bytes()
    compiled = _compile_existing_fixture(
        tmp_path,
        preflight="required",
        run_id="confirmed-preflight-reuse",
        existing_results="require-compatible",
    )
    runner = FakeConfirmedPiRunner(_planned_launch_plan_path(compiled))

    execution = execute_confirmed_launch(
        compiled.plan,
        confirmation_identity=compiled.plan.identity,
        runtime_resolver=_runtime_resolver_for(compiled),
        pi_runner=runner,
    )

    assert runner.calls == []
    assert execution.result_path.read_bytes() == result_before
    status = json.loads((execution.state_path / "status.json").read_text())
    preflight = status["preflight"]["task-a/baseline@1.0.0/rep0"]
    assert preflight["state"] == "passed"
    assert status["cells"]["task-a/baseline@1.0.0/rep0"]["state"] == ("skipped")


def test_failed_preflight_records_all_diagnostics_without_batch_fan_out(
    tmp_path: Path,
) -> None:
    """A failed atomic verdict records every unmet requirement and stops."""
    compiled, _, _, _, state_root = _compile_single_cell_launch(
        tmp_path,
        preflight="required",
        reps=2,
        smoke_contract_document={
            "equalsResultValues": {"reward_binary": 1},
            "minResultValues": {"worker_calls": 1},
            "requireFiles": ["usage/worker-usage.ndjson"],
            "requireUsageRecords": [
                {
                    "equals": {"role": "worker"},
                    "globs": ["usage/worker-usage.ndjson"],
                    "minimum": 1,
                }
            ],
        },
    )
    runner = InvalidPreflightEvidenceRunner()

    with pytest.raises(
        LaunchPreflightError,
        match="batch fan-out was not started",
    ):
        execute_confirmed_launch(
            compiled.plan,
            confirmation_identity=compiled.plan.identity,
            runtime_resolver=_runtime_resolver_for(compiled),
            pi_runner=runner,
        )

    assert len(runner.calls) == 1
    status = json.loads(
        (
            _registered_state_path(state_root, "confirmed-fixture")
            / "status.json"
        ).read_text()
    )
    preflight = status["preflight"]["task-a/baseline@1.0.0/rep0"]
    assert preflight["state"] == "failed"
    assert {item["target"] for item in preflight["diagnostics"]} == {
        "result.agent_exit",
        "result.agent_timed_out",
        "result.total_tokens",
        "session/*.jsonl",
        "logs/pi-rpc-runner.jsonl:prompt_sent",
        "logs/pi-rpc-runner.jsonl:quiescent",
        "logs/pi-rpc-runner.jsonl:transport=rpc",
        "result.reward_binary",
        "result.worker_calls",
        "usage/worker-usage.ndjson",
        "usage/worker-usage.ndjson:structured-records",
    }
    assert status["counts"]["batch_done"] == 0
    assert status["counts"]["batch_running"] == 0
    assert status["state"] == "failed"
    events = [
        json.loads(line)
        for line in (
            _registered_state_path(state_root, "confirmed-fixture")
            / "events.ndjson"
        )
        .read_text()
        .splitlines()
    ]
    event_names = [event["event"] for event in events]
    assert event_names.count("preflight_finished") == 1
    assert "cell_started" not in event_names
    result = json.loads(runner.calls[0].result_path.read_text())
    assert "preflight_passed" not in result


def test_preflight_verdict_controls_config_leaf_sealing(
    tmp_path: Path,
) -> None:
    """Only a passed preflight seals its referenced config lock."""
    passed, _, _, passed_results, _ = _compile_single_cell_launch(
        tmp_path / "passed",
        preflight="required",
    )
    execute_confirmed_launch(
        passed.plan,
        confirmation_identity=passed.plan.identity,
        runtime_resolver=_runtime_resolver_for(passed),
        pi_runner=FakeConfirmedPiRunner(
            _planned_launch_plan_path(passed)
        ),
    )
    sealed_recompile = _compile_existing_fixture(
        tmp_path / "passed",
        preflight="new-configs",
        run_id="confirmed-fixture-sealed",
    )
    assert sealed_recompile.plan.to_document()["preflightCells"] == []
    passed_repository = tmp_path / "passed" / "repository"
    passed_prompt = (
        passed_repository / "configs" / "baseline@1.0.0" / "orchestration.md"
    )
    passed_prompt.write_text("Revised candidate behavior.\n")

    with pytest.raises(ValueError, match=r"^Config lock sealed:"):
        config_lock.write_config_lock(
            passed_repository,
            "baseline@1.0.0",
            "provider/model",
            "low",
            "rerun",
            _config_lock_metadata(),
            replace=True,
            results_root=passed_results,
        )

    failed, _, _, failed_results, _ = _compile_single_cell_launch(
        tmp_path / "failed",
        preflight="required",
    )
    with pytest.raises(LaunchPreflightError):
        execute_confirmed_launch(
            failed.plan,
            confirmation_identity=failed.plan.identity,
            runtime_resolver=_runtime_resolver_for(failed),
            pi_runner=InvalidPreflightEvidenceRunner(),
        )
    failed_repository = tmp_path / "failed" / "repository"
    failed_prompt = (
        failed_repository / "configs" / "baseline@1.0.0" / "orchestration.md"
    )
    failed_prompt.write_text("Revised candidate behavior.\n")

    refreshed_path = config_lock.write_config_lock(
        failed_repository,
        "baseline@1.0.0",
        "provider/model",
        "low",
        "rerun",
        _config_lock_metadata(),
        replace=True,
        results_root=failed_results,
    )

    assert refreshed_path.is_file()
    failed_result = next(failed_results.glob("*/*/*/*/rep*/result.json"))
    failed_result.unlink()
    recompiled = _compile_existing_fixture(
        tmp_path / "failed",
        preflight="new-configs",
        run_id="confirmed-fixture-retry",
    )
    assert len(recompiled.plan.to_document()["preflightCells"]) == 1


def test_sealed_release_allows_only_leaves_with_unchanged_shared_behavior(
    tmp_path: Path,
) -> None:
    """A sealed release accepts new leaves only while shared inputs match."""
    compiled, _, _, results_root, state_root = _compile_single_cell_launch(
        tmp_path,
        preflight="required",
    )
    execute_confirmed_launch(
        compiled.plan,
        confirmation_identity=compiled.plan.identity,
        runtime_resolver=_runtime_resolver_for(compiled),
        pi_runner=FakeConfirmedPiRunner(
            _planned_launch_plan_path(compiled)
        ),
    )
    repository_root = tmp_path / "repository"
    config_root = repository_root / "configs" / "baseline@1.0.0"
    second_leaf = config_root / "other-model" / "low"
    second_leaf.mkdir(parents=True)
    (second_leaf / "smoke.json").write_text('{"requireFiles":[]}\n')

    second_lock = config_lock.write_config_lock(
        repository_root,
        "baseline@1.0.0",
        "provider/other-model",
        "low",
        "rerun",
        _config_lock_metadata(),
        results_root=results_root,
    )

    assert second_lock.is_file()
    (config_root / "orchestration.md").write_text("Changed shared behavior.\n")
    third_leaf = config_root / "third-model" / "low"
    third_leaf.mkdir(parents=True)
    (third_leaf / "smoke.json").write_text('{"requireFiles":[]}\n')

    with pytest.raises(
        ValueError,
        match=r"^Config release shared behavior sealed:",
    ):
        config_lock.write_config_lock(
            repository_root,
            "baseline@1.0.0",
            "provider/third-model",
            "low",
            "rerun",
            _config_lock_metadata(),
            results_root=results_root,
        )

    assert not (third_leaf / "config-lock.json").exists()


def test_confirmed_launch_reuses_compatible_result_without_writing(
    tmp_path: Path,
) -> None:
    """A compatible cell is reused without runner or artifact writes."""
    first, _, _, _, _ = _compile_single_cell_launch(tmp_path)
    first_runner = FakeConfirmedPiRunner(
        _planned_launch_plan_path(first)
    )
    first_execution = execute_confirmed_launch(
        first.plan,
        confirmation_identity=first.plan.identity,
        runtime_resolver=_runtime_resolver_for(first),
        pi_runner=first_runner,
    )
    result_before = first_execution.result_path.read_bytes()
    artifact_before = (
        first_execution.result_path.parent / "artifacts" / "model.patch"
    ).read_bytes()
    compiled = _compile_existing_fixture(
        tmp_path,
        preflight="disabled",
        run_id="confirmed-reuse",
        existing_results="require-compatible",
    )
    reuse_runner = FakeConfirmedPiRunner(
        _planned_launch_plan_path(compiled)
    )

    execution = execute_confirmed_launch(
        compiled.plan,
        confirmation_identity=compiled.plan.identity,
        runtime_resolver=_runtime_resolver_for(compiled),
        pi_runner=reuse_runner,
    )

    assert reuse_runner.calls == []
    assert execution.result_path.read_bytes() == result_before
    assert (
        execution.result_path.parent / "artifacts" / "model.patch"
    ).read_bytes() == artifact_before
    status = json.loads((execution.state_path / "status.json").read_text())
    cell = status["cells"]["task-a/baseline@1.0.0/rep0"]
    assert cell["state"] == "skipped"
    assert cell["reason"] == "compatible_existing_result"


@pytest.mark.parametrize(
    ("field", "incompatible_value"),
    [
        ("config", "baseline@0.9.0"),
        ("config_lock_identity", "sha256:other-lock"),
        ("subject", "omp"),
        ("subject_version", "pi@earlier"),
        ("model", "provider/other-model"),
        ("thinking_level", "high"),
        ("task", "task-other"),
        ("rep", 7),
        ("harness_revision", "sha256:other-harness"),
        ("task_revision", "sha256:other-task"),
        ("verifier_identity", "sha256:other-verifier"),
        (
            "immutable_image_identities",
            {
                "agent": "sha256:other-agent",
                "environment": "sha256:environment-image",
                "verifier": "sha256:verifier-image",
            },
        ),
    ],
)
def test_launch_planning_rejects_each_incompatible_result_provenance_field(
    tmp_path: Path,
    field: str,
    incompatible_value: object,
) -> None:
    """Automatic reuse requires every behavior-defining identity to match."""
    first, _, _, _, state_root = _compile_single_cell_launch(tmp_path)
    execution = execute_confirmed_launch(
        first.plan,
        confirmation_identity=first.plan.identity,
        runtime_resolver=_runtime_resolver_for(first),
        pi_runner=FakeConfirmedPiRunner(_planned_launch_plan_path(first)),
    )
    result = json.loads(execution.result_path.read_text())
    result[field] = incompatible_value
    execution.result_path.write_text(json.dumps(result) + "\n")

    with pytest.raises(
        ValueError,
        match=r"^Result provenance mismatch:",
    ) as raised:
        _compile_existing_fixture(
            tmp_path,
            preflight="disabled",
            run_id=f"incompatible-{field.replace('_', '-')}",
            existing_results="require-compatible",
        )

    assert field in str(raised.value)
    assert str(execution.result_path) in str(raised.value)


def test_execute_confirmed_launch_rejects_reuse_changed_after_confirmation(
    tmp_path: Path,
) -> None:
    """Confirmed reuse stops if the reviewed result changes before execution."""
    first, _, _, _, _ = _compile_single_cell_launch(tmp_path)
    first_execution = execute_confirmed_launch(
        first.plan,
        confirmation_identity=first.plan.identity,
        runtime_resolver=_runtime_resolver_for(first),
        pi_runner=FakeConfirmedPiRunner(
            _planned_launch_plan_path(first)
        ),
    )
    compiled = _compile_existing_fixture(
        tmp_path,
        preflight="disabled",
        run_id="confirmed-reuse-drift",
        existing_results="require-compatible",
    )
    changed = json.loads(first_execution.result_path.read_text())
    changed["harness_revision"] = "sha256:changed-after-confirmation"
    first_execution.result_path.write_text(json.dumps(changed) + "\n")
    state_root = tmp_path / "central-state"
    runner = FakeConfirmedPiRunner(
        _planned_launch_plan_path(compiled)
    )

    with pytest.raises(
        ValueError,
        match=r"^Result provenance mismatch:",
    ) as raised:
        execute_confirmed_launch(
            compiled.plan,
            confirmation_identity=compiled.plan.identity,
            runtime_resolver=_runtime_resolver_for(compiled),
            pi_runner=runner,
        )

    assert "harness_revision" in str(raised.value)
    assert str(first_execution.result_path) in str(raised.value)
    assert runner.calls == []
    status = json.loads(
        (
            _registered_state_path(state_root, "confirmed-reuse-drift")
            / "status.json"
        ).read_text()
    )
    assert status["state"] == "failed"
    events = [
        json.loads(line)
        for line in (
            _registered_state_path(state_root, "confirmed-reuse-drift")
            / "events.ndjson"
        )
        .read_text()
        .splitlines()
    ]
    failure = next(event for event in events if event["event"] == "run_failed")
    assert "Result provenance mismatch" in failure["reason"]


def test_execute_confirmed_launch_honors_exact_explicit_legacy_reuse(
    tmp_path: Path,
) -> None:
    """An exact legacy decision reuses bytes without fabricating provenance."""
    compiled, _, _, _, state_root = _compile_single_cell_launch(tmp_path)
    result_path_value = compiled.plan.to_document()["batchCells"][0][
        "resultPath"
    ]
    assert isinstance(result_path_value, str)
    result_path = Path(result_path_value)
    result_path.parent.mkdir(parents=True)
    legacy_result = {
        "config": "baseline",
        "model": "provider/model",
        "rep": 0,
        "task": "task-a",
        "thinking_level": "low",
    }
    legacy_bytes = (json.dumps(legacy_result, sort_keys=True) + "\n").encode()
    result_path.write_bytes(legacy_bytes)
    decision = launch.ExplicitResultReuseDecision(
        result_path=result_path,
        prior_config_identity="baseline",
        result_identity=f"sha256:{hashlib.sha256(legacy_bytes).hexdigest()}",
        recorded_provenance=legacy_result,
        rationale="Reviewed legacy baseline remains valid for this rep.",
    )
    approved = _compile_existing_fixture(
        tmp_path,
        preflight="disabled",
        run_id="confirmed-legacy-reuse",
        existing_results="require-compatible",
        reuse_decisions=(decision,),
    )
    runner = FakeConfirmedPiRunner(
        _planned_launch_plan_path(approved)
    )

    execution = execute_confirmed_launch(
        approved.plan,
        confirmation_identity=approved.plan.identity,
        runtime_resolver=_runtime_resolver_for(approved),
        pi_runner=runner,
    )

    assert runner.calls == []
    assert result_path.read_bytes() == legacy_bytes
    assert "config_lock_identity" not in json.loads(result_path.read_text())
    planned_cell = approved.plan.to_document()["batchCells"][0]
    reuse_decision = planned_cell["reuseDecision"]
    assert isinstance(reuse_decision, Mapping)
    assert reuse_decision.get("rationale") == decision.rationale
    status = json.loads((execution.state_path / "status.json").read_text())
    cell = status["cells"]["task-a/baseline@1.0.0/rep0"]
    assert cell["reason"] == "explicit_result_reuse"


def test_launch_planning_rejects_wrong_explicit_reuse_provenance(
    tmp_path: Path,
) -> None:
    """An explicit decision accepts only its named earlier provenance."""
    compiled, _, _, _, _ = _compile_single_cell_launch(tmp_path)
    result_path_value = compiled.plan.to_document()["batchCells"][0][
        "resultPath"
    ]
    assert isinstance(result_path_value, str)
    result_path = Path(result_path_value)
    result_path.parent.mkdir(parents=True)
    legacy_result = {
        "config": "baseline",
        "model": "provider/model",
        "rep": 0,
        "task": "task-a",
        "thinking_level": "low",
    }
    legacy_bytes = (json.dumps(legacy_result, sort_keys=True) + "\n").encode()
    result_path.write_bytes(legacy_bytes)
    decision = launch.ExplicitResultReuseDecision(
        result_path=result_path,
        prior_config_identity="different-baseline",
        result_identity=f"sha256:{hashlib.sha256(legacy_bytes).hexdigest()}",
        recorded_provenance=legacy_result,
        rationale="Fixture intentionally names the wrong earlier config.",
    )

    with pytest.raises(
        ValueError,
        match=r"^Result reuse decision mismatch:",
    ) as raised:
        _compile_existing_fixture(
            tmp_path,
            preflight="disabled",
            run_id="wrong-explicit-reuse",
            existing_results="require-compatible",
            reuse_decisions=(decision,),
        )

    assert "prior_config_identity" in str(raised.value)
    assert str(result_path) in str(raised.value)
    assert result_path.read_bytes() == legacy_bytes


def test_version_impact_reuse_does_not_authorize_legacy_result(
    tmp_path: Path,
) -> None:
    """Version impact records intent but cannot authorize reuse itself."""
    compiled, config_leaf, _, _, _ = _compile_single_cell_launch(
        tmp_path,
        version_impact="reuse",
    )
    result_path_value = compiled.plan.to_document()["batchCells"][0][
        "resultPath"
    ]
    assert isinstance(result_path_value, str)
    result_path = Path(result_path_value)
    result_path.parent.mkdir(parents=True)
    legacy_bytes = b'{"config":"baseline","task":"task-a","rep":0}\n'
    result_path.write_bytes(legacy_bytes)
    lock_before = (config_leaf / "config-lock.json").read_bytes()

    with pytest.raises(
        ValueError,
        match=r"^Result provenance mismatch:",
    ):
        _compile_existing_fixture(
            tmp_path,
            preflight="disabled",
            run_id="version-impact-is-not-a-decision",
            existing_results="require-compatible",
        )

    assert result_path.read_bytes() == legacy_bytes
    assert (config_leaf / "config-lock.json").read_bytes() == lock_before
    assert json.loads(lock_before)["versionImpact"] == "reuse"


def test_launch_planning_rejects_incompatible_occupied_rerun_path(
    tmp_path: Path,
) -> None:
    """Rerun policy cannot overwrite an incompatible canonical occupant."""
    first, _, _, _, _ = _compile_single_cell_launch(tmp_path)
    first_execution = execute_confirmed_launch(
        first.plan,
        confirmation_identity=first.plan.identity,
        runtime_resolver=_runtime_resolver_for(first),
        pi_runner=FakeConfirmedPiRunner(
            _planned_launch_plan_path(first)
        ),
    )
    result = json.loads(first_execution.result_path.read_text())
    result["subject_version"] = "pi@earlier"
    first_execution.result_path.write_text(json.dumps(result) + "\n")
    occupied_result = first_execution.result_path.read_bytes()

    with pytest.raises(
        ValueError,
        match=r"^Result provenance mismatch:",
    ) as raised:
        _compile_existing_fixture(
            tmp_path,
            preflight="disabled",
            run_id="confirmed-rerun",
            existing_results="rerun",
        )

    message = str(raised.value)
    assert str(first_execution.result_path) in message
    assert "subject_version" in message
    assert first_execution.result_path.read_bytes() == occupied_result


def test_execute_confirmed_launch_runs_exact_planned_pi_cell(
    tmp_path: Path,
) -> None:
    """A matching confirmation executes one plan-resolved Pi cell."""
    compiled, config_leaf, smoke_contract, results_root, state_root = (
        _compile_single_cell_launch(tmp_path)
    )
    plan_path = _planned_launch_plan_path(compiled)
    fake_runner = FakeConfirmedPiRunner(plan_path)
    assert not results_root.exists()
    assert fake_runner.calls == []

    execution = execute_confirmed_launch(
        compiled.plan,
        confirmation_identity=compiled.plan.identity,
        runtime_resolver=_runtime_resolver_for(compiled),
        pi_runner=fake_runner,
    )

    assert len(fake_runner.calls) == 1
    cell = fake_runner.calls[0]
    assert cell.config_leaf == config_leaf.resolve()
    assert cell.smoke_contract == smoke_contract.resolve()
    assert cell.subject_runner.name == "run.py"
    assert cell.immutable_image_identities == {
        "agent": "sha256:agent-image",
        "environment": "sha256:environment-image",
        "verifier": "sha256:verifier-image",
    }
    result = json.loads(execution.result_path.read_text())
    assert result["config"] == "baseline@1.0.0"
    assert result["config_name"] == "baseline"
    assert result["config_version"] == "1.0.0"
    assert result["config_lock_identity"].startswith("sha256:")
    assert result["subject"] == "pi"
    assert result["subject_version"] == "pi@0.81.1"
    assert result["model"] == "provider/model"
    assert result["thinking_level"] == "low"
    assert result["harness_revision"] == "sha256:harness-fixture"
    assert result["task_revision"] == "sha256:task-fixture"
    assert result["verifier_identity"] == "sha256:verifier-fixture"
    assert (
        result["immutable_image_identities"] == cell.immutable_image_identities
    )
    assert result["launch_plan_identity"] == compiled.plan.identity
    assert result["arm_advisor"] == {"model": "fixture-advisor"}
    assert result["arm_models"] == {"providers": []}
    assert result["arm_pi_flags"] == ["--fixture-flag"]
    assert result["arm_settings"] == {"defaultThinkingLevel": "low"}
    assert (
        execution.result_path.parent / "artifacts" / "model.patch"
    ).is_file()
    assert (
        execution.result_path.parent / "session" / "fixture.jsonl"
    ).is_file()
    assert (
        json.loads(plan_path.read_text())["planIdentity"]
        == compiled.plan.identity
    )
    status = json.loads(
        (
            _registered_state_path(state_root, "confirmed-fixture")
            / "status.json"
        ).read_text()
    )
    assert status["state"] == "completed"
    assert status["counts"]["batch_done"] == 1


@pytest.mark.parametrize("confirmation_identity", [None, "sha256:stale-plan"])
def test_execute_confirmed_launch_rejects_missing_or_stale_confirmation(
    tmp_path: Path,
    confirmation_identity: str | None,
) -> None:
    """No subject or canonical artifact is written without exact approval."""
    compiled, _, _, results_root, state_root = _compile_single_cell_launch(
        tmp_path
    )
    fake_runner = FakeConfirmedPiRunner(
        _planned_launch_plan_path(compiled)
    )

    with pytest.raises(ValueError, match="Launch confirmation"):
        execute_confirmed_launch(
            compiled.plan,
            confirmation_identity=confirmation_identity,
            runtime_resolver=_runtime_resolver_for(compiled),
            pi_runner=fake_runner,
        )

    assert fake_runner.calls == []
    assert not results_root.exists()
    assert not state_root.exists()


@pytest.mark.parametrize(
    ("relative_path", "changed_content"),
    [
        ("orchestration.md", "Drifted fixture behavior.\n"),
        ("extensions/machine-markers.ts", "export default {drift: true};\n"),
        ("model/low/settings.json", '{"defaultThinkingLevel":"high"}\n'),
        ("model/low/smoke.json", '{"minResultValues":{"worker_calls":2}}\n'),
    ],
)
def test_execute_confirmed_launch_stops_before_config_input_drifted_rep(
    tmp_path: Path,
    relative_path: str,
    changed_content: str,
) -> None:
    """Config input drift records both identities before the next rep."""
    compiled, _, _, _, state_root = _compile_single_cell_launch(
        tmp_path,
        reps=2,
    )
    behavior_path = (
        tmp_path
        / "repository"
        / "configs"
        / "baseline@1.0.0"
        / relative_path
    )

    def change_behavior_after_first_rep(cell: ConfirmedPiCell) -> None:
        if cell.rep == 0:
            behavior_path.write_text(changed_content)

    runner = FakeConfirmedPiRunner(
        _planned_launch_plan_path(compiled),
        after_call=change_behavior_after_first_rep,
    )

    with pytest.raises(RuntimeError, match=r"^Launch input drift:"):
        execute_confirmed_launch(
            compiled.plan,
            confirmation_identity=compiled.plan.identity,
            runtime_resolver=_runtime_resolver_for(compiled),
            pi_runner=runner,
        )

    assert [cell.rep for cell in runner.calls] == [0]
    events = [
        json.loads(line)
        for line in (
            _registered_state_path(state_root, "confirmed-fixture")
            / "events.ndjson"
        )
        .read_text()
        .splitlines()
    ]
    drift_event = next(
        event for event in events if event["event"] == "launch_input_drift"
    )
    assert drift_event["pending_cell_id"].endswith("/rep1")
    assert drift_event["active_cell_ids"] == []
    assert drift_event["active_preflight_ids"] == []
    assert len(drift_event["changes"]) == 1
    change = drift_event["changes"][0]
    assert change["category"] == "config-input"
    assert change["config"] == "baseline@1.0.0"
    assert change["input"] == relative_path
    assert change["approvedIdentity"].startswith("sha256:")
    assert change["observedIdentity"] != change["approvedIdentity"]


def test_execute_confirmed_launch_stops_before_config_lock_drifted_rep(
    tmp_path: Path,
) -> None:
    """Config lock drift is distinct from behavior-file drift."""
    compiled, config_leaf, _, _, state_root = _compile_single_cell_launch(
        tmp_path,
        reps=2,
    )
    lock_path = config_leaf / "config-lock.json"

    def change_lock_after_first_rep(cell: ConfirmedPiCell) -> None:
        if cell.rep != 0:
            return
        lock_document = json.loads(lock_path.read_text())
        lock_document["versionImpact"] = "recompute"
        lock_path.write_text(json.dumps(lock_document) + "\n")

    runner = FakeConfirmedPiRunner(
        _planned_launch_plan_path(compiled),
        after_call=change_lock_after_first_rep,
    )

    with pytest.raises(RuntimeError, match=r"^Launch input drift:"):
        execute_confirmed_launch(
            compiled.plan,
            confirmation_identity=compiled.plan.identity,
            runtime_resolver=_runtime_resolver_for(compiled),
            pi_runner=runner,
        )

    assert [cell.rep for cell in runner.calls] == [0]
    events = [
        json.loads(line)
        for line in (
            _registered_state_path(state_root, "confirmed-fixture")
            / "events.ndjson"
        )
        .read_text()
        .splitlines()
    ]
    drift_event = next(
        event for event in events if event["event"] == "launch_input_drift"
    )
    assert drift_event["changes"][0]["category"] == "config-lock"
    assert drift_event["changes"][0]["input"] == "baseline@1.0.0"
    assert (
        drift_event["changes"][0]["approvedIdentity"]
        == compiled.plan.to_document()["configs"][0]["lockIdentity"]
    )
    assert (
        drift_event["changes"][0]["observedIdentity"]
        != drift_event["changes"][0]["approvedIdentity"]
    )


@pytest.mark.parametrize(
    "changed_category",
    [
        "subject-version",
        "harness-revision",
        "task-revision",
        "verifier-identity",
        "immutable-image-identity",
    ],
)
def test_execute_confirmed_launch_stops_before_runtime_drifted_rep(
    tmp_path: Path,
    changed_category: str,
) -> None:
    """Runtime identity drift is re-resolved before another rep starts."""
    compiled, _, _, _, state_root = _compile_single_cell_launch(
        tmp_path,
        reps=2,
    )
    runtime_resolver = _runtime_resolver_for(compiled)

    def change_runtime_after_first_rep(cell: ConfirmedPiCell) -> None:
        if cell.rep != 0:
            return
        approved = runtime_resolver.identity
        verifier_identities = dict(approved.verifier_identities)
        image_identities = {
            task: dict(identities)
            for task, identities in approved.immutable_image_identities.items()
        }
        subject_version = approved.subject_version
        harness_revision = approved.harness_revision
        task_revision = approved.task_revision
        if changed_category == "subject-version":
            subject_version = "pi@drifted-fixture"
        elif changed_category == "harness-revision":
            harness_revision = "sha256:drifted-harness"
        elif changed_category == "task-revision":
            task_revision = "sha256:drifted-task"
        elif changed_category == "verifier-identity":
            verifier_identities["task-a"] = "sha256:drifted-verifier"
        else:
            image_identities["task-a"]["agent"] = "sha256:drifted-image"
        runtime_resolver.identity = LaunchRuntimeIdentity(
            subject_version=subject_version,
            harness_revision=harness_revision,
            task_revision=task_revision,
            verifier_identities=verifier_identities,
            immutable_image_identities=image_identities,
            subject_capabilities=approved.subject_capabilities,
            available_credential_routes=(
                approved.available_credential_routes
            ),
        )

    runner = FakeConfirmedPiRunner(
        _planned_launch_plan_path(compiled),
        after_call=change_runtime_after_first_rep,
    )

    with pytest.raises(RuntimeError, match=r"^Launch input drift:"):
        execute_confirmed_launch(
            compiled.plan,
            confirmation_identity=compiled.plan.identity,
            runtime_resolver=runtime_resolver,
            pi_runner=runner,
        )

    assert [cell.rep for cell in runner.calls] == [0]
    events = [
        json.loads(line)
        for line in (
            _registered_state_path(state_root, "confirmed-fixture")
            / "events.ndjson"
        )
        .read_text()
        .splitlines()
    ]
    drift_event = next(
        event for event in events if event["event"] == "launch_input_drift"
    )
    assert len(drift_event["changes"]) == 1
    change = drift_event["changes"][0]
    assert change["category"] == changed_category
    expected_inputs = {
        "subject-version": "pi",
        "harness-revision": str((tmp_path / "repository").resolve()),
        "task-revision": "selected-tasks",
        "verifier-identity": "task-a",
        "immutable-image-identity": "task-a:agent",
    }
    assert change["input"] == expected_inputs[changed_category]
    assert change["observedIdentity"] != change["approvedIdentity"]


def test_execute_confirmed_launch_records_every_changed_input(
    tmp_path: Path,
) -> None:
    """One drift event reports all config and runtime identity changes."""
    compiled, config_leaf, _, _, state_root = _compile_single_cell_launch(
        tmp_path,
        reps=2,
    )
    runtime_resolver = _runtime_resolver_for(compiled)
    prompt_path = config_leaf.parent.parent / "orchestration.md"
    lock_path = config_leaf / "config-lock.json"

    def change_all_inputs_after_first_rep(cell: ConfirmedPiCell) -> None:
        if cell.rep != 0:
            return
        prompt_path.write_text("All inputs drifted.\n")
        lock_document = json.loads(lock_path.read_text())
        lock_document["versionImpact"] = "recompute"
        lock_path.write_text(json.dumps(lock_document) + "\n")
        runtime_resolver.identity = LaunchRuntimeIdentity(
            subject_version="pi@drifted-fixture",
            harness_revision="sha256:drifted-harness",
            task_revision="sha256:drifted-task",
            verifier_identities={"task-a": "sha256:drifted-verifier"},
            immutable_image_identities={
                "task-a": {
                    "agent": "sha256:drifted-agent",
                    "environment": "sha256:drifted-environment",
                    "verifier": "sha256:drifted-verifier-image",
                }
            },
        )

    runner = FakeConfirmedPiRunner(
        _planned_launch_plan_path(compiled),
        after_call=change_all_inputs_after_first_rep,
    )

    with pytest.raises(RuntimeError, match=r"^Launch input drift:"):
        execute_confirmed_launch(
            compiled.plan,
            confirmation_identity=compiled.plan.identity,
            runtime_resolver=runtime_resolver,
            pi_runner=runner,
        )

    events = [
        json.loads(line)
        for line in (
            _registered_state_path(state_root, "confirmed-fixture")
            / "events.ndjson"
        )
        .read_text()
        .splitlines()
    ]
    drift_event = next(
        event for event in events if event["event"] == "launch_input_drift"
    )
    assert len(drift_event["changes"]) == 9
    assert {change["category"] for change in drift_event["changes"]} == {
        "config-input",
        "config-lock",
        "subject-version",
        "harness-revision",
        "task-revision",
        "verifier-identity",
        "immutable-image-identity",
    }
    assert all(
        change["approvedIdentity"] != change["observedIdentity"]
        for change in drift_event["changes"]
    )
    assert [cell.rep for cell in runner.calls] == [0]


def test_execute_confirmed_launch_records_runtime_resolution_drift(
    tmp_path: Path,
) -> None:
    """A newly unresolved runtime identity stops before another rep."""
    compiled, _, _, _, state_root = _compile_single_cell_launch(
        tmp_path,
        reps=2,
    )
    approved_resolver = _runtime_resolver_for(compiled)

    class FailingRuntimeResolver:
        """Become unresolved only after the first fake rep."""

        def __init__(self) -> None:
            self.available = True

        def resolve_launch_runtime(
            self,
            request: LaunchRequest,
            tasks: tuple[str, ...],
        ) -> LaunchRuntimeIdentity:
            if not self.available:
                raise ValueError("fixture image identity unavailable")
            return approved_resolver.resolve_launch_runtime(request, tasks)

    runtime_resolver = FailingRuntimeResolver()

    def lose_runtime_identity_after_first_rep(cell: ConfirmedPiCell) -> None:
        if cell.rep == 0:
            runtime_resolver.available = False

    runner = FakeConfirmedPiRunner(
        _planned_launch_plan_path(compiled),
        after_call=lose_runtime_identity_after_first_rep,
    )

    with pytest.raises(RuntimeError, match=r"^Launch input drift:"):
        execute_confirmed_launch(
            compiled.plan,
            confirmation_identity=compiled.plan.identity,
            runtime_resolver=runtime_resolver,
            pi_runner=runner,
        )

    events = [
        json.loads(line)
        for line in (
            _registered_state_path(state_root, "confirmed-fixture")
            / "events.ndjson"
        )
        .read_text()
        .splitlines()
    ]
    drift_event = next(
        event for event in events if event["event"] == "launch_input_drift"
    )
    assert drift_event["changes"][0]["category"] == (
        "runtime-identity-resolution"
    )
    assert drift_event["changes"][0]["observedIdentity"] is None
    assert [cell.rep for cell in runner.calls] == [0]


def test_execute_confirmed_launch_ignores_routine_host_state_changes(
    tmp_path: Path,
) -> None:
    """Undeclared volatile host state does not invalidate a launch plan."""
    compiled, _, _, _, state_root = _compile_single_cell_launch(
        tmp_path,
        reps=2,
    )
    host_state_path = tmp_path / "host-state.json"

    def change_host_state_after_first_rep(cell: ConfirmedPiCell) -> None:
        if cell.rep == 0:
            host_state_path.write_text('{"freeDiskBytes":1,"quota":"wait"}\n')

    runner = FakeConfirmedPiRunner(
        _planned_launch_plan_path(compiled),
        after_call=change_host_state_after_first_rep,
    )

    execution = execute_confirmed_launch(
        compiled.plan,
        confirmation_identity=compiled.plan.identity,
        runtime_resolver=_runtime_resolver_for(compiled),
        pi_runner=runner,
    )

    assert [cell.rep for cell in runner.calls] == [0, 1]
    status = json.loads((execution.state_path / "status.json").read_text())
    assert status["state"] == "completed"


def test_execute_confirmed_launch_failure_keeps_plan_cell_state_and_log(
    tmp_path: Path,
) -> None:
    """A failed confirmed cell remains attributable in structured state."""
    compiled, _, _, _, state_root = _compile_single_cell_launch(tmp_path)
    failing_runner = FailingConfirmedPiRunner()

    with pytest.raises(RuntimeError, match="fixture runner stopped"):
        execute_confirmed_launch(
            compiled.plan,
            confirmation_identity=compiled.plan.identity,
            runtime_resolver=_runtime_resolver_for(compiled),
            pi_runner=failing_runner,
        )

    assert len(failing_runner.calls) == 1
    cell = failing_runner.calls[0]
    assert not cell.result_path.exists()
    run_state_root = _registered_state_path(state_root, "confirmed-fixture")
    plan = json.loads((run_state_root / "launch-plan.json").read_text())
    assert plan["planIdentity"] == compiled.plan.identity
    status = json.loads((run_state_root / "status.json").read_text())
    assert status["state"] == "failed"
    failed_cell = status["cells"]["task-a/baseline@1.0.0/rep0"]
    assert failed_cell["outcome"] == "exit=exception"
    log = (run_state_root / "logs" / "confirmed-pi-cell.log").read_text()
    assert f"launch_plan_identity={compiled.plan.identity}" in log
    assert "cell=task-a/baseline@1.0.0/rep0" in log
    assert "fixture runner stopped" in log
