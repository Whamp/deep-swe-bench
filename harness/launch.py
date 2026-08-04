"""Preserve the public seam for confirmed launch planning and execution."""

from harness.launch_contract import (  # noqa: F401 - public re-exports
    CompiledLaunch,
    ConfirmedLaunchExecution,
    ConfirmedOmpCell,
    ConfirmedOmpRunner,
    ConfirmedPiCell,
    ConfirmedPiRunner,
    ConfirmedSubjectCell,
    ExplicitResultReuseDecision,
    LaunchClarificationError,
    LaunchConfigDocument,
    LaunchCountsDocument,
    LaunchExecutionPolicies,
    LaunchInputDriftError,
    LaunchPathsDocument,
    LaunchPlan,
    LaunchPlanDocument,
    LaunchPreflightError,
    LaunchRequest,
    LaunchResourceDocument,
    LaunchResourceHaltError,
    LaunchResourcePolicy,
    LaunchRuntimeDocument,
    LaunchRuntimeIdentity,
    LaunchRuntimeResolver,
    LaunchSubjectDocument,
    LaunchTaskSelection,
    LaunchTransientModelError,
    LaunchTransientResumer,
)
from harness.launch_execution import execute_confirmed_launch_with_heartbeat
from harness.launch_planning import (  # noqa: F401 - public re-exports
    canonical_launch_plan_json,
    compile_launch_request,
    confirmed_launch_run_key,
    parse_launch_plan_json,
)
from harness.launch_runtime import RepositoryLaunchRuntimeResolver  # noqa: F401

_CONFIRMED_HEARTBEAT_INTERVAL_S = 15.0


def execute_confirmed_launch(
    plan: LaunchPlan,
    *,
    confirmation_identity: str | None,
    runtime_resolver: LaunchRuntimeResolver,
    pi_runner: ConfirmedPiRunner | None = None,
    omp_runner: ConfirmedOmpRunner | None = None,
    transient_resumer: LaunchTransientResumer | None = None,
) -> ConfirmedLaunchExecution:
    """Execute one plan using the public heartbeat test and tuning seam."""
    return execute_confirmed_launch_with_heartbeat(
        plan,
        confirmation_identity=confirmation_identity,
        runtime_resolver=runtime_resolver,
        pi_runner=pi_runner,
        omp_runner=omp_runner,
        transient_resumer=transient_resumer,
        heartbeat_interval_s=_CONFIRMED_HEARTBEAT_INTERVAL_S,
    )
