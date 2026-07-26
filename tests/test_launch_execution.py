"""Execute confirmed plans through the public batch-launch seam."""

from __future__ import annotations

import concurrent.futures
import hashlib
import json
import threading
import time
from collections.abc import Callable, Mapping
from dataclasses import replace
from pathlib import Path
from typing import cast
from unittest.mock import patch

import pytest

from harness import config_lock, launch, run_batch
from harness.launch import (
    CompiledLaunch,
    ConfirmedOmpCell,
    ConfirmedPiCell,
    LaunchExecutionPolicies,
    LaunchInputDriftError,
    LaunchPreflightError,
    LaunchRequest,
    LaunchRuntimeIdentity,
    LaunchTaskSelection,
    LaunchTransientModelError,
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


def _install_confirmed_subject_helper(repository_root: Path) -> None:
    """Install the production child-process loader in a fixture workspace."""
    source_path = Path(run_batch.__file__).with_name(
        "confirmed_subject_process.py"
    )
    helper_path = repository_root / "harness" / source_path.name
    helper_path.write_text(source_path.read_text())


def _registered_state_path(state_root: Path, run_id: str) -> Path:
    """Find one registered state directory by its public manifest run id."""
    matches: list[Path] = []
    for manifest_path in state_root.glob("*/manifest.json"):
        manifest = json.loads(manifest_path.read_text())
        if manifest.get("run_id") == run_id:
            matches.append(manifest_path.parent)
    assert len(matches) == 1
    return matches[0]


class FakeConfirmedOmpRunner:
    """Produce controlled OMP results without a subject or model call."""

    def __init__(
        self,
        expected_plan_path: Path,
        after_call: Callable[[ConfirmedOmpCell], None] | None = None,
    ) -> None:
        """Require durable confirmed-plan state before fake execution."""
        self.expected_plan_path = expected_plan_path
        self.after_call = after_call
        self.calls: list[ConfirmedOmpCell] = []
        self.preflight_was_running = False

    def run_confirmed_omp_cell(
        self,
        cell: ConfirmedOmpCell,
    ) -> dict[str, object]:
        """Return OMP evidence through the same public launch lifecycle."""
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
        (cell_root / "logs" / "pi-rpc-runner.jsonl").write_text(
            '{"event":"prompt_sent","transport":"rpc"}\n'
            '{"event":"quiescent","transport":"rpc"}\n'
        )
        if self.after_call is not None:
            self.after_call(cell)
        return {
            "agent_exit": 0,
            "arm_advisor": {},
            "arm_models": {},
            "arm_pi_flags": [],
            "arm_settings": {},
            "omp_tools": ",".join(
                cast(list[str], cell.subject_behavior["toolWhitelist"])
            ),
            "reward_binary": 1,
            "reward_partial": 1.0,
            "total_tokens": 10,
            "verifier_exit": 0,
        }


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
            '{"type":"thinking_level_change","thinkingLevel":"low"}\n'
            '{"message":{"usage":{"total":10}}}\n'
        )
        (cell_root / "initial_context").mkdir(exist_ok=True)
        for request_number in (1, 2):
            request_path = (
                cell_root
                / "initial_context"
                / f"provider_request_{request_number:04d}.json"
            )
            request_path.write_text(
                json.dumps(
                    {
                        "model": "provider/model",
                        "reasoning": {"effort": "low"},
                    }
                )
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
        "requiredCapabilities": ["pi-rpc"],
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
    concurrency: int = 1,
    cell_retries: int = 0,
    transient_errors: str = "stop",
    agent_timeout_s: float | None = None,
    rpc_quiescence_s: float = 2.0,
    capture_initial_context: bool = True,
    auto_resume: bool = True,
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
        concurrency=concurrency,
        run_id=run_id,
        policies=LaunchExecutionPolicies(
            preflight=preflight,
            existing_results=existing_results,
            transient_errors=transient_errors,
            cell_retries=cell_retries,
            agent_timeout_s=agent_timeout_s,
            rpc_quiescence_s=rpc_quiescence_s,
            capture_initial_context=capture_initial_context,
            auto_resume=auto_resume,
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
    configs = document["configs"]
    return StaticLaunchRuntimeResolver(
        LaunchRuntimeIdentity(
            subject_version=document["subject"]["version"],
            harness_revision=runtime["harnessRevision"],
            task_revision=runtime["taskRevision"],
            verifier_identities=runtime["verifierIdentities"],
            immutable_image_identities=runtime["immutableImageIdentities"],
            subject_capabilities=frozenset(
                capability
                for config in configs
                for capability in config["requiredCapabilities"]
            ),
            available_credential_routes=frozenset(
                route
                for config in configs
                for route in config["credentialRoutes"]
            ),
            subject_runtime_identity=document["subject"].get(
                "runtimeIdentity",
                {},
            ),
        )
    )


def _compile_single_omp_launch(
    tmp_path: Path,
    *,
    preflight: str = "required",
    reps: int = 1,
    agent_timeout_s: float | None = None,
    rpc_quiescence_s: float = 2.0,
    capture_initial_context: bool = True,
    system_prompt_template: str | None = None,
) -> tuple[CompiledLaunch, Path]:
    """Compile one OMP preflight cell against temporary fixture inputs."""
    repository_root = tmp_path / "repository"
    tasks_root = tmp_path / "tasks"
    results_root = tmp_path / "canonical-results"
    state_root = tmp_path / "central-state"
    config_identity = "baseline-omp@1.0.0"
    config_root = repository_root / "configs" / config_identity
    config_leaf = config_root / "gpt-5.5" / "low"
    config_leaf.mkdir(parents=True)
    (config_root / "orchestration.md").write_text("Fixture behavior.\n")
    (config_root / "omp-tools.txt").write_text("read,bash,edit,write\n")
    if system_prompt_template is not None:
        (config_root / "omp-system-prompt.md").write_text(
            system_prompt_template
        )
    (config_leaf / "smoke.json").write_text('{"requireFiles":[]}\n')
    config_lock.write_config_lock(
        repository_root,
        config_identity,
        "openai-codex/gpt-5.5",
        "low",
        "rerun",
        {
            "credentialRoutes": ["OPENAI_CODEX_OAUTH"],
            "declaredRoles": [
                {
                    "billingCategory": "subscription quota",
                    "callBehavior": {
                        "callsPerRep": 1,
                        "kind": "fixed",
                        "maxConcurrency": 1,
                    },
                    "credentialRoute": "OPENAI_CODEX_OAUTH",
                    "modelSelection": {
                        "kind": "fixed",
                        "model": "openai-codex/gpt-5.5",
                        "provider": "openai-codex",
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
            "requiredCapabilities": ["omp-rpc"],
            "testedSubjectVersions": ["omp@16.3.5"],
            "usageSources": ["session/*.jsonl"],
        },
        state_root=state_root,
    )
    subject_runner = repository_root / "harness" / "run_omp.py"
    subject_runner.parent.mkdir(parents=True)
    subject_runner.write_text(
        """from pathlib import Path


def render_omp_system_prompt_template(template):
    return template.replace("{{current_date}}", "2025-01-02")


def run_cell(config, task, **kwargs):
    return {
        "agent_exit": 0,
        "arm_advisor": {},
        "arm_models": {},
        "arm_pi_flags": [],
        "arm_settings": {},
        "fixture_capture_initial_context": kwargs["capture_initial_context"],
        "fixture_config_leaf": str(kwargs["config_leaf"]),
        "fixture_config_root": str(kwargs["config_root"]),
        "fixture_credential_routes": list(kwargs["credential_routes"]),
        "fixture_omp_binary_path": str(kwargs["omp_binary_path"]),
        "fixture_output_cell": str(kwargs["output_cell"]),
        "fixture_persist_result_file": kwargs["persist_result_file"],
        "fixture_persist_result_index": kwargs["persist_result_index"],
        "fixture_rpc_quiescence": kwargs["rpc_quiescence"],
        "fixture_runner_path": str(Path(__file__).resolve()),
        "fixture_subject_behavior": kwargs["subject_behavior"],
        "fixture_timeout": kwargs["agent_timeout"],
        "reward_binary": 1,
        "reward_partial": 1.0,
        "total_tokens": 10,
        "verifier_exit": 0,
    }
"""
    )
    _install_confirmed_subject_helper(repository_root)
    task_root = tasks_root / "task-a"
    task_root.mkdir(parents=True)
    (task_root / "task.toml").write_text("[metadata]\n")
    request = LaunchRequest(
        subject="omp",
        model="openai-codex/gpt-5.5",
        thinking="low",
        configs=(config_identity,),
        baseline_config=config_identity,
        task_selection=LaunchTaskSelection(kind="tasks", tasks=("task-a",)),
        reps=reps,
        concurrency=1,
        run_id="confirmed-omp-fixture",
        policies=LaunchExecutionPolicies(
            preflight=preflight,
            existing_results="rerun",
            transient_errors="stop",
            cell_retries=0,
            agent_timeout_s=agent_timeout_s,
            rpc_quiescence_s=rpc_quiescence_s,
            capture_initial_context=capture_initial_context,
        ),
    )
    runtime = LaunchRuntimeIdentity(
        subject_version="omp@16.3.5",
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
        subject_capabilities=frozenset({"omp-rpc"}),
        available_credential_routes=frozenset({"OPENAI_CODEX_OAUTH"}),
        subject_runtime_identity={
            "binaryFingerprint": "sha256:omp-binary-fixture",
            "binaryPath": "/fixture/bin/omp",
            "versionOutput": "omp 16.3.5",
        },
    )
    compiled = compile_launch_request(
        request,
        repository_root=repository_root,
        tasks_root=tasks_root,
        results_root=results_root,
        state_root=state_root,
        runtime_resolver=StaticLaunchRuntimeResolver(runtime),
    )
    return compiled, state_root


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
    concurrency: int = 1,
    cell_retries: int = 0,
    transient_errors: str = "stop",
    agent_timeout_s: float | None = None,
    rpc_quiescence_s: float = 2.0,
    capture_initial_context: bool = True,
    auto_resume: bool = True,
    config_lock_metadata: Mapping[str, object] | None = None,
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
        config_lock_metadata or _config_lock_metadata(),
        state_root=state_root,
    )
    subject_runner = repository_root / "harness" / "run.py"
    subject_runner.parent.mkdir(parents=True)
    subject_runner.write_text(
        """from pathlib import Path


def run_cell(config, task, **kwargs):
    return {
        "agent_exit": 0,
        "arm_advisor": {},
        "arm_models": {},
        "arm_pi_flags": [],
        "arm_settings": {},
        "fixture_capture_initial_context": kwargs["capture_initial_context"],
        "fixture_config_leaf": str(kwargs["config_leaf"]),
        "fixture_config_root": str(kwargs["config_root"]),
        "fixture_credential_routes": list(kwargs["credential_routes"]),
        "fixture_output_cell": str(kwargs["output_cell"]),
        "fixture_persist_result_file": kwargs["persist_result_file"],
        "fixture_persist_result_index": kwargs["persist_result_index"],
        "fixture_rpc_quiescence": kwargs["rpc_quiescence"],
        "fixture_runner_path": str(Path(__file__).resolve()),
        "fixture_timeout": kwargs["agent_timeout"],
        "reward_binary": 1,
        "reward_partial": 1.0,
        "total_tokens": 10,
        "verifier_exit": 0,
    }
"""
    )
    _install_confirmed_subject_helper(repository_root)
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
        concurrency=concurrency,
        cell_retries=cell_retries,
        transient_errors=transient_errors,
        agent_timeout_s=agent_timeout_s,
        rpc_quiescence_s=rpc_quiescence_s,
        capture_initial_context=capture_initial_context,
        auto_resume=auto_resume,
    )
    return compiled, config_leaf, smoke_contract, results_root, state_root


def test_confirmed_execution_rejects_legacy_config_before_subject_call(
    tmp_path: Path,
) -> None:
    """Legacy configs stay readable but cannot create canonical results."""
    repository_root = tmp_path / "repository"
    tasks_root = tmp_path / "tasks"
    results_root = tmp_path / "canonical-results"
    state_root = tmp_path / "central-state"
    (repository_root / "configs" / "legacy" / "model" / "low").mkdir(
        parents=True
    )
    runner_path = repository_root / "harness" / "run.py"
    runner_path.parent.mkdir()
    runner_path.write_text("# fixture runner\n")
    task_root = tasks_root / "task-a"
    task_root.mkdir(parents=True)
    (task_root / "task.toml").write_text("[metadata]\n")
    request = LaunchRequest(
        subject="pi",
        model="provider/model",
        thinking="low",
        configs=("legacy",),
        baseline_config="legacy",
        task_selection=LaunchTaskSelection(kind="tasks", tasks=("task-a",)),
        reps=1,
        concurrency=1,
        run_id="legacy-plan",
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
    )
    resolver = StaticLaunchRuntimeResolver(runtime)
    compiled = compile_launch_request(
        request,
        repository_root=repository_root,
        tasks_root=tasks_root,
        results_root=results_root,
        state_root=state_root,
        runtime_resolver=resolver,
    )
    runner = FakeConfirmedPiRunner(_planned_launch_plan_path(compiled))

    with pytest.raises(
        ValueError,
        match=r"^Confirmed config release required:",
    ):
        execute_confirmed_launch(
            compiled.plan,
            confirmation_identity=compiled.plan.identity,
            runtime_resolver=resolver,
            pi_runner=runner,
        )

    assert runner.calls == []
    assert not results_root.exists()
    assert not state_root.exists()


def test_execute_command_consumes_only_reviewed_plan_and_confirmation(
    tmp_path: Path,
) -> None:
    """Canonical CLI execution consumes no repeated launch arguments."""
    compiled, _, _, _, _ = _compile_single_cell_launch(tmp_path)
    reviewed_plan_path = tmp_path / "reviewed-launch-plan.json"
    reviewed_plan_path.write_text(compiled.plan.canonical_json)
    runner = FakeConfirmedPiRunner(_planned_launch_plan_path(compiled))

    run_batch.main(
        [
            "execute",
            "--plan",
            str(reviewed_plan_path),
            "--confirm",
            compiled.plan.identity,
        ],
        runtime_resolver=_runtime_resolver_for(compiled),
        pi_runner=runner,
    )

    assert len(runner.calls) == 1
    assert runner.calls[0].launch_plan_identity == compiled.plan.identity
    result = json.loads(runner.calls[0].result_path.read_text())
    assert result["launch_plan_identity"] == compiled.plan.identity


def test_execute_command_default_pi_runner_uses_planned_workspace(
    tmp_path: Path,
) -> None:
    """The real Pi adapter executes the runner stored in the approved plan."""
    compiled, config_leaf, _, _, state_root = _compile_single_cell_launch(
        tmp_path,
        agent_timeout_s=321.0,
        rpc_quiescence_s=4.5,
        capture_initial_context=False,
    )
    reviewed_plan_path = tmp_path / "reviewed-launch-plan.json"
    reviewed_plan_path.write_text(compiled.plan.canonical_json)

    with patch(
        "harness.run.run_cell",
        side_effect=AssertionError("executing checkout runner was used"),
    ) as current_checkout_runner:
        run_batch.main(
            [
                "execute",
                "--plan",
                str(reviewed_plan_path),
                "--confirm",
                compiled.plan.identity,
            ],
            runtime_resolver=_runtime_resolver_for(compiled),
        )

    current_checkout_runner.assert_not_called()
    plan_document = compiled.plan.to_document()
    result_path = plan_document["batchCells"][0]["resultPath"]
    assert isinstance(result_path, str)
    result = json.loads(Path(result_path).read_text())
    assert result["fixture_runner_path"] == plan_document["subject"]["runner"]
    assert result["fixture_config_root"] == str(config_leaf.parents[1])
    assert result["fixture_config_leaf"] == str(config_leaf)
    assert result["fixture_output_cell"] == str(Path(result_path).parent)
    assert result["fixture_persist_result_file"] is False
    assert result["fixture_persist_result_index"] is False
    assert result["fixture_timeout"] == 321.0
    assert result["fixture_rpc_quiescence"] == 4.5
    assert result["fixture_capture_initial_context"] is False
    assert result["fixture_credential_routes"] == ["FIXTURE_CREDENTIAL"]

    manifest = json.loads(
        (
            _registered_state_path(state_root, "confirmed-fixture")
            / "manifest.json"
        ).read_text()
    )
    assert manifest["agent_timeout_s"] == 321.0
    assert manifest["rpc_quiescence_s"] == 4.5
    assert manifest["capture_initial_context"] is False


def test_confirmed_launch_resumes_after_transient_without_rerunning_rep(
    tmp_path: Path,
) -> None:
    """The same confirmed plan resumes read-only after a quota transient."""
    compiled, _, _, _, state_root = _compile_single_cell_launch(
        tmp_path,
        preflight="required",
        reps=2,
        transient_errors="pause",
    )

    class PauseOnSecondRepRunner(FakeConfirmedPiRunner):
        """Produce rep0, then emulate a provider transient on rep1."""

        def run_confirmed_pi_cell(
            self,
            cell: ConfirmedPiCell,
        ) -> dict[str, object]:
            if cell.rep == 1:
                self.calls.append(cell)
                raise LaunchTransientModelError("fixture quota window")
            return super().run_confirmed_pi_cell(cell)

    first_runner = PauseOnSecondRepRunner(_planned_launch_plan_path(compiled))
    with pytest.raises(LaunchTransientModelError):
        execute_confirmed_launch(
            compiled.plan,
            confirmation_identity=compiled.plan.identity,
            runtime_resolver=_runtime_resolver_for(compiled),
            pi_runner=first_runner,
        )

    state_path = _registered_state_path(state_root, "confirmed-fixture")
    first_status = json.loads((state_path / "status.json").read_text())
    assert first_status["state"] == "paused"
    assert [cell.rep for cell in first_runner.calls] == [0, 1]

    resumed_runner = FakeConfirmedPiRunner(_planned_launch_plan_path(compiled))
    execute_confirmed_launch(
        compiled.plan,
        confirmation_identity=compiled.plan.identity,
        runtime_resolver=_runtime_resolver_for(compiled),
        pi_runner=resumed_runner,
    )

    assert [cell.rep for cell in resumed_runner.calls] == [1]
    resumed_status = json.loads((state_path / "status.json").read_text())
    assert resumed_status["state"] == "completed"
    assert resumed_status["counts"]["batch_skipped"] == 1
    event_names = [
        json.loads(line)["event"]
        for line in (state_path / "events.ndjson").read_text().splitlines()
    ]
    assert "run_paused" in event_names
    assert "run_resumed" in event_names


def test_execute_command_automatically_resumes_confirmed_plan_after_transient(
    tmp_path: Path,
) -> None:
    """Canonical execution waits and retries without changing the plan."""
    compiled, _, _, _, state_root = _compile_single_cell_launch(
        tmp_path,
        transient_errors="pause",
    )
    reviewed_plan_path = tmp_path / "reviewed-launch-plan.json"
    reviewed_plan_path.write_text(compiled.plan.canonical_json)

    class PauseOnceRunner(FakeConfirmedPiRunner):
        """Pause one attempt, then produce the approved cell result."""

        def run_confirmed_pi_cell(
            self,
            cell: ConfirmedPiCell,
        ) -> dict[str, object]:
            """Raise one transient before delegating the retry."""
            if not self.calls:
                self.calls.append(cell)
                raise LaunchTransientModelError("fixture quota window")
            return super().run_confirmed_pi_cell(cell)

    runner = PauseOnceRunner(_planned_launch_plan_path(compiled))
    with patch.object(run_batch, "QuotaResumer") as resumer_class:
        resumer_class.return_value.on_transient_pause.return_value = {
            "reason": "fixture quota reset",
            "retry": True,
        }
        run_batch.main(
            [
                "execute",
                "--plan",
                str(reviewed_plan_path),
                "--confirm",
                compiled.plan.identity,
            ],
            runtime_resolver=_runtime_resolver_for(compiled),
            pi_runner=runner,
        )

    assert len(runner.calls) == 2
    assert all(
        cell.launch_plan_identity == compiled.plan.identity
        for cell in runner.calls
    )
    resumer_class.return_value.on_transient_pause.assert_called_once()
    state_path = _registered_state_path(state_root, "confirmed-fixture")
    status = json.loads((state_path / "status.json").read_text())
    assert status["state"] == "completed"
    event_names = [
        json.loads(line)["event"]
        for line in (state_path / "events.ndjson").read_text().splitlines()
    ]
    assert "run_paused" in event_names
    assert "run_resumed" in event_names


def test_confirmed_preflight_pause_resumes_with_one_terminal_verdict(
    tmp_path: Path,
) -> None:
    """A transient attempt stays nonterminal until resumed preflight passes."""
    compiled, _, _, _, state_root = _compile_single_cell_launch(
        tmp_path,
        preflight="required",
        transient_errors="pause",
    )

    class PausedPreflightRunner(FakeConfirmedPiRunner):
        """Pause the first preflight attempt before writing evidence."""

        def run_confirmed_pi_cell(
            self,
            cell: ConfirmedPiCell,
        ) -> dict[str, object]:
            self.calls.append(cell)
            raise LaunchTransientModelError("fixture preflight quota window")

    paused_runner = PausedPreflightRunner(_planned_launch_plan_path(compiled))
    with pytest.raises(LaunchTransientModelError):
        execute_confirmed_launch(
            compiled.plan,
            confirmation_identity=compiled.plan.identity,
            runtime_resolver=_runtime_resolver_for(compiled),
            pi_runner=paused_runner,
        )

    state_path = _registered_state_path(state_root, "confirmed-fixture")
    paused_status = json.loads((state_path / "status.json").read_text())
    paused_preflight = paused_status["preflight"]["task-a/baseline@1.0.0/rep0"]
    assert paused_preflight["state"] == "pending"
    paused_events = [
        json.loads(line)
        for line in (state_path / "events.ndjson").read_text().splitlines()
    ]
    assert (
        sum(
            event["event"] == "preflight_attempt_paused"
            for event in paused_events
        )
        == 1
    )
    assert all(
        event["event"] != "preflight_finished" for event in paused_events
    )

    resumed_runner = FakeConfirmedPiRunner(_planned_launch_plan_path(compiled))
    execute_confirmed_launch(
        compiled.plan,
        confirmation_identity=compiled.plan.identity,
        runtime_resolver=_runtime_resolver_for(compiled),
        pi_runner=resumed_runner,
    )

    final_events = [
        json.loads(line)
        for line in (state_path / "events.ndjson").read_text().splitlines()
    ]
    assert (
        sum(event["event"] == "preflight_finished" for event in final_events)
        == 1
    )
    final_status = json.loads((state_path / "status.json").read_text())
    assert (
        final_status["preflight"]["task-a/baseline@1.0.0/rep0"]["state"]
        == "passed"
    )


@pytest.mark.parametrize("preflight", ["disabled", "required"])
def test_confirmed_launch_honors_transient_stop_policy(
    tmp_path: Path,
    preflight: str,
) -> None:
    """A stop policy converts a provider transient into a hard failure."""
    compiled, _, _, _, state_root = _compile_single_cell_launch(
        tmp_path,
        preflight=preflight,
        transient_errors="stop",
    )

    class TransientConfirmedPiRunner(FakeConfirmedPiRunner):
        """Emit one controlled provider transient without a model call."""

        def run_confirmed_pi_cell(
            self,
            cell: ConfirmedPiCell,
        ) -> dict[str, object]:
            self.calls.append(cell)
            raise LaunchTransientModelError("fixture quota window")

    runner = TransientConfirmedPiRunner(_planned_launch_plan_path(compiled))

    with pytest.raises(RuntimeError, match="stopped after transient"):
        execute_confirmed_launch(
            compiled.plan,
            confirmation_identity=compiled.plan.identity,
            runtime_resolver=_runtime_resolver_for(compiled),
            pi_runner=runner,
        )

    status = json.loads(
        (
            _registered_state_path(state_root, "confirmed-fixture")
            / "status.json"
        ).read_text()
    )
    assert status["state"] == "failed"
    events = [
        json.loads(line)["event"]
        for line in (
            _registered_state_path(state_root, "confirmed-fixture")
            / "events.ndjson"
        )
        .read_text()
        .splitlines()
    ]
    assert "run_paused" not in events
    assert runner.calls


def test_execute_command_reports_pause_when_auto_resume_is_disabled(
    tmp_path: Path,
) -> None:
    """The canonical CLI preserves exit 75 when automatic resume is off."""
    compiled, _, _, _, state_root = _compile_single_cell_launch(
        tmp_path,
        transient_errors="pause",
        auto_resume=False,
    )
    reviewed_plan_path = tmp_path / "reviewed-launch-plan.json"
    reviewed_plan_path.write_text(compiled.plan.canonical_json)

    class PausingRunner(FakeConfirmedPiRunner):
        """Emit a controlled transient for the disabled auto-resume path."""

        def run_confirmed_pi_cell(
            self,
            cell: ConfirmedPiCell,
        ) -> dict[str, object]:
            """Stop every attempted cell with the established pause signal."""
            self.calls.append(cell)
            raise LaunchTransientModelError("fixture quota window")

    runner = PausingRunner(_planned_launch_plan_path(compiled))
    with pytest.raises(SystemExit) as raised:
        run_batch.main(
            [
                "execute",
                "--plan",
                str(reviewed_plan_path),
                "--confirm",
                compiled.plan.identity,
            ],
            runtime_resolver=_runtime_resolver_for(compiled),
            pi_runner=runner,
        )

    assert raised.value.code == 75
    assert len(runner.calls) == 1
    state_path = _registered_state_path(state_root, "confirmed-fixture")
    status = json.loads((state_path / "status.json").read_text())
    assert status["state"] == "paused"


def test_execute_command_default_omp_runner_uses_planned_workspace(
    tmp_path: Path,
) -> None:
    """The real OMP adapter executes planned behavior in the planned runner."""
    compiled, _ = _compile_single_omp_launch(
        tmp_path,
        preflight="disabled",
        agent_timeout_s=654.0,
        rpc_quiescence_s=3.5,
        capture_initial_context=False,
        system_prompt_template="date={{current_date}} cwd={{cwd}}\n",
    )
    reviewed_plan_path = tmp_path / "reviewed-omp-launch-plan.json"
    reviewed_plan_path.write_text(compiled.plan.canonical_json)

    with patch(
        "harness.run_omp.run_cell",
        side_effect=AssertionError("executing checkout runner was used"),
    ) as current_checkout_runner:
        run_batch.main(
            [
                "execute",
                "--plan",
                str(reviewed_plan_path),
                "--confirm",
                compiled.plan.identity,
            ],
            runtime_resolver=_runtime_resolver_for(compiled),
        )

    current_checkout_runner.assert_not_called()
    plan_document = compiled.plan.to_document()
    planned_config = plan_document["configs"][0]
    result_path = plan_document["batchCells"][0]["resultPath"]
    assert isinstance(result_path, str)
    result = json.loads(Path(result_path).read_text())
    assert result["fixture_runner_path"] == plan_document["subject"]["runner"]
    assert result["fixture_config_root"] == planned_config["configRoot"]
    assert result["fixture_config_leaf"] == planned_config["configLeaf"]
    assert result["fixture_output_cell"] == str(Path(result_path).parent)
    planned_behavior = planned_config["subjectBehavior"]
    assert planned_behavior["systemPrompt"] == (
        "date={{current_date}} cwd=/app\n"
    )
    assert result["fixture_subject_behavior"] == {
        **planned_behavior,
        "systemPrompt": "date=2025-01-02 cwd=/app\n",
    }
    assert result["fixture_omp_binary_path"] == "/fixture/bin/omp"
    assert result["fixture_timeout"] == 654.0
    assert result["fixture_rpc_quiescence"] == 3.5
    assert result["fixture_capture_initial_context"] is False
    assert result["fixture_credential_routes"] == ["OPENAI_CODEX_OAUTH"]
    assert result["fixture_persist_result_file"] is False
    assert result["fixture_persist_result_index"] is False


def test_confirmed_omp_preflight_executes_plan_resolved_subject_behavior(
    tmp_path: Path,
) -> None:
    """OMP uses the confirmed one-cell and atomic preflight contract."""
    compiled, state_root = _compile_single_omp_launch(tmp_path)
    runner = FakeConfirmedOmpRunner(_planned_launch_plan_path(compiled))

    execution = execute_confirmed_launch(
        compiled.plan,
        confirmation_identity=compiled.plan.identity,
        runtime_resolver=_runtime_resolver_for(compiled),
        omp_runner=runner,
    )

    assert runner.preflight_was_running is True
    assert len(runner.calls) == 1
    cell = runner.calls[0]
    assert cell.subject == "omp"
    assert cell.subject_runner.name == "run_omp.py"
    assert cell.subject_behavior == {
        "appendSystemPrompt": "Fixture behavior.",
        "captureInitialContext": True,
        "credentialRoute": "OPENAI_CODEX_OAUTH",
        "extensions": [],
        "modelRoute": "openai-codex",
        "overlay": None,
        "systemPrompt": None,
        "toolWhitelist": ["read", "bash", "edit", "write"],
    }
    assert cell.subject_runtime_identity == {
        "binaryFingerprint": "sha256:omp-binary-fixture",
        "binaryPath": "/fixture/bin/omp",
        "versionOutput": "omp 16.3.5",
    }
    result = json.loads(execution.result_path.read_text())
    assert result["config"] == "baseline-omp@1.0.0"
    assert result["config_lock_identity"].startswith("sha256:")
    assert result["subject"] == "omp"
    assert result["subject_version"] == "omp@16.3.5"
    assert result["subject_runtime_identity"] == (cell.subject_runtime_identity)
    assert result["model"] == "openai-codex/gpt-5.5"
    assert result["thinking_level"] == "low"
    assert result["harness_revision"] == "sha256:harness-fixture"
    assert result["task_revision"] == "sha256:task-fixture"
    assert result["verifier_identity"] == "sha256:verifier-fixture"
    assert result["immutable_image_identities"] == (
        cell.immutable_image_identities
    )
    assert result["launch_plan_identity"] == compiled.plan.identity
    assert result["arm_advisor"] == {}
    assert result["arm_models"] == {}
    assert result["arm_pi_flags"] == []
    assert result["arm_settings"] == {}
    status_path = (
        _registered_state_path(state_root, "confirmed-omp-fixture")
        / "status.json"
    )
    status = json.loads(status_path.read_text())
    assert status["state"] == "completed"
    assert (
        status["preflight"]["task-a/baseline-omp@1.0.0/rep0"]["state"]
        == "passed"
    )


def test_confirmed_omp_launch_stops_before_binary_identity_drifted_rep(
    tmp_path: Path,
) -> None:
    """Changed OMP binary identity stops the next confirmed rep."""
    compiled, state_root = _compile_single_omp_launch(
        tmp_path,
        preflight="disabled",
        reps=2,
    )
    runtime_resolver = _runtime_resolver_for(compiled)

    def change_binary_after_first_rep(cell: ConfirmedOmpCell) -> None:
        if cell.rep != 0:
            return
        runtime_resolver.identity = replace(
            runtime_resolver.identity,
            subject_runtime_identity={
                "binaryFingerprint": "sha256:drifted-omp-binary",
                "binaryPath": "/fixture/bin/omp",
                "versionOutput": "omp 16.3.5",
            },
        )

    runner = FakeConfirmedOmpRunner(
        _planned_launch_plan_path(compiled),
        after_call=change_binary_after_first_rep,
    )

    with pytest.raises(RuntimeError, match=r"^Launch input drift:"):
        execute_confirmed_launch(
            compiled.plan,
            confirmation_identity=compiled.plan.identity,
            runtime_resolver=runtime_resolver,
            omp_runner=runner,
        )

    assert [cell.rep for cell in runner.calls] == [0]
    events = [
        json.loads(line)
        for line in (
            _registered_state_path(state_root, "confirmed-omp-fixture")
            / "events.ndjson"
        )
        .read_text()
        .splitlines()
    ]
    drift_event = next(
        event for event in events if event["event"] == "launch_input_drift"
    )
    assert drift_event["changes"] == [
        {
            "approvedIdentity": {
                "binaryFingerprint": "sha256:omp-binary-fixture",
                "binaryPath": "/fixture/bin/omp",
                "versionOutput": "omp 16.3.5",
            },
            "category": "subject-runtime-identity",
            "input": "omp",
            "observedIdentity": {
                "binaryFingerprint": "sha256:drifted-omp-binary",
                "binaryPath": "/fixture/bin/omp",
                "versionOutput": "omp 16.3.5",
            },
        }
    ]


def test_config_seal_blocks_refresh_from_another_result_root(
    tmp_path: Path,
) -> None:
    """Central preflight evidence seals matching locks across worktrees."""
    state_root = tmp_path / "central-state"
    workspace_a = tmp_path / "worktree-a"
    workspace_b = tmp_path / "worktree-b"
    compiled_a, _, _, _, _ = _compile_single_cell_launch(
        workspace_a,
        preflight="required",
        state_root=state_root,
    )
    _, config_leaf_b, _, results_b, _ = _compile_single_cell_launch(
        workspace_b,
        preflight="required",
        state_root=state_root,
    )
    execute_confirmed_launch(
        compiled_a.plan,
        confirmation_identity=compiled_a.plan.identity,
        runtime_resolver=_runtime_resolver_for(compiled_a),
        pi_runner=FakeConfirmedPiRunner(_planned_launch_plan_path(compiled_a)),
    )
    prompt_b = config_leaf_b.parents[1] / "orchestration.md"
    prompt_b.write_text("Changed from another worktree.\n")

    with pytest.raises(ValueError, match=r"^Config lock sealed:"):
        config_lock.write_config_lock(
            workspace_b / "repository",
            "baseline@1.0.0",
            "provider/model",
            "low",
            "rerun",
            _config_lock_metadata(),
            replace=True,
            results_root=results_b,
            state_root=state_root,
        )

    assert not results_b.exists()


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
    assert {run["workspace"] for run in runs} == {
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
        manifest = (
            detail["manifest"]
            if "manifest" in detail
            else json.loads(Path(detail["paths"]["manifest"]).read_text())
        )
        assert manifest["workspace"] == summary["workspace"]
        assert manifest["results_root"]
        assert manifest["state_root"] == str(state_root.resolve())
        assert manifest["config_identities"] == ["baseline@1.0.0"]
        assert (
            manifest["launch_plan_identity"] == summary["launch_plan_identity"]
        )
        assert detail["preflight_state"] == "passed"


def test_confirmed_batch_honors_approved_worker_concurrency(
    tmp_path: Path,
) -> None:
    """Confirmed fan-out uses the worker count stored in the launch plan."""
    tasks = ("task-a", "task-b", "task-c", "task-d")
    compiled, _, _, _, _ = _compile_single_cell_launch(
        tmp_path,
        tasks=tasks,
        concurrency=2,
    )

    class ConcurrentConfirmedPiRunner(FakeConfirmedPiRunner):
        """Measure active fake subject calls through the public runner seam."""

        def __init__(self, expected_plan_path: Path) -> None:
            super().__init__(expected_plan_path)
            self._active_lock = threading.Lock()
            self.active_calls = 0
            self.max_active_calls = 0

        def run_confirmed_pi_cell(
            self,
            cell: ConfirmedPiCell,
        ) -> dict[str, object]:
            with self._active_lock:
                self.active_calls += 1
                self.max_active_calls = max(
                    self.max_active_calls,
                    self.active_calls,
                )
            try:
                time.sleep(0.1)
                return super().run_confirmed_pi_cell(cell)
            finally:
                with self._active_lock:
                    self.active_calls -= 1

    runner = ConcurrentConfirmedPiRunner(_planned_launch_plan_path(compiled))

    execute_confirmed_launch(
        compiled.plan,
        confirmation_identity=compiled.plan.identity,
        runtime_resolver=_runtime_resolver_for(compiled),
        pi_runner=runner,
    )

    assert runner.max_active_calls == 2
    assert {(cell.task, cell.rep) for cell in runner.calls} == {
        (task, 0) for task in tasks
    }


def test_concurrent_drift_allows_active_reps_and_blocks_pending_reps(
    tmp_path: Path,
) -> None:
    """One drift verdict gates every worker waiting to start a subject."""
    tasks = ("task-a", "task-b", "task-c", "task-d")
    compiled, config_leaf, _, _, state_root = _compile_single_cell_launch(
        tmp_path,
        tasks=tasks,
        concurrency=2,
    )
    prompt_path = config_leaf.parent.parent / "orchestration.md"

    class DriftAfterTwoActiveRunner(FakeConfirmedPiRunner):
        """Ensure two calls are active before mutating a confirmed input."""

        def __init__(self, expected_plan_path: Path) -> None:
            super().__init__(expected_plan_path)
            self.both_active = threading.Barrier(2)
            self.input_changed = threading.Event()

        def run_confirmed_pi_cell(
            self,
            cell: ConfirmedPiCell,
        ) -> dict[str, object]:
            assert cell.task in {"task-a", "task-b"}
            self.both_active.wait(timeout=5)
            result = super().run_confirmed_pi_cell(cell)
            if cell.task == "task-a":
                prompt_path.write_text("Drift after active calls.\n")
                self.input_changed.set()
            else:
                assert self.input_changed.wait(timeout=5)
            return result

    runner = DriftAfterTwoActiveRunner(_planned_launch_plan_path(compiled))

    with pytest.raises(LaunchInputDriftError):
        execute_confirmed_launch(
            compiled.plan,
            confirmation_identity=compiled.plan.identity,
            runtime_resolver=_runtime_resolver_for(compiled),
            pi_runner=runner,
        )

    assert {cell.task for cell in runner.calls} == {"task-a", "task-b"}
    state_path = _registered_state_path(state_root, "confirmed-fixture")
    events = [
        json.loads(line)
        for line in (state_path / "events.ndjson").read_text().splitlines()
    ]
    assert sum(event["event"] == "launch_input_drift" for event in events) == 1


def test_confirmed_launch_heartbeats_while_a_cell_is_active(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Central status remains live throughout confirmed subject execution."""
    compiled, _, _, _, state_root = _compile_single_cell_launch(tmp_path)
    monkeypatch.setattr(
        launch,
        "_CONFIRMED_HEARTBEAT_INTERVAL_S",
        0.05,
        raising=False,
    )

    class BlockingConfirmedPiRunner(FakeConfirmedPiRunner):
        """Hold one fake cell active while the test observes state writes."""

        def __init__(self, expected_plan_path: Path) -> None:
            super().__init__(expected_plan_path)
            self.started = threading.Event()
            self.release = threading.Event()

        def run_confirmed_pi_cell(
            self,
            cell: ConfirmedPiCell,
        ) -> dict[str, object]:
            self.started.set()
            assert self.release.wait(timeout=5)
            return super().run_confirmed_pi_cell(cell)

    runner = BlockingConfirmedPiRunner(_planned_launch_plan_path(compiled))
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        execution_future = executor.submit(
            execute_confirmed_launch,
            compiled.plan,
            confirmation_identity=compiled.plan.identity,
            runtime_resolver=_runtime_resolver_for(compiled),
            pi_runner=runner,
        )
        try:
            assert runner.started.wait(timeout=5)
            status_path = (
                _registered_state_path(state_root, "confirmed-fixture")
                / "status.json"
            )
            initial_write_time = status_path.stat().st_mtime_ns
            time.sleep(0.2)
            assert status_path.stat().st_mtime_ns > initial_write_time
        finally:
            runner.release.set()
        execution = execution_future.result(timeout=5)

    assert execution.state_path == status_path.parent


def test_confirmed_batch_honors_approved_missing_result_retries(
    tmp_path: Path,
) -> None:
    """A runner failure without a result retries only as the plan allows."""
    compiled, _, _, _, _ = _compile_single_cell_launch(
        tmp_path,
        cell_retries=1,
    )

    class RetryOnceConfirmedPiRunner(FakeConfirmedPiRunner):
        """Fail the first fake attempt before producing durable output."""

        def run_confirmed_pi_cell(
            self,
            cell: ConfirmedPiCell,
        ) -> dict[str, object]:
            if not self.calls:
                self.calls.append(cell)
                raise RuntimeError("fixture infrastructure failure")
            return super().run_confirmed_pi_cell(cell)

    runner = RetryOnceConfirmedPiRunner(_planned_launch_plan_path(compiled))

    execution = execute_confirmed_launch(
        compiled.plan,
        confirmation_identity=compiled.plan.identity,
        runtime_resolver=_runtime_resolver_for(compiled),
        pi_runner=runner,
    )

    assert len(runner.calls) == 2
    assert execution.result_path.is_file()
    status = json.loads((execution.state_path / "status.json").read_text())
    assert status["state"] == "completed"
    event_names = [
        json.loads(line)["event"]
        for line in (execution.state_path / "events.ndjson")
        .read_text()
        .splitlines()
    ]
    assert "run_failed" not in event_names


def _secondary_usage_config_lock_metadata() -> dict[str, object]:
    """Declare one advisor with explicit trace and result accounting."""
    metadata = _config_lock_metadata()
    roles = cast(list[dict[str, object]], metadata["declaredRoles"])
    roles.append(
        {
            "billingCategory": "paid API",
            "callBehavior": {
                "kind": "bounded",
                "maxCallsPerRep": 2,
                "maxConcurrency": 1,
            },
            "credentialRoute": "FIXTURE_CREDENTIAL",
            "modelSelection": {
                "kind": "fixed",
                "model": "provider/advisor",
                "provider": "provider",
                "thinking": "medium",
            },
            "name": "advisor",
            "roleKind": "advisor",
            "usageSource": {
                "format": "filtered-tool-events",
                "path": "tool-usage.jsonl",
                "recordSelector": {
                    "toolName": "advisor",
                    "type": "tool_execution_end",
                },
                "resultAccounting": {
                    "calls": "advisor_calls",
                    "totalTokens": "advisor_total_tokens",
                },
            },
        }
    )
    surfaces = cast(list[dict[str, object]], metadata["launchSurfaces"])
    surfaces[0]["modelRoles"] = ["executor", "advisor"]
    metadata["usageSources"] = ["session/*.jsonl", "tool-usage.jsonl"]
    return metadata


def test_planning_rejects_secondary_role_without_usage_evidence_contract(
    tmp_path: Path,
) -> None:
    """A declared secondary source must be enforceable by preflight."""
    with pytest.raises(
        ValueError,
        match=r"^Launch model role usage evidence missing:",
    ):
        _compile_single_cell_launch(
            tmp_path,
            preflight="required",
            config_lock_metadata=_secondary_usage_config_lock_metadata(),
        )


def test_missing_secondary_role_trace_fails_confirmed_preflight(
    tmp_path: Path,
) -> None:
    """A fake runner cannot pass without the declared advisor trace."""
    compiled, _, _, _, state_root = _compile_single_cell_launch(
        tmp_path,
        preflight="required",
        config_lock_metadata=_secondary_usage_config_lock_metadata(),
        smoke_contract_document={
            "minResultValues": {
                "advisor_calls": 1,
                "advisor_total_tokens": 1,
            },
            "requireUsageRecords": [
                {
                    "equals": {
                        "toolName": "advisor",
                        "type": "tool_execution_end",
                    },
                    "globs": ["tool-usage.jsonl"],
                    "minimum": 1,
                }
            ],
        },
    )

    class MissingAdvisorTraceRunner(FakeConfirmedPiRunner):
        """Return advisor totals but deliberately omit tool-usage.jsonl."""

        def run_confirmed_pi_cell(
            self,
            cell: ConfirmedPiCell,
        ) -> dict[str, object]:
            record = super().run_confirmed_pi_cell(cell)
            record.update({"advisor_calls": 1, "advisor_total_tokens": 10})
            return record

    runner = MissingAdvisorTraceRunner(_planned_launch_plan_path(compiled))
    with pytest.raises(LaunchPreflightError):
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
    diagnostics = status["preflight"]["task-a/baseline@1.0.0/rep0"][
        "diagnostics"
    ]
    assert [diagnostic["target"] for diagnostic in diagnostics] == [
        "tool-usage.jsonl:structured-records"
    ]
    assert status["counts"]["batch_done"] == 0


def test_mismatched_json_record_fails_confirmed_preflight(
    tmp_path: Path,
) -> None:
    """Provider effort must match structured smoke evidence before fan-out."""
    compiled, _, _, _, state_root = _compile_single_cell_launch(
        tmp_path,
        preflight="required",
        smoke_contract_document={
            "requireJsonRecords": [
                {
                    "equals": {
                        "model": "provider/model",
                        "reasoning.effort": "low",
                    },
                    "format": "json",
                    "globs": ["initial_context/provider_request_*.json"],
                    "minimum": 2,
                },
                {
                    "equals": {
                        "thinkingLevel": "low",
                        "type": "thinking_level_change",
                    },
                    "format": "jsonl",
                    "globs": ["session/*.jsonl"],
                    "minimum": 1,
                },
            ]
        },
    )

    def replace_provider_effort(cell: ConfirmedPiCell) -> None:
        for request_path in cell.result_path.parent.glob(
            "initial_context/provider_request_*.json"
        ):
            request = json.loads(request_path.read_text())
            request["reasoning"]["effort"] = "high"
            request_path.write_text(json.dumps(request))

    runner = FakeConfirmedPiRunner(
        _planned_launch_plan_path(compiled),
        after_call=replace_provider_effort,
    )
    with pytest.raises(LaunchPreflightError):
        execute_confirmed_launch(
            compiled.plan,
            confirmation_identity=compiled.plan.identity,
            runtime_resolver=_runtime_resolver_for(compiled),
            pi_runner=runner,
        )

    status = json.loads(
        (
            _registered_state_path(state_root, "confirmed-fixture")
            / "status.json"
        ).read_text()
    )
    diagnostics = status["preflight"]["task-a/baseline@1.0.0/rep0"][
        "diagnostics"
    ]
    assert diagnostics == [
        {
            "reason": "expected at least 2, got 0",
            "requirement": "requireJsonRecords",
            "target": (
                "initial_context/provider_request_*.json:json-records"
            ),
        }
    ]
    assert status["counts"]["batch_done"] == 0


def test_malformed_json_record_fails_confirmed_preflight(
    tmp_path: Path,
) -> None:
    """Corrupt structured evidence must report its path and block fan-out."""
    compiled, _, _, _, state_root = _compile_single_cell_launch(
        tmp_path,
        preflight="required",
        smoke_contract_document={
            "requireJsonRecords": [
                {
                    "equals": {"reasoning.effort": "low"},
                    "format": "json",
                    "globs": ["initial_context/provider_request_*.json"],
                    "minimum": 2,
                }
            ]
        },
    )

    def corrupt_provider_request(cell: ConfirmedPiCell) -> None:
        request_path = (
            cell.result_path.parent
            / "initial_context"
            / "provider_request_0001.json"
        )
        request_path.write_text("{not-json\n")

    runner = FakeConfirmedPiRunner(
        _planned_launch_plan_path(compiled),
        after_call=corrupt_provider_request,
    )
    with pytest.raises(LaunchPreflightError):
        execute_confirmed_launch(
            compiled.plan,
            confirmation_identity=compiled.plan.identity,
            runtime_resolver=_runtime_resolver_for(compiled),
            pi_runner=runner,
        )

    status = json.loads(
        (
            _registered_state_path(state_root, "confirmed-fixture")
            / "status.json"
        ).read_text()
    )
    diagnostics = status["preflight"]["task-a/baseline@1.0.0/rep0"][
        "diagnostics"
    ]
    assert diagnostics == [
        {
            "reason": "JSON record evidence is invalid at line 1, column 2",
            "requirement": "requireJsonRecords",
            "target": "initial_context/provider_request_0001.json",
        }
    ]
    assert status["counts"]["batch_done"] == 0


def test_malformed_jsonl_record_fails_even_when_minimum_matches(
    tmp_path: Path,
) -> None:
    """One corrupt JSONL line invalidates otherwise sufficient evidence."""
    compiled, _, _, _, state_root = _compile_single_cell_launch(
        tmp_path,
        preflight="required",
        smoke_contract_document={
            "requireJsonRecords": [
                {
                    "equals": {
                        "thinkingLevel": "low",
                        "type": "thinking_level_change",
                    },
                    "format": "jsonl",
                    "globs": ["session/*.jsonl"],
                    "minimum": 1,
                }
            ]
        },
    )

    def corrupt_session_record(cell: ConfirmedPiCell) -> None:
        session_path = cell.result_path.parent / "session" / "fixture.jsonl"
        session_path.write_text("{not-json\n" + session_path.read_text())

    runner = FakeConfirmedPiRunner(
        _planned_launch_plan_path(compiled),
        after_call=corrupt_session_record,
    )
    with pytest.raises(LaunchPreflightError):
        execute_confirmed_launch(
            compiled.plan,
            confirmation_identity=compiled.plan.identity,
            runtime_resolver=_runtime_resolver_for(compiled),
            pi_runner=runner,
        )

    status = json.loads(
        (
            _registered_state_path(state_root, "confirmed-fixture")
            / "status.json"
        ).read_text()
    )
    diagnostics = status["preflight"]["task-a/baseline@1.0.0/rep0"][
        "diagnostics"
    ]
    assert diagnostics == [
        {
            "reason": "JSONL record evidence is invalid at line 1, column 2",
            "requirement": "requireJsonRecords",
            "target": "session/fixture.jsonl",
        }
    ]
    assert status["counts"]["batch_done"] == 0


def test_passing_preflight_fans_out_exactly_once_without_second_confirmation(
    tmp_path: Path,
) -> None:
    """One confirmation covers atomic preflight and its conditional batch."""
    compiled, _, _, _, _ = _compile_single_cell_launch(
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


def test_reused_unsealed_result_creates_central_config_seal(
    tmp_path: Path,
) -> None:
    """A successful required re-evaluation seals without rewriting a result."""
    first, _, _, _, _ = _compile_single_cell_launch(
        tmp_path,
        preflight="disabled",
    )
    first_execution = execute_confirmed_launch(
        first.plan,
        confirmation_identity=first.plan.identity,
        runtime_resolver=_runtime_resolver_for(first),
        pi_runner=FakeConfirmedPiRunner(_planned_launch_plan_path(first)),
    )
    result_before = first_execution.result_path.read_bytes()
    assert "preflight_passed" not in json.loads(result_before)

    required = _compile_existing_fixture(
        tmp_path,
        preflight="required",
        run_id="required-recheck",
        existing_results="require-compatible",
    )
    runner = FakeConfirmedPiRunner(_planned_launch_plan_path(required))
    execute_confirmed_launch(
        required.plan,
        confirmation_identity=required.plan.identity,
        runtime_resolver=_runtime_resolver_for(required),
        pi_runner=runner,
    )

    assert runner.calls == []
    assert first_execution.result_path.read_bytes() == result_before
    next_plan = _compile_existing_fixture(
        tmp_path,
        preflight="new-configs",
        run_id="after-central-seal",
        existing_results="require-compatible",
    )
    assert next_plan.plan.to_document()["preflightCells"] == []


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
        pi_runner=FakeConfirmedPiRunner(_planned_launch_plan_path(first)),
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
    passed, _, _, passed_results, passed_state = _compile_single_cell_launch(
        tmp_path / "passed",
        preflight="required",
    )
    execute_confirmed_launch(
        passed.plan,
        confirmation_identity=passed.plan.identity,
        runtime_resolver=_runtime_resolver_for(passed),
        pi_runner=FakeConfirmedPiRunner(_planned_launch_plan_path(passed)),
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
            state_root=passed_state,
            replace=True,
            results_root=passed_results,
        )

    failed, _, _, failed_results, failed_state = _compile_single_cell_launch(
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
        state_root=failed_state,
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
        pi_runner=FakeConfirmedPiRunner(_planned_launch_plan_path(compiled)),
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
        state_root=state_root,
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
            state_root=state_root,
            results_root=results_root,
        )

    assert not (third_leaf / "config-lock.json").exists()


def test_confirmed_launch_reuses_compatible_result_without_writing(
    tmp_path: Path,
) -> None:
    """A compatible cell is reused without runner or artifact writes."""
    first, _, _, _, _ = _compile_single_cell_launch(tmp_path)
    first_runner = FakeConfirmedPiRunner(_planned_launch_plan_path(first))
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
    reuse_runner = FakeConfirmedPiRunner(_planned_launch_plan_path(compiled))

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
    first, _, _, _, _ = _compile_single_cell_launch(tmp_path)
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
        pi_runner=FakeConfirmedPiRunner(_planned_launch_plan_path(first)),
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
    runner = FakeConfirmedPiRunner(_planned_launch_plan_path(compiled))

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
    runner = FakeConfirmedPiRunner(_planned_launch_plan_path(approved))

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
        pi_runner=FakeConfirmedPiRunner(_planned_launch_plan_path(first)),
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
    fake_runner = FakeConfirmedPiRunner(_planned_launch_plan_path(compiled))

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
        tmp_path / "repository" / "configs" / "baseline@1.0.0" / relative_path
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
        "subject-capability",
        "credential-route",
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
        subject_capabilities = approved.subject_capabilities
        available_credential_routes = approved.available_credential_routes
        if changed_category == "subject-version":
            subject_version = "pi@drifted-fixture"
        elif changed_category == "harness-revision":
            harness_revision = "sha256:drifted-harness"
        elif changed_category == "task-revision":
            task_revision = "sha256:drifted-task"
        elif changed_category == "verifier-identity":
            verifier_identities["task-a"] = "sha256:drifted-verifier"
        elif changed_category == "immutable-image-identity":
            image_identities["task-a"]["agent"] = "sha256:drifted-image"
        elif changed_category == "subject-capability":
            subject_capabilities = frozenset()
        else:
            available_credential_routes = frozenset({"OPENAI_CODEX_OAUTH"})
        runtime_resolver.identity = LaunchRuntimeIdentity(
            subject_version=subject_version,
            harness_revision=harness_revision,
            task_revision=task_revision,
            verifier_identities=verifier_identities,
            immutable_image_identities=image_identities,
            subject_capabilities=subject_capabilities,
            available_credential_routes=available_credential_routes,
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
        "subject-capability": "pi-rpc",
        "credential-route": "FIXTURE_CREDENTIAL",
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
    assert len(drift_event["changes"]) == 11
    assert {change["category"] for change in drift_event["changes"]} == {
        "config-input",
        "config-lock",
        "subject-version",
        "harness-revision",
        "task-revision",
        "verifier-identity",
        "immutable-image-identity",
        "subject-capability",
        "credential-route",
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
    compiled, _, _, _, _ = _compile_single_cell_launch(
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
