"""Public types and interfaces for compiled benchmark launches."""

from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import NotRequired, Protocol, TypedDict, cast

from harness import run_state


class LaunchClarificationError(ValueError):
    """Stop planning when model behavior remains unresolved."""

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


class LaunchTransientModelError(RuntimeError):
    """Pause a confirmed run after a transient provider or quota failure."""


class LaunchResourceHaltError(RuntimeError):
    """Pause a confirmed run after its host resource supervisor intervenes."""


class LaunchVerifierResourceError(RuntimeError):
    """Retry a rep whose verifier exhausted its confirmed memory budget."""


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
    smokeAssertions: dict[str, object] | None
    smokeContract: str | None
    subjectBehavior: NotRequired[dict[str, object]]
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
    """Exact workspace, task, result, and structured-state launch paths."""

    resultsRoot: str
    statePath: str
    stateRoot: str
    tasksRoot: str
    workspace: str


class LaunchResourceDocument(TypedDict):
    """Confirmed container and host memory limits measured in GiB."""

    additional_swap_gib: float
    host_reserve_gib: float
    subject_memory_gib: float
    verifier_memory_gib: float


class LaunchRuntimeDocument(TypedDict):
    """Exact harness, task, verifier, and immutable image identities."""

    harnessRevision: str
    hostMemoryBytes: int
    immutableImageIdentities: dict[str, dict[str, str]]
    taskRevision: str
    taskRevisionAliases: dict[str, list[str]]
    verifierIdentities: dict[str, str]


class LaunchSubjectDocument(TypedDict):
    """Resolved subject runner and exact subject version."""

    name: str
    runner: str
    runtimeIdentity: NotRequired[dict[str, object]]
    version: str


class LaunchPlanDocument(TypedDict):
    """Versioned canonical launch behavior and explicitly volatile metadata."""

    schemaVersion: int
    baselineConfig: str
    batchCells: list[dict[str, object]]
    comparisonBaseline: LaunchConfigDocument
    concurrency: int
    configs: list[LaunchConfigDocument]
    counts: LaunchCountsDocument
    identityExclusions: list[str]
    model: str
    paths: LaunchPathsDocument
    planIdentity: str
    policies: dict[str, object]
    preflightCells: list[dict[str, object]]
    resources: LaunchResourceDocument
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
class LaunchResourcePolicy:
    """Bound aggregate container memory and preserve host headroom."""

    subject_memory_gib: float = 12.0
    verifier_memory_gib: float = 12.0
    additional_swap_gib: float = 0.0
    host_reserve_gib: float = 12.0


@dataclass(frozen=True, slots=True)
class LaunchExecutionPolicies:
    """Freeze every behavior-changing execution policy in the launch plan."""

    preflight: str
    existing_results: str
    transient_errors: str
    cell_retries: int
    agent_timeout_s: float | None = None
    rpc_quiescence_s: float = 2.0
    capture_initial_context: bool = True
    auto_resume: bool = True
    max_quota_wait_s: float = 21600.0
    quota_poll_s: float = 300.0
    rate_limit_backoff_s: float = 60.0


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
    resources: LaunchResourcePolicy = LaunchResourcePolicy()
    reuse_decisions: tuple[ExplicitResultReuseDecision, ...] = ()


@dataclass(frozen=True, slots=True)
class LaunchRuntimeIdentity:
    """Record model-free runtime provenance resolved for selected tasks."""

    subject_version: str
    harness_revision: str
    task_revision: str
    verifier_identities: Mapping[str, str]
    immutable_image_identities: Mapping[str, Mapping[str, str]]
    host_memory_bytes: int
    task_revision_aliases: Mapping[str, frozenset[str]] = field(default_factory=dict)
    subject_capabilities: frozenset[str] = frozenset()
    available_credential_routes: frozenset[str] = frozenset()
    subject_runtime_identity: Mapping[str, object] = field(default_factory=dict)


class LaunchRuntimeResolver(Protocol):
    """Resolve exact runtime identities without starting a subject process."""

    def resolve_launch_runtime(
        self,
        request: LaunchRequest,
        tasks: tuple[str, ...],
    ) -> LaunchRuntimeIdentity:
        """Return runtime identities for a launch request and its tasks."""


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
class ConfirmedSubjectCell:
    """Supply one subject runner with only confirmed, plan-resolved behavior."""

    agent_timeout_s: float | None
    capture_initial_context: bool
    config_identity: str
    config_lock_identity: str
    config_root: Path
    config_leaf: Path
    credential_routes: tuple[str, ...]
    smoke_assertions: Mapping[str, object] | None
    smoke_contract: Path | None
    task: str
    rep: int
    model: str
    thinking: str
    result_path: Path
    rpc_quiescence_s: float
    run_key: str
    state_path: Path
    subject: str
    subject_behavior: Mapping[str, object]
    subject_runner: Path
    subject_runtime_identity: Mapping[str, object]
    subject_version: str
    harness_revision: str
    task_revision: str
    verifier_identity: str
    immutable_image_identities: Mapping[str, str]
    launch_plan_identity: str
    resources: LaunchResourcePolicy
    reuse_provenance: Mapping[str, object] | None
    reuse_reason: str | None
    reuse_result_identity: str | None


ConfirmedPiCell = ConfirmedSubjectCell
ConfirmedOmpCell = ConfirmedSubjectCell


class ConfirmedPiRunner(Protocol):
    """Execute one plan-resolved Pi cell without resolving launch inputs."""

    def run_confirmed_pi_cell(
        self,
        cell: ConfirmedPiCell,
    ) -> Mapping[str, object]:
        """Return one complete result record without writing result.json."""


class ConfirmedOmpRunner(Protocol):
    """Execute one plan-resolved OMP cell without resolving launch inputs."""

    def run_confirmed_omp_cell(
        self,
        cell: ConfirmedOmpCell,
    ) -> Mapping[str, object]:
        """Return one complete result record without writing result.json."""


class LaunchTransientResumer(Protocol):
    """Wait for a transient condition without changing a confirmed plan."""

    def on_transient_pause(
        self,
        state: run_state.RunStateWriter,
    ) -> Mapping[str, object]:
        """Return a retry decision after any required model-free wait."""


_ConfirmedSubjectRunner = ConfirmedPiRunner | ConfirmedOmpRunner


@dataclass(frozen=True, slots=True)
class ConfirmedLaunchExecution:
    """Identify durable artifacts produced by one confirmed cell execution."""

    result_path: Path
    state_path: Path
    log_path: Path
