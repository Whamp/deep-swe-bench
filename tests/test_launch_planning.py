"""Behavior tests for model-free launch planning through its public seam."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import replace
from pathlib import Path
from typing import cast

import pytest
from hypothesis import given
from hypothesis import strategies as st

from harness import config_lock, launch
from harness.launch import (
    LaunchExecutionPolicies,
    LaunchRequest,
    LaunchRuntimeIdentity,
    LaunchTaskSelection,
    canonical_launch_plan_json,
    compile_launch_request,
    confirmed_launch_run_key,
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
    smoke_contract: Mapping[str, object] | None = None,
) -> None:
    config_root = repository_root / "configs" / config_identity
    config_leaf = config_root / "model" / "low"
    config_leaf.mkdir(parents=True)
    (config_root / "README.md").write_text("Fixture documentation.\n")
    (config_root / "orchestration.md").write_text(prompt)
    if secret is not None:
        (config_root / "env").write_text(f"OPENAI_API_KEY={secret}\n")
    if smoke_contract is None:
        smoke_contract = {"requireFiles": []}
    (config_leaf / "smoke.json").write_text(
        json.dumps(smoke_contract, sort_keys=True) + "\n"
    )
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
        subject_capabilities=frozenset({"pi-rpc"}),
        available_credential_routes=frozenset(
            {
                "FIXTURE_CREDENTIAL",
                "OPENAI_API_KEY",
                "OPENAI_CODEX_OAUTH",
                "WORKFLOW_API_KEY",
            }
        ),
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


def _write_launch_fixture(
    tmp_path: Path,
    *,
    review_smoke_contract: Mapping[str, object] | None = None,
) -> tuple[Path, Path, Path, Path]:
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
        smoke_contract=review_smoke_contract,
    )
    return repository_root, tasks_root, results_root, state_root


def _reject_versioned_smoke_contract(
    tmp_path: Path,
    contract: Mapping[str, object],
) -> str:
    """Compile through the public seam and return its smoke rejection."""
    repository_root, tasks_root, results_root, state_root = (
        _write_launch_fixture(
            tmp_path,
            review_smoke_contract=contract,
        )
    )
    runtime_resolver = FakeLaunchRuntimeResolver(_runtime_identity())

    with pytest.raises(
        ValueError,
        match=r"^Smoke contract rejected:",
    ) as raised:
        compile_launch_request(
            _launch_request(),
            repository_root=repository_root,
            tasks_root=tasks_root,
            results_root=results_root,
            state_root=state_root,
            runtime_resolver=runtime_resolver,
        )

    assert runtime_resolver.requests == []
    assert not results_root.exists()
    assert not state_root.exists()
    return str(raised.value)


def test_launch_planning_rejects_readme_prose_smoke_gate(
    tmp_path: Path,
) -> None:
    """README wording cannot authorize a versioned launch."""
    target = "configs/review-assistant@1.0.0/README.md"
    message = _reject_versioned_smoke_contract(
        tmp_path,
        {
            "requireRepoText": [
                {"globs": [target], "text": "Fixture documentation."}
            ]
        },
    )

    assert "model/low/smoke.json#/requireRepoText/0" in message
    assert "assertion_kind='requireRepoText'" in message
    assert f"target={target!r}" in message
    assert "README prose" in message


def test_launch_planning_rejects_documentation_wording_smoke_gate(
    tmp_path: Path,
) -> None:
    """Documentation wording cannot authorize a versioned launch."""
    target = "docs/subject-compatibility.md"
    message = _reject_versioned_smoke_contract(
        tmp_path,
        {
            "requireRepoText": [
                {"globs": [target], "text": "Compatible with the subject."}
            ]
        },
    )

    assert "assertion_kind='requireRepoText'" in message
    assert f"target={target!r}" in message
    assert "documentation wording" in message


def test_launch_planning_rejects_source_prose_smoke_gate(
    tmp_path: Path,
) -> None:
    """Source prose and formatting cannot authorize a versioned launch."""
    target = "harness/run.py"
    message = _reject_versioned_smoke_contract(
        tmp_path,
        {
            "requireRepoText": [
                {"globs": [target], "text": "# fixture subject runner"}
            ]
        },
    )

    assert "assertion_kind='requireRepoText'" in message
    assert f"target={target!r}" in message
    assert "source prose or formatting" in message


def test_launch_planning_rejects_newline_sensitive_smoke_gate(
    tmp_path: Path,
) -> None:
    """Newline placement cannot authorize a versioned launch."""
    target = "logs/extension.jsonl"
    message = _reject_versioned_smoke_contract(
        tmp_path,
        {
            "requireText": [
                {
                    "globs": [target],
                    "text": "first machine line\nsecond line",
                }
            ]
        },
    )

    assert "assertion_kind='requireText'" in message
    assert f"target={target!r}" in message
    assert "newline placement" in message


def test_launch_planning_rejects_character_count_smoke_gate(
    tmp_path: Path,
) -> None:
    """Character counts cannot authorize a versioned launch."""
    message = _reject_versioned_smoke_contract(
        tmp_path,
        {"equalsResultValues": {"orchestration_chars": 973}},
    )

    assert "assertion_kind='equalsResultValues'" in message
    assert "target='orchestration_chars'" in message
    assert "character counts" in message


def test_launch_planning_rejects_unknown_smoke_assertion_kind(
    tmp_path: Path,
) -> None:
    """Unknown versioned assertion kinds cannot be silently ignored."""
    message = _reject_versioned_smoke_contract(
        tmp_path,
        {"requireExactTextLength": {"README.md": 42}},
    )

    assert "location=" in message
    assert "assertion_kind='requireExactTextLength'" in message
    assert "target='<contract>'" in message
    assert "unsupported assertion kind" in message


def test_launch_planning_rejects_malformed_smoke_assertion(
    tmp_path: Path,
) -> None:
    """Supported assertion kinds still require their documented JSON shape."""
    message = _reject_versioned_smoke_contract(
        tmp_path,
        {"requireFiles": {"session/*.jsonl": True}},
    )

    assert "model/low/smoke.json#/requireFiles" in message
    assert "assertion_kind='requireFiles'" in message
    assert "target='<contract>'" in message
    assert "expected a list of relative file globs" in message


def test_launch_planning_rejects_missing_smoke_repository_artifact(
    tmp_path: Path,
) -> None:
    """Required repository artifacts must exist before launch approval."""
    target = "analysis/missing-provider-probe.jsonl"
    message = _reject_versioned_smoke_contract(
        tmp_path,
        {"requireRepoFiles": [target]},
    )

    assert "assertion_kind='requireRepoFiles'" in message
    assert f"target={target!r}" in message
    assert "referenced repository artifact does not exist" in message


def test_launch_planning_rejects_marker_without_extension_owner(
    tmp_path: Path,
) -> None:
    """A stable marker must identify an existing owning extension artifact."""
    owner = "configs/review-assistant@1.0.0/extensions/machine-markers.ts"
    message = _reject_versioned_smoke_contract(
        tmp_path,
        {
            "requireExtensionMarkers": [
                {
                    "extension": owner,
                    "globs": ["logs/pi.stderr.txt"],
                    "marker": "__REVIEW_ASSISTANT_READY__",
                }
            ]
        },
    )

    assert "assertion_kind='requireExtensionMarkers'" in message
    assert f"target={owner!r}" in message
    assert "owning extension artifact does not exist" in message


def test_launch_planning_rejects_unstructured_usage_record_gate(
    tmp_path: Path,
) -> None:
    """Usage gates must identify structured record fields and a count."""
    target = "usage/worker-usage.ndjson"
    message = _reject_versioned_smoke_contract(
        tmp_path,
        {
            "requireUsageRecords": [
                {
                    "globs": [target],
                    "minimum": 1,
                    "text": "assistant_usage",
                }
            ]
        },
    )

    assert "assertion_kind='requireUsageRecords'" in message
    assert f"target={target!r}" in message
    assert "structured equals fields" in message


def test_launch_planning_accepts_durable_versioned_smoke_gates(
    tmp_path: Path,
) -> None:
    """Structured evidence and extension-owned markers are valid gates."""
    config_identity = "review-assistant@1.0.0"
    owner = f"configs/{config_identity}/extensions/machine-markers.ts"
    contract = {
        "equalsResultValues": {
            "config": config_identity,
            "thinking_level": "low",
        },
        "minResultValues": {
            "combined_total_tokens": 1,
            "worker_calls": 1,
        },
        "requireFiles": [
            "session/*.jsonl",
            "usage/worker-usage.ndjson",
        ],
        "requireRepoFiles": [owner],
        "requireUsageRecords": [
            {
                "equals": {"event": "assistant_usage", "role": "worker"},
                "globs": ["usage/worker-usage.ndjson"],
                "minimum": 1,
            }
        ],
        "requireExtensionMarkers": [
            {
                "extension": owner,
                "globs": ["logs/pi.stderr.txt"],
                "marker": "__REVIEW_ASSISTANT_READY__",
            }
        ],
        "forbidExtensionMarkers": [
            {
                "extension": owner,
                "globs": ["logs/pi.stderr.txt"],
                "marker": "__REVIEW_ASSISTANT_BROKEN__",
            }
        ],
    }
    repository_root, tasks_root, results_root, state_root = (
        _write_launch_fixture(
            tmp_path,
            review_smoke_contract=contract,
        )
    )
    owner_path = repository_root / owner
    owner_path.parent.mkdir()
    owner_path.write_text("export default {}\n")
    lock_path = (
        repository_root
        / "configs"
        / config_identity
        / "model"
        / "low"
        / "config-lock.json"
    )
    previous_lock = json.loads(lock_path.read_text())
    lock_path.unlink()
    config_lock.write_config_lock(
        repository_root,
        config_identity,
        "provider/model",
        "low",
        "rerun",
        {
            "credentialRoutes": previous_lock["credentialRoutes"],
            "declaredRoles": previous_lock["declaredRoles"],
            "launchSurfaces": [
                {"modelRoles": [], "path": "extensions/machine-markers.ts"}
            ],
            "testedSubjectVersions": previous_lock["testedSubjectVersions"],
            "usageSources": previous_lock["usageSources"],
        },
    )

    compiled = compile_launch_request(
        _launch_request(),
        repository_root=repository_root,
        tasks_root=tasks_root,
        results_root=results_root,
        state_root=state_root,
        runtime_resolver=FakeLaunchRuntimeResolver(_runtime_identity()),
    )

    review_config = compiled.plan.to_document()["configs"][1]
    assert review_config["smokeContract"] == str(
        repository_root
        / "configs"
        / config_identity
        / "model"
        / "low"
        / "smoke.json"
    )
    assert not results_root.exists()
    assert not state_root.exists()


def test_launch_planning_preserves_legacy_smoke_contract_readability(
    tmp_path: Path,
) -> None:
    """Legacy contracts remain referenced without gaining versioned approval."""
    repository_root, tasks_root, results_root, state_root = (
        _write_launch_fixture(tmp_path)
    )
    legacy_root = repository_root / "configs" / "legacy-review"
    legacy_leaf = legacy_root / "model" / "low"
    legacy_leaf.mkdir(parents=True)
    (legacy_root / "README.md").write_text("Historical diagnosis only.\n")
    legacy_contract = legacy_leaf / "smoke.json"
    legacy_contract.write_text(
        json.dumps(
            {
                "requireRepoText": [
                    {
                        "globs": ["configs/legacy-review/README.md"],
                        "text": "Historical diagnosis only.",
                    }
                ]
            }
        )
        + "\n"
    )
    request = replace(
        _launch_request(),
        configs=("baseline@1.0.0", "legacy-review"),
    )

    compiled = compile_launch_request(
        request,
        repository_root=repository_root,
        tasks_root=tasks_root,
        results_root=results_root,
        state_root=state_root,
        runtime_resolver=FakeLaunchRuntimeResolver(_runtime_identity()),
    )

    legacy_config = compiled.plan.to_document()["configs"][1]
    assert legacy_config["legacy"] is True
    assert legacy_config["smokeContract"] == str(legacy_contract)
    assert "legacy configs have no config-lock provenance: legacy-review" in (
        compiled.receipt
    )


def test_launch_planning_reports_malformed_smoke_json(
    tmp_path: Path,
) -> None:
    """Malformed contract JSON fails with a smoke-specific location."""
    repository_root, tasks_root, results_root, state_root = (
        _write_launch_fixture(tmp_path)
    )
    contract_path = (
        repository_root
        / "configs"
        / "review-assistant@1.0.0"
        / "model"
        / "low"
        / "smoke.json"
    )
    contract_path.write_text('{"requireFiles": [}\n')

    with pytest.raises(
        ValueError,
        match=r"^Smoke contract rejected:",
    ) as raised:
        compile_launch_request(
            _launch_request(),
            repository_root=repository_root,
            tasks_root=tasks_root,
            results_root=results_root,
            state_root=state_root,
            runtime_resolver=FakeLaunchRuntimeResolver(_runtime_identity()),
        )

    message = str(raised.value)
    assert "model/low/smoke.json#/<contract>" in message
    assert "assertion_kind='<syntax>'" in message
    assert "target='<contract>'" in message
    assert "invalid JSON" in message


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
        (
            state_root
            / confirmed_launch_run_key("fixture-run", first.plan.identity)
        ).resolve()
    )
    assert len(plan["batchCells"]) == 4
    assert len(runtime_resolver.requests) == 2
    assert not results_root.exists()
    assert not state_root.exists()


def test_launch_plan_resolves_and_renders_declared_model_role_patterns(
    tmp_path: Path,
) -> None:
    """Planning resolves fixed, inherited, and bounded dynamic model roles."""
    repository_root, tasks_root, results_root, state_root = (
        _write_launch_fixture(tmp_path)
    )
    declared_roles = [
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
        },
        {
            "billingCategory": "paid API",
            "callBehavior": {
                "kind": "bounded",
                "maxCallsPerRep": 2,
                "maxConcurrency": 1,
            },
            "credentialRoute": "WORKFLOW_API_KEY",
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
            },
        },
        {
            "billingCategory": "subscription quota",
            "callBehavior": {
                "kind": "bounded",
                "maxCallsPerRep": 3,
                "maxConcurrency": 1,
            },
            "credentialRoute": "OPENAI_CODEX_OAUTH",
            "modelSelection": {"kind": "inherited", "role": "executor"},
            "name": "memory-observer",
            "roleKind": "observational-memory",
            "usageSource": {
                "format": "compact-worker-trace",
                "path": (
                    "pi-agent/observational-memory/worker-usage/usage.ndjson"
                ),
            },
        },
        {
            "billingCategory": "subscription quota",
            "callBehavior": {
                "kind": "bounded",
                "maxCallsPerRep": 2,
                "maxConcurrency": 1,
            },
            "credentialRoute": "OPENAI_CODEX_OAUTH",
            "modelSelection": {"kind": "inherited", "role": "executor"},
            "name": "recursive-child",
            "roleKind": "recursive",
            "usageSource": {
                "format": "compact-jsonl",
                "path": "recursive-usage/usage.ndjson",
            },
        },
        {
            "billingCategory": "paid API",
            "callBehavior": {
                "kind": "bounded",
                "maxCallsPerRep": 4,
                "maxConcurrency": 2,
            },
            "credentialRoute": "WORKFLOW_API_KEY",
            "modelSelection": {
                "kind": "bounded-dynamic",
                "models": [
                    {
                        "model": "provider/worker-a",
                        "provider": "provider",
                        "thinking": "medium",
                    },
                    {
                        "model": "provider/worker-b",
                        "provider": "provider",
                        "thinking": "high",
                    },
                ],
            },
            "name": "workflow-worker",
            "roleKind": "workflow",
            "usageSource": {
                "format": "compact-jsonl",
                "path": "workflow-usage/usage.ndjson",
            },
        },
    ]
    for config_identity in ("baseline@1.0.0", "review-assistant@1.0.0"):
        config_root = repository_root / "configs" / config_identity
        extension_path = config_root / "extensions" / "roles.ts"
        extension_path.parent.mkdir()
        extension_path.write_text("export default {}\n")
        lock_path = config_root / "model" / "low" / "config-lock.json"
        lock_path.unlink()
        config_lock.write_config_lock(
            repository_root,
            config_identity,
            "provider/model",
            "low",
            "rerun",
            {
                "credentialRoutes": [
                    "OPENAI_CODEX_OAUTH",
                    "WORKFLOW_API_KEY",
                ],
                "declaredRoles": declared_roles,
                "launchSurfaces": [
                    {
                        "modelRoles": [
                            "advisor",
                            "memory-observer",
                            "recursive-child",
                            "workflow-worker",
                        ],
                        "path": "extensions/roles.ts",
                    }
                ],
                "requiredCapabilities": ["pi-rpc"],
                "testedSubjectVersions": ["pi@0.81.1"],
                "usageSources": [
                    "pi-agent/observational-memory/worker-usage/usage.ndjson",
                    "recursive-usage/usage.ndjson",
                    "session/*.jsonl",
                    "tool-usage.jsonl",
                    "workflow-usage/usage.ndjson",
                ],
            },
        )

    compiled = compile_launch_request(
        _launch_request(),
        repository_root=repository_root,
        tasks_root=tasks_root,
        results_root=results_root,
        state_root=state_root,
        runtime_resolver=FakeLaunchRuntimeResolver(_runtime_identity()),
    )

    roles = {
        role["name"]: role
        for role in compiled.plan.to_document()["configs"][1]["declaredRoles"]
    }
    assert compiled.plan.to_document()["configs"][1]["launchSurfaces"] == [
        {
            "modelRoles": [
                "advisor",
                "memory-observer",
                "recursive-child",
                "workflow-worker",
            ],
            "path": "extensions/roles.ts",
        }
    ]
    assert roles["executor"]["models"] == [
        {
            "model": "provider/model",
            "provider": "provider",
            "thinking": "low",
        }
    ]
    advisor_models = roles["advisor"]["models"]
    workflow_models = roles["workflow-worker"]["models"]
    assert isinstance(advisor_models, list)
    advisor_model = cast(dict[str, object], advisor_models[0])
    assert advisor_model["model"] == "provider/advisor"
    assert roles["memory-observer"]["models"] == roles["executor"]["models"]
    assert roles["recursive-child"]["models"] == roles["executor"]["models"]
    assert isinstance(workflow_models, list)
    workflow_model_documents = cast(list[dict[str, object]], workflow_models)
    assert [model["model"] for model in workflow_model_documents] == [
        "provider/worker-a",
        "provider/worker-b",
    ]
    assert (
        "memory-observer | observational-memory | inherited from executor | "
        "provider | provider/model | low"
    ) in compiled.receipt
    assert "advisor | advisor | fixed | provider | provider/advisor" in (
        compiled.receipt
    )
    assert "recursive-child | recursive | inherited from executor" in (
        compiled.receipt
    )
    assert "workflow-worker | workflow | bounded dynamic (2 models)" in (
        compiled.receipt
    )
    assert "max 4 calls/rep; max concurrency 2" in compiled.receipt
    assert "Required capabilities: pi-rpc" in compiled.receipt
    assert "Tested subject versions: pi@0.81.1" in compiled.receipt


def test_launch_planning_rejects_untested_subject_version(
    tmp_path: Path,
) -> None:
    """A subject version absent from a config lock cannot reach approval."""
    repository_root, tasks_root, results_root, state_root = (
        _write_launch_fixture(tmp_path)
    )
    runtime = replace(_runtime_identity(), subject_version="pi@0.82.0")

    with pytest.raises(
        ValueError, match=r"^Untested subject version:"
    ) as raised:
        compile_launch_request(
            _launch_request(),
            repository_root=repository_root,
            tasks_root=tasks_root,
            results_root=results_root,
            state_root=state_root,
            runtime_resolver=FakeLaunchRuntimeResolver(runtime),
        )

    assert "baseline@1.0.0" in str(raised.value)
    assert "pi@0.82.0" in str(raised.value)
    assert not results_root.exists()
    assert not state_root.exists()


def test_launch_planning_rejects_missing_subject_capability(
    tmp_path: Path,
) -> None:
    """Every required subject capability must have runtime evidence."""
    repository_root, tasks_root, results_root, state_root = (
        _write_launch_fixture(tmp_path)
    )
    config_identity = "review-assistant@1.0.0"
    lock_path = (
        repository_root
        / "configs"
        / config_identity
        / "model"
        / "low"
        / "config-lock.json"
    )
    previous_lock = json.loads(lock_path.read_text())
    lock_path.unlink()
    config_lock.write_config_lock(
        repository_root,
        config_identity,
        "provider/model",
        "low",
        "rerun",
        {
            "credentialRoutes": previous_lock["credentialRoutes"],
            "declaredRoles": previous_lock["declaredRoles"],
            "requiredCapabilities": ["sandbox-rpc"],
            "testedSubjectVersions": previous_lock["testedSubjectVersions"],
            "usageSources": previous_lock["usageSources"],
        },
    )

    with pytest.raises(
        ValueError, match=r"^Launch subject capability missing:"
    ) as raised:
        compile_launch_request(
            _launch_request(),
            repository_root=repository_root,
            tasks_root=tasks_root,
            results_root=results_root,
            state_root=state_root,
            runtime_resolver=FakeLaunchRuntimeResolver(_runtime_identity()),
        )

    assert "sandbox-rpc" in str(raised.value)
    assert not results_root.exists()
    assert not state_root.exists()


def test_launch_planning_rejects_unavailable_credential_route(
    tmp_path: Path,
) -> None:
    """A declared credential route must be available before approval."""
    repository_root, tasks_root, results_root, state_root = (
        _write_launch_fixture(tmp_path)
    )
    runtime = replace(
        _runtime_identity(), available_credential_routes=frozenset()
    )

    with pytest.raises(
        ValueError, match=r"^Launch credential route unavailable:"
    ) as raised:
        compile_launch_request(
            _launch_request(),
            repository_root=repository_root,
            tasks_root=tasks_root,
            results_root=results_root,
            state_root=state_root,
            runtime_resolver=FakeLaunchRuntimeResolver(runtime),
        )

    assert "FIXTURE_CREDENTIAL" in str(raised.value)
    assert not results_root.exists()
    assert not state_root.exists()


def test_launch_planning_rejects_executor_role_mismatch(tmp_path: Path) -> None:
    """The declared executor must match the requested model and thinking."""
    repository_root, tasks_root, results_root, state_root = (
        _write_launch_fixture(tmp_path)
    )
    config_identity = "review-assistant@1.0.0"
    lock_path = (
        repository_root
        / "configs"
        / config_identity
        / "model"
        / "low"
        / "config-lock.json"
    )
    previous_lock = json.loads(lock_path.read_text())
    role = dict(previous_lock["declaredRoles"][0])
    selection = dict(role["modelSelection"])
    selection["model"] = "provider/other-model"
    role["modelSelection"] = selection
    lock_path.unlink()
    config_lock.write_config_lock(
        repository_root,
        config_identity,
        "provider/model",
        "low",
        "rerun",
        {
            "credentialRoutes": previous_lock["credentialRoutes"],
            "declaredRoles": [role],
            "testedSubjectVersions": previous_lock["testedSubjectVersions"],
            "usageSources": previous_lock["usageSources"],
        },
    )

    with pytest.raises(
        ValueError, match=r"^Launch executor role mismatch:"
    ) as raised:
        compile_launch_request(
            _launch_request(),
            repository_root=repository_root,
            tasks_root=tasks_root,
            results_root=results_root,
            state_root=state_root,
            runtime_resolver=FakeLaunchRuntimeResolver(_runtime_identity()),
        )

    assert "provider/other-model" in str(raised.value)
    assert "provider/model" in str(raised.value)
    assert not results_root.exists()
    assert not state_root.exists()


def test_launch_planning_rejects_incomplete_model_role_declaration(
    tmp_path: Path,
) -> None:
    """Provider, model, and thinking are mandatory for fixed role models."""
    repository_root, tasks_root, results_root, state_root = (
        _write_launch_fixture(tmp_path)
    )
    config_identity = "review-assistant@1.0.0"
    lock_path = (
        repository_root
        / "configs"
        / config_identity
        / "model"
        / "low"
        / "config-lock.json"
    )
    previous_lock = json.loads(lock_path.read_text())
    role = dict(previous_lock["declaredRoles"][0])
    selection = dict(role["modelSelection"])
    selection.pop("provider")
    role["modelSelection"] = selection
    lock_path.unlink()
    config_lock.write_config_lock(
        repository_root,
        config_identity,
        "provider/model",
        "low",
        "rerun",
        {
            "credentialRoutes": previous_lock["credentialRoutes"],
            "declaredRoles": [role],
            "testedSubjectVersions": previous_lock["testedSubjectVersions"],
            "usageSources": previous_lock["usageSources"],
        },
    )

    with pytest.raises(
        ValueError, match=r"^Launch model role invalid:"
    ) as raised:
        compile_launch_request(
            _launch_request(),
            repository_root=repository_root,
            tasks_root=tasks_root,
            results_root=results_root,
            state_root=state_root,
            runtime_resolver=FakeLaunchRuntimeResolver(_runtime_identity()),
        )

    assert "provider" in str(raised.value)
    assert "executor" in str(raised.value)
    assert not results_root.exists()
    assert not state_root.exists()


def test_launch_planning_rejects_role_without_compact_usage_source(
    tmp_path: Path,
) -> None:
    """Every role needs a compact source for smoke and result accounting."""
    repository_root, tasks_root, results_root, state_root = (
        _write_launch_fixture(tmp_path)
    )
    config_identity = "review-assistant@1.0.0"
    lock_path = (
        repository_root
        / "configs"
        / config_identity
        / "model"
        / "low"
        / "config-lock.json"
    )
    previous_lock = json.loads(lock_path.read_text())
    role = dict(previous_lock["declaredRoles"][0])
    role.pop("usageSource")
    lock_path.unlink()
    config_lock.write_config_lock(
        repository_root,
        config_identity,
        "provider/model",
        "low",
        "rerun",
        {
            "credentialRoutes": previous_lock["credentialRoutes"],
            "declaredRoles": [role],
            "testedSubjectVersions": previous_lock["testedSubjectVersions"],
            "usageSources": previous_lock["usageSources"],
        },
    )

    with pytest.raises(
        TypeError, match=r"^Launch model role invalid:"
    ) as raised:
        compile_launch_request(
            _launch_request(),
            repository_root=repository_root,
            tasks_root=tasks_root,
            results_root=results_root,
            state_root=state_root,
            runtime_resolver=FakeLaunchRuntimeResolver(_runtime_identity()),
        )

    assert "compact usage source" in str(raised.value)
    assert "executor" in str(raised.value)
    assert not results_root.exists()
    assert not state_root.exists()


def test_launch_planning_requires_clarification_for_undeclared_model_roles(
    tmp_path: Path,
) -> None:
    """A versioned config cannot hide all model-call surfaces."""
    repository_root, tasks_root, results_root, state_root = (
        _write_launch_fixture(tmp_path)
    )
    config_identity = "review-assistant@1.0.0"
    lock_path = (
        repository_root
        / "configs"
        / config_identity
        / "model"
        / "low"
        / "config-lock.json"
    )
    lock_path.unlink()
    config_lock.write_config_lock(
        repository_root,
        config_identity,
        "provider/model",
        "low",
        "rerun",
        {"testedSubjectVersions": ["pi@0.81.1"]},
    )

    with pytest.raises(launch.LaunchClarificationRequired) as raised:
        compile_launch_request(
            _launch_request(),
            repository_root=repository_root,
            tasks_root=tasks_root,
            results_root=results_root,
            state_root=state_root,
            runtime_resolver=FakeLaunchRuntimeResolver(_runtime_identity()),
        )

    assert raised.value.details == (
        {
            "config": config_identity,
            "reason": "undeclared-model-roles",
        },
    )
    assert not results_root.exists()
    assert not state_root.exists()


def test_launch_planning_requires_clarification_for_unbounded_role_calls(
    tmp_path: Path,
) -> None:
    """Every secondary call surface must declare finite per-rep bounds."""
    repository_root, tasks_root, results_root, state_root = (
        _write_launch_fixture(tmp_path)
    )
    config_identity = "review-assistant@1.0.0"
    lock_path = (
        repository_root
        / "configs"
        / config_identity
        / "model"
        / "low"
        / "config-lock.json"
    )
    previous_lock = json.loads(lock_path.read_text())
    role = dict(previous_lock["declaredRoles"][0])
    role["callBehavior"] = {"kind": "unbounded"}
    lock_path.unlink()
    config_lock.write_config_lock(
        repository_root,
        config_identity,
        "provider/model",
        "low",
        "rerun",
        {
            "credentialRoutes": previous_lock["credentialRoutes"],
            "declaredRoles": [role],
            "testedSubjectVersions": previous_lock["testedSubjectVersions"],
            "usageSources": previous_lock["usageSources"],
        },
    )

    with pytest.raises(launch.LaunchClarificationRequired) as raised:
        compile_launch_request(
            _launch_request(),
            repository_root=repository_root,
            tasks_root=tasks_root,
            results_root=results_root,
            state_root=state_root,
            runtime_resolver=FakeLaunchRuntimeResolver(_runtime_identity()),
        )

    assert raised.value.details == (
        {
            "callKind": "unbounded",
            "config": config_identity,
            "reason": "unbounded-call-behavior",
            "role": "executor",
        },
    )
    assert not results_root.exists()
    assert not state_root.exists()


def test_launch_planning_requires_clarification_for_unbounded_model_selection(
    tmp_path: Path,
) -> None:
    """An arbitrary model surface fails with structured planning evidence."""
    repository_root, tasks_root, results_root, state_root = (
        _write_launch_fixture(tmp_path)
    )
    config_identity = "review-assistant@1.0.0"
    lock_path = (
        repository_root
        / "configs"
        / config_identity
        / "model"
        / "low"
        / "config-lock.json"
    )
    lock_path.unlink()
    config_lock.write_config_lock(
        repository_root,
        config_identity,
        "provider/model",
        "low",
        "rerun",
        {
            "credentialRoutes": ["WORKFLOW_API_KEY"],
            "declaredRoles": [
                {
                    "billingCategory": "paid API",
                    "callBehavior": {
                        "kind": "bounded",
                        "maxCallsPerRep": 8,
                        "maxConcurrency": 8,
                    },
                    "credentialRoute": "WORKFLOW_API_KEY",
                    "modelSelection": {"kind": "arbitrary"},
                    "name": "workflow-worker",
                    "roleKind": "workflow",
                    "usageSource": {
                        "format": "compact-jsonl",
                        "path": "workflow-usage/usage.ndjson",
                    },
                }
            ],
            "testedSubjectVersions": ["pi@0.81.1"],
            "usageSources": ["workflow-usage/usage.ndjson"],
        },
    )

    with pytest.raises(launch.LaunchClarificationRequired) as raised:
        compile_launch_request(
            _launch_request(),
            repository_root=repository_root,
            tasks_root=tasks_root,
            results_root=results_root,
            state_root=state_root,
            runtime_resolver=FakeLaunchRuntimeResolver(_runtime_identity()),
        )

    assert raised.value.details == (
        {
            "config": config_identity,
            "reason": "unbounded-model-selection",
            "role": "workflow-worker",
            "selectionKind": "arbitrary",
        },
    )
    assert str(raised.value).startswith("Launch clarification required:")
    assert not results_root.exists()
    assert not state_root.exists()


def test_launch_planning_requires_clarification_for_unknown_extension_behavior(
    tmp_path: Path,
) -> None:
    """Undeclared extension behavior stops before subject execution."""
    repository_root, tasks_root, results_root, state_root = (
        _write_launch_fixture(tmp_path)
    )
    config_identity = "review-assistant@1.0.0"
    config_root = repository_root / "configs" / config_identity
    extension_path = config_root / "extensions" / "unknown.ts"
    extension_path.parent.mkdir()
    extension_path.write_text("export default {}\n")
    lock_path = config_root / "model" / "low" / "config-lock.json"
    lock_path.unlink()
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

    with pytest.raises(launch.LaunchClarificationRequired) as raised:
        compile_launch_request(
            _launch_request(),
            repository_root=repository_root,
            tasks_root=tasks_root,
            results_root=results_root,
            state_root=state_root,
            runtime_resolver=FakeLaunchRuntimeResolver(_runtime_identity()),
        )

    assert raised.value.details == (
        {
            "config": config_identity,
            "path": "extensions/unknown.ts",
            "reason": "unknown-extension-behavior",
        },
    )
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
    assert (
        "executor | executor | fixed | provider | provider/model | low"
        in receipt
    )
    assert "FIXTURE_CREDENTIAL | subscription quota" in receipt
    assert "BEHAVIOR DIFFERENCES FROM baseline@1.0.0" in receipt
    assert "review-assistant@1.0.0" in receipt
    assert "changed prompt: orchestration.md" in receipt
    assert f"Results root: {results_root.resolve()}" in receipt
    planned_state_path = compiled.plan.to_document()["paths"]["statePath"]
    assert f"Structured state: {planned_state_path}\n" in receipt


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
    monkeypatch.setenv("FIXTURE_CREDENTIAL", "available-to-fixture")

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
        previous_lock = json.loads(lock_path.read_text())
        role = dict(previous_lock["declaredRoles"][0])
        role["credentialRoute"] = "OPENAI_API_KEY"
        lock_path.unlink()
        (config_root / "env").write_text(f"OPENAI_API_KEY={secret}\n")
        config_lock.write_config_lock(
            repository_root,
            config_identity,
            "provider/model",
            "low",
            "rerun",
            {
                "credentialRoutes": ["OPENAI_API_KEY"],
                "declaredRoles": [role],
                "testedSubjectVersions": previous_lock["testedSubjectVersions"],
                "usageSources": previous_lock["usageSources"],
            },
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
