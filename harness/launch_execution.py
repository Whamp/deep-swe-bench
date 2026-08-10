"""Execute one confirmed launch plan without rediscovering approved behavior."""

from __future__ import annotations

import concurrent.futures
import hashlib
import json
import threading
import uuid
from collections.abc import Iterable, Iterator, Mapping, Sequence
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import cast

from harness import (
    config_lock,
    config_resolution,
    confirmed_preflight,
    result_provenance,
    run_state,
)
from harness.container_resources import (
    container_memory_result_fields,
    read_resource_halt_reason,
)
from harness.launch_contract import (
    ConfirmedLaunchExecution,
    ConfirmedOmpRunner,
    ConfirmedPiRunner,
    ConfirmedPrimeAgentRunner,
    ConfirmedSubjectCell,
    LaunchExecutionPolicies,
    LaunchInputDriftError,
    LaunchPlan,
    LaunchPlanDocument,
    LaunchPreflightError,
    LaunchRequest,
    LaunchResourceHaltError,
    LaunchResourcePolicy,
    LaunchRuntimeResolver,
    LaunchTaskSelection,
    LaunchTransientModelError,
    LaunchTransientResumer,
    LaunchVerifierResourceError,
    _ConfirmedSubjectRunner,
)
from harness.launch_planning import (
    _validate_launch_policies,
    _validate_launch_resources,
    canonical_launch_plan_json,
    confirmed_launch_run_key,
    parse_launch_plan_json,
)


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
    document = parsed_plan.to_document()
    legacy_configs = [
        config["identity"] for config in document["configs"] if config["legacy"]
    ]
    if legacy_configs:
        raise ValueError(
            "Confirmed config release required: legacy configs are "
            "diagnostic-only until versioned and locked; configs="
            f"{legacy_configs!r}"
        )
    return document


def _confirmed_subject_cell(
    document: LaunchPlanDocument,
    cell_document: Mapping[str, object],
) -> ConfirmedSubjectCell:
    subject = document["subject"]
    if subject["name"] not in {"pi", "omp", "prime-agent"}:
        raise ValueError(
            "Confirmed subject execution mismatch: "
            f"unsupported subject {subject['name']!r}"
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
            "Confirmed subject execution cell invalid: config, task, rep, and "
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
            "Confirmed subject execution config missing: "
            f"plan has no config document for {config_identity!r}"
        )
    lock_identity = config_document["lockIdentity"]
    if not isinstance(lock_identity, str):
        raise TypeError(
            "Confirmed subject execution config provenance missing: "
            f"config={config_identity!r}"
        )
    verifier_identity = document["runtime"]["verifierIdentities"].get(task)
    image_identities = document["runtime"]["immutableImageIdentities"].get(task)
    if not isinstance(verifier_identity, str) or not isinstance(
        image_identities,
        dict,
    ):
        raise TypeError(f"Confirmed subject execution runtime missing: task={task!r}")
    smoke_assertions = config_document["smokeAssertions"]
    if smoke_assertions is not None and not isinstance(
        smoke_assertions,
        Mapping,
    ):
        raise TypeError(
            "Confirmed smoke assertions invalid: expected an object or null"
        )
    smoke_contract = config_document["smokeContract"]
    subject_behavior = config_document.get("subjectBehavior", {})
    subject_runtime_identity = subject.get("runtimeIdentity", {})
    if not isinstance(subject_behavior, Mapping) or not isinstance(
        subject_runtime_identity,
        Mapping,
    ):
        raise TypeError(
            "Confirmed subject execution behavior invalid: expected objects"
        )
    if subject["name"] == "omp" and not subject_behavior:
        raise ValueError(
            "Confirmed OMP execution behavior missing: plan has no resolved "
            f"behavior for {config_identity!r}"
        )
    policies = _confirmed_launch_request(document).policies
    credential_routes = config_document["credentialRoutes"]
    if not isinstance(credential_routes, list) or not all(
        isinstance(route, str) for route in credential_routes
    ):
        raise TypeError("Confirmed subject credential routes invalid: expected strings")
    return ConfirmedSubjectCell(
        agent_timeout_s=policies.agent_timeout_s,
        capture_initial_context=policies.capture_initial_context,
        config_identity=config_identity,
        config_lock_identity=lock_identity,
        config_root=Path(config_document["configRoot"]),
        config_leaf=Path(config_document["configLeaf"]),
        credential_routes=tuple(credential_routes),
        smoke_assertions=(
            dict(smoke_assertions) if isinstance(smoke_assertions, Mapping) else None
        ),
        smoke_contract=(Path(smoke_contract) if smoke_contract is not None else None),
        task=task,
        rep=rep,
        model=document["model"],
        thinking=document["thinking"],
        result_path=Path(result_path),
        rpc_quiescence_s=policies.rpc_quiescence_s,
        run_key=Path(document["paths"]["statePath"]).name,
        state_path=Path(document["paths"]["statePath"]),
        subject=subject["name"],
        subject_behavior=dict(subject_behavior),
        subject_runner=Path(subject["runner"]),
        subject_runtime_identity=dict(subject_runtime_identity),
        subject_version=subject["version"],
        harness_revision=document["runtime"]["harnessRevision"],
        task_revision=str(
            cell_document.get(
                "taskRevision",
                document["runtime"]["taskRevision"],
            )
        ),
        verifier_identity=verifier_identity,
        immutable_image_identities={
            str(name): str(identity) for name, identity in image_identities.items()
        },
        launch_plan_identity=document["planIdentity"],
        resources=_confirmed_launch_request(document).resources,
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


def _confirmed_subject_cells(
    document: LaunchPlanDocument,
    plan_field: str,
) -> list[ConfirmedSubjectCell]:
    """Materialize plan-resolved cells without discovering launch inputs."""
    planned_cells = document.get(plan_field)
    if not isinstance(planned_cells, list):
        raise TypeError(
            f"Confirmed subject execution cells invalid: {plan_field} must be a list"
        )
    cells: list[ConfirmedSubjectCell] = []
    for index, cell_document in enumerate(planned_cells):
        if not isinstance(cell_document, Mapping):
            raise TypeError(
                "Confirmed subject execution cell invalid: "
                f"{plan_field}[{index}] must be an object"
            )
        structured_cell = cast(Mapping[str, object], cell_document)
        cells.append(_confirmed_subject_cell(document, structured_cell))
    return cells


def _confirmed_cell_provenance(
    cell: ConfirmedSubjectCell,
) -> result_provenance.ConfirmedResultProvenance:
    """Map one confirmed cell to the exact provenance written and resumed."""
    provenance: result_provenance.ConfirmedResultProvenance = {
        "config": cell.config_identity,
        "config_lock_identity": cell.config_lock_identity,
        "harness_revision": cell.harness_revision,
        "immutable_image_identities": dict(cell.immutable_image_identities),
        "launch_plan_identity": cell.launch_plan_identity,
        "model": cell.model,
        "rep": cell.rep,
        "resource_policy": asdict(cell.resources),
        "subject": cell.subject,
        "subject_version": cell.subject_version,
        "task": cell.task,
        "task_revision": cell.task_revision,
        "thinking_level": cell.thinking,
        "verifier_identity": cell.verifier_identity,
    }
    if cell.subject_runtime_identity:
        provenance["subject_runtime_identity"] = dict(cell.subject_runtime_identity)
    return provenance


def _confirmed_result_record(
    cell: ConfirmedSubjectCell,
    record: Mapping[str, object],
) -> dict[str, object]:
    config_identity = config_resolution.parse_versioned_config_identity(
        cell.config_identity
    )
    if config_identity is None:
        raise ValueError(
            "Confirmed subject execution config version missing: "
            f"config={cell.config_identity!r}"
        )
    return {
        **record,
        **_confirmed_cell_provenance(cell),
        "config_name": config_identity.name,
        "config_version": config_identity.version,
    }


def _confirmed_launch_log_path(state_path: Path, subject: str) -> Path:
    """Return the searchable structured-state log for a confirmed launch."""
    return state_path / "logs" / f"confirmed-{subject}-cell.log"


def _confirmed_state_cell(
    state_path: Path,
    cell: ConfirmedSubjectCell,
) -> dict[str, object]:
    """Project one plan-resolved cell into structured run state."""
    return run_state.make_cell(
        task=cell.task,
        config=cell.config_identity,
        rep=cell.rep,
        result_path=cell.result_path,
        log_path=_confirmed_launch_log_path(state_path, cell.subject),
        contract_path=(
            str(cell.smoke_contract) if cell.smoke_contract is not None else None
        ),
    )


def _confirmed_run_manifest(
    document: LaunchPlanDocument,
    batch_cells: Sequence[ConfirmedSubjectCell],
    preflight_cells: Sequence[ConfirmedSubjectCell],
    state_path: Path,
) -> dict[str, object]:
    policies = _confirmed_launch_request(document).policies
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
        agent=document["subject"]["name"],
        agent_timeout_s=policies.agent_timeout_s,
        rpc_quiescence_s=policies.rpc_quiescence_s,
        progress_interval_s=None,
        batch_cells=[_confirmed_state_cell(state_path, cell) for cell in batch_cells],
        preflight=[_confirmed_state_cell(state_path, cell) for cell in preflight_cells],
    )
    manifest.update(
        {
            "capture_initial_context": policies.capture_initial_context,
            "config_identities": [config["identity"] for config in document["configs"]],
            "launch_plan_identity": document["planIdentity"],
            "launch_plan_path": "launch-plan.json",
            "resources": dict(document["resources"]),
            "results_root": document["paths"]["resultsRoot"],
            "run_key": state_path.name,
            "state_root": document["paths"]["stateRoot"],
            "workspace": document["paths"]["workspace"],
        }
    )
    return manifest


def _append_confirmed_cell_log(
    log_path: Path,
    cell: ConfirmedSubjectCell,
    message: str,
) -> None:
    """Append one cell-attributed message to the confirmed launch log."""
    with log_path.open("a", encoding="utf-8") as log_file:
        log_file.write(
            f"cell={cell.task}/{cell.config_identity}/rep{cell.rep} {message}\n"
        )


def _record_verifier_resource_failure(
    cell: ConfirmedSubjectCell,
    runner_record: Mapping[str, object],
) -> None:
    """Persist infrastructure-invalid verifier evidence outside result.json."""
    evidence_path = (
        cell.result_path.parent / "logs" / "verifier-resource-events.ndjson"
    )
    evidence_path.parent.mkdir(parents=True, exist_ok=True)
    evidence = {
        "cell": f"{cell.task}/{cell.config_identity}/rep{cell.rep}",
        "launch_plan_identity": cell.launch_plan_identity,
        **container_memory_result_fields(runner_record),
    }
    with evidence_path.open("a", encoding="utf-8") as evidence_file:
        evidence_file.write(json.dumps(evidence, sort_keys=True) + "\n")


def _resolved_plan_config_leaf(
    config: Mapping[str, object],
) -> config_resolution.ResolvedConfigLeaf:
    """Reconstruct one config leaf solely from approved plan paths."""
    smoke_contract = config["smokeContract"]
    return config_resolution.ResolvedConfigLeaf(
        config_root=Path(cast(str, config["configRoot"])),
        config_leaf=Path(cast(str, config["configLeaf"])),
        smoke_contract=(
            Path(cast(str, smoke_contract)) if smoke_contract is not None else None
        ),
    )


def _config_lock_drift_changes(
    document: LaunchPlanDocument,
) -> list[dict[str, object]]:
    """Compare every approved config lock with its current document."""
    changes: list[dict[str, object]] = []
    for config in document["configs"]:
        approved_identity = config["lockIdentity"]
        lock_path = Path(config["configLeaf"]) / "config-lock.json"
        resolved = _resolved_plan_config_leaf(config)
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
                    "sha256:" + hashlib.sha256(lock_path.read_bytes()).hexdigest()
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
        resolved = _resolved_plan_config_leaf(config)
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
    resources = document.get("resources")
    if not isinstance(resources, Mapping):
        raise TypeError(
            "Confirmed launch resources invalid: expected a resolved object"
        )
    selected_tasks = selection.get("tasks")
    selection_kind = selection.get("kind")
    selection_name = selection.get("name")
    if not isinstance(selected_tasks, list) or not all(
        isinstance(task, str) for task in selected_tasks
    ):
        raise TypeError("Confirmed launch selection invalid: tasks must be strings")
    if not isinstance(selection_kind, str):
        raise TypeError("Confirmed launch selection invalid: kind must be a string")
    if selection_name is not None and not isinstance(selection_name, str):
        raise TypeError("Confirmed launch selection invalid: name must be a string")
    preflight = policies.get("preflight")
    existing_results = policies.get("existing_results")
    transient_errors = policies.get("transient_errors")
    cell_retries = policies.get("cell_retries")
    agent_timeout_s = policies.get("agent_timeout_s")
    rpc_quiescence_s = policies.get("rpc_quiescence_s")
    capture_initial_context = policies.get("capture_initial_context")
    auto_resume = policies.get("auto_resume")
    max_quota_wait_s = policies.get("max_quota_wait_s")
    quota_poll_s = policies.get("quota_poll_s")
    rate_limit_backoff_s = policies.get("rate_limit_backoff_s")
    subject_memory_gib = resources.get("subject_memory_gib")
    verifier_memory_gib = resources.get("verifier_memory_gib")
    additional_swap_gib = resources.get("additional_swap_gib")
    host_reserve_gib = resources.get("host_reserve_gib")
    resource_values = (
        subject_memory_gib,
        verifier_memory_gib,
        additional_swap_gib,
        host_reserve_gib,
    )
    if any(
        isinstance(value, bool) or not isinstance(value, int | float)
        for value in resource_values
    ):
        raise TypeError(
            "Confirmed launch resources invalid: expected resolved numbers"
        )
    if (
        not all(
            isinstance(policy, str)
            for policy in (preflight, existing_results, transient_errors)
        )
        or isinstance(cell_retries, bool)
        or not isinstance(cell_retries, int)
        or (
            agent_timeout_s is not None
            and (
                isinstance(agent_timeout_s, bool)
                or not isinstance(agent_timeout_s, int | float)
            )
        )
        or isinstance(rpc_quiescence_s, bool)
        or not isinstance(rpc_quiescence_s, int | float)
        or not isinstance(capture_initial_context, bool)
        or not isinstance(auto_resume, bool)
        or isinstance(max_quota_wait_s, bool)
        or not isinstance(max_quota_wait_s, int | float)
        or isinstance(quota_poll_s, bool)
        or not isinstance(quota_poll_s, int | float)
        or isinstance(rate_limit_backoff_s, bool)
        or not isinstance(rate_limit_backoff_s, int | float)
    ):
        raise TypeError("Confirmed launch policies invalid: expected resolved values")
    request = LaunchRequest(
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
            agent_timeout_s=(
                float(agent_timeout_s) if agent_timeout_s is not None else None
            ),
            rpc_quiescence_s=float(rpc_quiescence_s),
            capture_initial_context=capture_initial_context,
            auto_resume=auto_resume,
            max_quota_wait_s=float(max_quota_wait_s),
            quota_poll_s=float(quota_poll_s),
            rate_limit_backoff_s=float(rate_limit_backoff_s),
        ),
        resources=LaunchResourcePolicy(
            subject_memory_gib=float(subject_memory_gib),
            verifier_memory_gib=float(verifier_memory_gib),
            additional_swap_gib=float(additional_swap_gib),
            host_reserve_gib=float(host_reserve_gib),
        ),
    )
    _validate_launch_policies(request)
    _validate_launch_resources(request)
    return request


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
        "subject-runtime-identity",
        document["subject"]["name"],
        document["subject"].get("runtimeIdentity", {}),
        dict(observed.subject_runtime_identity),
    )
    required_capabilities = sorted(
        {
            capability
            for config in document["configs"]
            for capability in config["requiredCapabilities"]
        }
    )
    for capability in required_capabilities:
        compare(
            "subject-capability",
            capability,
            True,
            capability in observed.subject_capabilities,
        )
    credential_routes = sorted(
        {
            route
            for config in document["configs"]
            for route in config["credentialRoutes"]
        }
    )
    for route in credential_routes:
        compare(
            "credential-route",
            route,
            True,
            route in observed.available_credential_routes,
        )
    compare(
        "harness-revision",
        document["paths"]["workspace"],
        approved["harnessRevision"],
        observed.harness_revision,
    )
    compare(
        "host-memory",
        "physical-memory",
        approved["hostMemoryBytes"],
        observed.host_memory_bytes,
    )
    compare(
        "task-revision",
        "selected-tasks",
        approved["taskRevision"],
        observed.task_revision,
    )
    compare(
        "task-revision-aliases",
        "selected-subsets",
        approved.get("taskRevisionAliases", {}),
        {
            revision: sorted(alias_tasks)
            for revision, alias_tasks in sorted(observed.task_revision_aliases.items())
        },
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


def _resource_halt_error(state_path: Path) -> LaunchResourceHaltError | None:
    """Return the durable supervisor halt error for one run, when present."""
    try:
        reason = read_resource_halt_reason(state_path)
    except (TypeError, ValueError) as error:
        return LaunchResourceHaltError(str(error))
    return None if reason is None else LaunchResourceHaltError(reason)


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
        self._verification_lock = threading.Lock()
        self._drift_message: str | None = None

    def require_unchanged_before_rep(self, cell: ConfirmedSubjectCell) -> None:
        """Recheck inputs before each resumed, new, or retried submission."""
        halt_error = _resource_halt_error(cell.state_path)
        if halt_error is not None:
            raise halt_error
        with self._verification_lock:
            if self._drift_message is not None:
                raise LaunchInputDriftError(self._drift_message)
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
            self._drift_message = (
                "Launch input drift: approved inputs changed before "
                f"{state_cell['cell_id']}"
            )
            raise LaunchInputDriftError(self._drift_message)


@dataclass(frozen=True, slots=True)
class _ConfirmedLaunchExecutionContext:
    """Hold plan-owned dependencies shared by confirmed execution stages."""

    state_path: Path
    results_root: Path
    state: run_state.RunStateWriter
    input_verifier: _ApprovedLaunchInputVerifier
    subject_runner: _ConfirmedSubjectRunner
    transient_resumer: LaunchTransientResumer | None
    log_path: Path
    policies: LaunchExecutionPolicies


_QUARANTINE_MANIFEST_LOCK = threading.Lock()


def _quarantine_incomplete_confirmed_cell(
    cell: ConfirmedSubjectCell,
    results_root: Path,
) -> Path | None:
    """Move result-less artifacts aside before a confirmed cell attempt."""
    cell_root = cell.result_path.parent
    if cell.result_path.exists() or not cell_root.is_dir():
        return None
    if not any(cell_root.iterdir()):
        return None

    relative_cell = cell_root.resolve().relative_to(results_root.resolve())
    attempt_id = (
        datetime.now(UTC).strftime("%Y%m%dT%H%M%SZ") + "-" + uuid.uuid4().hex[:8]
    )
    quarantine_root = (
        results_root / "_contaminated" / "harness-failure" / "incomplete-cell-attempts"
    )
    quarantine_path = quarantine_root / relative_cell / attempt_id
    quarantine_path.parent.mkdir(parents=True, exist_ok=True)
    cell_root.rename(quarantine_path)
    cell_root.mkdir(parents=True, exist_ok=True)
    verifier_resource_events = (
        quarantine_path / "logs" / "verifier-resource-events.ndjson"
    )
    if verifier_resource_events.is_file():
        retained_events = cell_root / "logs" / verifier_resource_events.name
        retained_events.parent.mkdir(parents=True, exist_ok=True)
        retained_events.write_bytes(verifier_resource_events.read_bytes())

    reason = (
        "Incomplete confirmed cell attempt had artifacts without result.json; "
        "moved before retry to prevent mixed-attempt usage and session accounting."
    )
    record = {
        "category": "harness-failure",
        "original_path": str(cell_root),
        "quarantine_path": str(quarantine_path),
        "reason": reason,
        "run_key": cell.run_key,
        "timestamp": datetime.now(UTC).isoformat(),
    }
    manifest_path = results_root / "_contaminated" / "manifest.jsonl"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    with _QUARANTINE_MANIFEST_LOCK, manifest_path.open("a") as manifest:
        manifest.write(json.dumps(record, sort_keys=True) + "\n")
    return quarantine_path


def _run_confirmed_subject_cell(
    cell: ConfirmedSubjectCell,
    subject_runner: _ConfirmedSubjectRunner,
    log_path: Path,
    results_root: Path,
) -> dict[str, object]:
    """Run one exact planned cell and persist its provenance-bearing result."""
    _quarantine_incomplete_confirmed_cell(cell, results_root)
    cell.result_path.parent.mkdir(parents=True, exist_ok=True)
    _append_confirmed_cell_log(log_path, cell, "started")
    if cell.subject == "pi":
        runner_record = cast(
            ConfirmedPiRunner,
            subject_runner,
        ).run_confirmed_pi_cell(cell)
    elif cell.subject == "omp":
        runner_record = cast(
            ConfirmedOmpRunner,
            subject_runner,
        ).run_confirmed_omp_cell(cell)
    else:
        runner_record = cast(
            ConfirmedPrimeAgentRunner,
            subject_runner,
        ).run_confirmed_prime_agent_cell(cell)
    verifier_resource_error = (
        runner_record.get("verifier_resource_exhausted") is True
        or runner_record.get("verifier_resource_evidence_unavailable") is True
    )
    if verifier_resource_error:
        _record_verifier_resource_failure(cell, runner_record)
        diagnostic = runner_record.get("verifier_resource_diagnostic")
        raise LaunchVerifierResourceError(
            "Verifier resource evidence invalid: "
            f"{cell.task}/{cell.config_identity}/rep{cell.rep}; "
            f"diagnostic={diagnostic!r}"
        )
    result_record = _confirmed_result_record(cell, runner_record)
    run_state.atomic_write_json(cell.result_path, result_record)
    _append_confirmed_cell_log(log_path, cell, "completed")
    return result_record


def _record_successful_preflight_seal(
    cell: ConfirmedSubjectCell,
    context: _ConfirmedLaunchExecutionContext,
    result_record: dict[str, object],
    *,
    reused_result: bool,
) -> confirmed_preflight.PreflightDiagnostic | None:
    """Persist result and central seal evidence as one recoverable step."""
    original_result = cell.result_path.read_bytes()
    if not reused_result:
        result_record["preflight_passed"] = True
        run_state.atomic_write_json(cell.result_path, result_record)
    try:
        config_lock.record_successful_config_preflight(
            context.state.state_root,
            config_identity=cell.config_identity,
            lock_identity=cell.config_lock_identity,
            model=cell.model,
            thinking=cell.thinking,
            launch_plan_identity=cell.launch_plan_identity,
            result_path=cell.result_path,
            result_identity=result_provenance.result_file_identity(cell.result_path),
        )
    except (OSError, TypeError, ValueError) as error:
        if not reused_result:
            cell.result_path.write_bytes(original_result)
            result_record.pop("preflight_passed", None)
        return confirmed_preflight.preflight_diagnostic(
            "config_seal_registry",
            str(context.state.state_root),
            f"{type(error).__name__}: {error}",
        )
    return None


def _execute_confirmed_preflight_cell(
    cell: ConfirmedSubjectCell,
    context: _ConfirmedLaunchExecutionContext,
) -> bool:
    """Run and atomically decide one confirmed preflight cell."""
    state = context.state
    state_cell = _confirmed_state_cell(context.state_path, cell)
    context.input_verifier.require_unchanged_before_rep(cell)
    state.preflight_started(state_cell)
    diagnostics: list[confirmed_preflight.PreflightDiagnostic] = []
    result_record: dict[str, object] = {}
    exit_code: int | str | None = None
    resumed_preflight = False
    reused_result = False
    try:
        if cell.result_path.is_file() and cell.reuse_reason is None:
            resumed_record = _require_confirmed_resume_result(cell)
            if resumed_record.get("preflight_passed") is not True:
                raise ValueError(
                    f"Result provenance mismatch: path={cell.result_path}; "
                    "confirmed resume preflight evidence is not sealed"
                )
            result_record = dict(resumed_record)
            resumed_preflight = True
        reused_result = cell.reuse_reason is not None or resumed_preflight
        if cell.reuse_reason is not None:
            _require_planned_result_reuse(cell)
            result_record = dict(result_provenance.read_result_record(cell.result_path))
        elif not resumed_preflight:
            result_record = _run_confirmed_subject_cell(
                cell,
                context.subject_runner,
                context.log_path,
                context.results_root,
            )
        raw_exit = result_record.get("agent_exit")
        exit_code = raw_exit if isinstance(raw_exit, int | str) else None
    except LaunchTransientModelError as error:
        if context.policies.transient_errors == "pause":
            state.preflight_attempt_paused(
                state_cell,
                log_path=context.log_path,
                reason=str(error),
            )
            state.run_paused(reason=str(error))
            raise
        state.preflight_finished(
            state_cell,
            log_path=context.log_path,
            exit_code=75,
            diagnostics=[
                dict(
                    confirmed_preflight.preflight_diagnostic(
                        "subject_cell",
                        "runner",
                        str(error),
                    )
                )
            ],
        )
        state.run_failed(reason=f"Confirmed preflight stopped after transient: {error}")
        raise RuntimeError(
            "Confirmed launch stopped after transient model error"
        ) from error
    except Exception as error:
        # Subject adapters may raise arbitrary provider or process failures.
        halt_error = _resource_halt_error(cell.state_path)
        if halt_error is not None:
            state.preflight_attempt_paused(
                state_cell,
                log_path=context.log_path,
                reason=str(halt_error),
            )
            raise halt_error from error
        exit_code = "exception"
        diagnostics.append(
            confirmed_preflight.preflight_diagnostic(
                "subject_cell",
                "runner",
                f"{type(error).__name__}: {error}",
            )
        )
        _append_confirmed_cell_log(
            context.log_path,
            cell,
            f"failed: {type(error).__name__}: {error}",
        )
    cell_root = cell.result_path.parent
    diagnostics.extend(
        confirmed_preflight.evaluate_generic_preflight(cell_root, result_record)
    )
    diagnostics.extend(
        confirmed_preflight.evaluate_config_preflight_contract(
            cell.config_root.parent.parent,
            cell_root,
            cell.smoke_assertions,
            result_record,
        )
    )
    passed = not diagnostics
    if passed:
        seal_diagnostic = _record_successful_preflight_seal(
            cell,
            context,
            result_record,
            reused_result=reused_result,
        )
        if seal_diagnostic is not None:
            diagnostics.append(seal_diagnostic)
            passed = False
    state.preflight_finished(
        state_cell,
        result_path=(cell.result_path if cell.result_path.is_file() else None),
        log_path=context.log_path,
        exit_code=exit_code,
        diagnostics=[dict(diagnostic) for diagnostic in diagnostics],
    )
    return passed


def _execute_confirmed_preflights(
    cells: Sequence[ConfirmedSubjectCell],
    context: _ConfirmedLaunchExecutionContext,
) -> set[Path]:
    """Run every planned preflight and stop before batch on any failure."""
    passed_paths: set[Path] = set()
    failed_count = 0
    for cell in cells:
        if _execute_confirmed_preflight_cell(cell, context):
            passed_paths.add(cell.result_path.resolve())
        else:
            failed_count += 1
    if failed_count:
        context.state.run_failed(
            reason=(
                "Preflight assertion failure: "
                f"{failed_count} cell(s) did not satisfy requirements"
            )
        )
        raise LaunchPreflightError(
            "Preflight assertion failure: batch fan-out was not started"
        )
    return passed_paths


def _execute_confirmed_batch_cell(
    cell: ConfirmedSubjectCell,
    context: _ConfirmedLaunchExecutionContext,
) -> None:
    """Run one planned batch cell and record its durable outcome."""
    state = context.state
    state_cell = _confirmed_state_cell(context.state_path, cell)
    for attempt in range(context.policies.cell_retries + 1):
        context.input_verifier.require_unchanged_before_rep(cell)
        state.cell_started(state_cell)
        try:
            result_record = _run_confirmed_subject_cell(
                cell,
                context.subject_runner,
                context.log_path,
                context.results_root,
            )
        except LaunchTransientModelError as error:
            _append_confirmed_cell_log(
                context.log_path,
                cell,
                f"paused: {error}",
            )
            state.cell_finished(
                state_cell,
                log_path=context.log_path,
                exit_code=75,
                transient_exit=75,
            )
            if context.policies.transient_errors == "pause":
                state.run_paused(reason=str(error))
                raise
            state.run_failed(reason=f"Confirmed batch stopped after transient: {error}")
            raise RuntimeError(
                "Confirmed launch stopped after transient model error"
            ) from error
        except Exception as error:
            halt_error = _resource_halt_error(cell.state_path)
            if halt_error is not None:
                _append_confirmed_cell_log(
                    context.log_path,
                    cell,
                    f"paused: {halt_error}",
                )
                state.cell_finished(
                    state_cell,
                    log_path=context.log_path,
                    exit_code="resource_halt",
                )
                raise halt_error from error
            _append_confirmed_cell_log(
                context.log_path,
                cell,
                f"failed: {type(error).__name__}: {error}",
            )
            state.cell_finished(
                state_cell,
                log_path=context.log_path,
                exit_code="exception",
            )
            if (
                attempt < context.policies.cell_retries
                and not cell.result_path.exists()
            ):
                _append_confirmed_cell_log(
                    context.log_path,
                    cell,
                    f"retrying after attempt {attempt + 1}",
                )
                continue
            state.run_failed(reason=f"Confirmed {cell.subject} cell execution failed")
            raise
        raw_exit = result_record.get("agent_exit")
        exit_code = raw_exit if isinstance(raw_exit, int | str) else None
        state.cell_finished(
            state_cell,
            result_path=cell.result_path,
            log_path=context.log_path,
            exit_code=exit_code,
        )
        return


def _require_confirmed_resume_result(
    cell: ConfirmedSubjectCell,
) -> Mapping[str, object]:
    """Require an exact compatible result created by this confirmed plan."""
    record = result_provenance.read_result_record(cell.result_path)
    expected = _confirmed_cell_provenance(cell)
    mismatches = result_provenance.result_provenance_mismatches(
        record,
        expected,
    )
    if mismatches:
        raise ValueError(
            f"Result provenance mismatch: path={cell.result_path}; "
            f"incompatible fields={mismatches!r}"
        )
    return record


def _require_planned_result_reuse(cell: ConfirmedSubjectCell) -> None:
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


def _execute_confirmed_batch_entry(
    cell: ConfirmedSubjectCell,
    passed_preflight_paths: set[Path],
    context: _ConfirmedLaunchExecutionContext,
) -> None:
    """Execute or provenance-check one approved batch cell."""
    state = context.state
    state_cell = _confirmed_state_cell(context.state_path, cell)
    if cell.result_path.resolve() in passed_preflight_paths:
        state.cell_skipped(state_cell, reason="successful_preflight")
        return
    existing_result = cell.result_path.is_file()
    if existing_result or cell.reuse_reason is not None:
        skip_reason = cell.reuse_reason or "confirmed_plan_resume"
        try:
            if cell.reuse_reason is None:
                _require_confirmed_resume_result(cell)
            else:
                _require_planned_result_reuse(cell)
        except (OSError, TypeError, ValueError) as error:
            _append_confirmed_cell_log(
                context.log_path,
                cell,
                f"failed: {type(error).__name__}: {error}",
            )
            state.run_failed(reason=str(error))
            raise
        state.cell_skipped(state_cell, reason=skip_reason)
        return
    _execute_confirmed_batch_cell(cell, context)


def _submit_confirmed_batch_cell(
    executor: concurrent.futures.ThreadPoolExecutor,
    pending_cells: Iterator[ConfirmedSubjectCell],
    futures: dict[
        concurrent.futures.Future[None],
        ConfirmedSubjectCell,
    ],
    passed_preflight_paths: set[Path],
    context: _ConfirmedLaunchExecutionContext,
) -> bool:
    """Submit the next approved cell, returning false after exhaustion."""
    try:
        cell = next(pending_cells)
    except StopIteration:
        return False
    future = executor.submit(
        _execute_confirmed_batch_entry,
        cell,
        passed_preflight_paths,
        context,
    )
    futures[future] = cell
    return True


def _completed_confirmed_batch_failure(
    completed: Iterable[concurrent.futures.Future[None]],
    futures: dict[
        concurrent.futures.Future[None],
        ConfirmedSubjectCell,
    ],
) -> Exception | None:
    """Collect completed workers and return their first observed failure."""
    first_failure: Exception | None = None
    for future in completed:
        futures.pop(future)
        try:
            future.result()
        except Exception as error:  # noqa: BLE001
            # Preserve the first arbitrary worker failure for the coordinator.
            if first_failure is None:
                first_failure = error
    return first_failure


def _execute_confirmed_batch(
    cells: Sequence[ConfirmedSubjectCell],
    passed_preflight_paths: set[Path],
    context: _ConfirmedLaunchExecutionContext,
    concurrency: int,
) -> None:
    """Fan out approved batch cells with bounded plan-owned concurrency."""
    pending_cells = iter(cells)
    futures: dict[concurrent.futures.Future[None], ConfirmedSubjectCell] = {}
    with concurrent.futures.ThreadPoolExecutor(
        max_workers=concurrency,
    ) as executor:
        for _ in range(concurrency):
            if not _submit_confirmed_batch_cell(
                executor,
                pending_cells,
                futures,
                passed_preflight_paths,
                context,
            ):
                break
        while futures:
            completed, _ = concurrent.futures.wait(
                tuple(futures),
                return_when=concurrent.futures.FIRST_COMPLETED,
            )
            first_failure = _completed_confirmed_batch_failure(
                completed,
                futures,
            )
            if first_failure is not None:
                for future in futures:
                    future.cancel()
                raise first_failure
            for _ in completed:
                if not _submit_confirmed_batch_cell(
                    executor,
                    pending_cells,
                    futures,
                    passed_preflight_paths,
                    context,
                ):
                    break


def execute_confirmed_launch_with_heartbeat(
    plan: LaunchPlan,
    *,
    confirmation_identity: str | None,
    runtime_resolver: LaunchRuntimeResolver,
    pi_runner: ConfirmedPiRunner | None,
    omp_runner: ConfirmedOmpRunner | None,
    prime_agent_runner: ConfirmedPrimeAgentRunner | None,
    transient_resumer: LaunchTransientResumer | None,
    heartbeat_interval_s: float,
) -> ConfirmedLaunchExecution:
    """Execute atomic preflight and conditional fan-out for one exact plan."""
    document = _confirmed_plan_document(plan, confirmation_identity)
    launch_request = _confirmed_launch_request(document)
    subject = document["subject"]["name"]
    if subject == "pi":
        if pi_runner is None:
            raise ValueError(
                "Confirmed Pi runner missing: a Pi plan requires pi_runner"
            )
        subject_runner: _ConfirmedSubjectRunner = pi_runner
    elif subject == "omp":
        if omp_runner is None:
            raise ValueError(
                "Confirmed OMP runner missing: an OMP plan requires omp_runner"
            )
        subject_runner = omp_runner
    elif subject == "prime-agent":
        if prime_agent_runner is None:
            raise ValueError(
                "Confirmed Prime Agent runner missing: a Prime Agent plan "
                "requires prime_agent_runner"
            )
        subject_runner = prime_agent_runner
    else:
        raise ValueError(
            f"Confirmed subject runner missing: unsupported subject {subject!r}"
        )
    batch_cells = _confirmed_subject_cells(document, "batchCells")
    preflight_cells = _confirmed_subject_cells(document, "preflightCells")
    if not batch_cells:
        raise ValueError("Confirmed subject execution cells invalid: batch is empty")
    state_path = Path(document["paths"]["statePath"])
    expected_state_path = (
        Path(document["paths"]["stateRoot"])
        / confirmed_launch_run_key(
            document["runId"],
            document["planIdentity"],
        )
    ).resolve()
    if state_path.resolve() != expected_state_path:
        raise ValueError(
            "Confirmed launch state path mismatch: "
            f"planned={str(state_path)!r}, "
            f"expected={str(expected_state_path)!r}"
        )
    log_path = _confirmed_launch_log_path(state_path, subject)
    manifest = _confirmed_run_manifest(
        document,
        batch_cells,
        preflight_cells,
        state_path,
    )
    state = run_state.RunStateWriter(document["paths"]["stateRoot"], manifest)
    stored_plan_path = state_path / "launch-plan.json"
    if stored_plan_path.is_file():
        stored_plan = parse_launch_plan_json(stored_plan_path.read_text())
        if stored_plan.identity != plan.identity:
            raise ValueError(
                "Launch plan mismatch: registered state belongs to "
                f"{stored_plan.identity}, not {plan.identity}"
            )
        state.resume()
    else:
        state.start()
    stored_plan_path.write_text(plan.canonical_json)
    log_path.parent.mkdir(parents=True, exist_ok=True)
    subject_label = {
        "pi": "Pi",
        "omp": "OMP",
        "prime-agent": "Prime Agent",
    }[subject]
    log_path.write_text(
        f"Confirmed {subject_label} cell execution\n"
        f"launch_plan_identity={document['planIdentity']}\n"
    )
    input_verifier = _ApprovedLaunchInputVerifier(
        document,
        state,
        runtime_resolver,
    )
    execution_context = _ConfirmedLaunchExecutionContext(
        state_path=state_path,
        results_root=Path(document["paths"]["resultsRoot"]),
        state=state,
        input_verifier=input_verifier,
        subject_runner=subject_runner,
        transient_resumer=transient_resumer,
        log_path=log_path,
        policies=launch_request.policies,
    )

    state.start_heartbeat(heartbeat_interval_s)
    try:
        while True:
            try:
                passed_preflight_paths = _execute_confirmed_preflights(
                    preflight_cells,
                    execution_context,
                )
                _execute_confirmed_batch(
                    batch_cells,
                    passed_preflight_paths,
                    execution_context,
                    launch_request.concurrency,
                )
            except LaunchResourceHaltError as error:
                state.run_paused(reason=str(error))
                raise
            except LaunchTransientModelError:
                if (
                    not launch_request.policies.auto_resume
                    or execution_context.transient_resumer is None
                ):
                    raise
                decision = execution_context.transient_resumer.on_transient_pause(state)
                if decision.get("retry") is not True:
                    raise
                state.run_resumed(
                    reason=str(decision.get("reason", "transient cleared"))
                )
                continue
            break
        state.run_completed()
        return ConfirmedLaunchExecution(
            result_path=batch_cells[0].result_path,
            state_path=state_path,
            log_path=log_path,
        )
    finally:
        state.stop_heartbeat()
