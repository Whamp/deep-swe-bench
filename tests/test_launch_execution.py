"""Execute confirmed plans through the public batch-launch seam."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from harness import config_lock
from harness.launch import (
    CompiledLaunch,
    ConfirmedPiCell,
    LaunchExecutionPolicies,
    LaunchRequest,
    LaunchRuntimeIdentity,
    LaunchTaskSelection,
    compile_launch_request,
    execute_confirmed_launch,
)


class FailingConfirmedPiRunner:
    """Raise a controlled execution error without a subject or model call."""

    def __init__(self) -> None:
        """Track the one attempted confirmed cell."""
        self.calls: list[ConfirmedPiCell] = []

    def run_confirmed_pi_cell(self, cell: ConfirmedPiCell) -> dict[str, object]:
        """Fail after recording the exact plan-resolved cell."""
        self.calls.append(cell)
        raise RuntimeError("fixture runner stopped")


class FakeConfirmedPiRunner:
    """Produce one controlled Pi result without a subject or model call."""

    def __init__(self, expected_plan_path: Path) -> None:
        """Record calls and require durable plan state before execution."""
        self.expected_plan_path = expected_plan_path
        self.calls: list[ConfirmedPiCell] = []

    def run_confirmed_pi_cell(self, cell: ConfirmedPiCell) -> dict[str, object]:
        """Return a legacy-compatible result record for one confirmed cell."""
        assert self.expected_plan_path.is_file()
        self.calls.append(cell)
        cell_root = cell.result_path.parent
        (cell_root / "artifacts").mkdir(parents=True)
        (cell_root / "artifacts" / "model.patch").write_text("fixture patch\n")
        (cell_root / "session").mkdir()
        (cell_root / "session" / "fixture.jsonl").write_text(
            '{"message":{"usage":{"total":10}}}\n'
        )
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
        }


def _compile_single_cell_launch(
    tmp_path: Path,
) -> tuple[CompiledLaunch, Path, Path, Path, Path]:
    repository_root = tmp_path / "repository"
    tasks_root = tmp_path / "tasks"
    results_root = tmp_path / "canonical-results"
    state_root = tmp_path / "central-state"
    config_identity = "baseline@1.0.0"
    config_root = repository_root / "configs" / config_identity
    config_leaf = config_root / "model" / "low"
    config_leaf.mkdir(parents=True)
    (config_root / "orchestration.md").write_text("Fixture behavior.\n")
    smoke_contract = config_leaf / "smoke.json"
    smoke_contract.write_text('{"requireFiles":[]}\n')
    config_lock.write_config_lock(
        repository_root,
        config_identity,
        "provider/model",
        "low",
        "rerun",
        {
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
            "testedSubjectVersions": ["pi@0.81.1"],
            "usageSources": ["session/*.jsonl"],
        },
    )
    subject_runner = repository_root / "harness" / "run.py"
    subject_runner.parent.mkdir(parents=True)
    subject_runner.write_text("# fixture subject runner\n")
    task_root = tasks_root / "task-a"
    task_root.mkdir(parents=True)
    (task_root / "task.toml").write_text("[metadata]\n")
    request = LaunchRequest(
        subject="pi",
        model="provider/model",
        thinking="low",
        configs=(config_identity,),
        baseline_config=config_identity,
        task_selection=LaunchTaskSelection(kind="tasks", tasks=("task-a",)),
        reps=1,
        concurrency=1,
        run_id="confirmed-fixture",
        policies=LaunchExecutionPolicies(
            preflight="disabled",
            existing_results="rerun",
            transient_errors="stop",
            cell_retries=0,
        ),
    )
    runtime = LaunchRuntimeIdentity(
        subject_version="pi@0.81.1",
        harness_revision="sha256:harness-fixture",
        task_revision="sha256:task-fixture",
        verifier_identities={"task-a": "sha256:verifier-fixture"},
        immutable_image_identities={
            "task-a": {
                "agent": "sha256:agent-image",
                "environment": "sha256:environment-image",
                "verifier": "sha256:verifier-image",
            }
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

    compiled = compile_launch_request(
        request,
        repository_root=repository_root,
        tasks_root=tasks_root,
        results_root=results_root,
        state_root=state_root,
        runtime_resolver=RuntimeResolver(),
    )
    return compiled, config_leaf, smoke_contract, results_root, state_root


def test_execute_confirmed_launch_runs_exact_planned_pi_cell(
    tmp_path: Path,
) -> None:
    """A matching confirmation executes one plan-resolved Pi cell."""
    compiled, config_leaf, smoke_contract, results_root, state_root = (
        _compile_single_cell_launch(tmp_path)
    )
    plan_path = state_root / "confirmed-fixture" / "launch-plan.json"
    fake_runner = FakeConfirmedPiRunner(plan_path)
    assert not results_root.exists()
    assert fake_runner.calls == []

    execution = execute_confirmed_launch(
        compiled.plan,
        confirmation_identity=compiled.plan.identity,
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
        (state_root / "confirmed-fixture" / "status.json").read_text()
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
        state_root / "confirmed-fixture" / "launch-plan.json"
    )

    with pytest.raises(ValueError, match="Launch confirmation"):
        execute_confirmed_launch(
            compiled.plan,
            confirmation_identity=confirmation_identity,
            pi_runner=fake_runner,
        )

    assert fake_runner.calls == []
    assert not results_root.exists()
    assert not state_root.exists()


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
            pi_runner=failing_runner,
        )

    assert len(failing_runner.calls) == 1
    cell = failing_runner.calls[0]
    assert not cell.result_path.exists()
    run_state_root = state_root / "confirmed-fixture"
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
