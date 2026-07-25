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
    confirmed_preflight,
    lib,
    result_provenance,
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


class LaunchPreflightError(RuntimeError):
    """Stop batch fan-out after durable preflight diagnostics are recorded."""


class LaunchInputDriftError(RuntimeError):
    """Stop a confirmed run before changed launch inputs start another rep."""


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
class ExplicitResultReuseDecision:
    """Authorize reuse of one exact earlier result and recorded provenance."""

    result_path: Path
    prior_config_identity: str
    result_identity: str
    recorded_provenance: Mapping[str, object]
    rationale: str


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
    reuse_decisions: tuple[ExplicitResultReuseDecision, ...] = ()


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
    reuse_provenance: Mapping[str, object] | None
    reuse_reason: str | None
    reuse_result_identity: str | None


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
    if record.get("config") != decision.prior_config_identity:
        decision_mismatches["prior_config_identity"] = {
            "accepted": decision.prior_config_identity,
            "recorded": record.get("config"),
        }
    if dict(decision.recorded_provenance) != recorded_provenance:
        decision_mismatches["recorded_provenance"] = {
            "accepted": dict(decision.recorded_provenance),
            "recorded": recorded_provenance,
        }
    observed_identity = result_provenance.result_file_identity(result_path)
    if decision.result_identity != observed_identity:
        decision_mismatches["result_identity"] = {
            "accepted": decision.result_identity,
            "recorded": observed_identity,
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
) -> dict[str, object]:
    """Build the exact modern provenance required for automatic reuse."""
    return {
        "config": config["identity"],
        "config_lock_identity": config["lockIdentity"],
        "harness_revision": runtime.harness_revision,
        "immutable_image_identities": dict(
            runtime.immutable_image_identities[task]
        ),
        "model": request.model,
        "rep": rep,
        "subject": request.subject,
        "subject_version": runtime.subject_version,
        "task": task,
        "task_revision": runtime.task_revision,
        "thinking_level": request.thinking,
        "verifier_identity": runtime.verifier_identities[task],
    }


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
                reuse_provenance: dict[str, object] | None = None
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
                    decision, reuse_decision = (
                        _matching_explicit_reuse_decision(
                            result_path,
                            record,
                            request.reuse_decisions,
                        )
                    )
                    if decision is not None:
                        matched_decisions.add(result_path.resolve())
                        reuse_provenance = (
                            result_provenance.recorded_result_provenance(record)
                        )
                        reuse_reason = "explicit_result_reuse"
                        reuse_result_identity = decision.result_identity
                    elif mismatches:
                        raise ValueError(
                            f"Result provenance mismatch: path={result_path}; "
                            f"incompatible fields={mismatches!r}"
                        )
                    elif (
                        request.policies.existing_results
                        == "require-compatible"
                    ):
                        reuse_provenance = planned_provenance
                        reuse_reason = "compatible_existing_result"
                        reuse_result_identity = (
                            result_provenance.result_file_identity(result_path)
                        )
                cells.append(
                    {
                        "config": config_identity,
                        "existingResult": result_path.is_file(),
                        "existingResultPolicy": (
                            request.policies.existing_results
                        ),
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
            has_release_evidence = any(
                config_results.glob("*/rep*/result.json")
            )
        else:
            has_release_evidence = config["lockIdentity"] in (
                config_lock.sealed_config_lock_identities(
                    results_root,
                    config_identity,
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
            cell
            for cell in batch_cells
            if cell.get("resultPath") == str(result_path)
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
    for config_plan in config_plans:
        if config_plan["legacy"]:
            continue
        config_lock.require_shared_config_release_behavior(
            Path(config_plan["configRoot"]),
            str(config_plan["identity"]),
            {"behaviorInputs": config_plan["behaviorInputs"]},
            results_root,
        )
    if runtime_resolver is None:
        runtime_resolver = RepositoryLaunchRuntimeResolver(
            repository_root,
            tasks_root,
        )
    runtime = runtime_resolver.resolve_launch_runtime(request, tasks)
    _require_runtime_identity(runtime, tasks)
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


def _confirmed_pi_cell(
    document: LaunchPlanDocument,
    cell_document: Mapping[str, object],
) -> ConfirmedPiCell:
    subject = document["subject"]
    if subject["name"] != "pi":
        raise ValueError(
            "Confirmed Pi execution subject mismatch: "
            f"expected 'pi', got {subject['name']!r}"
        )
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
        reuse_provenance=(
            cast(Mapping[str, object], cell_document["reuseProvenance"])
            if isinstance(cell_document.get("reuseProvenance"), Mapping)
            else None
        ),
        reuse_reason=(
            str(cell_document["reuseReason"])
            if cell_document.get("reuseReason") is not None
            else None
        ),
        reuse_result_identity=(
            str(cell_document["reuseResultIdentity"])
            if cell_document.get("reuseResultIdentity") is not None
            else None
        ),
    )


def _confirmed_pi_cells(
    document: LaunchPlanDocument,
    plan_field: str,
) -> list[ConfirmedPiCell]:
    """Materialize plan-resolved Pi cells without discovering launch inputs."""
    planned_cells = document.get(plan_field)
    if not isinstance(planned_cells, list):
        raise TypeError(
            f"Confirmed Pi execution cells invalid: {plan_field} must be a list"
        )
    cells: list[ConfirmedPiCell] = []
    for index, cell_document in enumerate(planned_cells):
        if not isinstance(cell_document, Mapping):
            raise TypeError(
                "Confirmed Pi execution cell invalid: "
                f"{plan_field}[{index}] must be an object"
            )
        cells.append(
            _confirmed_pi_cell(
                document,
                cast(Mapping[str, object], cell_document),
            )
        )
    return cells


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


def _confirmed_launch_log_path(state_path: Path) -> Path:
    """Return the searchable structured-state log for a confirmed launch."""
    return state_path / "logs" / "confirmed-pi-cell.log"


def _confirmed_state_cell(
    state_path: Path,
    cell: ConfirmedPiCell,
) -> dict[str, object]:
    """Project one plan-resolved cell into structured run state."""
    return run_state.make_cell(
        task=cell.task,
        config=cell.config_identity,
        rep=cell.rep,
        result_path=cell.result_path,
        log_path=_confirmed_launch_log_path(state_path),
        contract_path=(
            str(cell.smoke_contract)
            if cell.smoke_contract is not None
            else None
        ),
    )


def _confirmed_run_manifest(
    document: LaunchPlanDocument,
    batch_cells: Sequence[ConfirmedPiCell],
    preflight_cells: Sequence[ConfirmedPiCell],
    state_path: Path,
) -> dict[str, object]:
    manifest = run_state.base_manifest(
        run_id=document["runId"],
        command=["execute_confirmed_launch", document["planIdentity"]],
        cwd=document["paths"]["workspace"],
        model=document["model"],
        thinking=document["thinking"],
        configs=[config["identity"] for config in document["configs"]],
        selection=dict(document["selection"]),
        runs=int(document["counts"]["reps"]),
        workers=int(document["concurrency"]),
        agent="pi",
        agent_timeout_s=None,
        rpc_quiescence_s=None,
        progress_interval_s=None,
        batch_cells=[
            _confirmed_state_cell(state_path, cell) for cell in batch_cells
        ],
        preflight=[
            _confirmed_state_cell(state_path, cell) for cell in preflight_cells
        ],
    )
    manifest.update(
        {
            "launch_plan_identity": document["planIdentity"],
            "launch_plan_path": "launch-plan.json",
        }
    )
    return manifest


def _append_confirmed_cell_log(
    log_path: Path,
    cell: ConfirmedPiCell,
    message: str,
) -> None:
    """Append one cell-attributed message to the confirmed launch log."""
    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(
            f"cell={cell.task}/{cell.config_identity}/rep{cell.rep} {message}\n"
        )


def _config_lock_drift_changes(
    document: LaunchPlanDocument,
) -> list[dict[str, object]]:
    """Compare every approved config lock with its current document."""
    changes: list[dict[str, object]] = []
    for config in document["configs"]:
        approved_identity = config["lockIdentity"]
        lock_path = Path(config["configLeaf"]) / "config-lock.json"
        resolved = config_resolution.ResolvedConfigLeaf(
            config_root=Path(config["configRoot"]),
            config_leaf=Path(config["configLeaf"]),
            smoke_contract=(
                Path(config["smokeContract"])
                if config["smokeContract"] is not None
                else None
            ),
        )
        observed_identity: object = None
        try:
            verification = config_lock.verify_config_lock(
                resolved,
                config["identity"],
            )
            observed_identity = verification.lock_identity
            if observed_identity == approved_identity:
                continue
        except (OSError, TypeError, ValueError):
            if lock_path.is_file():
                observed_identity = (
                    "sha256:"
                    + hashlib.sha256(lock_path.read_bytes()).hexdigest()
                )
        changes.append(
            {
                "approvedIdentity": approved_identity,
                "category": "config-lock",
                "input": config["identity"],
                "observedIdentity": observed_identity,
            }
        )
    return changes


def _launch_input_mapping_identity(
    value: Mapping[str, object] | None,
) -> str | None:
    """Identify a complete structured launch input, including file mode."""
    if value is None:
        return None
    digest = hashlib.sha256(canonical_launch_plan_json(value).encode())
    return f"sha256:{digest.hexdigest()}"


def _config_input_drift_changes(
    document: LaunchPlanDocument,
) -> list[dict[str, object]]:
    """Compare every approved config input with its current fingerprint."""
    changes: list[dict[str, object]] = []
    for config in document["configs"]:
        resolved = config_resolution.ResolvedConfigLeaf(
            config_root=Path(config["configRoot"]),
            config_leaf=Path(config["configLeaf"]),
            smoke_contract=(
                Path(config["smokeContract"])
                if config["smokeContract"] is not None
                else None
            ),
        )
        approved_by_path = {
            str(item["path"]): item for item in config["behaviorInputs"]
        }
        observed_by_path = {
            str(item["path"]): item
            for item in config_lock.collect_config_behavior_inputs(resolved)
        }
        all_input_paths = sorted(set(approved_by_path) | set(observed_by_path))
        for input_path in all_input_paths:
            approved = approved_by_path.get(input_path)
            observed = observed_by_path.get(input_path)
            approved_identity = _launch_input_mapping_identity(approved)
            observed_identity = _launch_input_mapping_identity(observed)
            if approved != observed:
                changes.append(
                    {
                        "approvedIdentity": approved_identity,
                        "category": "config-input",
                        "config": config["identity"],
                        "input": input_path,
                        "observedIdentity": observed_identity,
                    }
                )
    return changes


def _confirmed_launch_request(
    document: LaunchPlanDocument,
) -> LaunchRequest:
    """Reconstruct only the resolved request needed for runtime observation."""
    selection = document["selection"]
    policies = document["policies"]
    selected_tasks = selection.get("tasks")
    selection_kind = selection.get("kind")
    selection_name = selection.get("name")
    if not isinstance(selected_tasks, list) or not all(
        isinstance(task, str) for task in selected_tasks
    ):
        raise TypeError(
            "Confirmed launch selection invalid: tasks must be strings"
        )
    if not isinstance(selection_kind, str):
        raise TypeError(
            "Confirmed launch selection invalid: kind must be a string"
        )
    if selection_name is not None and not isinstance(selection_name, str):
        raise TypeError(
            "Confirmed launch selection invalid: name must be a string"
        )
    preflight = policies.get("preflight")
    existing_results = policies.get("existing_results")
    transient_errors = policies.get("transient_errors")
    cell_retries = policies.get("cell_retries")
    if not all(
        isinstance(policy, str)
        for policy in (preflight, existing_results, transient_errors)
    ) or not isinstance(cell_retries, int):
        raise TypeError(
            "Confirmed launch policies invalid: expected resolved values"
        )
    return LaunchRequest(
        subject=document["subject"]["name"],
        model=document["model"],
        thinking=document["thinking"],
        configs=tuple(config["identity"] for config in document["configs"]),
        baseline_config=document["baselineConfig"],
        task_selection=LaunchTaskSelection(
            kind=selection_kind,
            tasks=tuple(cast(list[str], selected_tasks)),
            name=selection_name,
        ),
        reps=document["counts"]["reps"],
        concurrency=document["concurrency"],
        run_id=document["runId"],
        policies=LaunchExecutionPolicies(
            preflight=cast(str, preflight),
            existing_results=cast(str, existing_results),
            transient_errors=cast(str, transient_errors),
            cell_retries=cell_retries,
        ),
    )


def _runtime_input_drift_changes(
    document: LaunchPlanDocument,
    runtime_resolver: LaunchRuntimeResolver,
) -> list[dict[str, object]]:
    """Resolve and compare every runtime identity approved by the plan."""
    request = _confirmed_launch_request(document)
    tasks = request.task_selection.tasks
    approved = document["runtime"]
    try:
        observed = runtime_resolver.resolve_launch_runtime(request, tasks)
    except (OSError, RuntimeError, TypeError, ValueError) as error:
        approved_identity = hashlib.sha256(
            canonical_launch_plan_json(approved).encode()
        ).hexdigest()
        return [
            {
                "approvedIdentity": f"sha256:{approved_identity}",
                "category": "runtime-identity-resolution",
                "detail": f"{type(error).__name__}: {error}",
                "input": "runtime-identities",
                "observedIdentity": None,
            }
        ]
    changes: list[dict[str, object]] = []

    def compare(
        category: str,
        input_name: str,
        approved_identity: object,
        observed_identity: object,
    ) -> None:
        if approved_identity != observed_identity:
            changes.append(
                {
                    "approvedIdentity": approved_identity,
                    "category": category,
                    "input": input_name,
                    "observedIdentity": observed_identity,
                }
            )

    compare(
        "subject-version",
        document["subject"]["name"],
        document["subject"]["version"],
        observed.subject_version,
    )
    compare(
        "harness-revision",
        document["paths"]["workspace"],
        approved["harnessRevision"],
        observed.harness_revision,
    )
    compare(
        "task-revision",
        "selected-tasks",
        approved["taskRevision"],
        observed.task_revision,
    )
    for task in sorted(tasks):
        compare(
            "verifier-identity",
            task,
            approved["verifierIdentities"].get(task),
            observed.verifier_identities.get(task),
        )
        approved_images = approved["immutableImageIdentities"].get(task, {})
        observed_images = observed.immutable_image_identities.get(task, {})
        for image_name in sorted(set(approved_images) | set(observed_images)):
            compare(
                "immutable-image-identity",
                f"{task}:{image_name}",
                approved_images.get(image_name),
                observed_images.get(image_name),
            )
    return changes


class _ApprovedLaunchInputVerifier:
    """Stop runner submissions when current inputs differ from the plan."""

    def __init__(
        self,
        document: LaunchPlanDocument,
        state: run_state.RunStateWriter,
        runtime_resolver: LaunchRuntimeResolver,
    ) -> None:
        self.document = document
        self.state = state
        self.runtime_resolver = runtime_resolver

    def require_unchanged_before_rep(self, cell: ConfirmedPiCell) -> None:
        """Recheck before every submission, including resumed or retried reps."""
        changes = _config_input_drift_changes(self.document)
        changes.extend(_config_lock_drift_changes(self.document))
        changes.extend(
            _runtime_input_drift_changes(
                self.document,
                self.runtime_resolver,
            )
        )
        if not changes:
            return
        state_cell = _confirmed_state_cell(self.state.run_dir, cell)
        self.state.launch_input_drift(
            pending_cell_id=str(state_cell["cell_id"]),
            changes=changes,
        )
        raise LaunchInputDriftError(
            "Launch input drift: approved inputs changed before "
            f"{state_cell['cell_id']}"
        )


def _run_confirmed_pi_cell(
    cell: ConfirmedPiCell,
    pi_runner: ConfirmedPiRunner,
    log_path: Path,
) -> dict[str, object]:
    """Run one exact planned cell and persist its provenance-bearing result."""
    cell.result_path.parent.mkdir(parents=True, exist_ok=True)
    _append_confirmed_cell_log(log_path, cell, "started")
    runner_record = pi_runner.run_confirmed_pi_cell(cell)
    result_record = _confirmed_result_record(cell, runner_record)
    run_state.atomic_write_json(cell.result_path, result_record)
    _append_confirmed_cell_log(log_path, cell, "completed")
    return result_record


def _execute_confirmed_preflight_cell(
    cell: ConfirmedPiCell,
    state_path: Path,
    state: run_state.RunStateWriter,
    input_verifier: _ApprovedLaunchInputVerifier,
    pi_runner: ConfirmedPiRunner,
    log_path: Path,
) -> bool:
    """Run and atomically decide one confirmed preflight cell."""
    state_cell = _confirmed_state_cell(state_path, cell)
    input_verifier.require_unchanged_before_rep(cell)
    state.preflight_started(state_cell)
    diagnostics: list[confirmed_preflight.PreflightDiagnostic] = []
    result_record: dict[str, object] = {}
    exit_code: int | str | None = None
    reused_result = cell.reuse_reason is not None
    try:
        if reused_result:
            _require_planned_result_reuse(cell)
            result_record = dict(
                result_provenance.read_result_record(cell.result_path)
            )
        else:
            result_record = _run_confirmed_pi_cell(cell, pi_runner, log_path)
        raw_exit = result_record.get("agent_exit")
        exit_code = raw_exit if isinstance(raw_exit, int | str) else None
    except Exception as error:  # noqa: BLE001 - runner boundary records failure
        exit_code = "exception"
        diagnostics.append(
            confirmed_preflight.preflight_diagnostic(
                "subject_cell",
                "runner",
                f"{type(error).__name__}: {error}",
            )
        )
        _append_confirmed_cell_log(
            log_path,
            cell,
            f"failed: {type(error).__name__}: {error}",
        )
    cell_root = cell.result_path.parent
    diagnostics.extend(
        confirmed_preflight.evaluate_generic_preflight(cell_root, result_record)
    )
    diagnostics.extend(
        confirmed_preflight.evaluate_config_preflight(
            cell.config_root.parent.parent,
            cell_root,
            cell.smoke_contract,
            result_record,
        )
    )
    passed = not diagnostics
    if passed and not reused_result:
        result_record["preflight_passed"] = True
        run_state.atomic_write_json(cell.result_path, result_record)
    state.preflight_finished(
        state_cell,
        result_path=(cell.result_path if cell.result_path.is_file() else None),
        log_path=log_path,
        exit_code=exit_code,
        diagnostics=[dict(diagnostic) for diagnostic in diagnostics],
    )
    return passed


def _execute_confirmed_preflights(
    cells: Sequence[ConfirmedPiCell],
    state_path: Path,
    state: run_state.RunStateWriter,
    input_verifier: _ApprovedLaunchInputVerifier,
    pi_runner: ConfirmedPiRunner,
    log_path: Path,
) -> set[Path]:
    """Run every planned preflight and stop before batch on any failure."""
    passed_paths: set[Path] = set()
    failed_count = 0
    for cell in cells:
        if _execute_confirmed_preflight_cell(
            cell,
            state_path,
            state,
            input_verifier,
            pi_runner,
            log_path,
        ):
            passed_paths.add(cell.result_path.resolve())
        else:
            failed_count += 1
    if failed_count:
        state.run_failed(
            reason=(
                "Confirmed launch preflight failed: "
                f"{failed_count} cell(s) did not satisfy requirements"
            )
        )
        raise LaunchPreflightError(
            "Confirmed launch preflight failed: batch fan-out was not started"
        )
    return passed_paths


def _execute_confirmed_batch_cell(
    cell: ConfirmedPiCell,
    state_path: Path,
    state: run_state.RunStateWriter,
    input_verifier: _ApprovedLaunchInputVerifier,
    pi_runner: ConfirmedPiRunner,
    log_path: Path,
) -> None:
    """Run one planned batch cell and record its durable outcome."""
    state_cell = _confirmed_state_cell(state_path, cell)
    input_verifier.require_unchanged_before_rep(cell)
    state.cell_started(state_cell)
    try:
        result_record = _run_confirmed_pi_cell(cell, pi_runner, log_path)
    except Exception as error:
        _append_confirmed_cell_log(
            log_path,
            cell,
            f"failed: {type(error).__name__}: {error}",
        )
        state.cell_finished(
            state_cell,
            log_path=log_path,
            exit_code="exception",
        )
        state.run_failed(reason="Confirmed Pi cell execution failed")
        raise
    raw_exit = result_record.get("agent_exit")
    exit_code = raw_exit if isinstance(raw_exit, int | str) else None
    state.cell_finished(
        state_cell,
        result_path=cell.result_path,
        log_path=log_path,
        exit_code=exit_code,
    )


def _require_planned_result_reuse(cell: ConfirmedPiCell) -> None:
    """Require the exact result bytes and provenance approved by the plan."""
    if (
        cell.reuse_provenance is None
        or cell.reuse_result_identity is None
        or not cell.result_path.is_file()
    ):
        raise ValueError(
            f"Result provenance mismatch: path={cell.result_path}; "
            "planned reusable result is missing"
        )
    record = result_provenance.read_result_record(cell.result_path)
    mismatches: dict[str, object] = dict(
        result_provenance.result_provenance_mismatches(
            record,
            cell.reuse_provenance,
        )
    )
    recorded_identity = result_provenance.result_file_identity(cell.result_path)
    if recorded_identity != cell.reuse_result_identity:
        mismatches["result_identity"] = {
            "expected": cell.reuse_result_identity,
            "recorded": recorded_identity,
        }
    if mismatches:
        raise ValueError(
            f"Result provenance mismatch: path={cell.result_path}; "
            f"incompatible fields={mismatches!r}"
        )


def _execute_confirmed_batch(
    cells: Sequence[ConfirmedPiCell],
    passed_preflight_paths: set[Path],
    state_path: Path,
    state: run_state.RunStateWriter,
    input_verifier: _ApprovedLaunchInputVerifier,
    pi_runner: ConfirmedPiRunner,
    log_path: Path,
) -> None:
    """Fan out every planned batch cell once after atomic preflight."""
    for cell in cells:
        state_cell = _confirmed_state_cell(state_path, cell)
        if cell.result_path.resolve() in passed_preflight_paths:
            state.cell_skipped(state_cell, reason="successful_preflight")
            continue
        if cell.reuse_reason is not None:
            try:
                _require_planned_result_reuse(cell)
            except (OSError, TypeError, ValueError) as error:
                _append_confirmed_cell_log(
                    log_path,
                    cell,
                    f"failed: {type(error).__name__}: {error}",
                )
                state.run_failed(reason=str(error))
                raise
            state.cell_skipped(state_cell, reason=cell.reuse_reason)
            continue
        _execute_confirmed_batch_cell(
            cell,
            state_path,
            state,
            input_verifier,
            pi_runner,
            log_path,
        )


def execute_confirmed_launch(
    plan: LaunchPlan,
    *,
    confirmation_identity: str | None,
    runtime_resolver: LaunchRuntimeResolver,
    pi_runner: ConfirmedPiRunner,
) -> ConfirmedLaunchExecution:
    """Execute atomic preflight and conditional fan-out for one exact plan."""
    document = _confirmed_plan_document(plan, confirmation_identity)
    batch_cells = _confirmed_pi_cells(document, "batchCells")
    preflight_cells = _confirmed_pi_cells(document, "preflightCells")
    if not batch_cells:
        raise ValueError("Confirmed Pi execution cells invalid: batch is empty")
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
    manifest = _confirmed_run_manifest(
        document,
        batch_cells,
        preflight_cells,
        state_path,
    )
    state = run_state.RunStateWriter(document["paths"]["stateRoot"], manifest)
    state.start()
    (state_path / "launch-plan.json").write_text(plan.canonical_json)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    log_path.write_text(
        "Confirmed Pi cell execution\n"
        f"launch_plan_identity={document['planIdentity']}\n"
    )
    input_verifier = _ApprovedLaunchInputVerifier(
        document,
        state,
        runtime_resolver,
    )

    passed_preflight_paths = _execute_confirmed_preflights(
        preflight_cells,
        state_path,
        state,
        input_verifier,
        pi_runner,
        log_path,
    )
    _execute_confirmed_batch(
        batch_cells,
        passed_preflight_paths,
        state_path,
        state,
        input_verifier,
        pi_runner,
        log_path,
    )
    state.run_completed()
    return ConfirmedLaunchExecution(
        result_path=batch_cells[0].result_path,
        state_path=state_path,
        log_path=log_path,
    )
