"""Compile model-free launch requests into immutable plans and receipts."""

from __future__ import annotations

import hashlib
import json
import math
from collections.abc import Mapping, Sequence
from dataclasses import asdict
from pathlib import Path
from typing import cast

from harness import (
    config_lock,
    config_resolution,
    lib,
    pi_config,
    result_provenance,
    versioned_smoke_contract,
)
from harness.launch_contract import (
    CompiledLaunch,
    ExplicitResultReuseDecision,
    LaunchClarificationError,
    LaunchConfigDocument,
    LaunchPlan,
    LaunchPlanDocument,
    LaunchRequest,
    LaunchRuntimeIdentity,
    LaunchRuntimeResolver,
    LaunchSubjectDocument,
)
from harness.launch_runtime import RepositoryLaunchRuntimeResolver
from harness.run_state import sanitize_run_id

_LAUNCH_PLAN_SCHEMA_VERSION = 1
_PI_THINKING_LEVELS = frozenset(
    {"off", "minimal", "low", "medium", "high", "xhigh", "max"}
)
_OMP_THINKING_LEVELS = frozenset(
    {"off", "minimal", "low", "medium", "high", "xhigh"}
)
_THINKING_LEVELS = _PI_THINKING_LEVELS | _OMP_THINKING_LEVELS
_TASK_SELECTION_KINDS = frozenset({"tasks", "subset", "range", "all"})
_PREFLIGHT_POLICIES = frozenset({"disabled", "new-configs", "required"})
_EXISTING_RESULT_POLICIES = frozenset({"require-compatible", "rerun"})
_TRANSIENT_ERROR_POLICIES = frozenset({"pause", "stop"})
_BILLING_CATEGORIES = frozenset({"local compute", "paid API", "subscription quota"})
_COMPACT_USAGE_FORMATS = frozenset(
    {
        "compact-jsonl",
        "compact-worker-trace",
        "filtered-tool-events",
        "native-session",
    }
)
_OMP_BASIC_TOOLS = ("read", "bash", "edit", "write", "grep", "glob")
_OMP_KNOWN_TOOLS = frozenset(
    {
        "ask",
        "ast_edit",
        "ast_grep",
        "bash",
        "browser",
        "edit",
        "glob",
        "grep",
        "inspect_image",
        "lsp",
        "notebook",
        "python",
        "read",
        "task",
        "todo",
        "web_search",
        "write",
    }
)


def canonical_launch_plan_json(document: Mapping[str, object]) -> str:
    """Serialize a launch plan deterministically for storage and identity."""
    return (
        json.dumps(
            document,
            allow_nan=False,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        )
        + "\n"
    )


def _launch_plan_identity(document: Mapping[str, object]) -> str:
    identity_input = dict(document)
    identity_input.pop("planIdentity", None)
    identity_input.pop("runId", None)
    paths = identity_input.get("paths")
    if isinstance(paths, dict):
        identity_paths = dict(paths)
        identity_paths.pop("statePath", None)
        identity_input["paths"] = identity_paths
    content = canonical_launch_plan_json(identity_input).encode()
    return f"sha256:{hashlib.sha256(content).hexdigest()}"


def confirmed_launch_run_key(run_id: str, plan_identity: str) -> str:
    """Return a workspace-safe structured-state key for one confirmed run.

    Args:
        run_id: Operator-supplied run identifier retained in the manifest.
        plan_identity: Content identity that distinguishes originating plans.

    Returns:
        A safe directory key under the configured central state root.

    """
    key_input = f"{run_id}\0{plan_identity}".encode()
    registration_identity = hashlib.sha256(key_input).hexdigest()
    return sanitize_run_id(f"{run_id[:48]}--{registration_identity}")


def parse_launch_plan_json(serialized: str) -> LaunchPlan:
    """Parse a plan and reject changed identity-bearing data."""
    document = json.loads(serialized)
    if not isinstance(document, dict):
        raise TypeError("Launch plan invalid: expected a JSON object")
    if document.get("schemaVersion") != _LAUNCH_PLAN_SCHEMA_VERSION:
        raise ValueError(
            "Launch plan schema unsupported: expected "
            f"{_LAUNCH_PLAN_SCHEMA_VERSION}, got "
            f"{document.get('schemaVersion')!r}"
        )
    stored_identity = document.get("planIdentity")
    if not isinstance(stored_identity, str):
        raise TypeError("Launch plan invalid: planIdentity must be a string")
    expected_identity = _launch_plan_identity(document)
    if stored_identity != expected_identity:
        raise ValueError(
            "Launch plan identity mismatch: "
            f"stored={stored_identity!r}, expected={expected_identity!r}"
        )
    return LaunchPlan(
        identity=stored_identity,
        canonical_json=canonical_launch_plan_json(document),
    )


def _require_supported_value(
    value: object,
    supported_values: frozenset[str],
    error_message: str,
) -> None:
    """Require one value from a named, finite launch vocabulary."""
    if value not in supported_values:
        raise ValueError(error_message)


def _validate_launch_subject(request: LaunchRequest) -> None:
    _require_supported_value(
        request.subject,
        frozenset({"pi", "omp"}),
        f"Launch subject invalid: expected 'pi' or 'omp'; got {request.subject!r}",
    )
    if not request.model.strip():
        raise ValueError("Launch model invalid: model cannot be empty")
    subject_thinking_levels = (
        _PI_THINKING_LEVELS if request.subject == "pi" else _OMP_THINKING_LEVELS
    )
    expected_thinking_levels = ", ".join(sorted(subject_thinking_levels))
    _require_supported_value(
        request.thinking,
        subject_thinking_levels,
        "Launch thinking invalid for "
        f"{request.subject}: expected {expected_thinking_levels}; "
        f"got {request.thinking!r}",
    )


def _validate_launch_configs(request: LaunchRequest) -> None:
    if not request.configs:
        raise ValueError("Launch configs invalid: select at least one config")
    if len(set(request.configs)) != len(request.configs):
        raise ValueError(
            "Launch configs invalid: duplicate config identities are not allowed"
        )
    if request.baseline_config not in request.configs:
        raise ValueError(
            "Launch baseline invalid: selected baseline must be a config; "
            f"got {request.baseline_config!r}"
        )


def _validate_launch_policies(request: LaunchRequest) -> None:
    _require_supported_value(
        request.policies.preflight,
        _PREFLIGHT_POLICIES,
        "Launch preflight policy invalid: expected disabled, "
        f"new-configs, or required; got {request.policies.preflight!r}",
    )
    _require_supported_value(
        request.policies.existing_results,
        _EXISTING_RESULT_POLICIES,
        "Launch existing-result policy invalid: expected "
        "require-compatible or rerun; "
        f"got {request.policies.existing_results!r}",
    )
    _require_supported_value(
        request.policies.transient_errors,
        _TRANSIENT_ERROR_POLICIES,
        "Launch transient-error policy invalid: expected pause or stop; "
        f"got {request.policies.transient_errors!r}",
    )
    if (
        isinstance(request.policies.cell_retries, bool)
        or not isinstance(request.policies.cell_retries, int)
        or request.policies.cell_retries < 0
    ):
        raise ValueError(
            "Launch cell-retry policy invalid: expected zero or more; "
            f"got {request.policies.cell_retries}"
        )
    agent_timeout_s = request.policies.agent_timeout_s
    if agent_timeout_s is not None and (
        isinstance(agent_timeout_s, bool)
        or not isinstance(agent_timeout_s, int | float)
        or not math.isfinite(agent_timeout_s)
        or agent_timeout_s <= 0
    ):
        raise ValueError(
            "Launch agent-timeout policy invalid: expected a finite positive "
            f"number or null; got {agent_timeout_s!r}"
        )
    rpc_quiescence_s = request.policies.rpc_quiescence_s
    if (
        isinstance(rpc_quiescence_s, bool)
        or not isinstance(rpc_quiescence_s, int | float)
        or not math.isfinite(rpc_quiescence_s)
        or rpc_quiescence_s < 0
    ):
        raise ValueError(
            "Launch RPC-quiescence policy invalid: expected a finite "
            f"non-negative number; got {rpc_quiescence_s!r}"
        )
    if not isinstance(request.policies.capture_initial_context, bool):
        raise TypeError(
            "Launch initial-context policy invalid: expected true or false; "
            f"got {request.policies.capture_initial_context!r}"
        )
    if not isinstance(request.policies.auto_resume, bool):
        raise TypeError(
            "Launch auto-resume policy invalid: expected true or false; "
            f"got {request.policies.auto_resume!r}"
        )
    quota_policies = {
        "max quota wait": request.policies.max_quota_wait_s,
        "quota poll": request.policies.quota_poll_s,
        "rate-limit backoff": request.policies.rate_limit_backoff_s,
    }
    for policy_name, policy_value in quota_policies.items():
        if (
            isinstance(policy_value, bool)
            or not isinstance(policy_value, int | float)
            or not math.isfinite(policy_value)
            or policy_value <= 0
        ):
            raise ValueError(
                "Launch quota policy invalid: expected finite positive "
                f"seconds for {policy_name}; got {policy_value!r}"
            )


def _validate_launch_request(request: LaunchRequest) -> tuple[str, ...]:
    try:
        sanitize_run_id(request.run_id)
    except ValueError as error:
        raise ValueError(f"Launch run id invalid: {error}") from error
    _validate_launch_subject(request)
    _validate_launch_configs(request)
    if request.reps < 1:
        raise ValueError(
            f"Launch reps invalid: expected at least 1; got {request.reps}"
        )
    if request.concurrency < 1:
        raise ValueError(
            "Launch concurrency invalid: expected at least 1; "
            f"got {request.concurrency}"
        )
    _validate_launch_policies(request)
    _require_supported_value(
        request.task_selection.kind,
        _TASK_SELECTION_KINDS,
        "Launch task selection invalid: expected tasks, subset, range, "
        f"or all; got {request.task_selection.kind!r}",
    )
    tasks = request.task_selection.tasks
    if not tasks:
        raise ValueError("Launch task selection invalid: select at least one task")
    if len(set(tasks)) != len(tasks):
        raise ValueError(
            "Launch task selection invalid: duplicate tasks are not allowed"
        )
    return tasks


def _validate_selected_tasks(tasks_root: Path, tasks: Sequence[str]) -> None:
    missing = [
        task for task in tasks if not (tasks_root / task / "task.toml").is_file()
    ]
    if missing:
        raise ValueError(
            "Launch task selection invalid: task.toml missing for "
            f"tasks={missing!r}; tasks_root={str(tasks_root)!r}"
        )


def _subject_runner_path(repository_root: Path, subject: str) -> Path:
    if subject == "pi":
        runner = repository_root / "harness" / "run.py"
    elif subject == "omp":
        runner = repository_root / "harness" / "run_omp.py"
    else:
        raise ValueError(f"Launch subject invalid: unsupported subject {subject!r}")
    if not runner.is_file():
        raise ValueError(f"Launch subject runner missing: {runner}")
    return runner


def _require_runtime_identity(
    runtime: LaunchRuntimeIdentity,
    tasks: tuple[str, ...],
) -> None:
    scalar_identities = {
        "subject version": runtime.subject_version,
        "harness revision": runtime.harness_revision,
        "task revision": runtime.task_revision,
    }
    unresolved = [name for name, value in scalar_identities.items() if not value]
    for task in tasks:
        image_identities = runtime.immutable_image_identities.get(task)
        task_requirements = (
            (
                not runtime.verifier_identities.get(task),
                f"verifier identity for {task}",
            ),
            (
                not image_identities,
                f"immutable image identities for {task}",
            ),
            (
                bool(image_identities)
                and any(not identity for identity in image_identities.values()),
                f"immutable image identity for {task}",
            ),
        )
        unresolved.extend(
            requirement for missing, requirement in task_requirements if missing
        )
    if unresolved:
        raise ValueError(
            "Launch runtime identity unresolved: " + ", ".join(sorted(unresolved))
        )


def _lock_typed_list(
    lock_document: Mapping[str, object],
    field: str,
    item_type: type,
    item_description: str,
) -> list[object]:
    value = lock_document.get(field, [])
    error_message = f"Config lock invalid: {field} must be a list of {item_description}"
    if not isinstance(value, list):
        raise TypeError(error_message)
    if any(not isinstance(item, item_type) for item in value):
        raise TypeError(error_message)
    return cast(list[object], value)


def _lock_string_list(
    lock_document: Mapping[str, object],
    field: str,
) -> list[str]:
    return cast(
        list[str],
        _lock_typed_list(lock_document, field, str, "strings"),
    )


def _lock_object_list(
    lock_document: Mapping[str, object],
    field: str,
) -> list[dict[str, object]]:
    objects = cast(
        list[dict[object, object]],
        _lock_typed_list(lock_document, field, dict, "objects"),
    )
    return [{str(key): child for key, child in item.items()} for item in objects]


def _declared_role_model(
    config_identity: str,
    role_name: str,
    value: object,
) -> dict[str, str]:
    if not isinstance(value, dict):
        raise TypeError(
            "Launch model role invalid: "
            f"config={config_identity!r}; role={role_name!r}; "
            "model declaration must be an object"
        )
    model = value.get("model")
    provider = value.get("provider")
    thinking = value.get("thinking")
    missing = [
        field
        for field, field_value in (
            ("provider", provider),
            ("model", model),
            ("thinking", thinking),
        )
        if not isinstance(field_value, str) or not field_value
    ]
    if missing:
        raise ValueError(
            "Launch model role invalid: "
            f"config={config_identity!r}; role={role_name!r}; "
            f"missing model fields={missing!r}"
        )
    _require_supported_value(
        thinking,
        _THINKING_LEVELS,
        "Launch model role invalid: "
        f"config={config_identity!r}; role={role_name!r}; "
        f"thinking={thinking!r}",
    )
    return {
        "model": str(model),
        "provider": str(provider),
        "thinking": str(thinking),
    }


def _resolved_role_models(
    config_identity: str,
    role_name: str,
    roles_by_name: Mapping[str, Mapping[str, object]],
    resolved_by_name: dict[str, list[dict[str, str]]],
    resolving: frozenset[str] = frozenset(),
) -> list[dict[str, str]]:
    if role_name in resolved_by_name:
        return resolved_by_name[role_name]
    if role_name in resolving:
        raise ValueError(
            f"Launch model role invalid: inherited role cycle at {role_name!r}"
        )
    role = roles_by_name[role_name]
    selection = role.get("modelSelection")
    if not isinstance(selection, dict):
        raise TypeError(
            "Launch model role invalid: "
            f"config={config_identity!r}; role={role_name!r}; "
            "modelSelection must be an object"
        )
    if selection.get("kind") == "fixed":
        models = [_declared_role_model(config_identity, role_name, selection)]
    elif selection.get("kind") == "inherited":
        inherited_role = selection.get("role")
        if not isinstance(inherited_role, str) or inherited_role not in roles_by_name:
            raise ValueError(
                "Launch model role invalid: inherited role "
                f"{role_name!r} references {inherited_role!r}"
            )
        models = _resolved_role_models(
            config_identity,
            inherited_role,
            roles_by_name,
            resolved_by_name,
            resolving | {role_name},
        )
    elif selection.get("kind") == "bounded-dynamic":
        choices = selection.get("models")
        if not isinstance(choices, list):
            raise TypeError(
                "Launch model role invalid: bounded-dynamic models must be a list"
            )
        if not choices:
            raise ValueError(
                "Launch model role invalid: "
                f"config={config_identity!r}; role={role_name!r}; "
                "bounded-dynamic models cannot be empty"
            )
        models = [
            _declared_role_model(config_identity, role_name, choice)
            for choice in choices
        ]
    else:
        raise ValueError(
            "Launch model role invalid: modelSelection kind must be fixed, "
            "inherited, or bounded-dynamic"
        )
    resolved_by_name[role_name] = [dict(model) for model in models]
    return models


def _declared_roles_by_name(
    config_identity: str,
    declared_roles: Sequence[Mapping[str, object]],
) -> dict[str, Mapping[str, object]]:
    if not declared_roles:
        raise LaunchClarificationError(
            [{"config": config_identity, "reason": "undeclared-model-roles"}]
        )
    roles_by_name: dict[str, Mapping[str, object]] = {}
    for role in declared_roles:
        role_name = role.get("name")
        required_strings = {
            "billingCategory": role.get("billingCategory"),
            "credentialRoute": role.get("credentialRoute"),
            "name": role_name,
            "roleKind": role.get("roleKind"),
        }
        missing = sorted(
            field
            for field, value in required_strings.items()
            if not isinstance(value, str) or not value
        )
        if missing:
            raise ValueError(
                "Launch model role invalid: "
                f"config={config_identity!r}; missing fields={missing!r}"
            )
        role_name = str(role_name)
        _require_supported_value(
            role.get("billingCategory"),
            _BILLING_CATEGORIES,
            "Launch model role invalid: "
            f"config={config_identity!r}; role={role_name!r}; "
            f"billing category={role.get('billingCategory')!r}",
        )
        if role_name in roles_by_name:
            raise ValueError(
                "Launch model role invalid: "
                f"config={config_identity!r}; duplicate role={role_name!r}"
            )
        roles_by_name[role_name] = role
    return roles_by_name


def _validate_role_call_behavior(
    config_identity: str,
    role_name: str,
    call_behavior: object,
) -> None:
    call_kind = call_behavior.get("kind") if isinstance(call_behavior, dict) else None
    if call_kind not in {"fixed", "bounded"}:
        raise LaunchClarificationError(
            [
                {
                    "callKind": call_kind,
                    "config": config_identity,
                    "reason": "unbounded-call-behavior",
                    "role": role_name,
                }
            ]
        )
    call_document = cast(dict[str, object], call_behavior)
    calls_field = "callsPerRep" if call_kind == "fixed" else "maxCallsPerRep"
    calls = call_document.get(calls_field)
    max_concurrency = call_document.get("maxConcurrency")
    if (
        not isinstance(calls, int)
        or isinstance(calls, bool)
        or calls < 1
        or not isinstance(max_concurrency, int)
        or isinstance(max_concurrency, bool)
        or max_concurrency < 1
    ):
        raise ValueError(
            "Launch model role invalid: "
            f"config={config_identity!r}; role={role_name!r}; "
            "call bounds must be positive integers"
        )


def _validated_role_selection_kind(
    config_identity: str,
    role_name: str,
    selection: object,
) -> str:
    selection_kind = selection.get("kind") if isinstance(selection, dict) else None
    if selection_kind not in {"fixed", "inherited", "bounded-dynamic"}:
        raise LaunchClarificationError(
            [
                {
                    "config": config_identity,
                    "reason": "unbounded-model-selection",
                    "role": role_name,
                    "selectionKind": selection_kind,
                }
            ]
        )
    return str(selection_kind)


def _role_selection_summary(
    selection_kind: str,
    selection: object,
    model_count: int,
) -> str:
    if selection_kind == "inherited":
        selection_document = cast(dict[str, object], selection)
        return f"inherited from {selection_document.get('role')}"
    if selection_kind == "bounded-dynamic":
        return f"bounded dynamic ({model_count} models)"
    return "fixed"


def _resolve_declared_roles(
    config_identity: str,
    declared_roles: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    roles_by_name = _declared_roles_by_name(config_identity, declared_roles)
    resolved_by_name: dict[str, list[dict[str, str]]] = {}
    resolved_roles: list[dict[str, object]] = []
    for role in declared_roles:
        role_name = str(role["name"])
        _validate_role_call_behavior(
            config_identity,
            role_name,
            role.get("callBehavior"),
        )
        selection = role.get("modelSelection")
        selection_kind = _validated_role_selection_kind(
            config_identity,
            role_name,
            selection,
        )
        resolved_role = dict(role)
        models = _resolved_role_models(
            config_identity,
            role_name,
            roles_by_name,
            resolved_by_name,
        )
        resolved_role["models"] = models
        resolved_role["selectionSummary"] = _role_selection_summary(
            selection_kind,
            selection,
            len(models),
        )
        resolved_roles.append(resolved_role)
    return resolved_roles


def _validate_executor_role(
    config_identity: str,
    roles: Sequence[Mapping[str, object]],
    request: LaunchRequest,
) -> None:
    executors = [role for role in roles if role.get("roleKind") == "executor"]
    models = executors[0].get("models") if len(executors) == 1 else None
    if (
        not isinstance(models, list)
        or len(models) != 1
        or not isinstance(models[0], dict)
        or models[0].get("model") != request.model
        or models[0].get("thinking") != request.thinking
    ):
        raise ValueError(
            "Launch executor role mismatch: "
            f"config={config_identity!r}; requested model={request.model!r}, "
            f"thinking={request.thinking!r}; declared={models!r}"
        )


def _validate_launch_surfaces(
    config_identity: str,
    launch_surfaces: Sequence[Mapping[str, object]],
    roles: Sequence[Mapping[str, object]],
) -> None:
    role_names = {str(role.get("name")) for role in roles}
    for surface in launch_surfaces:
        path = surface.get("path")
        model_roles = surface.get("modelRoles")
        if (
            not isinstance(path, str)
            or not path
            or Path(path).is_absolute()
            or ".." in Path(path).parts
            or not isinstance(model_roles, list)
            or any(not isinstance(role, str) for role in model_roles)
        ):
            raise ValueError(
                "Launch surface invalid: "
                f"config={config_identity!r}; surface={surface!r}"
            )
        declared_surface_roles = {role for role in model_roles if isinstance(role, str)}
        unknown_roles = sorted(declared_surface_roles - role_names)
        if unknown_roles:
            raise ValueError(
                "Launch surface invalid: "
                f"config={config_identity!r}; path={path!r}; "
                f"unknown roles={unknown_roles!r}"
            )


def _validate_role_usage_sources(
    config_identity: str,
    roles: Sequence[Mapping[str, object]],
    usage_sources: Sequence[str],
) -> None:
    for role in roles:
        role_name = str(role.get("name", ""))
        usage_source = role.get("usageSource")
        if not isinstance(usage_source, dict):
            raise TypeError(
                "Launch model role invalid: "
                f"config={config_identity!r}; role={role_name!r}; "
                "compact usage source is required"
            )
        source_path = usage_source.get("path")
        source_format = usage_source.get("format")
        if (
            not isinstance(source_path, str)
            or not source_path
            or source_path not in usage_sources
            or source_path.endswith("pi.jsonl")
            or source_format not in _COMPACT_USAGE_FORMATS
        ):
            raise ValueError(
                "Launch model role invalid: "
                f"config={config_identity!r}; role={role_name!r}; "
                "compact usage source must name a declared path and supported "
                f"format; got path={source_path!r}, format={source_format!r}"
            )


def _smoke_usage_assertion_matches(
    assertion: Mapping[str, object],
    source_path: str,
    record_selector: Mapping[str, object],
) -> bool:
    globs = assertion.get("globs")
    expected = assertion.get("equals")
    return (
        isinstance(globs, list)
        and source_path in globs
        and isinstance(expected, Mapping)
        and all(
            expected.get(field) == value for field, value in record_selector.items()
        )
    )


def _has_positive_result_minimum(
    result_minima: Mapping[str, object],
    field: str,
) -> bool:
    minimum = result_minima.get(field)
    return (
        isinstance(minimum, int | float)
        and not isinstance(minimum, bool)
        and minimum > 0
    )


def _validate_secondary_role_usage_evidence(
    config_identity: str,
    roles: Sequence[Mapping[str, object]],
    smoke_contract: Mapping[str, object] | None,
) -> None:
    """Require enforceable trace and result accounting for secondary roles."""
    assertions = (
        smoke_contract.get("requireUsageRecords", [])
        if smoke_contract is not None
        else []
    )
    result_minima_value = (
        smoke_contract.get("minResultValues", {}) if smoke_contract is not None else {}
    )
    usage_assertions = (
        [
            cast(Mapping[str, object], assertion)
            for assertion in assertions
            if isinstance(assertion, Mapping)
        ]
        if isinstance(assertions, list)
        else []
    )
    result_minima = (
        cast(Mapping[str, object], result_minima_value)
        if isinstance(result_minima_value, Mapping)
        else {}
    )
    for role in roles:
        if role.get("roleKind") == "executor":
            continue
        role_name = str(role.get("name", ""))
        usage_source = role.get("usageSource")
        if not isinstance(usage_source, Mapping):
            raise TypeError(
                "Launch model role usage evidence missing: "
                f"config={config_identity!r}; role={role_name!r}; "
                "usageSource must be an object"
            )
        source_path = usage_source.get("path")
        record_selector = usage_source.get("recordSelector")
        result_accounting = usage_source.get("resultAccounting")
        accounting_fields = (
            [
                field
                for field in result_accounting.values()
                if isinstance(field, str) and field
            ]
            if isinstance(result_accounting, Mapping)
            else []
        )
        if (
            not isinstance(source_path, str)
            or not isinstance(record_selector, Mapping)
            or not record_selector
            or not isinstance(result_accounting, Mapping)
            or set(result_accounting) != {"calls", "totalTokens"}
            or len(accounting_fields) != 2
            or len(set(accounting_fields)) != 2
        ):
            raise ValueError(
                "Launch model role usage evidence missing: "
                f"config={config_identity!r}; role={role_name!r}; "
                "secondary usageSource requires recordSelector and "
                "resultAccounting calls/totalTokens fields"
            )
        structured_selector = cast(Mapping[str, object], record_selector)
        matching_assertion = any(
            _smoke_usage_assertion_matches(
                assertion,
                source_path,
                structured_selector,
            )
            for assertion in usage_assertions
        )
        missing_result_fields = [
            field
            for field in accounting_fields
            if not _has_positive_result_minimum(result_minima, field)
        ]
        if not matching_assertion or missing_result_fields:
            raise ValueError(
                "Launch model role usage evidence missing: "
                f"config={config_identity!r}; role={role_name!r}; "
                f"source={source_path!r}; "
                f"usage_assertion={matching_assertion!r}; "
                f"missing_result_fields={missing_result_fields!r}"
            )


def _active_config_lines(path: Path) -> list[str]:
    if not path.is_file():
        return []
    return [
        line
        for raw_line in path.read_text().splitlines()
        if (line := raw_line.split("#", 1)[0].strip())
    ]


def _resolve_omp_tool_whitelist(config_root: Path) -> list[str]:
    tool_path = config_root / "omp-tools.txt"
    tools = list(_OMP_BASIC_TOOLS)
    if tool_path.is_file():
        tools = [
            tool
            for line in _active_config_lines(tool_path)
            for tool in (item.strip() for item in line.split(","))
            if tool
        ]
    unknown_tools = sorted(set(tools) - _OMP_KNOWN_TOOLS)
    if unknown_tools:
        raise ValueError(
            "OMP launch restriction: unknown tool ids "
            f"in {tool_path}: {unknown_tools!r}"
        )
    if not tools:
        raise ValueError(f"OMP launch restriction: empty tool whitelist in {tool_path}")
    return tools


def _resolve_omp_extension_paths(config_root: Path) -> list[str]:
    extension_list = config_root / "omp-extensions.txt"
    extensions: list[str] = []
    for relative_text in _active_config_lines(extension_list):
        relative_path = Path(relative_text)
        if relative_path.is_absolute() or ".." in relative_path.parts:
            raise ValueError(
                "OMP launch restriction: invalid extension path "
                f"in {extension_list}: {relative_text!r}"
            )
        if not (config_root / relative_path).is_file():
            raise ValueError(
                "OMP launch restriction: extension missing "
                f"for {extension_list}: {relative_text!r}"
            )
        extensions.append(f"/arm/{relative_path.as_posix()}")
    return extensions


def _config_append_system_prompt(config_root: Path) -> str:
    layers: list[str] = []
    for filename in ("system_preamble.md", "orchestration.md"):
        path = config_root / filename
        text = path.read_text().strip("\n") if path.is_file() else ""
        if text.strip():
            layers.append(text)
    return "\n\n".join(layers)


def _resolve_omp_subject_behavior(
    request: LaunchRequest,
    resolved: config_resolution.ResolvedConfigLeaf,
) -> dict[str, object]:
    if not request.model.startswith("openai-codex/"):
        raise ValueError(
            "OMP launch restriction: model must use explicit "
            f"openai-codex route; got {request.model!r}"
        )
    config_root = resolved.config_root
    skill_root = config_root / "skills"
    if skill_root.is_dir() and any(skill_root.iterdir()):
        raise ValueError("OMP launch restriction: configs must not define skills")
    if _active_config_lines(config_root / "pi-flags"):
        raise ValueError("OMP launch restriction: configs must not define Pi flags")
    forbidden_leaf_files = [
        filename
        for filename in ("advisor.json", "models.json", "settings.json")
        if (resolved.config_leaf / filename).is_file()
    ]
    if forbidden_leaf_files:
        raise ValueError(
            "OMP launch restriction: model, advisor, and settings leaf files "
            f"are not supported; found={forbidden_leaf_files!r}"
        )
    system_prompt_path = config_root / "omp-system-prompt.md"
    system_prompt: str | None = None
    if system_prompt_path.is_file():
        system_prompt = system_prompt_path.read_text().replace(
            "{{cwd}}",
            "/app",
        )
    return {
        "appendSystemPrompt": _config_append_system_prompt(config_root),
        "captureInitialContext": True,
        "credentialRoute": "OPENAI_CODEX_OAUTH",
        "extensions": _resolve_omp_extension_paths(config_root),
        "modelRoute": "openai-codex",
        "overlay": (
            "/arm/omp-overlay.yml"
            if (config_root / "omp-overlay.yml").is_file()
            else None
        ),
        "systemPrompt": system_prompt,
        "toolWhitelist": _resolve_omp_tool_whitelist(config_root),
    }


def _base_launch_config_document(
    resolved: config_resolution.ResolvedConfigLeaf,
    config_identity: str,
    subject_behavior: Mapping[str, object] | None,
) -> LaunchConfigDocument:
    document: LaunchConfigDocument = {
        "behaviorInputs": [],
        "configLeaf": str(resolved.config_leaf.resolve()),
        "configRoot": str(resolved.config_root.resolve()),
        "credentialRoutes": [],
        "declaredRoles": [],
        "identity": config_identity,
        "launchSurfaces": [],
        "legacy": True,
        "lockIdentity": None,
        "requiredCapabilities": [],
        "smokeAssertions": None,
        "smokeContract": (
            str(resolved.smoke_contract.resolve())
            if resolved.smoke_contract is not None
            else None
        ),
        "testedSubjectVersions": [],
        "usageSources": [],
        "versionImpact": None,
    }
    if subject_behavior is not None:
        document["subjectBehavior"] = dict(subject_behavior)
    return document


def _validate_extension_surface_coverage(
    config_identity: str,
    behavior_inputs: Sequence[Mapping[str, object]],
    launch_surfaces: Sequence[Mapping[str, object]],
) -> None:
    uncovered: list[dict[str, object]] = []
    for behavior_input in behavior_inputs:
        path = behavior_input.get("path")
        if behavior_input.get("kind") != "extension" or not isinstance(path, str):
            continue
        covered = any(
            isinstance(surface.get("path"), str)
            and (
                path == surface["path"]
                or path.startswith(str(surface["path"]).rstrip("/") + "/")
            )
            for surface in launch_surfaces
        )
        if not covered:
            uncovered.append(
                {
                    "config": config_identity,
                    "path": path,
                    "reason": "unknown-extension-behavior",
                }
            )
    if uncovered:
        raise LaunchClarificationError(uncovered)


def _validate_role_credential_routes(
    config_identity: str,
    roles: Sequence[Mapping[str, object]],
    credential_routes: Sequence[str],
) -> None:
    for role in roles:
        credential_route = role.get("credentialRoute")
        if credential_route not in credential_routes:
            raise ValueError(
                "Launch model role invalid: "
                f"config={config_identity!r}; role={role.get('name')!r}; "
                f"credential route {credential_route!r} is not declared"
            )


def _config_plan(
    repository_root: Path,
    request: LaunchRequest,
    config_identity: str,
) -> LaunchConfigDocument:
    resolved = config_resolution.resolve_config_leaf(
        repository_root,
        config_identity,
        request.model,
        request.thinking,
    )
    subject_behavior = (
        _resolve_omp_subject_behavior(request, resolved)
        if request.subject == "omp"
        else None
    )
    if request.subject == "pi":
        pi_config.validate_pi_config(resolved.config_root)
    versioned_identity = config_resolution.parse_versioned_config_identity(
        config_identity
    )
    smoke_contract_document: Mapping[str, object] | None = None
    if versioned_identity is not None:
        smoke_contract_document = (
            versioned_smoke_contract.validate_versioned_smoke_contract(
                repository_root,
                resolved.smoke_contract,
            )
        )
    document = _base_launch_config_document(
        resolved,
        config_identity,
        subject_behavior,
    )
    lock_document = config_lock.read_matching_config_lock(
        resolved,
        config_identity,
    )
    if lock_document is None:
        return document
    behavior_inputs = config_lock.config_behavior_inputs_from_lock(lock_document)
    launch_surfaces = _lock_object_list(lock_document, "launchSurfaces")
    _validate_extension_surface_coverage(
        config_identity,
        behavior_inputs,
        launch_surfaces,
    )
    credential_routes = _lock_string_list(lock_document, "credentialRoutes")
    if request.subject == "omp" and "OPENAI_CODEX_OAUTH" not in credential_routes:
        raise ValueError(
            "OMP launch restriction: OPENAI_CODEX_OAUTH must be a declared "
            "credential route"
        )
    declared_roles = _lock_object_list(lock_document, "declaredRoles")
    usage_sources = _lock_string_list(lock_document, "usageSources")
    _validate_role_usage_sources(
        config_identity,
        declared_roles,
        usage_sources,
    )
    resolved_roles = _resolve_declared_roles(config_identity, declared_roles)
    _validate_secondary_role_usage_evidence(
        config_identity,
        resolved_roles,
        smoke_contract_document,
    )
    _validate_executor_role(config_identity, resolved_roles, request)
    _validate_launch_surfaces(
        config_identity,
        launch_surfaces,
        resolved_roles,
    )
    _validate_role_credential_routes(
        config_identity,
        resolved_roles,
        credential_routes,
    )
    version_impact = lock_document.get("versionImpact")
    if version_impact is not None and not isinstance(version_impact, str):
        raise TypeError("Config lock invalid: versionImpact must be a string or null")
    lock_identity = lock_document.get("lockIdentity")
    if not isinstance(lock_identity, str):
        raise TypeError("Config lock invalid: lockIdentity must be a string")
    document.update(
        {
            "behaviorInputs": behavior_inputs,
            "credentialRoutes": credential_routes,
            "declaredRoles": resolved_roles,
            "launchSurfaces": launch_surfaces,
            "legacy": False,
            "lockIdentity": lock_identity,
            "requiredCapabilities": _lock_string_list(
                lock_document,
                "requiredCapabilities",
            ),
            "smokeAssertions": (
                dict(smoke_contract_document)
                if smoke_contract_document is not None
                else None
            ),
            "testedSubjectVersions": _lock_string_list(
                lock_document,
                "testedSubjectVersions",
            ),
            "usageSources": usage_sources,
            "versionImpact": version_impact,
        }
    )
    return document


def _validate_config_runtime_compatibility(
    configs: Sequence[LaunchConfigDocument],
    runtime: LaunchRuntimeIdentity,
) -> None:
    for config in configs:
        if config["legacy"]:
            continue
        tested_versions = config["testedSubjectVersions"]
        missing_capabilities = sorted(
            set(config["requiredCapabilities"]) - runtime.subject_capabilities
        )
        unavailable_routes = sorted(
            set(config["credentialRoutes"]) - runtime.available_credential_routes
        )
        incompatibilities = (
            (
                runtime.subject_version not in tested_versions,
                "Untested subject version: "
                + f"config={config['identity']!r}; "
                + f"subject={runtime.subject_version!r}; "
                + f"tested={tested_versions!r}",
            ),
            (
                bool(missing_capabilities),
                "Launch subject capability missing: "
                + f"config={config['identity']!r}; "
                + f"missing={missing_capabilities!r}; "
                + f"available={sorted(runtime.subject_capabilities)!r}",
            ),
            (
                bool(unavailable_routes),
                "Launch credential route unavailable: "
                + f"config={config['identity']!r}; "
                + f"routes={unavailable_routes!r}",
            ),
        )
        for incompatible, error_message in incompatibilities:
            if incompatible:
                raise ValueError(error_message)


def _cell_result_path(
    results_root: Path,
    request: LaunchRequest,
    config: str,
    task: str,
    rep: int,
) -> Path:
    return (
        results_root
        / lib.model_leaf(request.model)
        / request.thinking
        / config
        / task
        / f"rep{rep}"
        / "result.json"
    )


def _matching_explicit_reuse_decision(
    result_path: Path,
    record: Mapping[str, object],
    decisions: Sequence[ExplicitResultReuseDecision],
) -> tuple[ExplicitResultReuseDecision | None, dict[str, object] | None]:
    """Validate explicit reuse against exact bytes and earlier provenance."""
    matching = [
        decision
        for decision in decisions
        if decision.result_path.resolve() == result_path.resolve()
    ]
    if not matching:
        return None, None
    if len(matching) != 1:
        raise ValueError(
            f"Result reuse decision mismatch: path={result_path}; "
            "multiple decisions target the same result"
        )
    decision = matching[0]
    recorded_provenance = result_provenance.recorded_result_provenance(record)
    decision_mismatches: dict[str, object] = {}
    if not decision.rationale.strip():
        decision_mismatches["rationale"] = "must be non-empty"
    evidence_comparisons = {
        "prior_config_identity": (
            decision.prior_config_identity,
            record.get("config"),
        ),
        "recorded_provenance": (
            dict(decision.recorded_provenance),
            recorded_provenance,
        ),
        "result_identity": (
            decision.result_identity,
            result_provenance.result_file_identity(result_path),
        ),
    }
    for field, (accepted, recorded) in evidence_comparisons.items():
        if accepted != recorded:
            decision_mismatches[field] = {
                "accepted": accepted,
                "recorded": recorded,
            }
    if decision_mismatches:
        raise ValueError(
            f"Result reuse decision mismatch: path={result_path}; "
            f"incompatible fields={decision_mismatches!r}"
        )
    return decision, {
        "priorConfigIdentity": decision.prior_config_identity,
        "rationale": decision.rationale,
        "recordedProvenance": recorded_provenance,
        "resultIdentity": decision.result_identity,
        "resultPath": str(result_path.resolve()),
    }


def _planned_result_provenance(
    request: LaunchRequest,
    runtime: LaunchRuntimeIdentity,
    config: LaunchConfigDocument,
    task: str,
    rep: int,
) -> result_provenance.ResultProvenance:
    """Build the exact modern provenance required for automatic reuse."""
    provenance: result_provenance.ResultProvenance = {
        "config": config["identity"],
        "config_lock_identity": config["lockIdentity"],
        "harness_revision": runtime.harness_revision,
        "immutable_image_identities": dict(runtime.immutable_image_identities[task]),
        "model": request.model,
        "rep": rep,
        "subject": request.subject,
        "subject_version": runtime.subject_version,
        "task": task,
        "task_revision": runtime.task_revision,
        "thinking_level": request.thinking,
        "verifier_identity": runtime.verifier_identities[task],
    }
    if runtime.subject_runtime_identity:
        provenance["subject_runtime_identity"] = dict(runtime.subject_runtime_identity)
    return provenance


def _batch_cells(
    results_root: Path,
    request: LaunchRequest,
    tasks: tuple[str, ...],
    configs: Sequence[LaunchConfigDocument],
    runtime: LaunchRuntimeIdentity,
) -> list[dict[str, object]]:
    configs_by_identity = {config["identity"]: config for config in configs}
    matched_decisions: set[Path] = set()
    cells: list[dict[str, object]] = []
    for task in tasks:
        for rep in range(request.reps):
            for config_identity in request.configs:
                result_path = _cell_result_path(
                    results_root,
                    request,
                    config_identity,
                    task,
                    rep,
                )
                reuse_provenance: Mapping[str, object] | None = None
                reuse_reason: str | None = None
                reuse_result_identity: str | None = None
                reuse_decision: dict[str, object] | None = None
                if result_path.is_file():
                    record = result_provenance.read_result_record(result_path)
                    planned_provenance = _planned_result_provenance(
                        request,
                        runtime,
                        configs_by_identity[config_identity],
                        task,
                        rep,
                    )
                    mismatches = result_provenance.result_provenance_mismatches(
                        record,
                        planned_provenance,
                    )
                    decision, reuse_decision = _matching_explicit_reuse_decision(
                        result_path,
                        record,
                        request.reuse_decisions,
                    )
                    if decision is not None:
                        matched_decisions.add(result_path.resolve())
                        reuse_provenance = result_provenance.recorded_result_provenance(
                            record
                        )
                        reuse_reason = "explicit_result_reuse"
                        reuse_result_identity = decision.result_identity
                    elif mismatches:
                        raise ValueError(
                            f"Result provenance mismatch: path={result_path}; "
                            f"incompatible fields={mismatches!r}"
                        )
                    elif request.policies.existing_results == "require-compatible":
                        reuse_provenance = planned_provenance
                        reuse_reason = "compatible_existing_result"
                        reuse_result_identity = result_provenance.result_file_identity(
                            result_path
                        )
                cells.append(
                    {
                        "config": config_identity,
                        "existingResult": result_path.is_file(),
                        "existingResultPolicy": (request.policies.existing_results),
                        "rep": rep,
                        "resultPath": str(result_path.resolve()),
                        "reuseDecision": reuse_decision,
                        "reuseProvenance": reuse_provenance,
                        "reuseReason": reuse_reason,
                        "reuseResultIdentity": reuse_result_identity,
                        "task": task,
                    }
                )
    unmatched_decisions = sorted(
        str(decision.result_path.resolve())
        for decision in request.reuse_decisions
        if decision.result_path.resolve() not in matched_decisions
    )
    if unmatched_decisions:
        raise ValueError(
            "Result reuse decision mismatch: no occupied planned result at "
            f"paths={unmatched_decisions!r}"
        )
    return cells


def _preflight_task(repository_root: Path, tasks: tuple[str, ...]) -> str:
    smoke_subset = repository_root / "subsets" / "12_v0.txt"
    if smoke_subset.is_file():
        requested = set(tasks)
        for task in smoke_subset.read_text().splitlines():
            task = task.strip()
            if task in requested:
                return task
    return tasks[0]


def _preflight_cells(
    repository_root: Path,
    results_root: Path,
    state_root: Path,
    request: LaunchRequest,
    tasks: tuple[str, ...],
    config_plans: Sequence[Mapping[str, object]],
    batch_cells: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    if request.policies.preflight == "disabled":
        return []
    task = _preflight_task(repository_root, tasks)
    cells: list[dict[str, object]] = []
    for config in config_plans:
        config_identity = str(config["identity"])
        config_results = (
            results_root
            / lib.model_leaf(request.model)
            / request.thinking
            / config_identity
        )
        if config["legacy"]:
            has_release_evidence = any(config_results.glob("*/rep*/result.json"))
        else:
            has_release_evidence = config["lockIdentity"] in (
                config_lock.sealed_config_lock_identities(
                    results_root,
                    config_identity,
                    state_root=state_root,
                )
            )
        if request.policies.preflight == "new-configs" and has_release_evidence:
            continue
        result_path = _cell_result_path(
            results_root,
            request,
            config_identity,
            task,
            0,
        ).resolve()
        batch_cell = next(
            cell for cell in batch_cells if cell.get("resultPath") == str(result_path)
        )
        cells.append(
            {
                "config": config_identity,
                "contractPath": config["smokeContract"],
                "rep": 0,
                "resultPath": str(result_path),
                "reuseDecision": batch_cell.get("reuseDecision"),
                "reuseProvenance": batch_cell.get("reuseProvenance"),
                "reuseReason": batch_cell.get("reuseReason"),
                "reuseResultIdentity": batch_cell.get("reuseResultIdentity"),
                "task": task,
            }
        )
    return cells


def _receipt_warnings(document: LaunchPlanDocument) -> list[str]:
    warnings: list[str] = []
    legacy = [config["identity"] for config in document["configs"] if config["legacy"]]
    if legacy:
        warnings.append(
            "legacy configs are readable for diagnosis but require a "
            "versioned release before confirmed execution: " + ", ".join(legacy)
        )
    if document["policies"]["preflight"] == "disabled":
        warnings.append("preflight is disabled")
    return warnings


def _behavior_inputs_by_path(
    config: LaunchConfigDocument,
) -> dict[str, dict[str, object]]:
    return {cast(str, item["path"]): item for item in config["behaviorInputs"]}


def _render_behavior_differences(
    baseline: LaunchConfigDocument,
    config: LaunchConfigDocument,
) -> list[str]:
    baseline_inputs = _behavior_inputs_by_path(baseline)
    config_inputs = _behavior_inputs_by_path(config)
    lines = [f"- {config['identity']}"]
    changes = 0
    for path in sorted(set(config_inputs) - set(baseline_inputs)):
        item = config_inputs[path]
        lines.append(
            f"  added {item.get('kind', 'behavior-file')}: {path} "
            f"({item.get('fingerprint')})"
        )
        changes += 1
    for path in sorted(set(baseline_inputs) - set(config_inputs)):
        item = baseline_inputs[path]
        lines.append(
            f"  removed {item.get('kind', 'behavior-file')}: {path} "
            f"({item.get('fingerprint')})"
        )
        changes += 1
    for path in sorted(set(baseline_inputs) & set(config_inputs)):
        before = baseline_inputs[path]
        after = config_inputs[path]
        if before != after:
            lines.append(
                f"  changed {after.get('kind', 'behavior-file')}: {path} "
                f"({before.get('fingerprint')} -> {after.get('fingerprint')})"
            )
            changes += 1
    if not changes:
        lines.append("  no locked behavior differences")
    return lines


def _role_model_columns(role: Mapping[str, object]) -> tuple[str, str, str]:
    models = role.get("models")
    if not isinstance(models, list) or not models:
        return "-", "-", "-"
    structured_models = cast(list[Mapping[str, object]], models)
    return (
        ",".join(str(model.get("provider", "-")) for model in structured_models),
        ",".join(str(model.get("model", "-")) for model in structured_models),
        ",".join(str(model.get("thinking", "-")) for model in structured_models),
    )


def _role_call_summary(role: Mapping[str, object]) -> str:
    behavior = cast(Mapping[str, object], role["callBehavior"])
    max_concurrency = behavior.get("maxConcurrency", "-")
    if behavior.get("kind") == "fixed":
        calls_per_rep = behavior.get("callsPerRep", "-")
        if role.get("roleKind") == "executor":
            session_label = "session" if calls_per_rep == 1 else "sessions"
            return (
                f"{calls_per_rep} executor {session_label}/rep; "
                f"max concurrency {max_concurrency}"
            )
        return (
            f"{calls_per_rep} calls/rep; "
            f"max concurrency {max_concurrency}"
        )
    return (
        f"max {behavior.get('maxCallsPerRep', '-')} calls/rep; "
        f"max concurrency {max_concurrency}"
    )


def _render_role_lines(configs: Sequence[LaunchConfigDocument]) -> list[str]:
    lines = [
        (
            "config | role | kind | selection | provider | model | thinking | "
            "credential | billing | usage | bounds"
        )
    ]
    for config in configs:
        roles = config["declaredRoles"]
        if not roles:
            lines.append(
                f"{config['identity']} | undeclared | - | - | - | - | - | - | - | - | -"
            )
            continue
        for role in roles:
            provider, model, thinking = _role_model_columns(role)
            usage_source = cast(Mapping[str, object], role["usageSource"])
            usage = str(usage_source.get("path", "-"))
            lines.append(
                " | ".join(
                    [
                        str(config["identity"]),
                        str(role.get("name", "-")),
                        str(role.get("roleKind", "-")),
                        str(role.get("selectionSummary", "fixed")),
                        provider,
                        model,
                        thinking,
                        str(role.get("credentialRoute", "-")),
                        str(role.get("billingCategory", "-")),
                        usage,
                        _role_call_summary(role),
                    ]
                )
            )
    return lines


def _render_subject_behavior_lines(
    configs: Sequence[LaunchConfigDocument],
) -> list[str]:
    lines: list[str] = []
    for config in configs:
        behavior = config.get("subjectBehavior")
        if behavior is None:
            continue
        lines.append(
            f"- {config['identity']}: "
            + json.dumps(behavior, sort_keys=True, separators=(",", ":"))
        )
    return lines


def _render_config_release_lines(
    configs: Sequence[LaunchConfigDocument],
) -> list[str]:
    """Render exact lock, leaf, and smoke details for approval."""
    lines: list[str] = []
    for config in configs:
        smoke_assertions = config["smokeAssertions"]
        rendered_assertions = (
            json.dumps(
                smoke_assertions,
                sort_keys=True,
                separators=(",", ":"),
            )
            if smoke_assertions is not None
            else "-"
        )
        lines.extend(
            [
                f"- {config['identity']}",
                f"  Lock: {config['lockIdentity'] or '-'}",
                f"  Leaf: {config['configLeaf']}",
                f"  Smoke contract: {config['smokeContract'] or '-'}",
                f"  Smoke assertions: {rendered_assertions}",
            ]
        )
    return lines


def _render_selected_task_lines(
    selection: Mapping[str, object],
) -> list[str]:
    """Render every selected task in its approved order."""
    tasks = cast(list[str], selection["tasks"])
    return [f"Kind: {selection.get('kind', '-')}"] + [f"- {task}" for task in tasks]


def _render_planned_cell_lines(
    cells: Sequence[Mapping[str, object]],
    *,
    include_smoke: bool,
) -> list[str]:
    """Render every exact result cell and optional smoke contract path."""
    if not cells:
        return ["- none"]
    lines: list[str] = []
    for cell in cells:
        line = (
            f"- {cell.get('task')} | {cell.get('config')} | "
            f"rep{cell.get('rep')} | result={cell.get('resultPath')}"
        )
        if include_smoke:
            line += f" | smoke={cell.get('contractPath') or '-'}"
        lines.append(line)
    return lines


def _render_launch_receipt(document: LaunchPlanDocument) -> str:
    counts = document["counts"]
    subject = document["subject"]
    paths = document["paths"]
    configs = document["configs"]
    baseline_identity = str(document["baselineConfig"])
    baseline = next(
        config for config in configs if config.get("identity") == baseline_identity
    )
    warnings = _receipt_warnings(document)
    subject_behavior_lines = _render_subject_behavior_lines(configs)
    policies = document["policies"]
    preflight_result_paths = {
        cell["resultPath"] for cell in document["preflightCells"]
    }
    preflight_overlap_count = sum(
        cell["resultPath"] in preflight_result_paths
        for cell in document["batchCells"]
    )
    lines = ["LAUNCH RECEIPT", "WARNINGS"]
    lines.extend(f"- {warning}" for warning in warnings)
    if not warnings:
        lines.append("- none")
    lines.extend(
        [
            "",
            "SUMMARY",
            f"Plan: {document['planIdentity']}",
            f"Subject: {subject['name']} {subject['version']}",
            f"Model: {document['model']} (thinking={document['thinking']})",
            (
                f"Tasks: {counts['tasks']}; configs: {counts['configs']}; "
                f"reps: {counts['reps']}; "
                f"concurrency: {document['concurrency']}"
            ),
            (
                f"Cells: {counts['preflightCells']} preflight; "
                f"{counts['batchCells']} batch"
            ),
            (
                "Preflight-covered batch entries: "
                f"{preflight_overlap_count}; successful preflight makes no "
                "second subject call"
            ),
            (
                "Execution: "
                f"agent timeout={policies['agent_timeout_s']}; "
                f"RPC quiescence={policies['rpc_quiescence_s']}s; "
                "initial context="
                + (
                    "captured"
                    if policies["capture_initial_context"]
                    else "not captured"
                )
                + f"; cell retries={policies['cell_retries']}"
                + "; auto resume="
                + ("enabled" if policies["auto_resume"] else "disabled")
                + (
                    f"; max quota wait={policies['max_quota_wait_s']}s; "
                    f"quota poll={policies['quota_poll_s']}s; "
                    "rate-limit backoff="
                    f"{policies['rate_limit_backoff_s']}s"
                )
            ),
            "",
            "TASK SELECTION",
            *_render_selected_task_lines(document["selection"]),
            "",
            "CONFIG RELEASES",
            *_render_config_release_lines(configs),
            "",
            "MODEL ROLES",
            *_render_role_lines(configs),
            "",
            "SUBJECT COMPATIBILITY",
            *(
                line
                for config in configs
                for line in (
                    f"- {config['identity']}",
                    "  Tested subject versions: "
                    + (", ".join(config["testedSubjectVersions"]) or "-"),
                    "  Required capabilities: "
                    + (", ".join(config["requiredCapabilities"]) or "-"),
                )
            ),
            *(
                ["", "SUBJECT BEHAVIOR", *subject_behavior_lines]
                if subject_behavior_lines
                else []
            ),
            "",
            f"BEHAVIOR DIFFERENCES FROM {baseline_identity}",
        ]
    )
    for config in configs:
        if config is baseline:
            continue
        lines.extend(_render_behavior_differences(baseline, config))
    lines.extend(
        [
            "",
            "PREFLIGHT CELLS",
            *_render_planned_cell_lines(
                document["preflightCells"],
                include_smoke=True,
            ),
            "",
            "BATCH CELLS",
            *_render_planned_cell_lines(
                document["batchCells"],
                include_smoke=False,
            ),
            "",
            "PATHS",
            f"Workspace: {paths['workspace']}",
            f"Tasks root: {paths['tasksRoot']}",
            f"Results root: {paths['resultsRoot']}",
            f"Structured state: {paths['statePath']}",
        ]
    )
    return "\n".join(lines) + "\n"


def compile_launch_request(
    request: LaunchRequest,
    *,
    repository_root: Path,
    tasks_root: Path,
    results_root: Path,
    state_root: Path,
    runtime_resolver: LaunchRuntimeResolver | None = None,
) -> CompiledLaunch:
    """Compile a deterministic launch without executing a subject."""
    tasks = _validate_launch_request(request)
    _validate_selected_tasks(tasks_root, tasks)
    config_plans = [
        _config_plan(repository_root, request, config_identity)
        for config_identity in request.configs
    ]
    for config_plan in config_plans:
        if config_plan["legacy"]:
            continue
        config_lock.require_shared_config_release_behavior(
            Path(config_plan["configRoot"]),
            str(config_plan["identity"]),
            {"behaviorInputs": config_plan["behaviorInputs"]},
            results_root,
            state_root,
        )
    if runtime_resolver is None:
        runtime_resolver = RepositoryLaunchRuntimeResolver(
            repository_root,
            tasks_root,
        )
    runtime = runtime_resolver.resolve_launch_runtime(request, tasks)
    _require_runtime_identity(runtime, tasks)
    if request.subject == "omp" and not runtime.subject_runtime_identity:
        raise ValueError(
            "Launch runtime identity unresolved: OMP binary identity missing"
        )
    _validate_config_runtime_compatibility(config_plans, runtime)
    batch_cells = _batch_cells(
        results_root,
        request,
        tasks,
        config_plans,
        runtime,
    )
    preflight_cells = _preflight_cells(
        repository_root,
        results_root,
        state_root,
        request,
        tasks,
        config_plans,
        batch_cells,
    )
    selection: dict[str, object] = {
        "kind": request.task_selection.kind,
        "tasks": list(tasks),
    }
    if request.task_selection.name is not None:
        selection["name"] = request.task_selection.name
    subject_document: LaunchSubjectDocument = {
        "name": request.subject,
        "runner": str(_subject_runner_path(repository_root, request.subject).resolve()),
        "version": runtime.subject_version,
    }
    if runtime.subject_runtime_identity:
        subject_document["runtimeIdentity"] = dict(runtime.subject_runtime_identity)
    document: LaunchPlanDocument = {
        "schemaVersion": _LAUNCH_PLAN_SCHEMA_VERSION,
        "baselineConfig": request.baseline_config,
        "batchCells": batch_cells,
        "concurrency": request.concurrency,
        "configs": config_plans,
        "counts": {
            "batchCells": len(batch_cells),
            "configs": len(request.configs),
            "preflightCells": len(preflight_cells),
            "reps": request.reps,
            "tasks": len(tasks),
        },
        "identityExclusions": ["paths.statePath", "runId"],
        "model": request.model,
        "paths": {
            "resultsRoot": str(results_root.resolve()),
            "statePath": str((state_root / request.run_id).resolve()),
            "stateRoot": str(state_root.resolve()),
            "tasksRoot": str(tasks_root.resolve()),
            "workspace": str(repository_root.resolve()),
        },
        "planIdentity": "",
        "policies": cast(dict[str, object], asdict(request.policies)),
        "preflightCells": preflight_cells,
        "runId": request.run_id,
        "runtime": {
            "harnessRevision": runtime.harness_revision,
            "immutableImageIdentities": {
                task: dict(identities)
                for task, identities in (runtime.immutable_image_identities.items())
            },
            "taskRevision": runtime.task_revision,
            "verifierIdentities": dict(runtime.verifier_identities),
        },
        "selection": selection,
        "subject": subject_document,
        "thinking": request.thinking,
    }
    document["planIdentity"] = _launch_plan_identity(document)
    run_key = confirmed_launch_run_key(
        request.run_id,
        document["planIdentity"],
    )
    document["paths"]["statePath"] = str((state_root / run_key).resolve())
    canonical_json = canonical_launch_plan_json(document)
    plan = LaunchPlan(
        identity=str(document["planIdentity"]),
        canonical_json=canonical_json,
    )
    return CompiledLaunch(plan=plan, receipt=_render_launch_receipt(document))
