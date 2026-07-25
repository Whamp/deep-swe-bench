"""Compile model-free batch launch requests into immutable review artifacts."""

from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol, TypedDict, cast

from harness import (
    config_lock,
    config_resolution,
    lib,
    run_state,
    versioned_smoke_contract,
)
from harness.run_state import sanitize_run_id

_LAUNCH_PLAN_SCHEMA_VERSION = 1
_THINKING_LEVELS = frozenset(
    {"off", "minimal", "low", "medium", "high", "xhigh"}
)
_PREFLIGHT_POLICIES = frozenset({"disabled", "new-configs", "required"})
_EXISTING_RESULT_POLICIES = frozenset({"require-compatible", "rerun"})
_TRANSIENT_ERROR_POLICIES = frozenset({"pause", "stop"})
_BILLING_CATEGORIES = frozenset(
    {"local compute", "paid API", "subscription quota"}
)
_COMPACT_USAGE_FORMATS = frozenset(
    {
        "compact-jsonl",
        "compact-worker-trace",
        "filtered-tool-events",
        "native-session",
    }
)


class LaunchClarificationRequired(ValueError):
    """Stop planning with structured evidence about unresolved model behavior."""

    def __init__(self, details: Sequence[Mapping[str, object]]) -> None:
        """Record secret-free clarification evidence for the caller."""
        self.details = tuple(dict(detail) for detail in details)
        super().__init__(
            "Launch clarification required: "
            + json.dumps(self.details, sort_keys=True, separators=(",", ":"))
        )


class LaunchConfigDocument(TypedDict):
    """Resolved config fields stored in a canonical launch plan."""

    behaviorInputs: list[dict[str, object]]
    configLeaf: str
    configRoot: str
    credentialRoutes: list[str]
    declaredRoles: list[dict[str, object]]
    identity: str
    launchSurfaces: list[dict[str, object]]
    legacy: bool
    lockIdentity: str | None
    requiredCapabilities: list[str]
    smokeContract: str | None
    testedSubjectVersions: list[str]
    usageSources: list[str]
    versionImpact: str | None


class LaunchCountsDocument(TypedDict):
    """Resolved task, config, rep, preflight, and batch cell counts."""

    batchCells: int
    configs: int
    preflightCells: int
    reps: int
    tasks: int


class LaunchPathsDocument(TypedDict):
    """Exact workspace, result, and structured-state launch paths."""

    resultsRoot: str
    statePath: str
    stateRoot: str
    workspace: str


class LaunchRuntimeDocument(TypedDict):
    """Exact harness, task, verifier, and immutable image identities."""

    harnessRevision: str
    immutableImageIdentities: dict[str, dict[str, str]]
    taskRevision: str
    verifierIdentities: dict[str, str]


class LaunchSubjectDocument(TypedDict):
    """Resolved subject runner and exact subject version."""

    name: str
    runner: str
    version: str


class LaunchPlanDocument(TypedDict):
    """Versioned canonical launch behavior and explicitly volatile metadata."""

    schemaVersion: int
    baselineConfig: str
    batchCells: list[dict[str, object]]
    concurrency: int
    configs: list[LaunchConfigDocument]
    counts: LaunchCountsDocument
    identityExclusions: list[str]
    model: str
    paths: LaunchPathsDocument
    planIdentity: str
    policies: dict[str, object]
    preflightCells: list[dict[str, object]]
    runId: str
    runtime: LaunchRuntimeDocument
    selection: dict[str, object]
    subject: LaunchSubjectDocument
    thinking: str


@dataclass(frozen=True, slots=True)
class LaunchTaskSelection:
    """Identify the exact ordered task selection compiled into a launch plan."""

    kind: str
    tasks: tuple[str, ...]
    name: str | None = None


@dataclass(frozen=True, slots=True)
class LaunchExecutionPolicies:
    """Freeze preflight, result reuse, transient, and retry launch policies."""

    preflight: str
    existing_results: str
    transient_errors: str
    cell_retries: int


@dataclass(frozen=True, slots=True)
class LaunchRequest:
    """Capture unresolved operator intent before model-free launch planning."""

    subject: str
    model: str
    thinking: str
    configs: tuple[str, ...]
    baseline_config: str
    task_selection: LaunchTaskSelection
    reps: int
    concurrency: int
    run_id: str
    policies: LaunchExecutionPolicies


@dataclass(frozen=True, slots=True)
class LaunchRuntimeIdentity:
    """Record model-free runtime provenance resolved for selected tasks."""

    subject_version: str
    harness_revision: str
    task_revision: str
    verifier_identities: Mapping[str, str]
    immutable_image_identities: Mapping[str, Mapping[str, str]]
    subject_capabilities: frozenset[str] = frozenset()
    available_credential_routes: frozenset[str] = frozenset()


class LaunchRuntimeResolver(Protocol):
    """Resolve exact runtime identities without starting a subject process."""

    def resolve_launch_runtime(
        self,
        request: LaunchRequest,
        tasks: tuple[str, ...],
    ) -> LaunchRuntimeIdentity:
        """Return runtime identities for a launch request and its tasks."""


def _identity_files(paths: Iterable[Path]) -> list[Path]:
    files: set[Path] = set()
    for path in paths:
        if path.is_file() or path.is_symlink():
            files.add(path)
        elif path.is_dir():
            files.update(
                candidate
                for candidate in path.rglob("*")
                if (candidate.is_file() or candidate.is_symlink())
                and "__pycache__" not in candidate.parts
            )
    return sorted(files)


def _file_set_identity(root: Path, paths: Iterable[Path]) -> str:
    digest = hashlib.sha256()
    for path in _identity_files(paths):
        relative_path = path.relative_to(root).as_posix()
        digest.update(relative_path.encode())
        digest.update(b"\0")
        digest.update(b"1" if path.stat().st_mode & 0o100 else b"0")
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return f"sha256:{digest.hexdigest()}"


class RepositoryLaunchRuntimeResolver:
    """Resolve pinned runtime identities without pulling or running images."""

    def __init__(self, repository_root: Path, tasks_root: Path) -> None:
        """Bind runtime resolution to one repository and task corpus."""
        self.repository_root = repository_root
        self.tasks_root = tasks_root

    def _pi_subject_version(self) -> str:
        dockerfile = self.repository_root / "Dockerfile.pi-agent"
        if not dockerfile.is_file():
            raise ValueError(
                "Launch runtime identity unresolved: Pi Dockerfile missing at "
                f"{dockerfile}"
            )
        match = re.search(
            r"^ARG PI_VERSION=(?P<version>\S+)$",
            dockerfile.read_text(),
            re.MULTILINE,
        )
        if match is None:
            raise ValueError(
                "Launch runtime identity unresolved: PI_VERSION is not "
                f"pinned in {dockerfile}"
            )
        return f"pi@{match.group('version')}"

    @staticmethod
    def _image_identity(image_reference: str) -> str:
        completed = subprocess.run(
            [
                "docker",
                "image",
                "inspect",
                "--format",
                "{{.Id}}",
                image_reference,
            ],
            check=False,
            capture_output=True,
            text=True,
        )
        identity = completed.stdout.strip()
        if completed.returncode != 0 or not identity:
            detail = completed.stderr.strip() or "image is not present"
            raise ValueError(
                "Launch runtime identity unresolved: immutable image identity "
                f"for {image_reference!r}: {detail}"
            )
        return identity

    def _harness_revision(self) -> str:
        paths = [
            self.repository_root / "harness",
            self.repository_root / "Dockerfile.pi-agent",
            self.repository_root / "pyproject.toml",
            self.repository_root / "uv.lock",
        ]
        return _file_set_identity(self.repository_root, paths)

    def _task_revision(self, tasks: tuple[str, ...]) -> str:
        return _file_set_identity(
            self.tasks_root,
            [self.tasks_root / task for task in tasks],
        )

    def _verifier_identity(self, task: str) -> str:
        verifier_root = self.tasks_root / task / "tests"
        if not verifier_root.is_dir():
            raise ValueError(
                "Launch runtime identity unresolved: verifier inputs "
                f"missing for task {task!r} at {verifier_root}"
            )
        return _file_set_identity(self.tasks_root, [verifier_root])

    @staticmethod
    def _available_credential_routes() -> frozenset[str]:
        routes = frozenset(
            name for name, value in os.environ.items() if value.strip()
        )
        oauth_path = Path.home() / ".pi" / "agent" / "auth.json"
        if oauth_path.is_file():
            return routes | {"OPENAI_CODEX_OAUTH"}
        return routes

    def resolve_launch_runtime(
        self,
        request: LaunchRequest,
        tasks: tuple[str, ...],
    ) -> LaunchRuntimeIdentity:
        """Resolve repository, task, verifier, subject, and image identity."""
        if request.subject != "pi":
            raise ValueError(
                "Launch runtime identity unresolved: OMP confirmed-launch "
                "runtime resolution is not implemented; see issue #20"
            )
        verifier_identities: dict[str, str] = {}
        image_identities: dict[str, dict[str, str]] = {}
        for task_id in tasks:
            task = lib.load_task(task_id, root=self.tasks_root)
            verifier_identities[task_id] = self._verifier_identity(task_id)
            image_identities[task_id] = {
                "agent": self._image_identity(task.pi_image),
                "environment": self._image_identity(task.env_image),
                "verifier": self._image_identity(task.verifier_image),
            }
        return LaunchRuntimeIdentity(
            subject_version=self._pi_subject_version(),
            harness_revision=self._harness_revision(),
            task_revision=self._task_revision(tasks),
            verifier_identities=verifier_identities,
            immutable_image_identities=image_identities,
            subject_capabilities=frozenset(
                {"native-session-usage", "pi-extensions", "pi-rpc", "pi-skills"}
            ),
            available_credential_routes=self._available_credential_routes(),
        )


@dataclass(frozen=True, slots=True)
class LaunchPlan:
    """Hold one immutable, canonical launch plan and its content identity."""

    identity: str
    canonical_json: str

    def to_document(self) -> LaunchPlanDocument:
        """Return a fresh document for inspecting this immutable launch plan."""
        document = json.loads(self.canonical_json)
        if not isinstance(document, dict):
            raise TypeError("Launch plan invalid: expected a JSON object")
        return cast(LaunchPlanDocument, document)


@dataclass(frozen=True, slots=True)
class CompiledLaunch:
    """Pair the immutable launch plan with its human review receipt."""

    plan: LaunchPlan
    receipt: str


@dataclass(frozen=True, slots=True)
class ConfirmedPiCell:
    """Supply one Pi runner with only behavior resolved by a confirmed plan."""

    config_identity: str
    config_lock_identity: str
    config_root: Path
    config_leaf: Path
    smoke_contract: Path | None
    task: str
    rep: int
    model: str
    thinking: str
    result_path: Path
    subject_runner: Path
    subject_version: str
    harness_revision: str
    task_revision: str
    verifier_identity: str
    immutable_image_identities: Mapping[str, str]
    launch_plan_identity: str


class ConfirmedPiRunner(Protocol):
    """Execute one plan-resolved Pi cell without resolving launch inputs."""

    def run_confirmed_pi_cell(
        self,
        cell: ConfirmedPiCell,
    ) -> Mapping[str, object]:
        """Return one complete result record without writing result.json."""


@dataclass(frozen=True, slots=True)
class ConfirmedLaunchExecution:
    """Identify durable artifacts produced by one confirmed cell execution."""

    result_path: Path
    state_path: Path
    log_path: Path


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


def _validate_launch_subject(request: LaunchRequest) -> None:
    if request.subject not in {"pi", "omp"}:
        raise ValueError(
            "Launch subject invalid: expected 'pi' or 'omp'; "
            f"got {request.subject!r}"
        )
    if not request.model.strip():
        raise ValueError("Launch model invalid: model cannot be empty")
    if request.thinking not in _THINKING_LEVELS:
        raise ValueError(
            "Launch thinking invalid: expected off, minimal, low, medium, "
            f"high, or xhigh; got {request.thinking!r}"
        )


def _validate_launch_configs(request: LaunchRequest) -> None:
    if not request.configs:
        raise ValueError("Launch configs invalid: select at least one config")
    if len(set(request.configs)) != len(request.configs):
        raise ValueError(
            "Launch configs invalid: duplicate config identities are not "
            "allowed"
        )
    if request.baseline_config not in request.configs:
        raise ValueError(
            "Launch baseline invalid: selected baseline must be a config; "
            f"got {request.baseline_config!r}"
        )


def _validate_launch_policies(request: LaunchRequest) -> None:
    if request.policies.preflight not in _PREFLIGHT_POLICIES:
        raise ValueError(
            "Launch preflight policy invalid: expected disabled, "
            f"new-configs, or required; got {request.policies.preflight!r}"
        )
    if request.policies.existing_results not in _EXISTING_RESULT_POLICIES:
        raise ValueError(
            "Launch existing-result policy invalid: expected "
            "require-compatible or rerun; "
            f"got {request.policies.existing_results!r}"
        )
    if request.policies.transient_errors not in _TRANSIENT_ERROR_POLICIES:
        raise ValueError(
            "Launch transient-error policy invalid: expected pause or stop; "
            f"got {request.policies.transient_errors!r}"
        )
    if request.policies.cell_retries < 0:
        raise ValueError(
            "Launch cell-retry policy invalid: expected zero or more; "
            f"got {request.policies.cell_retries}"
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
    tasks = request.task_selection.tasks
    if not tasks:
        raise ValueError(
            "Launch task selection invalid: select at least one task"
        )
    if len(set(tasks)) != len(tasks):
        raise ValueError(
            "Launch task selection invalid: duplicate tasks are not allowed"
        )
    return tasks


def _validate_selected_tasks(tasks_root: Path, tasks: Sequence[str]) -> None:
    missing = [
        task
        for task in tasks
        if not (tasks_root / task / "task.toml").is_file()
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
        raise ValueError(
            f"Launch subject invalid: unsupported subject {subject!r}"
        )
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
    unresolved = [
        name for name, value in scalar_identities.items() if not value
    ]
    for task in tasks:
        if not runtime.verifier_identities.get(task):
            unresolved.append(f"verifier identity for {task}")
        image_identities = runtime.immutable_image_identities.get(task)
        if not image_identities:
            unresolved.append(f"immutable image identities for {task}")
        elif any(not identity for identity in image_identities.values()):
            unresolved.append(f"immutable image identity for {task}")
    if unresolved:
        raise ValueError(
            "Launch runtime identity unresolved: "
            + ", ".join(sorted(unresolved))
        )


def _lock_string_list(
    lock_document: Mapping[str, object],
    field: str,
) -> list[str]:
    value = lock_document.get(field, [])
    if not isinstance(value, list):
        raise TypeError(
            f"Config lock invalid: {field} must be a list of strings"
        )
    normalized: list[str] = []
    for item in value:
        if not isinstance(item, str):
            raise TypeError(
                f"Config lock invalid: {field} must be a list of strings"
            )
        normalized.append(item)
    return normalized


def _lock_object_list(
    lock_document: Mapping[str, object],
    field: str,
) -> list[dict[str, object]]:
    value = lock_document.get(field, [])
    if not isinstance(value, list):
        raise TypeError(
            f"Config lock invalid: {field} must be a list of objects"
        )
    normalized: list[dict[str, object]] = []
    for item in value:
        if not isinstance(item, dict):
            raise TypeError(
                f"Config lock invalid: {field} must be a list of objects"
            )
        normalized.append({str(key): child for key, child in item.items()})
    return normalized


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
    if thinking not in _THINKING_LEVELS:
        raise ValueError(
            "Launch model role invalid: "
            f"config={config_identity!r}; role={role_name!r}; "
            f"thinking={thinking!r}"
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
        if (
            not isinstance(inherited_role, str)
            or inherited_role not in roles_by_name
        ):
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
        raise LaunchClarificationRequired(
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
        if role.get("billingCategory") not in _BILLING_CATEGORIES:
            raise ValueError(
                "Launch model role invalid: "
                f"config={config_identity!r}; role={role_name!r}; "
                f"billing category={role.get('billingCategory')!r}"
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
    call_kind = (
        call_behavior.get("kind") if isinstance(call_behavior, dict) else None
    )
    if call_kind not in {"fixed", "bounded"}:
        raise LaunchClarificationRequired(
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
    selection_kind = (
        selection.get("kind") if isinstance(selection, dict) else None
    )
    if selection_kind not in {"fixed", "inherited", "bounded-dynamic"}:
        raise LaunchClarificationRequired(
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
        declared_surface_roles = {
            role for role in model_roles if isinstance(role, str)
        }
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


def _legacy_launch_config_document(
    resolved: config_resolution.ResolvedConfigLeaf,
    config_identity: str,
) -> LaunchConfigDocument:
    return {
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
        "smokeContract": (
            str(resolved.smoke_contract.resolve())
            if resolved.smoke_contract is not None
            else None
        ),
        "testedSubjectVersions": [],
        "usageSources": [],
        "versionImpact": None,
    }


def _validate_extension_surface_coverage(
    config_identity: str,
    behavior_inputs: Sequence[Mapping[str, object]],
    launch_surfaces: Sequence[Mapping[str, object]],
) -> None:
    uncovered: list[dict[str, object]] = []
    for behavior_input in behavior_inputs:
        path = behavior_input.get("path")
        if behavior_input.get("kind") != "extension" or not isinstance(
            path, str
        ):
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
        raise LaunchClarificationRequired(uncovered)


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
    versioned_identity = config_resolution.parse_versioned_config_identity(
        config_identity
    )
    if versioned_identity is not None:
        versioned_smoke_contract.validate_versioned_smoke_contract(
            repository_root,
            resolved.smoke_contract,
        )
    lock_document = config_lock.read_matching_config_lock(
        resolved,
        config_identity,
    )
    if lock_document is None:
        return _legacy_launch_config_document(resolved, config_identity)
    behavior_inputs = _lock_object_list(lock_document, "behaviorInputs")
    launch_surfaces = _lock_object_list(lock_document, "launchSurfaces")
    _validate_extension_surface_coverage(
        config_identity,
        behavior_inputs,
        launch_surfaces,
    )
    credential_routes = _lock_string_list(lock_document, "credentialRoutes")
    declared_roles = _lock_object_list(lock_document, "declaredRoles")
    usage_sources = _lock_string_list(lock_document, "usageSources")
    _validate_role_usage_sources(
        config_identity,
        declared_roles,
        usage_sources,
    )
    resolved_roles = _resolve_declared_roles(config_identity, declared_roles)
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
        raise TypeError(
            "Config lock invalid: versionImpact must be a string or null"
        )
    lock_identity = lock_document.get("lockIdentity")
    if not isinstance(lock_identity, str):
        raise TypeError("Config lock invalid: lockIdentity must be a string")
    return {
        "behaviorInputs": behavior_inputs,
        "configLeaf": str(resolved.config_leaf.resolve()),
        "configRoot": str(resolved.config_root.resolve()),
        "credentialRoutes": credential_routes,
        "declaredRoles": resolved_roles,
        "identity": config_identity,
        "launchSurfaces": launch_surfaces,
        "legacy": False,
        "lockIdentity": lock_identity,
        "requiredCapabilities": _lock_string_list(
            lock_document,
            "requiredCapabilities",
        ),
        "smokeContract": (
            str(resolved.smoke_contract.resolve())
            if resolved.smoke_contract is not None
            else None
        ),
        "testedSubjectVersions": _lock_string_list(
            lock_document,
            "testedSubjectVersions",
        ),
        "usageSources": usage_sources,
        "versionImpact": version_impact,
    }


def _validate_config_runtime_compatibility(
    configs: Sequence[LaunchConfigDocument],
    runtime: LaunchRuntimeIdentity,
) -> None:
    for config in configs:
        if config["legacy"]:
            continue
        tested_versions = config["testedSubjectVersions"]
        if runtime.subject_version not in tested_versions:
            raise ValueError(
                "Untested subject version: "
                f"config={config['identity']!r}; "
                f"subject={runtime.subject_version!r}; "
                f"tested={tested_versions!r}"
            )
        missing_capabilities = sorted(
            set(config["requiredCapabilities"]) - runtime.subject_capabilities
        )
        if missing_capabilities:
            raise ValueError(
                "Launch subject capability missing: "
                f"config={config['identity']!r}; "
                f"missing={missing_capabilities!r}; "
                f"available={sorted(runtime.subject_capabilities)!r}"
            )
        unavailable_routes = sorted(
            set(config["credentialRoutes"])
            - runtime.available_credential_routes
        )
        if unavailable_routes:
            raise ValueError(
                "Launch credential route unavailable: "
                f"config={config['identity']!r}; "
                f"routes={unavailable_routes!r}"
            )


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


def _batch_cells(
    results_root: Path,
    request: LaunchRequest,
    tasks: tuple[str, ...],
) -> list[dict[str, object]]:
    cells: list[dict[str, object]] = []
    for task in tasks:
        for rep in range(request.reps):
            for config in request.configs:
                result_path = _cell_result_path(
                    results_root,
                    request,
                    config,
                    task,
                    rep,
                )
                cells.append(
                    {
                        "config": config,
                        "existingResult": result_path.is_file(),
                        "existingResultPolicy": (
                            request.policies.existing_results
                        ),
                        "rep": rep,
                        "resultPath": str(result_path.resolve()),
                        "task": task,
                    }
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
    request: LaunchRequest,
    tasks: tuple[str, ...],
    config_plans: Sequence[Mapping[str, object]],
) -> list[dict[str, object]]:
    if request.policies.preflight == "disabled":
        return []
    task = _preflight_task(repository_root, tasks)
    cells: list[dict[str, object]] = []
    for config in config_plans:
        config_identity = str(config["identity"])
        has_results = any(
            (
                results_root
                / lib.model_leaf(request.model)
                / request.thinking
                / config_identity
            ).glob("*/rep*/result.json")
        )
        if request.policies.preflight == "new-configs" and has_results:
            continue
        cells.append(
            {
                "config": config_identity,
                "contractPath": config["smokeContract"],
                "rep": 0,
                "resultPath": str(
                    _cell_result_path(
                        results_root,
                        request,
                        config_identity,
                        task,
                        0,
                    ).resolve()
                ),
                "task": task,
            }
        )
    return cells


def _receipt_warnings(document: Mapping[str, object]) -> list[str]:
    configs = document.get("configs")
    warnings: list[str] = []
    if isinstance(configs, list):
        legacy = [
            str(config.get("identity"))
            for config in configs
            if isinstance(config, dict) and config.get("legacy") is True
        ]
        if legacy:
            warnings.append(
                "legacy configs have no config-lock provenance: "
                + ", ".join(legacy)
            )
    policies = document.get("policies")
    if isinstance(policies, dict) and policies.get("preflight") == "disabled":
        warnings.append("preflight is disabled")
    return warnings


def _behavior_inputs_by_path(
    config: LaunchConfigDocument,
) -> dict[str, dict[str, object]]:
    by_path: dict[str, dict[str, object]] = {}
    for item in config["behaviorInputs"]:
        path = item.get("path")
        if isinstance(path, str):
            by_path[path] = item
    return by_path


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
    return (
        ",".join(
            str(model.get("provider", "-"))
            for model in models
            if isinstance(model, dict)
        ),
        ",".join(
            str(model.get("model", "-"))
            for model in models
            if isinstance(model, dict)
        ),
        ",".join(
            str(model.get("thinking", "-"))
            for model in models
            if isinstance(model, dict)
        ),
    )


def _role_call_summary(role: Mapping[str, object]) -> str:
    behavior = role.get("callBehavior")
    if not isinstance(behavior, dict):
        return "-"
    max_concurrency = behavior.get("maxConcurrency", "-")
    if behavior.get("kind") == "fixed":
        return (
            f"{behavior.get('callsPerRep', '-')} calls/rep; "
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
                f"{config['identity']} | undeclared | - | - | - | - | - | "
                "- | - | - | -"
            )
            continue
        for role in roles:
            provider, model, thinking = _role_model_columns(role)
            usage_source = role.get("usageSource")
            usage = (
                str(usage_source.get("path", "-"))
                if isinstance(usage_source, dict)
                else ",".join(config["usageSources"]) or "-"
            )
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


def _render_launch_receipt(document: LaunchPlanDocument) -> str:
    counts = document["counts"]
    subject = document["subject"]
    paths = document["paths"]
    configs = document["configs"]
    baseline_identity = str(document["baselineConfig"])
    baseline = next(
        config
        for config in configs
        if config.get("identity") == baseline_identity
    )
    warnings = _receipt_warnings(document)
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
            "PATHS",
            f"Workspace: {paths['workspace']}",
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
    if runtime_resolver is None:
        runtime_resolver = RepositoryLaunchRuntimeResolver(
            repository_root,
            tasks_root,
        )
    runtime = runtime_resolver.resolve_launch_runtime(request, tasks)
    _require_runtime_identity(runtime, tasks)
    _validate_config_runtime_compatibility(config_plans, runtime)
    batch_cells = _batch_cells(results_root, request, tasks)
    preflight_cells = _preflight_cells(
        repository_root,
        results_root,
        request,
        tasks,
        config_plans,
    )
    selection: dict[str, object] = {
        "kind": request.task_selection.kind,
        "tasks": list(tasks),
    }
    if request.task_selection.name is not None:
        selection["name"] = request.task_selection.name
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
                for task, identities in (
                    runtime.immutable_image_identities.items()
                )
            },
            "taskRevision": runtime.task_revision,
            "verifierIdentities": dict(runtime.verifier_identities),
        },
        "selection": selection,
        "subject": {
            "name": request.subject,
            "runner": str(
                _subject_runner_path(repository_root, request.subject).resolve()
            ),
            "version": runtime.subject_version,
        },
        "thinking": request.thinking,
    }
    document["planIdentity"] = _launch_plan_identity(document)
    canonical_json = canonical_launch_plan_json(document)
    plan = LaunchPlan(
        identity=str(document["planIdentity"]),
        canonical_json=canonical_json,
    )
    return CompiledLaunch(plan=plan, receipt=_render_launch_receipt(document))


def _confirmed_plan_document(
    plan: LaunchPlan,
    confirmation_identity: str | None,
) -> LaunchPlanDocument:
    parsed_plan = parse_launch_plan_json(plan.canonical_json)
    if parsed_plan.identity != plan.identity:
        raise ValueError(
            "Launch plan mismatch: supplied plan identity does not match its "
            "canonical document"
        )
    if confirmation_identity is None:
        raise ValueError("Launch confirmation missing: plan was not confirmed")
    if confirmation_identity != parsed_plan.identity:
        raise ValueError(
            "Launch confirmation mismatch: "
            f"confirmed={confirmation_identity!r}, "
            f"plan={parsed_plan.identity!r}"
        )
    return parsed_plan.to_document()


def _single_confirmed_pi_cell(
    document: LaunchPlanDocument,
) -> ConfirmedPiCell:
    subject = document["subject"]
    if subject["name"] != "pi":
        raise ValueError(
            "Confirmed Pi execution subject mismatch: "
            f"expected 'pi', got {subject['name']!r}"
        )
    batch_cells = document["batchCells"]
    if len(batch_cells) != 1:
        raise ValueError(
            "Confirmed Pi execution cell count invalid: "
            f"expected exactly one batch cell, got {len(batch_cells)}"
        )
    cell_document = batch_cells[0]
    config_identity = cell_document.get("config")
    task = cell_document.get("task")
    rep = cell_document.get("rep")
    result_path = cell_document.get("resultPath")
    if (
        not isinstance(config_identity, str)
        or not isinstance(task, str)
        or not isinstance(rep, int)
        or not isinstance(result_path, str)
    ):
        raise TypeError(
            "Confirmed Pi execution cell invalid: config, task, rep, and "
            "resultPath must be resolved"
        )
    config_document = next(
        (
            config
            for config in document["configs"]
            if config["identity"] == config_identity
        ),
        None,
    )
    if config_document is None:
        raise ValueError(
            "Confirmed Pi execution config missing: "
            f"plan has no config document for {config_identity!r}"
        )
    lock_identity = config_document["lockIdentity"]
    if not isinstance(lock_identity, str):
        raise TypeError(
            "Confirmed Pi execution config provenance missing: "
            f"config={config_identity!r}"
        )
    verifier_identity = document["runtime"]["verifierIdentities"].get(task)
    image_identities = document["runtime"]["immutableImageIdentities"].get(task)
    if not isinstance(verifier_identity, str) or not isinstance(
        image_identities,
        dict,
    ):
        raise TypeError(
            f"Confirmed Pi execution runtime missing: task={task!r}"
        )
    smoke_contract = config_document["smokeContract"]
    return ConfirmedPiCell(
        config_identity=config_identity,
        config_lock_identity=lock_identity,
        config_root=Path(config_document["configRoot"]),
        config_leaf=Path(config_document["configLeaf"]),
        smoke_contract=(
            Path(smoke_contract) if smoke_contract is not None else None
        ),
        task=task,
        rep=rep,
        model=document["model"],
        thinking=document["thinking"],
        result_path=Path(result_path),
        subject_runner=Path(subject["runner"]),
        subject_version=subject["version"],
        harness_revision=document["runtime"]["harnessRevision"],
        task_revision=document["runtime"]["taskRevision"],
        verifier_identity=verifier_identity,
        immutable_image_identities={
            str(name): str(identity)
            for name, identity in image_identities.items()
        },
        launch_plan_identity=document["planIdentity"],
    )


def _confirmed_result_record(
    cell: ConfirmedPiCell,
    record: Mapping[str, object],
) -> dict[str, object]:
    config_identity = config_resolution.parse_versioned_config_identity(
        cell.config_identity
    )
    if config_identity is None:
        raise ValueError(
            "Confirmed Pi execution config version missing: "
            f"config={cell.config_identity!r}"
        )
    confirmed_record = dict(record)
    confirmed_record.update(
        {
            "config": cell.config_identity,
            "config_lock_identity": cell.config_lock_identity,
            "config_name": config_identity.name,
            "config_version": config_identity.version,
            "harness_revision": cell.harness_revision,
            "immutable_image_identities": dict(cell.immutable_image_identities),
            "launch_plan_identity": cell.launch_plan_identity,
            "model": cell.model,
            "rep": cell.rep,
            "subject": "pi",
            "subject_version": cell.subject_version,
            "task": cell.task,
            "task_revision": cell.task_revision,
            "thinking_level": cell.thinking,
            "verifier_identity": cell.verifier_identity,
        }
    )
    return confirmed_record


def _confirmed_run_manifest(
    document: LaunchPlanDocument,
    cell: ConfirmedPiCell,
    log_path: Path,
) -> tuple[dict[str, object], dict[str, object]]:
    state_cell = run_state.make_cell(
        task=cell.task,
        config=cell.config_identity,
        rep=cell.rep,
        result_path=cell.result_path,
        log_path=log_path,
    )
    manifest = run_state.base_manifest(
        run_id=document["runId"],
        command=["execute_confirmed_launch", document["planIdentity"]],
        cwd=document["paths"]["workspace"],
        model=cell.model,
        thinking=cell.thinking,
        configs=[cell.config_identity],
        selection=dict(document["selection"]),
        runs=1,
        workers=1,
        agent="pi",
        agent_timeout_s=None,
        rpc_quiescence_s=None,
        progress_interval_s=None,
        batch_cells=[state_cell],
        preflight=[],
    )
    manifest.update(
        {
            "launch_plan_identity": document["planIdentity"],
            "launch_plan_path": "launch-plan.json",
        }
    )
    return manifest, state_cell


def execute_confirmed_launch(
    plan: LaunchPlan,
    *,
    confirmation_identity: str | None,
    pi_runner: ConfirmedPiRunner,
) -> ConfirmedLaunchExecution:
    """Execute one Pi cell only when its exact launch plan was confirmed."""
    document = _confirmed_plan_document(plan, confirmation_identity)
    cell = _single_confirmed_pi_cell(document)
    state_path = Path(document["paths"]["statePath"])
    expected_state_path = (
        Path(document["paths"]["stateRoot"]) / document["runId"]
    ).resolve()
    if state_path.resolve() != expected_state_path:
        raise ValueError(
            "Confirmed launch state path mismatch: "
            f"planned={str(state_path)!r}, "
            f"expected={str(expected_state_path)!r}"
        )
    log_path = state_path / "logs" / "confirmed-pi-cell.log"
    manifest, state_cell = _confirmed_run_manifest(document, cell, log_path)
    state = run_state.RunStateWriter(
        document["paths"]["stateRoot"],
        manifest,
    )
    state.start()
    plan_path = state_path / "launch-plan.json"
    plan_path.write_text(plan.canonical_json)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(
        "Confirmed Pi cell execution\n"
        f"launch_plan_identity={cell.launch_plan_identity}\n"
        f"cell={cell.task}/{cell.config_identity}/rep{cell.rep}\n"
    )
    state.cell_started(state_cell)
    cell.result_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        runner_record = pi_runner.run_confirmed_pi_cell(cell)
        result_record = _confirmed_result_record(cell, runner_record)
        run_state.atomic_write_json(cell.result_path, result_record)
    except Exception as error:
        with log_path.open("a", encoding="utf-8") as log_file:
            log_file.write(
                "Confirmed Pi cell execution failed: "
                f"{type(error).__name__}: {error}\n"
            )
        state.cell_finished(
            state_cell,
            log_path=log_path,
            exit_code="exception",
        )
        state.run_failed(reason="Confirmed Pi cell execution failed")
        raise
    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write("Confirmed Pi cell execution completed\n")
    agent_exit = result_record.get("agent_exit")
    if not isinstance(agent_exit, (int, str)):
        agent_exit = None
    state.cell_finished(
        state_cell,
        result_path=cell.result_path,
        log_path=log_path,
        exit_code=agent_exit,
    )
    state.run_completed()
    return ConfirmedLaunchExecution(
        result_path=cell.result_path,
        state_path=state_path,
        log_path=log_path,
    )
