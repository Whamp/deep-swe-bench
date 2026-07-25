"""Compile model-free batch launch requests into immutable review artifacts."""

from __future__ import annotations

import hashlib
import json
import re
import subprocess
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Protocol, TypedDict, cast

from harness import config_lock, config_resolution, lib
from harness.run_state import sanitize_run_id

_LAUNCH_PLAN_SCHEMA_VERSION = 1
_THINKING_LEVELS = frozenset(
    {"off", "minimal", "low", "medium", "high", "xhigh"}
)
_PREFLIGHT_POLICIES = frozenset({"disabled", "new-configs", "required"})
_EXISTING_RESULT_POLICIES = frozenset({"require-compatible", "rerun"})
_TRANSIENT_ERROR_POLICIES = frozenset({"pause", "stop"})


class LaunchConfigDocument(TypedDict):
    """Resolved config fields stored in a canonical launch plan."""

    behaviorInputs: list[dict[str, object]]
    configLeaf: str
    configRoot: str
    credentialRoutes: list[str]
    declaredRoles: list[dict[str, object]]
    identity: str
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
    lock_document = config_lock.read_matching_config_lock(
        resolved,
        config_identity,
    )
    if lock_document is None:
        return {
            "behaviorInputs": [],
            "configLeaf": str(resolved.config_leaf.resolve()),
            "configRoot": str(resolved.config_root.resolve()),
            "credentialRoutes": [],
            "declaredRoles": [],
            "identity": config_identity,
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
    version_impact = lock_document.get("versionImpact")
    if version_impact is not None and not isinstance(version_impact, str):
        raise TypeError(
            "Config lock invalid: versionImpact must be a string or null"
        )
    lock_identity = lock_document.get("lockIdentity")
    if not isinstance(lock_identity, str):
        raise TypeError("Config lock invalid: lockIdentity must be a string")
    return {
        "behaviorInputs": _lock_object_list(lock_document, "behaviorInputs"),
        "configLeaf": str(resolved.config_leaf.resolve()),
        "configRoot": str(resolved.config_root.resolve()),
        "credentialRoutes": _lock_string_list(
            lock_document, "credentialRoutes"
        ),
        "declaredRoles": _lock_object_list(lock_document, "declaredRoles"),
        "identity": config_identity,
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
        "usageSources": _lock_string_list(lock_document, "usageSources"),
        "versionImpact": version_impact,
    }


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


def _render_role_lines(configs: Sequence[LaunchConfigDocument]) -> list[str]:
    lines = [
        "config | role | provider | model | thinking | credential | "
        "billing | usage"
    ]
    for config in configs:
        roles = config["declaredRoles"]
        usage = ",".join(config["usageSources"])
        if not roles:
            lines.append(
                f"{config['identity']} | undeclared | - | - | - | - | "
                f"- | {usage or '-'}"
            )
            continue
        for role in roles:
            if not isinstance(role, dict):
                continue
            lines.append(
                " | ".join(
                    [
                        str(config["identity"]),
                        str(role.get("name", "-")),
                        str(role.get("provider", "-")),
                        str(role.get("model", "-")),
                        str(role.get("thinking", "-")),
                        str(role.get("credentialRoute", "-")),
                        str(role.get("billingCategory", "-")),
                        usage or "-",
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
